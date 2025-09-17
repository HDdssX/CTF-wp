package com.rois.happy_shopping.controller;

import com.rois.happy_shopping.common.Result;
import com.rois.happy_shopping.entity.Coupon;
import com.rois.happy_shopping.service.CouponService;
import com.rois.happy_shopping.util.JwtUtil;
import java.util.List;
import javax.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping({"/api/coupon"})
@CrossOrigin(
   origins = {"*"}
)
public class CouponController {
   @Autowired
   private CouponService couponService;
   @Autowired
   private JwtUtil jwtUtil;

   @GetMapping({"/available"})
   public Result<List<Coupon>> getAvailableCoupons(HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         List<Coupon> coupons = this.couponService.getAvailableCoupons(userId);
         return Result.success("Get available coupons successfully", coupons);
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   @GetMapping({"/my"})
   public Result<List<Coupon>> getMyCoupons(HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         List<Coupon> coupons = this.couponService.getUserCoupons(userId);
         return Result.success("Get my coupons successfully", coupons);
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   private String getTokenFromRequest(HttpServletRequest request) {
      String bearerToken = request.getHeader("Authorization");
      return bearerToken != null && bearerToken.startsWith("Bearer ") ? bearerToken.substring(7) : null;
   }
}
