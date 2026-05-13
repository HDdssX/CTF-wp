package com.rois.happy_shopping.dto;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

public class OrderRequestDTO {
   @NotNull(
      message = "Order id cannot be empty"
   )
   private String productId;
   @Size(
      max = 9,
      message = "Quantity is too large"
   )
   @NotNull(
      message = "Quantity cannot be empty"
   )
   private String quantity;
   private String couponId;

   public String getProductId() {
      return this.productId;
   }

   public void setProductId(String productId) {
      this.productId = productId;
   }

   public String getQuantity() {
      return this.quantity;
   }

   public void setQuantity(String quantity) {
      this.quantity = quantity;
   }

   public String getCouponId() {
      return this.couponId;
   }

   public void setCouponId(String couponId) {
      this.couponId = couponId;
   }
}
