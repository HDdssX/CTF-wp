package com.rois.happy_shopping.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class Product {
   private String id;
   private String name;
   private String description;
   private BigDecimal price;
   private LocalDateTime createTime;
   private LocalDateTime updateTime;

   public Product() {
   }

   public Product(String name, String description, BigDecimal price) {
      this.id = UUID.randomUUID().toString();
      this.name = name;
      this.description = description;
      this.price = price;
      this.createTime = LocalDateTime.now();
      this.updateTime = LocalDateTime.now();
   }

   public String getId() {
      return this.id;
   }

   public void setId(String id) {
      this.id = id;
   }

   public String getName() {
      return this.name;
   }

   public void setName(String name) {
      this.name = name;
   }

   public String getDescription() {
      return this.description;
   }

   public void setDescription(String description) {
      this.description = description;
   }

   public BigDecimal getPrice() {
      return this.price;
   }

   public void setPrice(BigDecimal price) {
      this.price = price;
   }

   public LocalDateTime getCreateTime() {
      return this.createTime;
   }

   public void setCreateTime(LocalDateTime createTime) {
      this.createTime = createTime;
   }

   public LocalDateTime getUpdateTime() {
      return this.updateTime;
   }

   public void setUpdateTime(LocalDateTime updateTime) {
      this.updateTime = updateTime;
   }
}
