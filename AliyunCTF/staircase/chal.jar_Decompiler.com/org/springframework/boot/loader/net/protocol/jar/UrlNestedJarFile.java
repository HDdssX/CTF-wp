package org.springframework.boot.loader.net.protocol.jar;

import java.io.File;
import java.io.IOException;
import java.lang.Runtime.Version;
import java.util.function.Consumer;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.Manifest;
import org.springframework.boot.loader.jar.NestedJarFile;

class UrlNestedJarFile extends NestedJarFile {
   private final UrlJarManifest manifest = new UrlJarManifest(() -> {
      return super.getManifest();
   });
   private final Consumer<JarFile> closeAction;

   UrlNestedJarFile(File file, String nestedEntryName, Version version, Consumer<JarFile> closeAction) throws IOException {
      super(file, nestedEntryName, version);
      this.closeAction = closeAction;
   }

   public Manifest getManifest() throws IOException {
      return this.manifest.get();
   }

   public JarEntry getEntry(String name) {
      return UrlJarEntry.of(super.getEntry(name), this.manifest);
   }

   public void close() throws IOException {
      if (this.closeAction != null) {
         this.closeAction.accept(this);
      }

      super.close();
   }
}
