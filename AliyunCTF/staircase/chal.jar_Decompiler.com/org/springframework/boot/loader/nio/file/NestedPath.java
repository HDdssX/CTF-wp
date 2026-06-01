package org.springframework.boot.loader.nio.file;

import java.io.IOError;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.ProviderMismatchException;
import java.nio.file.WatchKey;
import java.nio.file.WatchService;
import java.nio.file.WatchEvent.Kind;
import java.nio.file.WatchEvent.Modifier;
import java.util.Objects;
import org.springframework.boot.loader.zip.ZipContent;

final class NestedPath implements Path {
   private final NestedFileSystem fileSystem;
   private final String nestedEntryName;
   private volatile Boolean entryExists;

   NestedPath(NestedFileSystem fileSystem, String nestedEntryName) {
      if (fileSystem != null && nestedEntryName != null && !nestedEntryName.isBlank()) {
         this.fileSystem = fileSystem;
         this.nestedEntryName = nestedEntryName;
      } else {
         throw new IllegalArgumentException("'filesSystem' and 'nestedEntryName' are required");
      }
   }

   Path getJarPath() {
      return this.fileSystem.getJarPath();
   }

   String getNestedEntryName() {
      return this.nestedEntryName;
   }

   public NestedFileSystem getFileSystem() {
      return this.fileSystem;
   }

   public boolean isAbsolute() {
      return true;
   }

   public Path getRoot() {
      return null;
   }

   public Path getFileName() {
      return this;
   }

   public Path getParent() {
      return null;
   }

   public int getNameCount() {
      return 1;
   }

   public Path getName(int index) {
      if (index != 0) {
         throw new IllegalArgumentException("Nested paths only have a single element");
      } else {
         return this;
      }
   }

   public Path subpath(int beginIndex, int endIndex) {
      if (beginIndex == 0 && endIndex == 1) {
         return this;
      } else {
         throw new IllegalArgumentException("Nested paths only have a single element");
      }
   }

   public boolean startsWith(Path other) {
      return this.equals(other);
   }

   public boolean endsWith(Path other) {
      return this.equals(other);
   }

   public Path normalize() {
      return this;
   }

   public Path resolve(Path other) {
      throw new UnsupportedOperationException("Unable to resolve nested path");
   }

   public Path relativize(Path other) {
      throw new UnsupportedOperationException("Unable to relativize nested path");
   }

   public URI toUri() {
      try {
         String jarFilePath = this.fileSystem.getJarPath().toUri().getPath();
         return new URI("nested:" + jarFilePath + "/!" + this.nestedEntryName);
      } catch (URISyntaxException var2) {
         throw new IOError(var2);
      }
   }

   public Path toAbsolutePath() {
      return this;
   }

   public Path toRealPath(LinkOption... options) throws IOException {
      return this;
   }

   public WatchKey register(WatchService watcher, Kind<?>[] events, Modifier... modifiers) throws IOException {
      throw new UnsupportedOperationException("Nested paths cannot be watched");
   }

   public int compareTo(Path other) {
      NestedPath otherNestedPath = cast(other);
      return this.nestedEntryName.compareTo(otherNestedPath.nestedEntryName);
   }

   public boolean equals(Object obj) {
      if (this == obj) {
         return true;
      } else if (obj != null && this.getClass() == obj.getClass()) {
         NestedPath other = (NestedPath)obj;
         return Objects.equals(this.fileSystem, other.fileSystem) && Objects.equals(this.nestedEntryName, other.nestedEntryName);
      } else {
         return false;
      }
   }

   public int hashCode() {
      return Objects.hash(new Object[]{this.fileSystem, this.nestedEntryName});
   }

   public String toString() {
      Path var10000 = this.fileSystem.getJarPath();
      return var10000 + this.fileSystem.getSeparator() + this.nestedEntryName;
   }

   void assertExists() throws NoSuchFileException {
      if (!Files.isRegularFile(this.getJarPath(), new LinkOption[0])) {
         throw new NoSuchFileException(this.toString());
      } else {
         Boolean entryExists = this.entryExists;
         if (entryExists == null) {
            try {
               ZipContent content = ZipContent.open(this.getJarPath(), this.nestedEntryName);

               try {
                  entryExists = true;
               } catch (Throwable var6) {
                  if (content != null) {
                     try {
                        content.close();
                     } catch (Throwable var5) {
                        var6.addSuppressed(var5);
                     }
                  }

                  throw var6;
               }

               if (content != null) {
                  content.close();
               }
            } catch (IOException var7) {
               entryExists = false;
            }

            this.entryExists = entryExists;
         }

         if (!entryExists) {
            throw new NoSuchFileException(this.toString());
         }
      }
   }

   static NestedPath cast(Path path) {
      if (path instanceof NestedPath) {
         NestedPath nestedPath = (NestedPath)path;
         return nestedPath;
      } else {
         throw new ProviderMismatchException();
      }
   }
}
