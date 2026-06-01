package com.rois.happy_shopping.service;

import com.rois.happy_shopping.entity.Product;
import com.rois.happy_shopping.mapper.ProductMapper;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ProductService {
   @Autowired
   private ProductMapper productMapper;

   public List<Product> getAllProducts() {
      return this.productMapper.findAll();
   }

   public Product getProductById(String id) {
      return this.productMapper.findById(id);
   }
}
