package org.springframework.boot.loader.jar;

import java.util.jar.Attributes;
import java.util.jar.Manifest;
import java.util.jar.Attributes.Name;

class ManifestInfo {
   private static final Name MULTI_RELEASE = new Name("Multi-Release");
   static final ManifestInfo NONE = new ManifestInfo((Manifest)null, false);
   private final Manifest manifest;
   private volatile Boolean multiRelease;

   ManifestInfo(Manifest manifest) {
      this(manifest, (Boolean)null);
   }

   private ManifestInfo(Manifest manifest, Boolean multiRelease) {
      this.manifest = manifest;
      this.multiRelease = multiRelease;
   }

   Manifest getManifest() {
      return this.manifest;
   }

   boolean isMultiRelease() {
      if (this.manifest == null) {
         return false;
      } else {
         Boolean multiRelease = this.multiRelease;
         if (multiRelease != null) {
            return multiRelease;
         } else {
            Attributes attributes = this.manifest.getMainAttributes();
            multiRelease = attributes.containsKey(MULTI_RELEASE);
            this.multiRelease = multiRelease;
            return multiRelease;
         }
      }
   }
}
