package org.springframework.boot.loader.launch;

import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Set;
import java.util.jar.Attributes;
import java.util.jar.Manifest;

public abstract class ExecutableArchiveLauncher extends Launcher {
   private static final String START_CLASS_ATTRIBUTE = "Start-Class";
   protected static final String BOOT_CLASSPATH_INDEX_ATTRIBUTE = "Spring-Boot-Classpath-Index";
   protected static final String DEFAULT_CLASSPATH_INDEX_FILE_NAME = "classpath.idx";
   private final Archive archive;
   private final ClassPathIndexFile classPathIndex;

   public ExecutableArchiveLauncher() throws Exception {
      this(Archive.create(Launcher.class));
   }

   protected ExecutableArchiveLauncher(Archive archive) throws Exception {
      this.archive = archive;
      this.classPathIndex = this.getClassPathIndex(this.archive);
   }

   ClassPathIndexFile getClassPathIndex(Archive archive) throws IOException {
      if (!archive.isExploded()) {
         return null;
      } else {
         String location = this.getClassPathIndexFileLocation(archive);
         return ClassPathIndexFile.loadIfPossible(archive.getRootDirectory(), location);
      }
   }

   private String getClassPathIndexFileLocation(Archive archive) throws IOException {
      Manifest manifest = archive.getManifest();
      Attributes attributes = manifest != null ? manifest.getMainAttributes() : null;
      String location = attributes != null ? attributes.getValue("Spring-Boot-Classpath-Index") : null;
      return location != null ? location : this.getEntryPathPrefix() + "classpath.idx";
   }

   protected ClassLoader createClassLoader(Collection<URL> urls) throws Exception {
      if (this.classPathIndex != null) {
         urls = new ArrayList((Collection)urls);
         ((Collection)urls).addAll(this.classPathIndex.getUrls());
      }

      return super.createClassLoader((Collection)urls);
   }

   protected final Archive getArchive() {
      return this.archive;
   }

   protected String getMainClass() throws Exception {
      Manifest manifest = this.archive.getManifest();
      String mainClass = manifest != null ? manifest.getMainAttributes().getValue("Start-Class") : null;
      if (mainClass == null) {
         throw new IllegalStateException("No 'Start-Class' manifest entry specified in " + this);
      } else {
         return mainClass;
      }
   }

   protected Set<URL> getClassPathUrls() throws Exception {
      return this.archive.getClassPathUrls(this::isIncludedOnClassPathAndNotIndexed, this::isSearchedDirectory);
   }

   private boolean isIncludedOnClassPathAndNotIndexed(Archive.Entry entry) {
      if (!this.isIncludedOnClassPath(entry)) {
         return false;
      } else {
         return this.classPathIndex == null || !this.classPathIndex.containsEntry(entry.name());
      }
   }

   protected boolean isSearchedDirectory(Archive.Entry entry) {
      return (this.getEntryPathPrefix() == null || entry.name().startsWith(this.getEntryPathPrefix())) && !this.isIncludedOnClassPath(entry);
   }

   protected abstract boolean isIncludedOnClassPath(Archive.Entry entry);

   protected abstract String getEntryPathPrefix();
}
