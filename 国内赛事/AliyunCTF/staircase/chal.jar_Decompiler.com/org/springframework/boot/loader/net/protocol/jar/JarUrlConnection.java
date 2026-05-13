package org.springframework.boot.loader.net.protocol.jar;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.JarURLConnection;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLStreamHandler;
import java.security.Permission;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import org.springframework.boot.loader.jar.NestedJarFile;
import org.springframework.boot.loader.net.util.UrlDecoder;

final class JarUrlConnection extends JarURLConnection {
   static final UrlJarFiles jarFiles = new UrlJarFiles();
   static final InputStream emptyInputStream = new ByteArrayInputStream(new byte[0]);
   static final FileNotFoundException FILE_NOT_FOUND_EXCEPTION = new FileNotFoundException("Jar file or entry not found");
   private static final URL NOT_FOUND_URL;
   static final JarUrlConnection NOT_FOUND_CONNECTION;
   private final String entryName;
   private final Supplier<FileNotFoundException> notFound;
   private JarFile jarFile;
   private URLConnection jarFileConnection;
   private JarEntry jarEntry;
   private String contentType;

   private JarUrlConnection(URL url) throws IOException {
      super(url);
      this.entryName = this.getEntryName();
      this.notFound = null;
      this.jarFileConnection = this.getJarFileURL().openConnection();
      this.jarFileConnection.setUseCaches(this.useCaches);
   }

   private JarUrlConnection(Supplier<FileNotFoundException> notFound) throws IOException {
      super(NOT_FOUND_URL);
      this.entryName = null;
      this.notFound = notFound;
   }

   public JarFile getJarFile() throws IOException {
      this.connect();
      return this.jarFile;
   }

   public JarEntry getJarEntry() throws IOException {
      this.connect();
      return this.jarEntry;
   }

   public int getContentLength() {
      long contentLength = this.getContentLengthLong();
      return contentLength <= 2147483647L ? (int)contentLength : -1;
   }

   public long getContentLengthLong() {
      try {
         this.connect();
         return this.jarEntry != null ? this.jarEntry.getSize() : this.jarFileConnection.getContentLengthLong();
      } catch (IOException var2) {
         return -1L;
      }
   }

   public String getContentType() {
      if (this.contentType == null) {
         this.contentType = this.deduceContentType();
      }

      return this.contentType;
   }

   private String deduceContentType() {
      String type = this.entryName != null ? null : "x-java/jar";
      type = type != null ? type : this.deduceContentTypeFromStream();
      type = type != null ? type : this.deduceContentTypeFromEntryName();
      return type != null ? type : "content/unknown";
   }

   private String deduceContentTypeFromStream() {
      try {
         this.connect();
         InputStream in = this.jarFile.getInputStream(this.jarEntry);

         String var2;
         try {
            var2 = guessContentTypeFromStream(new BufferedInputStream(in));
         } catch (Throwable var5) {
            if (in != null) {
               try {
                  in.close();
               } catch (Throwable var4) {
                  var5.addSuppressed(var4);
               }
            }

            throw var5;
         }

         if (in != null) {
            in.close();
         }

         return var2;
      } catch (IOException var6) {
         return null;
      }
   }

   private String deduceContentTypeFromEntryName() {
      return guessContentTypeFromName(this.entryName);
   }

   public long getLastModified() {
      return this.jarFileConnection != null ? this.jarFileConnection.getLastModified() : super.getLastModified();
   }

   public String getHeaderField(String name) {
      return this.jarFileConnection != null ? this.jarFileConnection.getHeaderField(name) : null;
   }

   public Object getContent() throws IOException {
      this.connect();
      return this.entryName != null ? super.getContent() : this.jarFile;
   }

   public Permission getPermission() throws IOException {
      return this.jarFileConnection.getPermission();
   }

   public InputStream getInputStream() throws IOException {
      if (this.notFound != null) {
         this.throwFileNotFound();
      }

      URL jarFileURL = this.getJarFileURL();
      if (this.entryName == null && !UrlJarFileFactory.isNestedUrl(jarFileURL)) {
         throw new IOException("no entry name specified");
      } else {
         if (!this.getUseCaches() && Optimizations.isEnabled(false) && this.entryName != null) {
            JarFile cached = jarFiles.getCached(jarFileURL);
            if (cached != null && cached.getEntry(this.entryName) != null) {
               return emptyInputStream;
            }
         }

         this.connect();
         if (this.jarEntry == null) {
            JarFile var3 = this.jarFile;
            if (var3 instanceof NestedJarFile) {
               NestedJarFile nestedJarFile = (NestedJarFile)var3;
               return nestedJarFile.getRawZipDataInputStream();
            }

            this.throwFileNotFound();
         }

         return new JarUrlConnection.ConnectionInputStream();
      }
   }

   public boolean getAllowUserInteraction() {
      return this.jarFileConnection != null ? this.jarFileConnection.getAllowUserInteraction() : false;
   }

