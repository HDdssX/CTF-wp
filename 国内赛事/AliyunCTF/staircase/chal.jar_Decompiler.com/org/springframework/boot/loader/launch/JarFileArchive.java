package org.springframework.boot.loader.launch;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.net.URL;
import java.nio.file.CopyOption;
import java.nio.file.FileSystem;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.FileAttribute;
import java.nio.file.attribute.PosixFilePermission;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.UUID;
import java.util.function.Predicate;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import java.util.stream.Collectors;
import org.springframework.boot.loader.net.protocol.jar.JarUrl;

class JarFileArchive implements Archive {
   private static final String UNPACK_MARKER = "UNPACK:";
   private static final FileAttribute<?>[] NO_FILE_ATTRIBUTES = new FileAttribute[0];
   private static final FileAttribute<?>[] DIRECTORY_PERMISSION_ATTRIBUTES;
   private static final FileAttribute<?>[] FILE_PERMISSION_ATTRIBUTES;
   private static final Path TEMP;
   private final File file;
   private final JarFile jarFile;
   private volatile Path tempUnpackDirectory;

   JarFileArchive(File file) throws IOException {
      this(file, new JarFile(file));
   }

   private JarFileArchive(File file, JarFile jarFile) {
      this.file = file;
      this.jarFile = jarFile;
   }

   public Manifest getManifest() throws IOException {
      return this.jarFile.getManifest();
   }

   public Set<URL> getClassPathUrls(Predicate<Archive.Entry> includeFilter, Predicate<Archive.Entry> directorySearchFilter) throws IOException {
      return (Set)this.jarFile.stream().map(JarFileArchive.JarArchiveEntry::new).filter(includeFilter).map(this::getNestedJarUrl).collect(Collectors.toCollection(LinkedHashSet::new));
   }

   private URL getNestedJarUrl(JarFileArchive.JarArchiveEntry archiveEntry) {
      try {
         JarEntry jarEntry = archiveEntry.jarEntry();
         String comment = jarEntry.getComment();
         return comment != null && comment.startsWith("UNPACK:") ? this.getUnpackedNestedJarUrl(jarEntry) : JarUrl.create(this.file, jarEntry);
      } catch (IOException var4) {
         throw new UncheckedIOException(var4);
      }
   }

   private URL getUnpackedNestedJarUrl(JarEntry jarEntry) throws IOException {
      String name = jarEntry.getName();
      if (name.lastIndexOf(47) != -1) {
         name = name.substring(name.lastIndexOf(47) + 1);
      }

      Path path = this.getTempUnpackDirectory().resolve(name);
      if (!Files.exists(path, new LinkOption[0]) || Files.size(path) != jarEntry.getSize()) {
         this.unpack(jarEntry, path);
      }

      return JarUrl.create(path.toFile());
   }

   private Path getTempUnpackDirectory() {
      Path tempUnpackDirectory = this.tempUnpackDirectory;
      if (tempUnpackDirectory != null) {
         return tempUnpackDirectory;
      } else {
         synchronized(TEMP) {
            tempUnpackDirectory = this.tempUnpackDirectory;
            if (tempUnpackDirectory == null) {
               tempUnpackDirectory = this.createUnpackDirectory(TEMP);
               this.tempUnpackDirectory = tempUnpackDirectory;
            }

            return tempUnpackDirectory;
         }
      }
   }

   private Path createUnpackDirectory(Path parent) {
      int attempts = 0;
      String fileName = Paths.get(this.jarFile.getName()).getFileName().toString();

      while(attempts++ < 100) {
         Path unpackDirectory = parent.resolve(fileName + "-spring-boot-libs-" + UUID.randomUUID());

         try {
            this.createDirectory(unpackDirectory);
            return unpackDirectory;
         } catch (IOException var6) {
         }
      }

      throw new IllegalStateException("Failed to create unpack directory in directory '" + parent + "'");
   }

   private void createDirectory(Path path) throws IOException {
      Files.createDirectory(path, this.getFileAttributes(path, DIRECTORY_PERMISSION_ATTRIBUTES));
   }

   private void unpack(JarEntry entry, Path path) throws IOException {
      this.createFile(path);
      path.toFile().deleteOnExit();
      InputStream in = this.jarFile.getInputStream(entry);

      try {
         Files.copy(in, path, new CopyOption[]{StandardCopyOption.REPLACE_EXISTING});
      } catch (Throwable var7) {
         if (in != null) {
            try {
               in.close();
            } catch (Throwable var6) {
               var7.addSuppressed(var6);
            }
         }

         throw var7;
      }

      if (in != null) {
         in.close();
      }

   }

   private void createFile(Path path) throws IOException {
      Files.createFile(path, this.getFileAttributes(path, FILE_PERMISSION_ATTRIBUTES));
   }

   private FileAttribute<?>[] getFileAttributes(Path path, FileAttribute<?>[] permissionAttributes) {
      return !this.supportsPosix(path.getFileSystem()) ? NO_FILE_ATTRIBUTES : permissionAttributes;
   }

   private boolean supportsPosix(FileSystem fileSystem) {
      return fileSystem.supportedFileAttributeViews().contains("posix");
   }

   public void close() throws IOException {
      this.jarFile.close();
   }

   public String toString() {
      return this.file.toString();
   }

   private static FileAttribute<?>[] asFileAttributes(PosixFilePermission... permissions) {
      return new FileAttribute[]{PosixFilePermissions.asFileAttribute(Set.of(permissions))};
   }

   static {
      DIRECTORY_PERMISSION_ATTRIBUTES = asFileAttributes(PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE);
      FILE_PERMISSION_ATTRIBUTES = asFileAttributes(PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE);
      TEMP = Paths.get(System.getProperty("java.io.tmpdir"));
   }

   private static record JarArchiveEntry(JarEntry jarEntry) implements Archive.Entry {
      private JarArchiveEntry(JarEntry jarEntry) {
         this.jarEntry = jarEntry;
      }

      public String name() {
         return this.jarEntry.getName();
      }

      public boolean isDirectory() {
         return this.jarEntry.isDirectory();
      }

      public JarEntry jarEntry() {
         return this.jarEntry;
      }
   }
}
