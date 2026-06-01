package org.springframework.boot.loader.jar;

import java.io.File;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.lang.Runtime.Version;
import java.lang.ref.Cleaner.Cleanable;
import java.nio.ByteBuffer;
import java.nio.file.attribute.FileTime;
import java.security.CodeSigner;
import java.security.cert.Certificate;
import java.time.LocalDateTime;
import java.util.Enumeration;
import java.util.NoSuchElementException;
import java.util.Objects;
import java.util.Spliterators.AbstractSpliterator;
import java.util.function.Consumer;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.Inflater;
import java.util.zip.ZipEntry;
import java.util.zip.ZipException;
import org.springframework.boot.loader.log.DebugLogger;
import org.springframework.boot.loader.ref.Cleaner;
import org.springframework.boot.loader.zip.CloseableDataBlock;
import org.springframework.boot.loader.zip.ZipContent;

public class NestedJarFile extends JarFile {
   private static final int DECIMAL = 10;
   private static final String META_INF = "META-INF/";
   static final String META_INF_VERSIONS = "META-INF/versions/";
   static final int BASE_VERSION = baseVersion().feature();
   private static final DebugLogger debug = DebugLogger.get(NestedJarFile.class);
   private final Cleaner cleaner;
   private final NestedJarFileResources resources;
   private final Cleanable cleanup;
   private final String name;
   private final int version;
   private volatile NestedJarFile.NestedJarEntry lastEntry;
   private volatile boolean closed;
   private volatile ManifestInfo manifestInfo;
   private volatile MetaInfVersionsInfo metaInfVersionsInfo;

   NestedJarFile(File file) throws IOException {
      this(file, (String)null, (Version)null, false, Cleaner.instance);
   }

   public NestedJarFile(File file, String nestedEntryName) throws IOException {
      this(file, nestedEntryName, (Version)null, true, Cleaner.instance);
   }

   public NestedJarFile(File file, String nestedEntryName, Version version) throws IOException {
      this(file, nestedEntryName, version, true, Cleaner.instance);
   }

   NestedJarFile(File file, String nestedEntryName, Version version, boolean onlyNestedJars, Cleaner cleaner) throws IOException {
      super(file);
      if (onlyNestedJars && (nestedEntryName == null || nestedEntryName.isEmpty())) {
         throw new IllegalArgumentException("nestedEntryName must not be empty");
      } else {
         debug.log("Created nested jar file (%s, %s, %s)", file, nestedEntryName, version);
         this.cleaner = cleaner;
         this.resources = new NestedJarFileResources(file, nestedEntryName);
         this.cleanup = cleaner.register(this, this.resources);
         String var10001 = file.getPath();
         this.name = var10001 + (nestedEntryName != null ? "!/" + nestedEntryName : "");
         this.version = version != null ? version.feature() : baseVersion().feature();
      }
   }

   public InputStream getRawZipDataInputStream() throws IOException {
      NestedJarFile.RawZipDataInputStream inputStream = new NestedJarFile.RawZipDataInputStream(this.resources.zipContent().openRawZipData().asInputStream());
      this.resources.addInputStream(inputStream);
      return inputStream;
   }

   public Manifest getManifest() throws IOException {
      try {
         return ((ManifestInfo)this.resources.zipContent().getInfo(ManifestInfo.class, this::getManifestInfo)).getManifest();
      } catch (UncheckedIOException var2) {
         throw var2.getCause();
      }
   }

   public Enumeration<JarEntry> entries() {
      synchronized(this) {
         this.ensureOpen();
         return new NestedJarFile.JarEntriesEnumeration(this.resources.zipContent());
      }
   }

   public Stream<JarEntry> stream() {
      synchronized(this) {
         this.ensureOpen();
         return this.streamContentEntries().map((x$0) -> {
            return new NestedJarFile.NestedJarEntry(x$0);
         });
      }
   }

   public Stream<JarEntry> versionedStream() {
      synchronized(this) {
         this.ensureOpen();
         return this.streamContentEntries().map(this::getBaseName).filter(Objects::nonNull).distinct().map(this::getJarEntry).filter(Objects::nonNull);
      }
   }

