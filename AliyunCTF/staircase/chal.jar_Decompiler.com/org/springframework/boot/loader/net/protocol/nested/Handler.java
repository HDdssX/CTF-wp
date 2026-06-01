package org.springframework.boot.loader.net.protocol.nested;

import java.io.IOException;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLStreamHandler;

public class Handler extends URLStreamHandler {
   private static final String PREFIX = "nested:";

   protected URLConnection openConnection(URL url) throws IOException {
      return new NestedUrlConnection(url);
   }

   public static void assertUrlIsNotMalformed(String url) {
      if (url != null && url.startsWith("nested:")) {
         NestedLocation.parse(url.substring("nested:".length()));
      } else {
         throw new IllegalArgumentException("'url' must not be null and must use 'nested' protocol");
      }
   }

   public static void clearCache() {
      NestedLocation.clearCache();
   }
}
