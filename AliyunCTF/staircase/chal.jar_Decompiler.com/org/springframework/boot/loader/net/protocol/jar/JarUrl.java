package org.springframework.boot.loader.net.protocol.jar;

import java.io.File;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.jar.JarEntry;

public final class JarUrl {
   private JarUrl() {
   }

   public static URL create(File file) {
      return create(file, (String)null);
   }

   public static URL create(File file, JarEntry nestedEntry) {
      return create(file, nestedEntry != null ? nestedEntry.getName() : null);
   }

   public static URL create(File file, String nestedEntryName) {
      return create(file, nestedEntryName, (String)null);
   }

   public static URL create(File file, String nestedEntryName, String path) {
      try {
         path = path != null ? path : "";
         return new URL((URL)null, "jar:" + getJarReference(file, nestedEntryName) + "!/" + path, Handler.INSTANCE);
      } catch (MalformedURLException var4) {
         throw new IllegalStateException("Unable to create JarFileArchive URL", var4);
      }
   }

   private static String getJarReference(File file, String nestedEntryName) {
      String jarFilePath = file.toURI().getPath();
      return nestedEntryName != null ? "nested:" + jarFilePath + "/!" + nestedEntryName : "file:" + jarFilePath;
   }
}
