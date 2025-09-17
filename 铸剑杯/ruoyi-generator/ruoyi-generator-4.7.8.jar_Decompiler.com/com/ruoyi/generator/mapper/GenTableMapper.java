package com.ruoyi.generator.mapper;

import com.ruoyi.generator.domain.GenTable;
import java.util.List;

public interface GenTableMapper {
   List<GenTable> selectGenTableList(GenTable var1);

   List<GenTable> selectDbTableList(GenTable var1);

   List<GenTable> selectDbTableListByNames(String[] var1);

   List<GenTable> selectGenTableAll();

   GenTable selectGenTableById(Long var1);

   GenTable selectGenTableByName(String var1);

   int insertGenTable(GenTable var1);

   int updateGenTable(GenTable var1);

   int deleteGenTableByIds(Long[] var1);

   int createTable(String var1);
}