   private Stream<ZipContent.Entry> streamContentEntries() {
      NestedJarFile.ZipContentEntriesSpliterator spliterator = new NestedJarFile.ZipContentEntriesSpliterator(this.resources.zipContent());
      return StreamSupport.stream(spliterator, false);
   }

   private String getBaseName(ZipContent.Entry contentEntry) {
      String name = contentEntry.getName();
      if (!name.startsWith("META-INF/versions/")) {
         return name;
      } else {
         int versionNumberStartIndex = "META-INF/versions/".length();
         int versionNumberEndIndex = versionNumberStartIndex != -1 ? name.indexOf(47, versionNumberStartIndex) : -1;
         if (versionNumberEndIndex != -1 && versionNumberEndIndex != name.length() - 1) {
            try {
               int versionNumber = Integer.parseInt(name, versionNumberStartIndex, versionNumberEndIndex, 10);
               if (versionNumber > this.version) {
                  return null;
               }
            } catch (NumberFormatException var6) {
               return null;
            }

            return name.substring(versionNumberEndIndex + 1);
         } else {
            return null;
         }
      }
   }

   public JarEntry getJarEntry(String name) {
      return this.getNestedJarEntry(name);
   }

   public JarEntry getEntry(String name) {
      return this.getNestedJarEntry(name);
   }

   public boolean hasEntry(String name) {
      NestedJarFile.NestedJarEntry lastEntry = this.lastEntry;
      if (lastEntry != null && name.equals(lastEntry.getName())) {
         return true;
      } else {
         ZipContent.Entry entry = this.getVersionedContentEntry(name);
         if (entry != null) {
            return true;
         } else {
            synchronized(this) {
               this.ensureOpen();
               return this.resources.zipContent().hasEntry((CharSequence)null, name);
            }
         }
      }
   }

   private NestedJarFile.NestedJarEntry getNestedJarEntry(String name) {
      Objects.requireNonNull(name, "name");
      NestedJarFile.NestedJarEntry lastEntry = this.lastEntry;
      if (lastEntry != null && name.equals(lastEntry.getName())) {
         return lastEntry;
      } else {
         ZipContent.Entry entry = this.getVersionedContentEntry(name);
         entry = entry != null ? entry : this.getContentEntry((String)null, name);
         if (entry == null) {
            return null;
         } else {
            NestedJarFile.NestedJarEntry nestedJarEntry = new NestedJarFile.NestedJarEntry(entry, name);
            this.lastEntry = nestedJarEntry;
            return nestedJarEntry;
         }
      }
   }

   private ZipContent.Entry getVersionedContentEntry(String name) {
      if (BASE_VERSION < this.version && !name.startsWith("META-INF/") && this.getManifestInfo().isMultiRelease()) {
         MetaInfVersionsInfo metaInfVersionsInfo = this.getMetaInfVersionsInfo();
         int[] versions = metaInfVersionsInfo.versions();
         String[] directories = metaInfVersionsInfo.directories();

         for(int i = versions.length - 1; i >= 0; --i) {
            if (versions[i] <= this.version) {
               ZipContent.Entry entry = this.getContentEntry(directories[i], name);
               if (entry != null) {
                  return entry;
               }
            }
         }

         return null;
      } else {
         return null;
      }
   }

   private ZipContent.Entry getContentEntry(String namePrefix, String name) {
      synchronized(this) {
         this.ensureOpen();
         return this.resources.zipContent().getEntry(namePrefix, name);
      }
   }

   private ManifestInfo getManifestInfo() {
      ManifestInfo manifestInfo = this.manifestInfo;
      if (manifestInfo != null) {
         return manifestInfo;
      } else {
         synchronized(this) {
            this.ensureOpen();
            manifestInfo = (ManifestInfo)this.resources.zipContent().getInfo(ManifestInfo.class, this::getManifestInfo);
         }

         this.manifestInfo = manifestInfo;
         return manifestInfo;
      }
   }

