package org.springframework.boot.loader.nio.file;

import java.io.IOException;
import java.net.URI;
import java.nio.file.ClosedFileSystemException;
import java.nio.file.FileStore;
import java.nio.file.FileSystem;
import java.nio.file.FileSystemNotFoundException;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.nio.file.PathMatcher;
import java.nio.file.WatchService;
import java.nio.file.attribute.UserPrincipalLookupService;
import java.nio.file.spi.FileSystemProvider;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Stream;

class NestedFileSystem extends FileSystem {
   private static final Set<String> SUPPORTED_FILE_ATTRIBUTE_VIEWS = Set.of("basic");
   private static final String FILE_SYSTEMS_CLASS_NAME = FileSystems.class.getName();
   private static final Object EXISTING_FILE_SYSTEM = new Object();
   private final NestedFileSystemProvider provider;
   private final Path jarPath;
   private volatile boolean closed;
   private final Map<String, Object> zipFileSystems = new HashMap();

   NestedFileSystem(NestedFileSystemProvider provider, Path jarPath) {
      if (provider != null && jarPath != null) {
         this.provider = provider;
         this.jarPath = jarPath;
      } else {
         throw new IllegalArgumentException("Provider and JarPath must not be null");
      }
   }

   void installZipFileSystemIfNecessary(String nestedEntryName) {
      try {
         boolean seen;
         synchronized(this.zipFileSystems) {
            seen = this.zipFileSystems.putIfAbsent(nestedEntryName, EXISTING_FILE_SYSTEM) != null;
         }

         if (!seen) {
            String var10002 = this.jarPath.toUri().getPath();
            URI uri = new URI("jar:nested:" + var10002 + "/!" + nestedEntryName);
            if (!this.hasFileSystem(uri)) {
               FileSystem zipFileSystem = FileSystems.newFileSystem(uri, Collections.emptyMap());
               synchronized(this.zipFileSystems) {
                  this.zipFileSystems.put(nestedEntryName, zipFileSystem);
               }
            }
         }
      } catch (Exception var9) {
      }

   }

   private boolean hasFileSystem(URI uri) {
      try {
         FileSystems.getFileSystem(uri);
         return true;
      } catch (FileSystemNotFoundException var3) {
         return this.isCreatingNewFileSystem();
      }
   }

   private boolean isCreatingNewFileSystem() {
      StackTraceElement[] stack = Thread.currentThread().getStackTrace();
      if (stack != null) {
         StackTraceElement[] var2 = stack;
         int var3 = stack.length;

         for(int var4 = 0; var4 < var3; ++var4) {
            StackTraceElement element = var2[var4];
            if (FILE_SYSTEMS_CLASS_NAME.equals(element.getClassName())) {
               return "newFileSystem".equals(element.getMethodName());
            }
         }
      }

      return false;
   }

   public FileSystemProvider provider() {
      return this.provider;
   }

   Path getJarPath() {
      return this.jarPath;
   }

   public void close() throws IOException {
      if (!this.closed) {
         this.closed = true;
         synchronized(this.zipFileSystems) {
            Stream var10000 = this.zipFileSystems.values().stream();
            Objects.requireNonNull(FileSystem.class);
            var10000 = var10000.filter(FileSystem.class::isInstance);
            Objects.requireNonNull(FileSystem.class);
            var10000.map(FileSystem.class::cast).forEach(this::closeZipFileSystem);
         }

         this.provider.removeFileSystem(this);
      }
   }

   private void closeZipFileSystem(FileSystem zipFileSystem) {
      try {
         zipFileSystem.close();
      } catch (Exception var3) {
      }

   }

   public boolean isOpen() {
      return !this.closed;
   }

   public boolean isReadOnly() {
      return true;
   }

   public String getSeparator() {
      return "/!";
   }

   public Iterable<Path> getRootDirectories() {
      this.assertNotClosed();
      return Collections.emptySet();
   }

   public Iterable<FileStore> getFileStores() {
      this.assertNotClosed();
      return Collections.emptySet();
   }

   public Set<String> supportedFileAttributeViews() {
      this.assertNotClosed();
      return SUPPORTED_FILE_ATTRIBUTE_VIEWS;
   }

   public Path getPath(String first, String... more) {
      this.assertNotClosed();
      if (first != null && !first.isBlank() && more.length == 0) {
         return new NestedPath(this, first);
      } else {
         throw new IllegalArgumentException("Nested paths must contain a single element");
      }
   }

   public PathMatcher getPathMatcher(String syntaxAndPattern) {
      throw new UnsupportedOperationException("Nested paths do not support path matchers");
   }

   public UserPrincipalLookupService getUserPrincipalLookupService() {
      throw new UnsupportedOperationException("Nested paths do not have a user principal lookup service");
   }

   public WatchService newWatchService() throws IOException {
      throw new UnsupportedOperationException("Nested paths do not support the WacherService");
   }

   public boolean equals(Object obj) {
      if (this == obj) {
         return true;
      } else if (obj != null && this.getClass() == obj.getClass()) {
         NestedFileSystem other = (NestedFileSystem)obj;
         return this.jarPath.equals(other.jarPath);
      } else {
         return false;
      }
   }

   public int hashCode() {
      return this.jarPath.hashCode();
   }

   public String toString() {
      return this.jarPath.toAbsolutePath().toString();
   }

   private void assertNotClosed() {
      if (this.closed) {
         throw new ClosedFileSystemException();
      }
   }
}
