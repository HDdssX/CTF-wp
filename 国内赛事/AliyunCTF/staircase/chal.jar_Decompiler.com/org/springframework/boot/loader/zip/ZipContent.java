package org.springframework.boot.loader.zip;

import java.io.Closeable;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.ref.SoftReference;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedChannelException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.zip.ZipEntry;
import org.springframework.boot.loader.log.DebugLogger;

public final class ZipContent implements Closeable {
   private static final String META_INF = "META-INF/";
   private static final byte[] SIGNATURE_SUFFIX;
   private static final DebugLogger debug;
   private static final Map<ZipContent.Source, ZipContent> cache;
   private final ZipContent.Source source;
   private final FileChannelDataBlock data;
   private final long centralDirectoryPos;
   private final long commentPos;
   private final long commentLength;
   private final int[] lookupIndexes;
   private final int[] nameHashLookups;
   private final int[] relativeCentralDirectoryOffsetLookups;
   private final NameOffsetLookups nameOffsetLookups;
   private final boolean hasJarSignatureFile;
   private SoftReference<CloseableDataBlock> virtualData;
   private SoftReference<Map<Class<?>, Object>> info;

   private ZipContent(ZipContent.Source source, FileChannelDataBlock data, long centralDirectoryPos, long commentPos, long commentLength, int[] lookupIndexes, int[] nameHashLookups, int[] relativeCentralDirectoryOffsetLookups, NameOffsetLookups nameOffsetLookups, boolean hasJarSignatureFile) {
      this.source = source;
      this.data = data;
      this.centralDirectoryPos = centralDirectoryPos;
      this.commentPos = commentPos;
      this.commentLength = commentLength;
      this.lookupIndexes = lookupIndexes;
      this.nameHashLookups = nameHashLookups;
      this.relativeCentralDirectoryOffsetLookups = relativeCentralDirectoryOffsetLookups;
      this.nameOffsetLookups = nameOffsetLookups;
      this.hasJarSignatureFile = hasJarSignatureFile;
   }

   public CloseableDataBlock openRawZipData() throws IOException {
      this.data.open();
      return (CloseableDataBlock)(!this.nameOffsetLookups.hasAnyEnabled() ? this.data : this.getVirtualData());
   }

   private CloseableDataBlock getVirtualData() throws IOException {
      CloseableDataBlock virtualData = this.virtualData != null ? (CloseableDataBlock)this.virtualData.get() : null;
      if (virtualData != null) {
         return virtualData;
      } else {
         virtualData = this.createVirtualData();
         this.virtualData = new SoftReference(virtualData);
         return virtualData;
      }
   }

   private CloseableDataBlock createVirtualData() throws IOException {
      int size = this.size();
      NameOffsetLookups nameOffsetLookups = this.nameOffsetLookups.emptyCopy();
      ZipCentralDirectoryFileHeaderRecord[] centralRecords = new ZipCentralDirectoryFileHeaderRecord[size];
      long[] centralRecordPositions = new long[size];

      for(int i = 0; i < size; ++i) {
         int lookupIndex = this.lookupIndexes[i];
         long pos = this.getCentralDirectoryFileHeaderRecordPos(lookupIndex);
         nameOffsetLookups.enable(i, this.nameOffsetLookups.isEnabled(lookupIndex));
         centralRecords[i] = ZipCentralDirectoryFileHeaderRecord.load(this.data, pos);
         centralRecordPositions[i] = pos;
      }

      return new VirtualZipDataBlock(this.data, nameOffsetLookups, centralRecords, centralRecordPositions);
   }

   public int size() {
      return this.lookupIndexes.length;
   }

   public String getComment() {
      try {
         return ZipString.readString(this.data, this.commentPos, this.commentLength);
      } catch (UncheckedIOException var2) {
         if (var2.getCause() instanceof ClosedChannelException) {
            throw new IllegalStateException("Zip content closed", var2);
         } else {
            throw var2;
         }
      }
   }

   public ZipContent.Entry getEntry(CharSequence name) {
      return this.getEntry((CharSequence)null, name);
   }