   private ManifestInfo getManifestInfo(ZipContent zipContent) {
      ZipContent.Entry contentEntry = zipContent.getEntry("META-INF/MANIFEST.MF");
      if (contentEntry == null) {
         return ManifestInfo.NONE;
      } else {
         try {
            InputStream inputStream = this.getInputStream(contentEntry);

            ManifestInfo var5;
            try {
               Manifest manifest = new Manifest(inputStream);
               var5 = new ManifestInfo(manifest);
            } catch (Throwable var7) {
               if (inputStream != null) {
                  try {
                     inputStream.close();
                  } catch (Throwable var6) {
                     var7.addSuppressed(var6);
                  }
               }

               throw var7;
            }

            if (inputStream != null) {
               inputStream.close();
            }

            return var5;
         } catch (IOException var8) {
            throw new UncheckedIOException(var8);
         }
      }
   }

   private MetaInfVersionsInfo getMetaInfVersionsInfo() {
      MetaInfVersionsInfo metaInfVersionsInfo = this.metaInfVersionsInfo;
      if (metaInfVersionsInfo != null) {
         return metaInfVersionsInfo;
      } else {
         synchronized(this) {
            this.ensureOpen();
            metaInfVersionsInfo = (MetaInfVersionsInfo)this.resources.zipContent().getInfo(MetaInfVersionsInfo.class, MetaInfVersionsInfo::get);
         }

         this.metaInfVersionsInfo = metaInfVersionsInfo;
         return metaInfVersionsInfo;
      }
   }

   public InputStream getInputStream(ZipEntry entry) throws IOException {
      Objects.requireNonNull(entry, "entry");
      if (entry instanceof NestedJarFile.NestedJarEntry) {
         NestedJarFile.NestedJarEntry nestedJarEntry = (NestedJarFile.NestedJarEntry)entry;
         if (nestedJarEntry.isOwnedBy(this)) {
            return this.getInputStream(nestedJarEntry.contentEntry());
         }
      }

      return this.getInputStream(this.getNestedJarEntry(entry.getName()).contentEntry());
   }

   private InputStream getInputStream(ZipContent.Entry contentEntry) throws IOException {
      int compression = contentEntry.getCompressionMethod();
      if (compression != 0 && compression != 8) {
         throw new ZipException("invalid compression method");
      } else {
         synchronized(this) {
            this.ensureOpen();
            Object inputStream = new NestedJarFile.JarEntryInputStream(contentEntry);

            Object var10000;
            try {
               if (compression == 8) {
                  inputStream = new NestedJarFile.JarEntryInflaterInputStream((NestedJarFile.JarEntryInputStream)inputStream, this.resources);
               }

               this.resources.addInputStream((InputStream)inputStream);
               var10000 = inputStream;
            } catch (RuntimeException var7) {
               ((InputStream)inputStream).close();
               throw var7;
            }

            return (InputStream)var10000;
         }
      }
   }

   public String getComment() {
      synchronized(this) {
         this.ensureOpen();
         return this.resources.zipContent().getComment();
      }
   }

   public int size() {
      synchronized(this) {
         this.ensureOpen();
         return this.resources.zipContent().size();
      }
   }

   public void close() throws IOException {
      super.close();
      if (!this.closed) {
         this.closed = true;
         synchronized(this) {
            try {
               this.cleanup.clean();
            } catch (UncheckedIOException var4) {
               throw var4.getCause();
            }

         }
      }
   }

   public String getName() {
      return this.name;
   }

   private void ensureOpen() {
      if (this.closed) {
         throw new IllegalStateException("Zip file closed");
      } else if (this.resources.zipContent() == null) {
         throw new IllegalStateException("The object is not initialized.");
      }
   }

   public void clearCache() {
      synchronized(this) {
         this.lastEntry = null;
      }
   }

   private class RawZipDataInputStream extends FilterInputStream {
      private volatile boolean closed;

      RawZipDataInputStream(InputStream in) {
         super(in);
      }

      public void close() throws IOException {
         if (!this.closed) {
            this.closed = true;
            super.close();
            NestedJarFile.this.resources.removeInputStream(this);
         }
      }
   }

