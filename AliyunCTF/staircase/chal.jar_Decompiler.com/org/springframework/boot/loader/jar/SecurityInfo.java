package org.springframework.boot.loader.jar;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.security.CodeSigner;
import java.security.cert.Certificate;
import java.util.jar.JarEntry;
import java.util.jar.JarInputStream;
import org.springframework.boot.loader.zip.ZipContent;

final class SecurityInfo {
   static final SecurityInfo NONE = new SecurityInfo((Certificate[][])null, (CodeSigner[][])null);
   private final Certificate[][] certificateLookups;
   private final CodeSigner[][] codeSignerLookups;

   private SecurityInfo(Certificate[][] entryCertificates, CodeSigner[][] entryCodeSigners) {
      this.certificateLookups = entryCertificates;
      this.codeSignerLookups = entryCodeSigners;
   }

   Certificate[] getCertificates(ZipContent.Entry contentEntry) {
      return this.certificateLookups != null ? (Certificate[])this.clone(this.certificateLookups[contentEntry.getLookupIndex()]) : null;
   }

   CodeSigner[] getCodeSigners(ZipContent.Entry contentEntry) {
      return this.codeSignerLookups != null ? (CodeSigner[])this.clone(this.codeSignerLookups[contentEntry.getLookupIndex()]) : null;
   }

   private <T> T[] clone(T[] array) {
      return array != null ? (Object[])array.clone() : null;
   }

   static SecurityInfo get(ZipContent content) {
      if (!content.hasJarSignatureFile()) {
         return NONE;
      } else {
         try {
            return load(content);
         } catch (IOException var2) {
            throw new UncheckedIOException(var2);
         }
      }
   }

   private static SecurityInfo load(ZipContent content) throws IOException {
      int size = content.size();
      boolean hasSecurityInfo = false;
      Certificate[][] entryCertificates = new Certificate[size][];
      CodeSigner[][] entryCodeSigners = new CodeSigner[size][];
      JarInputStream in = new JarInputStream(content.openRawZipData().asInputStream());

      SecurityInfo var12;
      try {
         JarEntry jarEntry = in.getNextJarEntry();

         while(true) {
            if (jarEntry == null) {
               var12 = !hasSecurityInfo ? NONE : new SecurityInfo(entryCertificates, entryCodeSigners);
               break;
            }

            in.closeEntry();
            Certificate[] certificates = jarEntry.getCertificates();
            CodeSigner[] codeSigners = jarEntry.getCodeSigners();
            if (certificates != null || codeSigners != null) {
               ZipContent.Entry contentEntry = content.getEntry(jarEntry.getName());
               if (contentEntry != null) {
                  hasSecurityInfo = true;
                  entryCertificates[contentEntry.getLookupIndex()] = certificates;
                  entryCodeSigners[contentEntry.getLookupIndex()] = codeSigners;
               }
            }

            jarEntry = in.getNextJarEntry();
         }
      } catch (Throwable var11) {
         try {
            in.close();
         } catch (Throwable var10) {
            var11.addSuppressed(var10);
         }

         throw var11;
      }

      in.close();
      return var12;
   }
}
