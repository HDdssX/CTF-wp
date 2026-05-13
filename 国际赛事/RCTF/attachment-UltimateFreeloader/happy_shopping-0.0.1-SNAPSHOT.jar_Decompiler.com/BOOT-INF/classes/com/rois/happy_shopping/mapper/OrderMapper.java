package com.rois.happy_shopping.mapper;

import com.rois.happy_shopping.entity.Order;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface OrderMapper {
   int insert(Order var1);

   Order findById(@Param("id") String var1);

   List<Order> findByUserId(@Param("userId") String var1);

   int updateStatus(@Param("id") String var1, @Param("status") String var2);
}
