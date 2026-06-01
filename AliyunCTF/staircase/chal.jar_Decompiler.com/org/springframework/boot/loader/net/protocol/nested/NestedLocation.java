package org.springframework.boot.loader.net.protocol.nested;

import java.io.File;
import java.net.URI;
import java.net.URL;
import java.nio.file.Path;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.boot.loader.net.util.UrlDecoder;

public record NestedLocation(Path path, String nestedEntryName) {
   private static final Map<String, NestedLocation> cache = new ConcurrentHashMap();

   public NestedLocation(Path path, String nestedEntryName) {
      if (path == null) {
         throw new IllegalArgumentException("'path' must not be null");
      } else if (nestedEntryName != null && !nestedEntryName.trim().isEmpty()) {
         this.path = path;
         this.nestedEntryName = nestedEntryName;
      } else {
         throw new IllegalArgumentException("'nestedEntryName' must not be empty");
      }
   }

   public static NestedLocation fromUrl(URL url) {
      if (url != null && "nested".equalsIgnoreCase(url.getProtocol())) {
         return parse(UrlDecoder.decode(url.getPath()));
      } else {
         throw new IllegalArgumentException("'url' must not be null and must use 'nested' protocol");
      }
   }

   public static NestedLocation fromUri(URI uri) {
      if (uri != null && "nested".equalsIgnoreCase(uri.getScheme())) {
         return parse(uri.getSchemeSpecificPart());
      } else {
         throw new IllegalArgumentException("'uri' must not be null and must use 'nested' scheme");
      }
   }

   static NestedLocation parse(String path) {
      if (path != null && !path.isEmpty()) {
         int index = path.lastIndexOf("/!");
         if (index == -1) {
            throw new IllegalArgumentException("'path' must contain '/!'");
         } else {
            return (NestedLocation)cache.computeIfAbsent(path, (l) -> {
               return create(index, l);
            });
         }
      } else {
         throw new IllegalArgumentException("'path' must not be empty");
      }
   }

   private static NestedLocation create(int index, String location) {
      String locationPath = location.substring(0, index);
      if (isWindows()) {
         while(locationPath.startsWith("/")) {
            locationPath = locationPath.substring(1, locationPath.length());
         }
      }

      String nestedEntryName = location.substring(index + 2);
      return new NestedLocation(!locationPath.isEmpty() ? Path.of(locationPath, new String[0]) : null, nestedEntryName);
   }

   private static boolean isWindows() {
      return File.separatorChar == '\\';
   }

   static void clearCache() {
      cache.clear();
   }

   public Path path() {
      return this.path;
   }

   public String nestedEntryName() {
      return this.nestedEntryName;
   }
}
