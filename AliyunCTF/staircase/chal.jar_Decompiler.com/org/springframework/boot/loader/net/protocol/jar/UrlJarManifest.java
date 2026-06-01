package org.springframework.boot.loader.net.protocol.jar;

import java.io.IOException;
import java.util.Map;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.Manifest;

class UrlJarManifest {
   private static final Object NONE = new Object();
   private final UrlJarManifest.ManifestSupplier supplier;
   private volatile Object supplied;

   UrlJarManifest(UrlJarManifest.ManifestSupplier supplier) {
      this.supplier = supplier;
   }

   Manifest get() throws IOException {
      Manifest manifest = this.supply();
      if (manifest == null) {
         return null;
      } else {
         Manifest copy = new Manifest();
         copy.getMainAttributes().putAll((Map)manifest.getMainAttributes().clone());
         manifest.getEntries().forEach((key, value) -> {
            copy.getEntries().put(key, this.cloneAttributes(value));
         });
         return copy;
      }
   }

   Attributes getEntryAttributes(JarEntry entry) throws IOException {
      Manifest manifest = this.supply();
      if (manifest == null) {
         return null;
      } else {
         Attributes attributes = (Attributes)manifest.getEntries().get(entry.getName());
         return this.cloneAttributes(attributes);
      }
   }

   private Attributes cloneAttributes(Attributes attributes) {
      return attributes != null ? (Attributes)attributes.clone() : null;
   }

   private Manifest supply() throws IOException {
      Object supplied = this.supplied;
      if (supplied == null) {
         supplied = this.supplier.getManifest();
         this.supplied = supplied != null ? supplied : NONE;
      }

      return supplied != NONE ? (Manifest)supplied : null;
   }

   @FunctionalInterface
   interface ManifestSupplier {
      Manifest getManifest() throws IOException;
   }
}
