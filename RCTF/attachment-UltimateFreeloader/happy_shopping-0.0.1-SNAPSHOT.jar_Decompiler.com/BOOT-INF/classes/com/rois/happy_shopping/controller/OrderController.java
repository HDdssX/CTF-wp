package com.rois.happy_shopping.controller;

import com.rois.happy_shopping.common.Result;
import com.rois.happy_shopping.dto.OrderRequestDTO;
import com.rois.happy_shopping.entity.Order;
import com.rois.happy_shopping.service.OrderService;
import com.rois.happy_shopping.util.JwtUtil;
import java.util.List;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping({"/api/order"})
@CrossOrigin(
   origins = {"*"}
)
public class OrderController {
   @Autowired
   private OrderService orderService;
   @Autowired
   private JwtUtil jwtUtil;

   @PostMapping({"/create"})
   public Result<?> createOrder(@Valid @RequestBody OrderRequestDTO orderRequest, HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         Map<String, Object> result = this.orderService.createOrder(userId, orderRequest);
         return (Boolean)result.get("success") ? Result.success("Order created successfully", result) : Result.error((String)result.get("message"));
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   @GetMapping({"/my"})
   public Result<List<Order>> getMyOrders(HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         List<Order> orders = this.orderService.getUserOrders(userId);
         return Result.success("Get order list successfully", orders);
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   @GetMapping({"/{id}"})
   public Result<Order> getOrderById(@PathVariable String id, HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         Order order = this.orderService.getOrderById(id);
         if (order != null) {
            String userId = this.jwtUtil.getUserIdFromToken(token);
            return !order.getUserId().equals(userId) ? Result.error(403, "No permission to access this order") : Result.success("Get order details successfully", order);
         } else {
            return Result.error("Order not found");
         }
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   @PostMapping({"/refund/{id}"})
   public Result<?> refundOrder(@PathVariable String id, HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         Map<String, Object> result = this.orderService.refundOrder(id, userId);
         return (Boolean)result.get("success") ? Result.success("Refund successful", result) : Result.error((String)result.get("message"));
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   private String getTokenFromRequest(HttpServletRequest request) {
      String bearerToken = request.getHeader("Authorization");
      return bearerToken != null && bearerToken.startsWith("Bearer ") ? bearerToken.substring(7) : null;
   }
}
