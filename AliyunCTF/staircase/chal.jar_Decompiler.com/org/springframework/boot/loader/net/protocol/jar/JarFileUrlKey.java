package org.springframework.boot.loader.net.protocol.jar;

import java.lang.ref.SoftReference;
import java.net.URL;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

final class JarFileUrlKey {
   private static volatile SoftReference<Map<URL, String>> cache;

   private JarFileUrlKey() {
   }

   static String get(URL url) {
      Map<URL, String> cache = JarFileUrlKey.cache != null ? (Map)JarFileUrlKey.cache.get() : null;
      if (cache == null) {
         cache = new ConcurrentHashMap();
         JarFileUrlKey.cache = new SoftReference(cache);
      }

      return (String)((Map)cache).computeIfAbsent(url, JarFileUrlKey::create);
   }

   private static String create(URL url) {
      StringBuilder value = new StringBuilder();
      String protocol = url.getProtocol();
      String host = url.getHost();
      int port = url.getPort() != -1 ? url.getPort() : url.getDefaultPort();
      String file = url.getFile();
      value.append(protocol.toLowerCase());
      value.append(":");
      if (host != null && !host.isEmpty()) {
         value.append(host.toLowerCase());
         value.append(port != -1 ? ":" + port : "");
      }

      value.append(file != null ? file : "");
      if ("runtime".equals(url.getRef())) {
         value.append("#runtime");
      }

      return value.toString();
   }

   static void clearCache() {
      cache = null;
   }
}
