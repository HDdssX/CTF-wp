package com.ruoyi.generator.service;

import com.ruoyi.generator.domain.GenTable;
import java.util.List;
import java.util.Map;

public interface IGenTableService {
   List<GenTable> selectGenTableList(GenTable var1);

   List<GenTable> selectDbTableList(GenTable var1);

   List<GenTable> selectDbTableListByNames(String[] var1);

   List<GenTable> selectGenTableAll();

   GenTable selectGenTableById(Long var1);

   void updateGenTable(GenTable var1);

   void deleteGenTableByIds(String var1);

   boolean createTable(String var1);

   void importGenTable(List<GenTable> var1, String var2);

   Map<String, String> previewCode(Long var1);

   byte[] downloadCode(String var1);

   void generatorCode(String var1);

   void synchDb(String var1);

   byte[] downloadCode(String[] var1);

   void validateEdit(GenTable var1);
}
