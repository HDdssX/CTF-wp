package com.demo.controller;

import com.demo.model.FileModificationRequest;
import com.demo.service.FileStorageService;
import com.demo.service.IconStorageService;
import jakarta.validation.Valid;
import java.nio.file.Path;
import java.util.Base64;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.ResponseEntity.BodyBuilder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RequestMapping({"/files"})
@RestController
public class FileProcessorController {
   private final FileStorageService fileStorageService;
   private final IconStorageService iconStorageService;

   public FileProcessorController(FileStorageService fileStorageService, IconStorageService iconStorageService) {
      this.fileStorageService = fileStorageService;
      this.iconStorageService = iconStorageService;
   }

   @PostMapping({"/upload"})
   public ResponseEntity uploadFile(@RequestParam("file") MultipartFile file, @RequestParam(value = "icon",required = false) MultipartFile icon) {
      try {
         String storedFilename = this.fileStorageService.storeFile(file);
         byte[] iconBytes;
         if (icon != null) {
            iconBytes = icon.getBytes();
         } else {
            iconBytes = IconStorageService.defaultIcon;
         }

         this.iconStorageService.storeIcon(iconBytes);
         this.fileStorageService.saveFileName(storedFilename);
         return ResponseEntity.ok("upload success");
      } catch (Exception var5) {
         return ResponseEntity.badRequest().build();
      }
   }

   @GetMapping({"/icon"})
   public ResponseEntity<byte[]> getIcon() {
      try {
         byte[] iconBytes = this.iconStorageService.getIcon();
         return ((BodyBuilder)ResponseEntity.ok().contentType(MediaType.IMAGE_JPEG).header("Content-Disposition", new String[]{"inline; filename=\"icon.png\""})).body(iconBytes);
      } catch (Exception var2) {
         var2.printStackTrace();
         return ResponseEntity.notFound().build();
      }
   }

   @PutMapping({"/modify"})
   public ResponseEntity<String> modifyFile(@Valid @RequestBody FileModificationRequest request) {
      try {
         byte[] data = Base64.getDecoder().decode(request.getData());
         if (data.length > 8) {
            throw new IllegalArgumentException("data length cannot exceed 8");
         } else {
            Path filePath = this.fileStorageService.loadFile(request.getFileName());
            this.fileStorageService.modifyFile(filePath, data, request.getOffset());
            return ResponseEntity.ok("modify success");
         }
      } catch (IllegalArgumentException var4) {
         return ResponseEntity.badRequest().body(var4.getMessage());
      } catch (Exception var5) {
         return ResponseEntity.internalServerError().body("Error: " + var5.getMessage());
      }
   }

   @GetMapping({"/download"})
   public ResponseEntity<Resource> downloadFile() {
      try {
         String fileName = this.fileStorageService.getFileName();
         Path filePath = this.fileStorageService.loadFile(fileName);
         this.fileStorageService.check(filePath);
         UrlResource urlResource = new UrlResource(filePath.toUri());
         return urlResource.exists() && urlResource.isReadable() ? ((BodyBuilder)ResponseEntity.ok().contentType(MediaType.APPLICATION_OCTET_STREAM).header("Content-Disposition", new String[]{"attachment; filename=\"" + fileName + "\""})).body(urlResource) : ResponseEntity.notFound().build();
      } catch (Exception var4) {
         return ResponseEntity.notFound().build();
      }
   }

   @GetMapping({"/info"})
   public ResponseEntity getFileInfo() {
      try {
         return ResponseEntity.ok("{\"filename\":\"" + this.fileStorageService.getFileName() + "\"}");
      } catch (Exception var2) {
         return ResponseEntity.notFound().build();
      }
   }
}
