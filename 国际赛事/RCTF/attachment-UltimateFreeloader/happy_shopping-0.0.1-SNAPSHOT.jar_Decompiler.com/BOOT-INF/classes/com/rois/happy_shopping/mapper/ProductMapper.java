package com.rois.happy_shopping.mapper;

import com.rois.happy_shopping.entity.Product;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface ProductMapper {
   int insert(Product var1);

   Product findById(@Param("id") String var1);

   List<Product> findAll();
}
