package org.springframework.boot.loader.launch;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URL;
import java.security.CodeSource;
import java.security.ProtectionDomain;
import java.util.Set;
import java.util.function.Predicate;
import java.util.jar.Manifest;

public interface Archive extends AutoCloseable {
   Predicate<Archive.Entry> ALL_ENTRIES = (entry) -> {
      return true;
   };

   Manifest getManifest() throws IOException;

   default Set<URL> getClassPathUrls(Predicate<Archive.Entry> includeFilter) throws IOException {
      return this.getClassPathUrls(includeFilter, ALL_ENTRIES);
   }

   Set<URL> getClassPathUrls(Predicate<Archive.Entry> includeFilter, Predicate<Archive.Entry> directorySearchFilter) throws IOException;

   default boolean isExploded() {
      return this.getRootDirectory() != null;
   }

   default File getRootDirectory() {
      return null;
   }

   default void close() throws Exception {
   }

   static Archive create(Class<?> target) throws Exception {
      return create(target.getProtectionDomain());
   }

   static Archive create(ProtectionDomain protectionDomain) throws Exception {
      CodeSource codeSource = protectionDomain.getCodeSource();
      URI location = codeSource != null ? codeSource.getLocation().toURI() : null;
      String path = location != null ? location.getSchemeSpecificPart() : null;
      if (path == null) {
         throw new IllegalStateException("Unable to determine code source archive");
      } else {
         return create(new File(path));
      }
   }

   static Archive create(File target) throws Exception {
      if (!target.exists()) {
         throw new IllegalStateException("Unable to determine code source archive from " + target);
      } else {
         return (Archive)(target.isDirectory() ? new ExplodedArchive(target) : new JarFileArchive(target));
      }
   }

   public interface Entry {
      String name();

      boolean isDirectory();
   }
}
