package org.springframework.boot.loader.net.protocol.jar;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.lang.Runtime.Version;
import java.net.URL;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.function.Consumer;
import java.util.jar.JarFile;
import org.springframework.boot.loader.net.protocol.nested.NestedLocation;
import org.springframework.boot.loader.net.util.UrlDecoder;

class UrlJarFileFactory {
   JarFile createJarFile(URL jarFileUrl, Consumer<JarFile> closeAction) throws IOException {
      Version version = this.getVersion(jarFileUrl);
      if (this.isLocalFileUrl(jarFileUrl)) {
         return this.createJarFileForLocalFile(jarFileUrl, version, closeAction);
      } else {
         return isNestedUrl(jarFileUrl) ? this.createJarFileForNested(jarFileUrl, version, closeAction) : this.createJarFileForStream(jarFileUrl, version, closeAction);
      }
   }

   private Version getVersion(URL url) {
      return "base".equals(url.getRef()) ? JarFile.baseVersion() : JarFile.runtimeVersion();
   }

   private boolean isLocalFileUrl(URL url) {
      return url.getProtocol().equalsIgnoreCase("file") && this.isLocal(url.getHost());
   }

   private boolean isLocal(String host) {
      return host == null || host.isEmpty() || host.equals("~") || host.equalsIgnoreCase("localhost");
   }

   private JarFile createJarFileForLocalFile(URL url, Version version, Consumer<JarFile> closeAction) throws IOException {
      String path = UrlDecoder.decode(url.getPath());
      return new UrlJarFile(new File(path), version, closeAction);
   }

   private JarFile createJarFileForNested(URL url, Version version, Consumer<JarFile> closeAction) throws IOException {
      NestedLocation location = NestedLocation.fromUrl(url);
      return new UrlNestedJarFile(location.path().toFile(), location.nestedEntryName(), version, closeAction);
   }

   private JarFile createJarFileForStream(URL url, Version version, Consumer<JarFile> closeAction) throws IOException {
      InputStream in = url.openStream();

      JarFile var5;
      try {
         var5 = this.createJarFileForStream(in, version, closeAction);
      } catch (Throwable var8) {
         if (in != null) {
            try {
               in.close();
            } catch (Throwable var7) {
               var8.addSuppressed(var7);
            }
         }

         throw var8;
      }

      if (in != null) {
         in.close();
      }

      return var5;
   }

   private JarFile createJarFileForStream(InputStream in, Version version, Consumer<JarFile> closeAction) throws IOException {
      Path local = Files.createTempFile("jar_cache", (String)null);

      try {
         Files.copy(in, local, new CopyOption[]{StandardCopyOption.REPLACE_EXISTING});
         JarFile jarFile = new UrlJarFile(local.toFile(), version, closeAction);
         local.toFile().deleteOnExit();
         return jarFile;
      } catch (Throwable var6) {
         this.deleteIfPossible(local, var6);
         throw var6;
      }
   }

   private void deleteIfPossible(Path local, Throwable cause) {
      try {
         Files.delete(local);
      } catch (IOException var4) {
         cause.addSuppressed(var4);
      }

   }

   static boolean isNestedUrl(URL url) {
      return url.getProtocol().equalsIgnoreCase("nested");
   }
}
