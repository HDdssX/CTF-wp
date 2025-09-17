package com.rois.happy_shopping.mapper;

import com.rois.happy_shopping.entity.Coupon;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface CouponMapper {
   int insert(Coupon var1);

   Coupon findById(@Param("id") String var1);

   List<Coupon> findAvailableByUserId(@Param("userId") String var1);

   int updateUsedStatus(@Param("id") String var1, @Param("isUsed") Boolean var2);

   List<Coupon> findByUserId(@Param("userId") String var1);
}