   private class JarEntriesEnumeration implements Enumeration<JarEntry> {
      private final ZipContent zipContent;
      private int cursor;

      JarEntriesEnumeration(ZipContent zipContent) {
         this.zipContent = zipContent;
      }

      public boolean hasMoreElements() {
         return this.cursor < this.zipContent.size();
      }

      public NestedJarFile.NestedJarEntry nextElement() {
         if (!this.hasMoreElements()) {
            throw new NoSuchElementException();
         } else {
            synchronized(NestedJarFile.this) {
               NestedJarFile.this.ensureOpen();
               return NestedJarFile.this.new NestedJarEntry(this.zipContent.getEntry(this.cursor++));
            }
         }
      }
   }

   private class ZipContentEntriesSpliterator extends AbstractSpliterator<ZipContent.Entry> {
      private static final int ADDITIONAL_CHARACTERISTICS = 1297;
      private final ZipContent zipContent;
      private int cursor;

      ZipContentEntriesSpliterator(ZipContent zipContent) {
         super((long)zipContent.size(), 1297);
         this.zipContent = zipContent;
      }

      public boolean tryAdvance(Consumer<? super ZipContent.Entry> action) {
         if (this.cursor < this.zipContent.size()) {
            synchronized(NestedJarFile.this) {
               NestedJarFile.this.ensureOpen();
               action.accept(this.zipContent.getEntry(this.cursor++));
               return true;
            }
         } else {
            return false;
         }
      }
   }

   private class NestedJarEntry extends JarEntry {
      private static final IllegalStateException CANNOT_BE_MODIFIED_EXCEPTION = new IllegalStateException("Neste jar entries cannot be modified");
      private final ZipContent.Entry contentEntry;
      private final String name;
      private volatile boolean populated;

      NestedJarEntry(ZipContent.Entry contentEntry) {
         this(contentEntry, contentEntry.getName());
      }

      NestedJarEntry(ZipContent.Entry contentEntry, String name) {
         super(contentEntry.getName());
         this.contentEntry = contentEntry;
         this.name = name;
      }

      public long getTime() {
         this.populate();
         return super.getTime();
      }

      public LocalDateTime getTimeLocal() {
         this.populate();
         return super.getTimeLocal();
      }

      public void setTime(long time) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public void setTimeLocal(LocalDateTime time) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public FileTime getLastModifiedTime() {
         this.populate();
         return super.getLastModifiedTime();
      }

      public ZipEntry setLastModifiedTime(FileTime time) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public FileTime getLastAccessTime() {
         this.populate();
         return super.getLastAccessTime();
      }

      public ZipEntry setLastAccessTime(FileTime time) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public FileTime getCreationTime() {
         this.populate();
         return super.getCreationTime();
      }

      public ZipEntry setCreationTime(FileTime time) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public long getSize() {
         return (long)this.contentEntry.getUncompressedSize() & 4294967295L;
      }

      public void setSize(long size) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public long getCompressedSize() {
         this.populate();
         return super.getCompressedSize();
      }

      public void setCompressedSize(long csize) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public long getCrc() {
         this.populate();
         return super.getCrc();
      }

      public void setCrc(long crc) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public int getMethod() {
         this.populate();
         return super.getMethod();
      }

      public void setMethod(int method) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public byte[] getExtra() {
         this.populate();
         return super.getExtra();
      }

      public void setExtra(byte[] extra) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      public String getComment() {
         this.populate();
         return super.getComment();
      }

      public void setComment(String comment) {
         throw CANNOT_BE_MODIFIED_EXCEPTION;
      }

      boolean isOwnedBy(NestedJarFile nestedJarFile) {
         return NestedJarFile.this == nestedJarFile;
      }

      public String getRealName() {
         return super.getName();
      }

      public String getName() {
         return this.name;
      }

      public Attributes getAttributes() throws IOException {
         Manifest manifest = NestedJarFile.this.getManifest();
         return manifest != null ? manifest.getAttributes(this.getName()) : null;
      }