   public ZipContent.Entry getEntry(CharSequence namePrefix, CharSequence name) {
      int nameHash = this.nameHash(namePrefix, name);
      int lookupIndex = this.getFirstLookupIndex(nameHash);

      for(int size = this.size(); lookupIndex >= 0 && lookupIndex < size && this.nameHashLookups[lookupIndex] == nameHash; ++lookupIndex) {
         long pos = this.getCentralDirectoryFileHeaderRecordPos(lookupIndex);
         ZipCentralDirectoryFileHeaderRecord centralRecord = this.loadZipCentralDirectoryFileHeaderRecord(pos);
         if (this.hasName(lookupIndex, centralRecord, pos, namePrefix, name)) {
            return new ZipContent.Entry(lookupIndex, centralRecord);
         }
      }

      return null;
   }

   public boolean hasEntry(CharSequence namePrefix, CharSequence name) {
      int nameHash = this.nameHash(namePrefix, name);
      int lookupIndex = this.getFirstLookupIndex(nameHash);

      for(int size = this.size(); lookupIndex >= 0 && lookupIndex < size && this.nameHashLookups[lookupIndex] == nameHash; ++lookupIndex) {
         long pos = this.getCentralDirectoryFileHeaderRecordPos(lookupIndex);
         ZipCentralDirectoryFileHeaderRecord centralRecord = this.loadZipCentralDirectoryFileHeaderRecord(pos);
         if (this.hasName(lookupIndex, centralRecord, pos, namePrefix, name)) {
            return true;
         }
      }

      return false;
   }

   public ZipContent.Entry getEntry(int index) {
      int lookupIndex = this.lookupIndexes[index];
      long pos = this.getCentralDirectoryFileHeaderRecordPos(lookupIndex);
      ZipCentralDirectoryFileHeaderRecord centralRecord = this.loadZipCentralDirectoryFileHeaderRecord(pos);
      return new ZipContent.Entry(lookupIndex, centralRecord);
   }

   private ZipCentralDirectoryFileHeaderRecord loadZipCentralDirectoryFileHeaderRecord(long pos) {
      try {
         return ZipCentralDirectoryFileHeaderRecord.load(this.data, pos);
      } catch (IOException var4) {
         if (var4 instanceof ClosedChannelException) {
            throw new IllegalStateException("Zip content closed", var4);
         } else {
            throw new UncheckedIOException(var4);
         }
      }
   }

   private int nameHash(CharSequence namePrefix, CharSequence name) {
      int nameHash = 0;
      int nameHash = namePrefix != null ? ZipString.hash(nameHash, namePrefix, false) : nameHash;
      nameHash = ZipString.hash(nameHash, name, true);
      return nameHash;
   }

   private int getFirstLookupIndex(int nameHash) {
      int lookupIndex = Arrays.binarySearch(this.nameHashLookups, 0, this.nameHashLookups.length, nameHash);
      if (lookupIndex < 0) {
         return -1;
      } else {
         while(lookupIndex > 0 && this.nameHashLookups[lookupIndex - 1] == nameHash) {
            --lookupIndex;
         }

         return lookupIndex;
      }
   }

   private long getCentralDirectoryFileHeaderRecordPos(int lookupIndex) {
      return this.centralDirectoryPos + (long)this.relativeCentralDirectoryOffsetLookups[lookupIndex];
   }

   private boolean hasName(int lookupIndex, ZipCentralDirectoryFileHeaderRecord centralRecord, long pos, CharSequence namePrefix, CharSequence name) {
      int offset = this.nameOffsetLookups.get(lookupIndex);
      pos += (long)(46 + offset);
      int len = centralRecord.fileNameLength() - offset;
      ByteBuffer buffer = ByteBuffer.allocate(256);
      if (namePrefix != null) {
         int startsWithNamePrefix = ZipString.startsWith(buffer, this.data, pos, len, namePrefix);
         if (startsWithNamePrefix == -1) {
            return false;
         }

         pos += (long)startsWithNamePrefix;
         len -= startsWithNamePrefix;
      }

      return ZipString.matches(buffer, this.data, pos, len, name, true);
   }