   public void setAllowUserInteraction(boolean allowuserinteraction) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.setAllowUserInteraction(allowuserinteraction);
      }

   }

   public boolean getUseCaches() {
      return this.jarFileConnection != null ? this.jarFileConnection.getUseCaches() : true;
   }

   public void setUseCaches(boolean usecaches) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.setUseCaches(usecaches);
      }

   }

   public boolean getDefaultUseCaches() {
      return this.jarFileConnection != null ? this.jarFileConnection.getDefaultUseCaches() : true;
   }

   public void setDefaultUseCaches(boolean defaultusecaches) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.setDefaultUseCaches(defaultusecaches);
      }

   }

   public void setIfModifiedSince(long ifModifiedSince) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.setIfModifiedSince(ifModifiedSince);
      }

   }

   public String getRequestProperty(String key) {
      return this.jarFileConnection != null ? this.jarFileConnection.getRequestProperty(key) : null;
   }

   public void setRequestProperty(String key, String value) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.setRequestProperty(key, value);
      }

   }

   public void addRequestProperty(String key, String value) {
      if (this.jarFileConnection != null) {
         this.jarFileConnection.addRequestProperty(key, value);
      }

   }

   public Map<String, List<String>> getRequestProperties() {
      return this.jarFileConnection != null ? this.jarFileConnection.getRequestProperties() : Collections.emptyMap();
   }

   public void connect() throws IOException {
      if (!this.connected) {
         if (this.notFound != null) {
            this.throwFileNotFound();
         }

         boolean useCaches = this.getUseCaches();
         URL jarFileURL = this.getJarFileURL();
         if (this.entryName != null && Optimizations.isEnabled()) {
            this.assertCachedJarFileHasEntry(jarFileURL, this.entryName);
         }

         this.jarFile = jarFiles.getOrCreate(useCaches, jarFileURL);
         this.jarEntry = this.getJarEntry(jarFileURL);
         boolean addedToCache = jarFiles.cacheIfAbsent(useCaches, jarFileURL, this.jarFile);
         if (addedToCache) {
            this.jarFileConnection = jarFiles.reconnect(this.jarFile, this.jarFileConnection);
         }

         this.connected = true;
      }
   }

   private void assertCachedJarFileHasEntry(URL jarFileURL, String entryName) throws FileNotFoundException {
      JarFile cachedJarFile = jarFiles.getCached(jarFileURL);
      if (cachedJarFile != null && cachedJarFile.getJarEntry(entryName) == null) {
         throw FILE_NOT_FOUND_EXCEPTION;
      }
   }

   private JarEntry getJarEntry(URL jarFileUrl) throws IOException {
      if (this.entryName == null) {
         return null;
      } else {
         JarEntry jarEntry = this.jarFile.getJarEntry(this.entryName);
         if (jarEntry == null) {
            jarFiles.closeIfNotCached(jarFileUrl, this.jarFile);
            this.throwFileNotFound();
         }

         return jarEntry;
      }
   }

   private void throwFileNotFound() throws FileNotFoundException {
      if (Optimizations.isEnabled()) {
         throw FILE_NOT_FOUND_EXCEPTION;
      } else if (this.notFound != null) {
         throw (FileNotFoundException)this.notFound.get();
      } else {
         String var10002 = this.entryName;
         throw new FileNotFoundException("JAR entry " + var10002 + " not found in " + this.jarFile.getName());
      }
   }

   static JarUrlConnection open(URL url) throws IOException {
      String spec = url.getFile();
      if (spec.startsWith("nested:")) {
         int separator = spec.indexOf("!/");
         boolean specHasEntry = separator != -1 && separator + 2 != spec.length();
         if (specHasEntry) {
            URL jarFileUrl = new URL(spec.substring(0, separator));
            if ("runtime".equals(url.getRef())) {
               jarFileUrl = new URL(jarFileUrl, "#runtime");
            }

            String entryName = UrlDecoder.decode(spec.substring(separator + 2));
            JarFile jarFile = jarFiles.getOrCreate(true, jarFileUrl);
            jarFiles.cacheIfAbsent(true, jarFileUrl, jarFile);
            if (!hasEntry(jarFile, entryName)) {
               return notFoundConnection(jarFile.getName(), entryName);
            }
         }
      }

      return new JarUrlConnection(url);
   }

   private static boolean hasEntry(JarFile jarFile, String name) {
      boolean var10000;
      if (jarFile instanceof NestedJarFile) {
         NestedJarFile nestedJarFile = (NestedJarFile)jarFile;
         var10000 = nestedJarFile.hasEntry(name);
      } else {
         var10000 = jarFile.getEntry(name) != null;
      }

      return var10000;
   }

   private static JarUrlConnection notFoundConnection(String jarFileName, String entryName) throws IOException {
      return Optimizations.isEnabled() ? NOT_FOUND_CONNECTION : new JarUrlConnection(() -> {
         return new FileNotFoundException("JAR entry " + entryName + " not found in " + jarFileName);
      });
   }

   static void clearCache() {
      jarFiles.clearCache();
   }

   static {
      try {
         NOT_FOUND_URL = new URL("jar:", (String)null, 0, "nested:!/", new JarUrlConnection.EmptyUrlStreamHandler());
         NOT_FOUND_CONNECTION = new JarUrlConnection(() -> {
            return FILE_NOT_FOUND_EXCEPTION;
         });
      } catch (IOException var1) {
         throw new IllegalStateException(var1);
      }
   }

   class ConnectionInputStream extends LazyDelegatingInputStream {
      public void close() throws IOException {
         try {
            super.close();
         } finally {
            if (!JarUrlConnection.this.getUseCaches()) {
               JarUrlConnection.this.jarFile.close();
            }

         }

      }

      protected InputStream getDelegateInputStream() throws IOException {
         return JarUrlConnection.this.jarFile.getInputStream(JarUrlConnection.this.jarEntry);
      }
   }

   private static class EmptyUrlStreamHandler extends URLStreamHandler {
      protected URLConnection openConnection(URL url) {
         return null;
      }
   }
}
