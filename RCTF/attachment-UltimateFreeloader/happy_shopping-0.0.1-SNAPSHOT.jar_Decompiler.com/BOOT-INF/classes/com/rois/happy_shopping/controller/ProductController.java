package com.rois.happy_shopping.controller;

import com.rois.happy_shopping.common.Result;
import com.rois.happy_shopping.entity.Product;
import com.rois.happy_shopping.service.ProductService;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping({"/api/product"})
@CrossOrigin(
   origins = {"*"}
)
public class ProductController {
   @Autowired
   private ProductService productService;

   @GetMapping({"/list"})
   public Result<List<Product>> getAllProducts() {
      List<Product> products = this.productService.getAllProducts();
      return Result.success("Get product list successfully", products);
   }

   @GetMapping({"/{id}"})
   public Result<Product> getProductById(@PathVariable String id) {
      Product product = this.productService.getProductById(id);
      return product != null ? Result.success("Get product details successfully", product) : Result.error("Product not found");
   }
}
