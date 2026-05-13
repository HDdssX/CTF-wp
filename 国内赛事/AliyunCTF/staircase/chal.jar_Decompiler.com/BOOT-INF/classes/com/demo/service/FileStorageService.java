package com.demo.service;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class FileStorageService {
   private final Path uploadDir;
   private String fileName = null;

   public void saveFileName(String filename) {
      if (filename != null && !filename.equals("")) {
         this.fileName = filename;
      } else {
         throw new IllegalArgumentException("filename cannot be empty");
      }
   }

   public String getFileName() {
      return this.fileName;
   }

   public FileStorageService(@Value("${app.upload-dir}") String uploadDir) {
      this.uploadDir = Paths.get(uploadDir).toAbsolutePath().normalize();

      try {
         Files.createDirectories(this.uploadDir);
      } catch (IOException var3) {
         throw new RuntimeException("Unable to create upload directory: " + this.uploadDir, var3);
      }
   }

   public String sanitizeFilename(String filename) {
      if (filename != null && !filename.trim().isEmpty()) {
         String baseName = Paths.get(filename).getFileName().toString();
         String safeName = baseName.replaceAll("[^a-zA-Z0-9.-]", "_");
         if (safeName.length() > 255) {
            safeName = safeName.substring(0, 255);
         }

         return safeName;
      } else {
         throw new IllegalArgumentException("filename cannot be empty");
      }
   }

   public String storeFile(MultipartFile file) throws IOException {
      String originalFilename = file.getOriginalFilename();
      String safeFilename = this.sanitizeFilename(originalFilename);
      Path targetLocation = this.uploadDir.resolve(safeFilename);
      this.check(targetLocation);
      Files.copy(file.getInputStream(), targetLocation, new CopyOption[]{StandardCopyOption.REPLACE_EXISTING});
      return safeFilename;
   }

   public void check(Path path) throws SecurityException {
      if (!path.normalize().startsWith(this.uploadDir)) {
         throw new SecurityException("no path traversal");
      } else if (Files.isDirectory(path.normalize(), new LinkOption[0])) {
         throw new SecurityException("can not open dir");
      }
   }

   public Path loadFile(String filename) {
      Path filePath = this.uploadDir.resolve(filename).normalize();
      if (!Files.exists(filePath, new LinkOption[0])) {
         throw new RuntimeException("file not found: " + filename);
      } else {
         return filePath;
      }
   }

   public synchronized void modifyFile(Path filePath, byte[] data, long offset) throws IOException {
      byte[] prefix = "<start>".getBytes();
      byte[] suffix = "<end>".getBytes();
      byte[] contentToWrite = new byte[prefix.length + data.length + suffix.length];
      System.arraycopy(prefix, 0, contentToWrite, 0, prefix.length);
      System.arraycopy(data, 0, contentToWrite, prefix.length, data.length);
      System.arraycopy(suffix, 0, contentToWrite, prefix.length + data.length, suffix.length);
      RandomAccessFile raf = new RandomAccessFile(filePath.toFile(), "rw");

      try {
         long fileSize = raf.length();
         if (offset >= 0L && offset + (long)contentToWrite.length <= fileSize) {
            raf.seek(offset);
            raf.write(contentToWrite);
            raf.close();
         } else {
            throw new IllegalArgumentException("invalid offset");
         }
      } catch (Throwable var12) {
         try {
            raf.close();
         } catch (Throwable var11) {
            var12.addSuppressed(var11);
         }

         throw var12;
      }
   }
}