   public <I> I getInfo(Class<I> type, Function<ZipContent, I> function) {
      Map<Class<?>, Object> info = this.info != null ? (Map)this.info.get() : null;
      if (info == null) {
         info = new ConcurrentHashMap();
         this.info = new SoftReference(info);
      }

      return ((Map)info).computeIfAbsent(type, (key) -> {
         debug.log("Getting %s info from zip '%s'", type.getName(), this);
         return function.apply(this);
      });
   }

   public boolean hasJarSignatureFile() {
      return this.hasJarSignatureFile;
   }

   public void close() throws IOException {
      this.data.close();
   }

   public String toString() {
      return this.source.toString();
   }

   public static ZipContent open(Path path) throws IOException {
      return open(new ZipContent.Source(path.toAbsolutePath(), (String)null));
   }

   public static ZipContent open(Path path, String nestedEntryName) throws IOException {
      return open(new ZipContent.Source(path.toAbsolutePath(), nestedEntryName));
   }

   private static ZipContent open(ZipContent.Source source) throws IOException {
      ZipContent zipContent = (ZipContent)cache.get(source);
      if (zipContent != null) {
         debug.log("Opening existing cached zip content for %s", zipContent);
         zipContent.data.open();
         return zipContent;
      } else {
         debug.log("Loading zip content from %s", source);
         zipContent = ZipContent.Loader.load(source);
         ZipContent previouslyCached = (ZipContent)cache.putIfAbsent(source, zipContent);
         if (previouslyCached != null) {
            debug.log("Closing zip content from %s since cache was populated from another thread", source);
            zipContent.close();
            previouslyCached.data.open();
            return previouslyCached;
         } else {
            return zipContent;
         }
      }
   }

   static {
      SIGNATURE_SUFFIX = ".DSA".getBytes(StandardCharsets.UTF_8);
      debug = DebugLogger.get(ZipContent.class);
      cache = new ConcurrentHashMap();
   }

   private static record Source(Path path, String nestedEntryName) {
      private Source(Path path, String nestedEntryName) {
         this.path = path;
         this.nestedEntryName = nestedEntryName;
      }

      boolean isNested() {
         return this.nestedEntryName != null;
      }

      public String toString() {
         return !this.isNested() ? this.path().toString() : this.path() + "[" + this.nestedEntryName() + "]";
      }

      public Path path() {
         return this.path;
      }

      public String nestedEntryName() {
         return this.nestedEntryName;
      }
   }

   public class Entry {
      private final int lookupIndex;
      private final ZipCentralDirectoryFileHeaderRecord centralRecord;
      private volatile String name;
      private volatile FileChannelDataBlock content;

      Entry(int lookupIndex, ZipCentralDirectoryFileHeaderRecord centralRecord) {
         this.lookupIndex = lookupIndex;
         this.centralRecord = centralRecord;
      }

      public int getLookupIndex() {
         return this.lookupIndex;
      }

      public boolean isDirectory() {
         return this.getName().endsWith("/");
      }

      public boolean hasNameStartingWith(CharSequence prefix) {
         String name = this.name;
         if (name != null) {
            return name.startsWith(prefix.toString());
         } else {
            long pos = ZipContent.this.getCentralDirectoryFileHeaderRecordPos(this.lookupIndex) + 46L;
            return ZipString.startsWith((ByteBuffer)null, ZipContent.this.data, pos, this.centralRecord.fileNameLength(), prefix) != -1;
         }
      }

      public String getName() {
         String name = this.name;
         if (name == null) {
            int offset = ZipContent.this.nameOffsetLookups.get(this.lookupIndex);
            long pos = ZipContent.this.getCentralDirectoryFileHeaderRecordPos(this.lookupIndex) + 46L + (long)offset;
            name = ZipString.readString(ZipContent.this.data, pos, (long)(this.centralRecord.fileNameLength() - offset));
            this.name = name;
         }

         return name;
      }

      public int getCompressionMethod() {
         return this.centralRecord.compressionMethod();
      }

      public int getUncompressedSize() {
         return this.centralRecord.uncompressedSize();
      }

      public CloseableDataBlock openContent() throws IOException {
         FileChannelDataBlock content = this.getContent();
         content.open();
         return content;
      }

