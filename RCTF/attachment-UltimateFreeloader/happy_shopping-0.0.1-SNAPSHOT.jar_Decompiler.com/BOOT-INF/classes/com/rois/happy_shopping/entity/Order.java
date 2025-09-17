package com.rois.happy_shopping.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class Order {
   private String id;
   private String userId;
   private String productId;
   private Integer quantity;
   private BigDecimal originalPrice;
   private BigDecimal discountAmount;
   private BigDecimal finalPrice;
   private String couponId;
   private String status;
   private LocalDateTime createTime;
   private LocalDateTime updateTime;

   public Order() {
   }

   public Order(String userId, String productId, Integer quantity, BigDecimal originalPrice) {
      this.id = UUID.randomUUID().toString();
      this.userId = userId;
      this.productId = productId;
      this.quantity = quantity;
      this.originalPrice = originalPrice;
      this.discountAmount = BigDecimal.ZERO;
      this.finalPrice = originalPrice;
      this.status = "PENDING";
      this.createTime = LocalDateTime.now();
      this.updateTime = LocalDateTime.now();
   }

   public String getId() {
      return this.id;
   }

   public void setId(String id) {
      this.id = id;
   }

   public String getUserId() {
      return this.userId;
   }

   public void setUserId(String userId) {
      this.userId = userId;
   }

   public String getProductId() {
      return this.productId;
   }

   public void setProductId(String productId) {
      this.productId = productId;
   }

   public Integer getQuantity() {
      return this.quantity;
   }

   public void setQuantity(Integer quantity) {
      this.quantity = quantity;
   }

   public BigDecimal getOriginalPrice() {
      return this.originalPrice;
   }

   public void setOriginalPrice(BigDecimal originalPrice) {
      this.originalPrice = originalPrice;
   }

   public BigDecimal getDiscountAmount() {
      return this.discountAmount;
   }

   public void setDiscountAmount(BigDecimal discountAmount) {
      this.discountAmount = discountAmount;
   }

   public BigDecimal getFinalPrice() {
      return this.finalPrice;
   }

   public void setFinalPrice(BigDecimal finalPrice) {
      this.finalPrice = finalPrice;
   }

   public String getCouponId() {
      return this.couponId;
   }

   public void setCouponId(String couponId) {
      this.couponId = couponId;
   }

   public String getStatus() {
      return this.status;
   }

   public void setStatus(String status) {
      this.status = status;
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
