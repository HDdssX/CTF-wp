package org.springframework.boot.loader.net.protocol.jar;

import java.io.IOException;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.zip.ZipEntry;

final class UrlJarEntry extends JarEntry {
   private final UrlJarManifest manifest;

   private UrlJarEntry(JarEntry entry, UrlJarManifest manifest) {
      super(entry);
      this.manifest = manifest;
   }

   public Attributes getAttributes() throws IOException {
      return this.manifest.getEntryAttributes(this);
   }

   static UrlJarEntry of(ZipEntry entry, UrlJarManifest manifest) {
      return entry != null ? new UrlJarEntry((JarEntry)entry, manifest) : null;
   }
}
