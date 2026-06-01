package org.springframework.boot.loader.launch;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URL;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;
import java.util.jar.Manifest;

class ExplodedArchive implements Archive {
   private static final Object NO_MANIFEST = new Object();
   private static final Set<String> SKIPPED_NAMES = Set.of(".", "..");
   private static final Comparator<File> entryComparator = Comparator.comparing(File::getAbsolutePath);
   private final File rootDirectory;
   private final String rootUriPath;
   private volatile Object manifest;

   ExplodedArchive(File rootDirectory) {
      if (rootDirectory.exists() && rootDirectory.isDirectory()) {
         this.rootDirectory = rootDirectory;
         this.rootUriPath = this.rootDirectory.toURI().getPath();
      } else {
         throw new IllegalArgumentException("Invalid source directory " + rootDirectory);
      }
   }

   public Manifest getManifest() throws IOException {
      Object manifest = this.manifest;
      if (manifest == null) {
         manifest = this.loadManifest();
         this.manifest = manifest;
      }

      return manifest != NO_MANIFEST ? (Manifest)manifest : null;
   }

   private Object loadManifest() throws IOException {
      File file = new File(this.rootDirectory, "META-INF/MANIFEST.MF");
      if (!file.exists()) {
         return NO_MANIFEST;
      } else {
         FileInputStream inputStream = new FileInputStream(file);

         Manifest var3;
         try {
            var3 = new Manifest(inputStream);
         } catch (Throwable var6) {
            try {
               inputStream.close();
            } catch (Throwable var5) {
               var6.addSuppressed(var5);
            }

            throw var6;
         }

         inputStream.close();
         return var3;
      }
   }

   public Set<URL> getClassPathUrls(Predicate<Archive.Entry> includeFilter, Predicate<Archive.Entry> directorySearchFilter) throws IOException {
      Set<URL> urls = new LinkedHashSet();
      LinkedList files = new LinkedList(this.listFiles(this.rootDirectory));

      while(!files.isEmpty()) {
         File file = (File)files.poll();
         if (!SKIPPED_NAMES.contains(file.getName())) {
            String entryName = file.toURI().getPath().substring(this.rootUriPath.length());
            Archive.Entry entry = new ExplodedArchive.FileArchiveEntry(entryName, file);
            if (entry.isDirectory() && directorySearchFilter.test(entry)) {
               files.addAll(0, this.listFiles(file));
            }

            if (includeFilter.test(entry)) {
               urls.add(file.toURI().toURL());
            }
         }
      }

      return urls;
   }

   private List<File> listFiles(File file) {
      File[] files = file.listFiles();
      if (files == null) {
         return Collections.emptyList();
      } else {
         Arrays.sort(files, entryComparator);
         return Arrays.asList(files);
      }
   }

   public File getRootDirectory() {
      return this.rootDirectory;
   }

   public String toString() {
      return this.rootDirectory.toString();
   }

   private static record FileArchiveEntry(String name, File file) implements Archive.Entry {
      private FileArchiveEntry(String name, File file) {
         this.name = name;
         this.file = file;
      }

      public boolean isDirectory() {
         return this.file.isDirectory();
      }

      public String name() {
         return this.name;
      }

      public File file() {
         return this.file;
      }
   }
}