      private FileChannelDataBlock getContent() throws IOException {
         FileChannelDataBlock content = this.content;
         if (content == null) {
            int pos = this.centralRecord.offsetToLocalHeader();
            this.checkNotZip64Extended(pos);
            ZipLocalFileHeaderRecord localHeader = ZipLocalFileHeaderRecord.load(ZipContent.this.data, (long)pos);
            int size = this.centralRecord.compressedSize();
            this.checkNotZip64Extended(size);
            content = ZipContent.this.data.slice((long)pos + localHeader.size(), (long)size);
            this.content = content;
         }

         return content;
      }

      private void checkNotZip64Extended(int value) throws IOException {
         if (value == -1) {
            throw new IOException("Zip64 extended information extra fields are not supported");
         }
      }

      public <E extends ZipEntry> E as(Function<String, E> factory) {
         return this.as((entry, name) -> {
            return (ZipEntry)factory.apply(name);
         });
      }

      public <E extends ZipEntry> E as(BiFunction<ZipContent.Entry, String, E> factory) {
         try {
            E result = (ZipEntry)factory.apply(this, this.getName());
            long pos = ZipContent.this.getCentralDirectoryFileHeaderRecordPos(this.lookupIndex);
            this.centralRecord.copyTo(ZipContent.this.data, pos, result);
            return result;
         } catch (IOException var5) {
            throw new UncheckedIOException(var5);
         }
      }
   }

   private static final class Loader {
      private final ByteBuffer buffer = ByteBuffer.allocate(256);
      private final ZipContent.Source source;
      private final FileChannelDataBlock data;
      private final long centralDirectoryPos;
      private final int[] index;
      private int[] nameHashLookups;
      private int[] relativeCentralDirectoryOffsetLookups;
      private final NameOffsetLookups nameOffsetLookups;
      private int cursor;

      private Loader(ZipContent.Source source, ZipContent.Entry directoryEntry, FileChannelDataBlock data, long centralDirectoryPos, int maxSize) {
         this.source = source;
         this.data = data;
         this.centralDirectoryPos = centralDirectoryPos;
         this.index = new int[maxSize];
         this.nameHashLookups = new int[maxSize];
         this.relativeCentralDirectoryOffsetLookups = new int[maxSize];
         this.nameOffsetLookups = directoryEntry != null ? new NameOffsetLookups(directoryEntry.getName().length(), maxSize) : NameOffsetLookups.NONE;
      }

      private void add(ZipCentralDirectoryFileHeaderRecord centralRecord, long pos, boolean enableNameOffset) throws IOException {
         int nameOffset = this.nameOffsetLookups.enable(this.cursor, enableNameOffset);
         int hash = ZipString.hash(this.buffer, this.data, pos + 46L + (long)nameOffset, centralRecord.fileNameLength() - nameOffset, true);
         this.nameHashLookups[this.cursor] = hash;
         this.relativeCentralDirectoryOffsetLookups[this.cursor] = (int)(pos - this.centralDirectoryPos);
         this.index[this.cursor] = this.cursor++;
      }

      private ZipContent finish(long commentPos, long commentLength, boolean hasJarSignatureFile) {
         if (this.cursor != this.nameHashLookups.length) {
            this.nameHashLookups = Arrays.copyOf(this.nameHashLookups, this.cursor);
            this.relativeCentralDirectoryOffsetLookups = Arrays.copyOf(this.relativeCentralDirectoryOffsetLookups, this.cursor);
         }

         int size = this.nameHashLookups.length;
         this.sort(0, size - 1);
         int[] lookupIndexes = new int[size];

         for(int i = 0; i < size; lookupIndexes[this.index[i]] = i++) {
         }

         return new ZipContent(this.source, this.data, this.centralDirectoryPos, commentPos, commentLength, lookupIndexes, this.nameHashLookups, this.relativeCentralDirectoryOffsetLookups, this.nameOffsetLookups, hasJarSignatureFile);
      }

      private void sort(int left, int right) {
         if (left < right) {
            int pivot = this.nameHashLookups[left + (right - left) / 2];
            int i = left;
            int j = right;

            while(i <= j) {
               while(this.nameHashLookups[i] < pivot) {
                  ++i;
               }

               while(this.nameHashLookups[j] > pivot) {
                  --j;
               }

               if (i <= j) {
                  this.swap(i, j);
                  ++i;
                  --j;
               }
            }

            if (left < j) {
               this.sort(left, j);
            }

            if (right > i) {
               this.sort(i, right);
            }
         }

      }

