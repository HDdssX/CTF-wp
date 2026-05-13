package org.springframework.boot.loader.nio.file;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.FileStore;
import java.nio.file.Files;
import java.nio.file.attribute.FileAttributeView;
import java.nio.file.attribute.FileStoreAttributeView;

class NestedFileStore extends FileStore {
   private final NestedFileSystem fileSystem;

   NestedFileStore(NestedFileSystem fileSystem) {
      this.fileSystem = fileSystem;
   }

   public String name() {
      return this.fileSystem.toString();
   }

   public String type() {
      return "nestedfs";
   }

   public boolean isReadOnly() {
      return this.fileSystem.isReadOnly();
   }

   public long getTotalSpace() throws IOException {
      return 0L;
   }

   public long getUsableSpace() throws IOException {
      return 0L;
   }

   public long getUnallocatedSpace() throws IOException {
      return 0L;
   }

   public boolean supportsFileAttributeView(Class<? extends FileAttributeView> type) {
      return this.getJarPathFileStore().supportsFileAttributeView(type);
   }

   public boolean supportsFileAttributeView(String name) {
      return this.getJarPathFileStore().supportsFileAttributeView(name);
   }

   public <V extends FileStoreAttributeView> V getFileStoreAttributeView(Class<V> type) {
      return this.getJarPathFileStore().getFileStoreAttributeView(type);
   }

   public Object getAttribute(String attribute) throws IOException {
      try {
         return this.getJarPathFileStore().getAttribute(attribute);
      } catch (UncheckedIOException var3) {
         throw var3.getCause();
      }
   }

   protected FileStore getJarPathFileStore() {
      try {
         return Files.getFileStore(this.fileSystem.getJarPath());
      } catch (IOException var2) {
         throw new UncheckedIOException(var2);
      }
   }
}
