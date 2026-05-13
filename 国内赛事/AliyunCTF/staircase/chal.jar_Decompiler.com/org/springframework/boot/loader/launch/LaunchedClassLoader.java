package org.springframework.boot.loader.launch;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.function.Supplier;
import java.util.jar.Manifest;
import org.springframework.boot.loader.net.protocol.jar.JarUrlClassLoader;

public class LaunchedClassLoader extends JarUrlClassLoader {
   private static final String JAR_MODE_PACKAGE_PREFIX = "org.springframework.boot.loader.jarmode.";
   private static final String JAR_MODE_RUNNER_CLASS_NAME = JarModeRunner.class.getName();
   private final boolean exploded;
   private final Archive rootArchive;
   private final Object definePackageLock;
   private volatile LaunchedClassLoader.DefinePackageCallType definePackageCallType;

   public LaunchedClassLoader(boolean exploded, URL[] urls, ClassLoader parent) {
      this(exploded, (Archive)null, urls, parent);
   }

   public LaunchedClassLoader(boolean exploded, Archive rootArchive, URL[] urls, ClassLoader parent) {
      super(urls, parent);
      this.definePackageLock = new Object();
      this.exploded = exploded;
      this.rootArchive = rootArchive;
   }

   protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
      if (name.startsWith("org.springframework.boot.loader.jarmode.") || name.equals(JAR_MODE_RUNNER_CLASS_NAME)) {
         try {
            Class<?> result = this.loadClassInLaunchedClassLoader(name);
            if (resolve) {
               this.resolveClass(result);
            }

            return result;
         } catch (ClassNotFoundException var4) {
         }
      }

      return super.loadClass(name, resolve);
   }

   private Class<?> loadClassInLaunchedClassLoader(String name) throws ClassNotFoundException {
      try {
         String internalName = name.replace('.', '/') + ".class";
         InputStream inputStream = this.getParent().getResourceAsStream(internalName);

         Class var7;
         try {
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

            try {
               if (inputStream == null) {
                  throw new ClassNotFoundException(name);
               }

               inputStream.transferTo(outputStream);
               byte[] bytes = outputStream.toByteArray();
               Class<?> definedClass = this.defineClass(name, bytes, 0, bytes.length);
               this.definePackageIfNecessary(name);
               var7 = definedClass;
            } catch (Throwable var10) {
               try {
                  outputStream.close();
               } catch (Throwable var9) {
                  var10.addSuppressed(var9);
               }

               throw var10;
            }

            outputStream.close();
         } catch (Throwable var11) {
            if (inputStream != null) {
               try {
                  inputStream.close();
               } catch (Throwable var8) {
                  var11.addSuppressed(var8);
               }
            }

            throw var11;
         }

         if (inputStream != null) {
            inputStream.close();
         }

         return var7;
      } catch (IOException var12) {
         throw new ClassNotFoundException("Cannot load resource for class [" + name + "]", var12);
      }
   }

   protected Package definePackage(String name, Manifest man, URL url) throws IllegalArgumentException {
      return !this.exploded ? super.definePackage(name, man, url) : this.definePackageForExploded(name, man, url);
   }

   private Package definePackageForExploded(String name, Manifest man, URL url) {
      synchronized(this.definePackageLock) {
         return (Package)this.definePackage(LaunchedClassLoader.DefinePackageCallType.MANIFEST, () -> {
            return super.definePackage(name, man, url);
         });
      }
   }

   protected Package definePackage(String name, String specTitle, String specVersion, String specVendor, String implTitle, String implVersion, String implVendor, URL sealBase) throws IllegalArgumentException {
      return !this.exploded ? super.definePackage(name, specTitle, specVersion, specVendor, implTitle, implVersion, implVendor, sealBase) : this.definePackageForExploded(name, sealBase, () -> {
         return super.definePackage(name, specTitle, specVersion, specVendor, implTitle, implVersion, implVendor, sealBase);
      });
   }

   private Package definePackageForExploded(String name, URL sealBase, Supplier<Package> call) {
      synchronized(this.definePackageLock) {
         if (this.definePackageCallType == null) {
            Manifest manifest = this.getManifest(this.rootArchive);
            if (manifest != null) {
               return this.definePackage(name, manifest, sealBase);
            }
         }

         return (Package)this.definePackage(LaunchedClassLoader.DefinePackageCallType.ATTRIBUTES, call);
      }
   }

   private <T> T definePackage(LaunchedClassLoader.DefinePackageCallType type, Supplier<T> call) {
      LaunchedClassLoader.DefinePackageCallType existingType = this.definePackageCallType;

      Object var4;
      try {
         this.definePackageCallType = type;
         var4 = call.get();
      } finally {
         this.definePackageCallType = existingType;
      }

      return var4;
   }

   private Manifest getManifest(Archive archive) {
      try {
         return archive != null ? archive.getManifest() : null;
      } catch (IOException var3) {
         return null;
      }
   }

   static {
      ClassLoader.registerAsParallelCapable();
   }

   private static enum DefinePackageCallType {
      MANIFEST,
      ATTRIBUTES;

      // $FF: synthetic method
      private static LaunchedClassLoader.DefinePackageCallType[] $values() {
         return new LaunchedClassLoader.DefinePackageCallType[]{MANIFEST, ATTRIBUTES};
      }
   }
}