      private void swap(int i, int j) {
         swap(this.index, i, j);
         swap(this.nameHashLookups, i, j);
         swap(this.relativeCentralDirectoryOffsetLookups, i, j);
         this.nameOffsetLookups.swap(i, j);
      }

      private static void swap(int[] array, int i, int j) {
         int temp = array[i];
         array[i] = array[j];
         array[j] = temp;
      }

      static ZipContent load(ZipContent.Source source) throws IOException {
         if (!source.isNested()) {
            return loadNonNested(source);
         } else {
            ZipContent zip = ZipContent.open(source.path());

            ZipContent var3;
            try {
               ZipContent.Entry entry = zip.getEntry(source.nestedEntryName());
               if (entry == null) {
                  throw new IOException("Nested entry '%s' not found in container zip '%s'".formatted(new Object[]{source.nestedEntryName(), source.path()}));
               }

               var3 = !entry.isDirectory() ? loadNestedZip(source, entry) : loadNestedDirectory(source, zip, entry);
            } catch (Throwable var5) {
               if (zip != null) {
                  try {
                     zip.close();
                  } catch (Throwable var4) {
                     var5.addSuppressed(var4);
                  }
               }

               throw var5;
            }

            if (zip != null) {
               zip.close();
            }

            return var3;
         }
      }

      private static ZipContent loadNonNested(ZipContent.Source source) throws IOException {
         ZipContent.debug.log("Loading non-nested zip '%s'", source.path());
         return openAndLoad(source, new FileChannelDataBlock(source.path()));
      }

      private static ZipContent loadNestedZip(ZipContent.Source source, ZipContent.Entry entry) throws IOException {
         if (entry.centralRecord.compressionMethod() != 0) {
            throw new IOException("Nested entry '%s' in container zip '%s' must not be compressed".formatted(new Object[]{source.nestedEntryName(), source.path()}));
         } else {
            ZipContent.debug.log("Loading nested zip entry '%s' from '%s'", source.nestedEntryName(), source.path());
            return openAndLoad(source, entry.getContent());
         }
      }

      private static ZipContent openAndLoad(ZipContent.Source source, FileChannelDataBlock data) throws IOException {
         try {
            data.open();
            return loadContent(source, data);
         } catch (RuntimeException | IOException var3) {
            data.close();
            throw var3;
         }
      }

      private static ZipContent loadContent(ZipContent.Source source, FileChannelDataBlock data) throws IOException {
         ZipEndOfCentralDirectoryRecord.Located locatedEocd = ZipEndOfCentralDirectoryRecord.load(data);
         ZipEndOfCentralDirectoryRecord eocd = locatedEocd.endOfCentralDirectoryRecord();
         long eocdPos = locatedEocd.pos();
         Zip64EndOfCentralDirectoryLocator zip64Locator = Zip64EndOfCentralDirectoryLocator.find(data, eocdPos);
         Zip64EndOfCentralDirectoryRecord zip64Eocd = Zip64EndOfCentralDirectoryRecord.load(data, zip64Locator);
         data = data.slice(getStartOfZipContent(data, eocd, zip64Eocd));
         long centralDirectoryPos = zip64Eocd != null ? zip64Eocd.offsetToStartOfCentralDirectory() : (long)eocd.offsetToStartOfCentralDirectory();
         long numberOfEntries = zip64Eocd != null ? zip64Eocd.totalNumberOfCentralDirectoryEntries() : (long)eocd.totalNumberOfCentralDirectoryEntries();
         if (numberOfEntries > 4294967295L) {
            throw new IllegalStateException("Too many zip entries in " + source);
         } else {
            ZipContent.Loader loader = new ZipContent.Loader(source, (ZipContent.Entry)null, data, centralDirectoryPos, (int)(numberOfEntries & 4294967295L));
            ByteBuffer signatureNameSuffixBuffer = ByteBuffer.allocate(ZipContent.SIGNATURE_SUFFIX.length);
            boolean hasJarSignatureFile = false;
            long pos = centralDirectoryPos;

            for(int i = 0; (long)i < numberOfEntries; ++i) {
               ZipCentralDirectoryFileHeaderRecord centralRecord = ZipCentralDirectoryFileHeaderRecord.load(data, pos);
               if (!hasJarSignatureFile) {
                  long filenamePos = pos + 46L;
                  if (centralRecord.fileNameLength() > ZipContent.SIGNATURE_SUFFIX.length && ZipString.startsWith(loader.buffer, data, filenamePos, centralRecord.fileNameLength(), "META-INF/") >= 0) {
                     signatureNameSuffixBuffer.clear();
                     data.readFully(signatureNameSuffixBuffer, filenamePos + (long)centralRecord.fileNameLength() - (long)ZipContent.SIGNATURE_SUFFIX.length);
                     hasJarSignatureFile = Arrays.equals(ZipContent.SIGNATURE_SUFFIX, signatureNameSuffixBuffer.array());
                  }
               }

               loader.add(centralRecord, pos, false);
               pos += centralRecord.size();
            }

            long commentPos = locatedEocd.pos() + 22L;
            return loader.finish(commentPos, (long)eocd.commentLength(), hasJarSignatureFile);
         }
      }

