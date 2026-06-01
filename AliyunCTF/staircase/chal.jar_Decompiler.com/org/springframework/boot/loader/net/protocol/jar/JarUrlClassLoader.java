package org.springframework.boot.loader.net.protocol.jar;

import java.io.IOException;
import java.net.JarURLConnection;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.URLConnection;
import java.util.Arrays;
import java.util.Collections;
import java.util.Enumeration;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.jar.JarFile;
import org.springframework.boot.loader.jar.NestedJarFile;

public abstract class JarUrlClassLoader extends URLClassLoader {
   private final URL[] urls;
   private final boolean hasJarUrls;
   private final Map<URL, JarFile> jarFiles = new ConcurrentHashMap();
   private final Set<String> undefinablePackages = Collections.newSetFromMap(new ConcurrentHashMap());

   public JarUrlClassLoader(URL[] urls, ClassLoader parent) {
      super(urls, parent);
      this.urls = urls;
      this.hasJarUrls = Arrays.stream(urls).anyMatch(this::isJarUrl);
   }

   public URL findResource(String name) {
      if (!this.hasJarUrls) {
         return super.findResource(name);
      } else {
         Optimizations.enable(false);

         URL var2;
         try {
            var2 = super.findResource(name);
         } finally {
            Optimizations.disable();
         }

         return var2;
      }
   }

   public Enumeration<URL> findResources(String name) throws IOException {
      if (!this.hasJarUrls) {
         return super.findResources(name);
      } else {
         Optimizations.enable(false);

         JarUrlClassLoader.OptimizedEnumeration var2;
         try {
            var2 = new JarUrlClassLoader.OptimizedEnumeration(super.findResources(name));
         } finally {
            Optimizations.disable();
         }

         return var2;
      }
   }

   protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
      if (!this.hasJarUrls) {
         return super.loadClass(name, resolve);
      } else {
         Optimizations.enable(true);

         Class var3;
         try {
            try {
               this.definePackageIfNecessary(name);
            } catch (IllegalArgumentException var7) {
               this.tolerateRaceConditionDueToBeingParallelCapable(var7, name);
            }

            var3 = super.loadClass(name, resolve);
         } finally {
            Optimizations.disable();
         }

         return var3;
      }
   }

   protected final void definePackageIfNecessary(String className) {
      if (!className.startsWith("java.")) {
         int lastDot = className.lastIndexOf(46);
         if (lastDot >= 0) {
            String packageName = className.substring(0, lastDot);
            if (this.getDefinedPackage(packageName) == null) {
               try {
                  this.definePackage(className, packageName);
               } catch (IllegalArgumentException var5) {
                  this.tolerateRaceConditionDueToBeingParallelCapable(var5, packageName);
               }
            }
         }

      }
   }

   private void definePackage(String className, String packageName) {
      if (!this.undefinablePackages.contains(packageName)) {
         String packageEntryName = packageName.replace('.', '/') + "/";
         String classEntryName = className.replace('.', '/') + ".class";
         URL[] var5 = this.urls;
         int var6 = var5.length;

         for(int var7 = 0; var7 < var6; ++var7) {
            URL url = var5[var7];

            try {
               JarFile jarFile = this.getJarFile(url);
               if (jarFile != null && this.hasEntry(jarFile, classEntryName) && this.hasEntry(jarFile, packageEntryName) && jarFile.getManifest() != null) {
                  this.definePackage(packageName, jarFile.getManifest(), url);
                  return;
               }
            } catch (IOException var10) {
            }
         }

         this.undefinablePackages.add(packageName);
      }
   }

   private void tolerateRaceConditionDueToBeingParallelCapable(IllegalArgumentException ex, String packageName) throws AssertionError {
      if (this.getDefinedPackage(packageName) == null) {
         throw new AssertionError("Package %s has already been defined but it could not be found".formatted(new Object[]{packageName}), ex);
      }
   }

   private boolean hasEntry(JarFile jarFile, String name) {
      boolean var10000;
      if (jarFile instanceof NestedJarFile) {
         NestedJarFile nestedJarFile = (NestedJarFile)jarFile;
         var10000 = nestedJarFile.hasEntry(name);
      } else {
         var10000 = jarFile.getEntry(name) != null;
      }

      return var10000;
   }

   private JarFile getJarFile(URL url) throws IOException {
      JarFile jarFile = (JarFile)this.jarFiles.get(url);
      if (jarFile != null) {
         return jarFile;
      } else {
         URLConnection connection = url.openConnection();
         if (!(connection instanceof JarURLConnection)) {
            return null;
         } else {
            connection.setUseCaches(false);
            jarFile = ((JarURLConnection)connection).getJarFile();
            synchronized(this.jarFiles) {
               JarFile previous = (JarFile)this.jarFiles.putIfAbsent(url, jarFile);
               if (previous != null) {
                  jarFile.close();
                  jarFile = previous;
               }

               return jarFile;
            }
         }
      }
   }

   public void clearCache() {
      Handler.clearCache();
      org.springframework.boot.loader.net.protocol.nested.Handler.clearCache();

      try {
         this.clearJarFiles();
      } catch (IOException var5) {
      }

      URL[] var1 = this.urls;
      int var2 = var1.length;

      for(int var3 = 0; var3 < var2; ++var3) {
         URL url = var1[var3];
         if (this.isJarUrl(url)) {
            this.clearCache(url);
         }
      }

   }

   private void clearCache(URL url) {
      try {
         URLConnection connection = url.openConnection();
         if (connection instanceof JarURLConnection) {
            JarURLConnection jarUrlConnection = (JarURLConnection)connection;
            this.clearCache(jarUrlConnection);
         }
      } catch (IOException var4) {
      }

   }

   private void clearCache(JarURLConnection connection) throws IOException {
      JarFile jarFile = connection.getJarFile();
      if (jarFile instanceof NestedJarFile) {
         NestedJarFile nestedJarFile = (NestedJarFile)jarFile;
         nestedJarFile.clearCache();
      }

   }

   private boolean isJarUrl(URL url) {
      return "jar".equals(url.getProtocol());
   }

   public void close() throws IOException {
      super.close();
      this.clearJarFiles();
   }

   private void clearJarFiles() throws IOException {
      synchronized(this.jarFiles) {
         Iterator var2 = this.jarFiles.values().iterator();

         while(var2.hasNext()) {
            JarFile jarFile = (JarFile)var2.next();
            jarFile.close();
         }

         this.jarFiles.clear();
      }
   }

   private static class OptimizedEnumeration implements Enumeration<URL> {
      private final Enumeration<URL> delegate;

      OptimizedEnumeration(Enumeration<URL> delegate) {
         this.delegate = delegate;
      }

      public boolean hasMoreElements() {
         Optimizations.enable(false);

         boolean var1;
         try {
            var1 = this.delegate.hasMoreElements();
         } finally {
            Optimizations.disable();
         }

         return var1;
      }

      public URL nextElement() {
         Optimizations.enable(false);

         URL var1;
         try {
            var1 = (URL)this.delegate.nextElement();
         } finally {
            Optimizations.disable();
         }

         return var1;
      }
   }
}
