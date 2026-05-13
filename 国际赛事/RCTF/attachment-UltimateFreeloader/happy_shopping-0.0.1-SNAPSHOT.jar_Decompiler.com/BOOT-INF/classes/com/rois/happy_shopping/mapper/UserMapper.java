package com.rois.happy_shopping.mapper;

import com.rois.happy_shopping.entity.User;
import java.math.BigDecimal;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper {
   int insert(User var1);

   User findByUsername(@Param("username") String var1);

   User findById(@Param("id") String var1);

   int updateBalance(@Param("id") String var1, @Param("balance") BigDecimal var2);

   int countByUsername(@Param("username") String var1);

   int countByEmail(@Param("email") String var1);
}