      private static long getStartOfZipContent(FileChannelDataBlock data, ZipEndOfCentralDirectoryRecord eocd, Zip64EndOfCentralDirectoryRecord zip64Eocd) throws IOException {
         long specifiedOffsetToStartOfCentralDirectory = zip64Eocd != null ? zip64Eocd.offsetToStartOfCentralDirectory() : (long)eocd.offsetToStartOfCentralDirectory();
         long sizeOfCentralDirectoryAndEndRecords = getSizeOfCentralDirectoryAndEndRecords(eocd, zip64Eocd);
         long actualOffsetToStartOfCentralDirectory = data.size() - sizeOfCentralDirectoryAndEndRecords;
         return actualOffsetToStartOfCentralDirectory - specifiedOffsetToStartOfCentralDirectory;
      }

      private static long getSizeOfCentralDirectoryAndEndRecords(ZipEndOfCentralDirectoryRecord eocd, Zip64EndOfCentralDirectoryRecord zip64Eocd) {
         long result = 0L;
         result += eocd.size();
         if (zip64Eocd != null) {
            result += 20L;
            result += zip64Eocd.size();
         }

         result += zip64Eocd != null ? zip64Eocd.sizeOfCentralDirectory() : (long)eocd.sizeOfCentralDirectory();
         return result;
      }

      private static ZipContent loadNestedDirectory(ZipContent.Source source, ZipContent zip, ZipContent.Entry directoryEntry) throws IOException {
         ZipContent.debug.log("Loading nested directry entry '%s' from '%s'", source.nestedEntryName(), source.path());
         if (!source.nestedEntryName().endsWith("/")) {
            throw new IllegalArgumentException("Nested entry name must end with '/'");
         } else {
            String directoryName = directoryEntry.getName();
            zip.data.open();

            try {
               ZipContent.Loader loader = new ZipContent.Loader(source, directoryEntry, zip.data, zip.centralDirectoryPos, zip.size());

               for(int cursor = 0; cursor < zip.size(); ++cursor) {
                  int index = zip.lookupIndexes[cursor];
                  if (index != directoryEntry.getLookupIndex()) {
                     long pos = zip.getCentralDirectoryFileHeaderRecordPos(index);
                     ZipCentralDirectoryFileHeaderRecord centralRecord = ZipCentralDirectoryFileHeaderRecord.load(zip.data, pos);
                     long namePos = pos + 46L;
                     short nameLen = centralRecord.fileNameLength();
                     if (ZipString.startsWith(loader.buffer, zip.data, namePos, nameLen, "META-INF/") != -1) {
                        loader.add(centralRecord, pos, false);
                     } else if (ZipString.startsWith(loader.buffer, zip.data, namePos, nameLen, directoryName) != -1) {
                        loader.add(centralRecord, pos, true);
                     }
                  }
               }

               return loader.finish(zip.commentPos, zip.commentLength, zip.hasJarSignatureFile);
            } catch (RuntimeException | IOException var13) {
               zip.data.close();
               throw var13;
            }
         }
      }
   }
}
