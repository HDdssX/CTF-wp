package org.springframework.boot.loader.net.protocol.jar;

import java.io.IOException;
import java.net.URL;
import java.net.URLConnection;
import java.util.HashMap;
import java.util.Map;
import java.util.jar.JarFile;

class UrlJarFiles {
   private final UrlJarFileFactory factory;
   private final UrlJarFiles.Cache cache;

   UrlJarFiles() {
      this(new UrlJarFileFactory());
   }

   UrlJarFiles(UrlJarFileFactory factory) {
      this.cache = new UrlJarFiles.Cache();
      this.factory = factory;
   }

   JarFile getOrCreate(boolean useCaches, URL jarFileUrl) throws IOException {
      if (useCaches) {
         JarFile cached = this.getCached(jarFileUrl);
         if (cached != null) {
            return cached;
         }
      }

      return this.factory.createJarFile(jarFileUrl, this::onClose);
   }

   JarFile getCached(URL jarFileUrl) {
      return this.cache.get(jarFileUrl);
   }

   boolean cacheIfAbsent(boolean useCaches, URL jarFileUrl, JarFile jarFile) {
      return !useCaches ? false : this.cache.putIfAbsent(jarFileUrl, jarFile);
   }

   void closeIfNotCached(URL jarFileUrl, JarFile jarFile) throws IOException {
      JarFile cached = this.getCached(jarFileUrl);
      if (cached != jarFile) {
         jarFile.close();
      }

   }

   URLConnection reconnect(JarFile jarFile, URLConnection existingConnection) throws IOException {
      Boolean useCaches = existingConnection != null ? existingConnection.getUseCaches() : null;
      URLConnection connection = this.openConnection(jarFile);
      if (useCaches != null && connection != null) {
         connection.setUseCaches(useCaches);
      }

      return connection;
   }

   private URLConnection openConnection(JarFile jarFile) throws IOException {
      URL url = this.cache.get(jarFile);
      return url != null ? url.openConnection() : null;
   }

   private void onClose(JarFile jarFile) {
      this.cache.remove(jarFile);
   }

   void clearCache() {
      this.cache.clear();
   }

   private static class Cache {
      private final Map<String, JarFile> jarFileUrlToJarFile = new HashMap();
      private final Map<JarFile, URL> jarFileToJarFileUrl = new HashMap();

      JarFile get(URL jarFileUrl) {
         String urlKey = JarFileUrlKey.get(jarFileUrl);
         synchronized(this) {
            return (JarFile)this.jarFileUrlToJarFile.get(urlKey);
         }
      }

      URL get(JarFile jarFile) {
         synchronized(this) {
            return (URL)this.jarFileToJarFileUrl.get(jarFile);
         }
      }

      boolean putIfAbsent(URL jarFileUrl, JarFile jarFile) {
         String urlKey = JarFileUrlKey.get(jarFileUrl);
         synchronized(this) {
            JarFile cached = (JarFile)this.jarFileUrlToJarFile.get(urlKey);
            if (cached == null) {
               this.jarFileUrlToJarFile.put(urlKey, jarFile);
               this.jarFileToJarFileUrl.put(jarFile, jarFileUrl);
               return true;
            } else {
               return false;
            }
         }
      }

      void remove(JarFile jarFile) {
         synchronized(this) {
            URL removedUrl = (URL)this.jarFileToJarFileUrl.remove(jarFile);
            if (removedUrl != null) {
               this.jarFileUrlToJarFile.remove(JarFileUrlKey.get(removedUrl));
            }

         }
      }

      void clear() {
         synchronized(this) {
            this.jarFileToJarFileUrl.clear();
            this.jarFileUrlToJarFile.clear();
         }
      }
   }
}
