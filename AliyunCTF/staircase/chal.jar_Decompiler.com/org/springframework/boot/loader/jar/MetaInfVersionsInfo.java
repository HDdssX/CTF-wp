package org.springframework.boot.loader.jar;

import java.util.Collections;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.IntFunction;
import org.springframework.boot.loader.zip.ZipContent;

final class MetaInfVersionsInfo {
   static final MetaInfVersionsInfo NONE = new MetaInfVersionsInfo(Collections.emptySet());
   private static final String META_INF_VERSIONS = "META-INF/versions/";
   private final int[] versions;
   private final String[] directories;

   private MetaInfVersionsInfo(Set<Integer> versions) {
      this.versions = versions.stream().mapToInt(Integer::intValue).toArray();
      this.directories = (String[])versions.stream().map((version) -> {
         return "META-INF/versions/" + version + "/";
      }).toArray((x$0) -> {
         return new String[x$0];
      });
   }

   int[] versions() {
      return this.versions;
   }

   String[] directories() {
      return this.directories;
   }

   static MetaInfVersionsInfo get(ZipContent zipContent) {
      int var10000 = zipContent.size();
      Objects.requireNonNull(zipContent);
      return get(var10000, zipContent::getEntry);
   }

   static MetaInfVersionsInfo get(int size, IntFunction<ZipContent.Entry> entries) {
      Set<Integer> versions = new TreeSet();

      for(int i = 0; i < size; ++i) {
         ZipContent.Entry contentEntry = (ZipContent.Entry)entries.apply(i);
         if (contentEntry.hasNameStartingWith("META-INF/versions/") && !contentEntry.isDirectory()) {
            String name = contentEntry.getName();
            int slash = name.indexOf(47, "META-INF/versions/".length());
            String version = name.substring("META-INF/versions/".length(), slash);

            try {
               int versionNumber = Integer.parseInt(version);
               if (versionNumber >= NestedJarFile.BASE_VERSION) {
                  versions.add(versionNumber);
               }
            } catch (NumberFormatException var9) {
            }
         }
      }

      return !versions.isEmpty() ? new MetaInfVersionsInfo(versions) : NONE;
   }
}
