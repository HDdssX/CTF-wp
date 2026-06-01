package org.springframework.boot.loader.nio.file;

import java.io.IOException;
import java.net.URI;
import java.nio.channels.SeekableByteChannel;
import java.nio.file.AccessMode;
import java.nio.file.CopyOption;
import java.nio.file.DirectoryStream;
import java.nio.file.FileStore;
import java.nio.file.FileSystem;
import java.nio.file.FileSystemAlreadyExistsException;
import java.nio.file.FileSystemNotFoundException;
import java.nio.file.LinkOption;
import java.nio.file.NotDirectoryException;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.ReadOnlyFileSystemException;
import java.nio.file.DirectoryStream.Filter;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileAttribute;
import java.nio.file.attribute.FileAttributeView;
import java.nio.file.spi.FileSystemProvider;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import org.springframework.boot.loader.net.protocol.nested.NestedLocation;

public class NestedFileSystemProvider extends FileSystemProvider {
   private Map<Path, NestedFileSystem> fileSystems = new HashMap();

   public String getScheme() {
      return "nested";
   }

   public FileSystem newFileSystem(URI uri, Map<String, ?> env) throws IOException {
      NestedLocation location = NestedLocation.fromUri(uri);
      Path jarPath = location.path();
      synchronized(this.fileSystems) {
         if (this.fileSystems.containsKey(jarPath)) {
            throw new FileSystemAlreadyExistsException();
         } else {
            NestedFileSystem fileSystem = new NestedFileSystem(this, location.path());
            this.fileSystems.put(location.path(), fileSystem);
            return fileSystem;
         }
      }
   }

   public FileSystem getFileSystem(URI uri) {
      NestedLocation location = NestedLocation.fromUri(uri);
      synchronized(this.fileSystems) {
         NestedFileSystem fileSystem = (NestedFileSystem)this.fileSystems.get(location.path());
         if (fileSystem == null) {
            throw new FileSystemNotFoundException();
         } else {
            return fileSystem;
         }
      }
   }

   public Path getPath(URI uri) {
      NestedLocation location = NestedLocation.fromUri(uri);
      synchronized(this.fileSystems) {
         NestedFileSystem fileSystem = (NestedFileSystem)this.fileSystems.computeIfAbsent(location.path(), (path) -> {
            return new NestedFileSystem(this, path);
         });
         fileSystem.installZipFileSystemIfNecessary(location.nestedEntryName());
         return fileSystem.getPath(location.nestedEntryName());
      }
   }

   void removeFileSystem(NestedFileSystem fileSystem) {
      synchronized(this.fileSystems) {
         this.fileSystems.remove(fileSystem.getJarPath());
      }
   }

   public SeekableByteChannel newByteChannel(Path path, Set<? extends OpenOption> options, FileAttribute<?>... attrs) throws IOException {
      NestedPath nestedPath = NestedPath.cast(path);
      return new NestedByteChannel(nestedPath.getJarPath(), nestedPath.getNestedEntryName());
   }

   public DirectoryStream<Path> newDirectoryStream(Path dir, Filter<? super Path> filter) throws IOException {
      throw new NotDirectoryException(NestedPath.cast(dir).toString());
   }

   public void createDirectory(Path dir, FileAttribute<?>... attrs) throws IOException {
      throw new ReadOnlyFileSystemException();
   }

   public void delete(Path path) throws IOException {
      throw new ReadOnlyFileSystemException();
   }

   public void copy(Path source, Path target, CopyOption... options) throws IOException {
      throw new ReadOnlyFileSystemException();
   }

   public void move(Path source, Path target, CopyOption... options) throws IOException {
      throw new ReadOnlyFileSystemException();
   }

   public boolean isSameFile(Path path, Path path2) throws IOException {
      return path.equals(path2);
   }

   public boolean isHidden(Path path) throws IOException {
      return false;
   }

   public FileStore getFileStore(Path path) throws IOException {
      NestedPath nestedPath = NestedPath.cast(path);
      nestedPath.assertExists();
      return new NestedFileStore(nestedPath.getFileSystem());
   }

   public void checkAccess(Path path, AccessMode... modes) throws IOException {
      Path jarPath = this.getJarPath(path);
      jarPath.getFileSystem().provider().checkAccess(jarPath, modes);
   }

   public <V extends FileAttributeView> V getFileAttributeView(Path path, Class<V> type, LinkOption... options) {
      Path jarPath = this.getJarPath(path);
      return jarPath.getFileSystem().provider().getFileAttributeView(jarPath, type, options);
   }

   public <A extends BasicFileAttributes> A readAttributes(Path path, Class<A> type, LinkOption... options) throws IOException {
      Path jarPath = this.getJarPath(path);
      return jarPath.getFileSystem().provider().readAttributes(jarPath, type, options);
   }

   public Map<String, Object> readAttributes(Path path, String attributes, LinkOption... options) throws IOException {
      Path jarPath = this.getJarPath(path);
      return jarPath.getFileSystem().provider().readAttributes(jarPath, attributes, options);
   }

   protected Path getJarPath(Path path) {
      return NestedPath.cast(path).getJarPath();
   }

   public void setAttribute(Path path, String attribute, Object value, LinkOption... options) throws IOException {
      throw new ReadOnlyFileSystemException();
   }
}
