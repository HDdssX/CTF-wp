package com.demo.model;

import jakarta.validation.constraints.NotBlank;

public class FileModificationRequest {
   @NotBlank(
      message = "data cannot be empty"
   )
   private String data;
   private long offset;
   private String fileName;

   public String getFileName() {
      return this.fileName;
   }

   public void setFileName(String fileName) {
      this.fileName = fileName;
   }

   public String getData() {
      return this.data;
   }

   public void setData(String data) {
      this.data = data;
   }

   public long getOffset() {
      return this.offset;
   }

   public void setOffset(long offset) {
      this.offset = offset;
   }
}
