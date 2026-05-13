package org.springframework.boot.loader.launch;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.file.Files;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

final class ClassPathIndexFile {
   private final File root;
   private final Set<String> lines;

   private ClassPathIndexFile(File root, List<String> lines) {
      this.root = root;
      this.lines = (Set)lines.stream().map(this::extractName).collect(Collectors.toCollection(LinkedHashSet::new));
   }

   private String extractName(String line) {
      if (line.startsWith("- \"") && line.endsWith("\"")) {
         return line.substring(3, line.length() - 1);
      } else {
         throw new IllegalStateException("Malformed classpath index line [" + line + "]");
      }
   }

   int size() {
      return this.lines.size();
   }

   boolean containsEntry(String name) {
      return name != null && !name.isEmpty() ? this.lines.contains(name) : false;
   }

   List<URL> getUrls() {
      return this.lines.stream().map(this::asUrl).toList();
   }

   private URL asUrl(String line) {
      try {
         return (new File(this.root, line)).toURI().toURL();
      } catch (MalformedURLException var3) {
         throw new IllegalStateException(var3);
      }
   }

   static ClassPathIndexFile loadIfPossible(File root, String location) throws IOException {
      return loadIfPossible(root, new File(root, location));
   }

   private static ClassPathIndexFile loadIfPossible(File root, File indexFile) throws IOException {
      if (indexFile.exists() && indexFile.isFile()) {
         List<String> lines = Files.readAllLines(indexFile.toPath()).stream().filter(ClassPathIndexFile::lineHasText).toList();
         return new ClassPathIndexFile(root, lines);
      } else {
         return null;
      }
   }

   private static boolean lineHasText(String line) {
      return !line.trim().isEmpty();
   }
}