      public Certificate[] getCertificates() {
         return this.getSecurityInfo().getCertificates(this.contentEntry());
      }

      public CodeSigner[] getCodeSigners() {
         return this.getSecurityInfo().getCodeSigners(this.contentEntry());
      }

      private SecurityInfo getSecurityInfo() {
         return (SecurityInfo)NestedJarFile.this.resources.zipContent().getInfo(SecurityInfo.class, SecurityInfo::get);
      }

      ZipContent.Entry contentEntry() {
         return this.contentEntry;
      }

      private void populate() {
         boolean populated = this.populated;
         if (!populated) {
            ZipEntry entry = this.contentEntry.as(ZipEntry::new);
            super.setMethod(entry.getMethod());
            super.setTime(entry.getTime());
            super.setCrc(entry.getCrc());
            super.setCompressedSize(entry.getCompressedSize());
            super.setSize(entry.getSize());
            super.setExtra(entry.getExtra());
            super.setComment(entry.getComment());
            this.populated = true;
         }

      }
   }

   private class JarEntryInputStream extends InputStream {
      private final int uncompressedSize;
      private final CloseableDataBlock content;
      private long pos;
      private long remaining;
      private volatile boolean closed;

      JarEntryInputStream(ZipContent.Entry entry) throws IOException {
         this.uncompressedSize = entry.getUncompressedSize();
         this.content = entry.openContent();
      }

      public int read() throws IOException {
         byte[] b = new byte[1];
         return this.read(b, 0, 1) == 1 ? b[0] & 255 : -1;
      }

      public int read(byte[] b, int off, int len) throws IOException {
         int result;
         synchronized(NestedJarFile.this) {
            this.ensureOpen();
            ByteBuffer dst = ByteBuffer.wrap(b, off, len);
            int count = this.content.read(dst, this.pos);
            if (count > 0) {
               this.pos += (long)count;
               this.remaining -= (long)count;
            }

            result = count;
         }

         if (this.remaining == 0L) {
            this.close();
         }

         return result;
      }

      public long skip(long n) throws IOException {
         long result;
         synchronized(NestedJarFile.this) {
            result = n > 0L ? this.maxForwardSkip(n) : this.maxBackwardSkip(n);
            this.pos += result;
            this.remaining -= result;
         }

         if (this.remaining == 0L) {
            this.close();
         }

         return result;
      }

      private long maxForwardSkip(long n) {
         boolean willCauseOverflow = this.pos + n < 0L;
         return !willCauseOverflow && n <= this.remaining ? n : this.remaining;
      }

      private long maxBackwardSkip(long n) {
         return Math.max(-this.pos, n);
      }

      public int available() {
         return this.remaining < 2147483647L ? (int)this.remaining : Integer.MAX_VALUE;
      }

      private void ensureOpen() throws ZipException {
         if (NestedJarFile.this.closed || this.closed) {
            throw new ZipException("ZipFile closed");
         }
      }

      public void close() throws IOException {
         if (!this.closed) {
            this.closed = true;
            this.content.close();
            NestedJarFile.this.resources.removeInputStream(this);
         }
      }

      int getUncompressedSize() {
         return this.uncompressedSize;
      }
   }

   private class JarEntryInflaterInputStream extends ZipInflaterInputStream {
      private final Cleanable cleanup;
      private volatile boolean closed;

      JarEntryInflaterInputStream(NestedJarFile.JarEntryInputStream inputStream, NestedJarFileResources resources) {
         this(inputStream, resources, resources.getOrCreateInflater());
      }

      private JarEntryInflaterInputStream(NestedJarFile.JarEntryInputStream inputStream, NestedJarFileResources resources, Inflater inflater) {
         super(inputStream, inflater, inputStream.getUncompressedSize());
         this.cleanup = NestedJarFile.this.cleaner.register(this, resources.createInflatorCleanupAction(inflater));
      }

      public void close() throws IOException {
         if (!this.closed) {
            this.closed = true;
            super.close();
            NestedJarFile.this.resources.removeInputStream(this);
            this.cleanup.clean();
         }
      }
   }
}
