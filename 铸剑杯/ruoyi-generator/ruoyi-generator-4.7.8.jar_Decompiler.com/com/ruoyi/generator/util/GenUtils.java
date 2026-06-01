package com.ruoyi.generator.util;

import com.ruoyi.common.constant.GenConstants;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.generator.config.GenConfig;
import com.ruoyi.generator.domain.GenTable;
import com.ruoyi.generator.domain.GenTableColumn;
import java.util.Arrays;
import org.apache.commons.lang3.RegExUtils;

public class GenUtils {
   public static void initTable(GenTable genTable, String operName) {
      genTable.setClassName(convertClassName(genTable.getTableName()));
      genTable.setPackageName(GenConfig.getPackageName());
      genTable.setModuleName(getModuleName(GenConfig.getPackageName()));
      genTable.setBusinessName(getBusinessName(genTable.getTableName()));
      genTable.setFunctionName(replaceText(genTable.getTableComment()));
      genTable.setFunctionAuthor(GenConfig.getAuthor());
      genTable.setCreateBy(operName);
   }

   public static void initColumnField(GenTableColumn column, GenTable table) {
      String dataType = getDbType(column.getColumnType());
      String columnName = column.getColumnName();
      column.setTableId(table.getTableId());
      column.setCreateBy(table.getCreateBy());
      column.setJavaField(StringUtils.toCamelCase(columnName));
      column.setJavaType("String");
      column.setQueryType("EQ");
      if (!arraysContains(GenConstants.COLUMNTYPE_STR, dataType) && !arraysContains(GenConstants.COLUMNTYPE_TEXT, dataType)) {
         if (arraysContains(GenConstants.COLUMNTYPE_TIME, dataType)) {
            column.setJavaType("Date");
            column.setHtmlType("datetime");
         } else if (arraysContains(GenConstants.COLUMNTYPE_NUMBER, dataType)) {
            column.setHtmlType("input");
            String[] str = StringUtils.split(StringUtils.substringBetween(column.getColumnType(), "(", ")"), ",");
            if (str != null && str.length == 2 && Integer.parseInt(str[1]) > 0) {
               column.setJavaType("BigDecimal");
            } else if (str != null && str.length == 1 && Integer.parseInt(str[0]) <= 10) {
               column.setJavaType("Integer");
            } else {
               column.setJavaType("Long");
            }
         }
      } else {
         Integer columnLength = getColumnLength(column.getColumnType());
         String htmlType = columnLength < 500 && !arraysContains(GenConstants.COLUMNTYPE_TEXT, dataType) ? "input" : "textarea";
         column.setHtmlType(htmlType);
      }

      column.setIsInsert("1");
      if (!arraysContains(GenConstants.COLUMNNAME_NOT_EDIT, columnName) && !column.isPk()) {
         column.setIsEdit("1");
      }

      if (!arraysContains(GenConstants.COLUMNNAME_NOT_LIST, columnName) && !column.isPk()) {
         column.setIsList("1");
      }

      if (!arraysContains(GenConstants.COLUMNNAME_NOT_QUERY, columnName) && !column.isPk()) {
         column.setIsQuery("1");
      }

      if (StringUtils.endsWithIgnoreCase(columnName, "name")) {
         column.setQueryType("LIKE");
      }

      if (StringUtils.endsWithIgnoreCase(columnName, "status")) {
         column.setHtmlType("radio");
      } else if (!StringUtils.endsWithIgnoreCase(columnName, "type") && !StringUtils.endsWithIgnoreCase(columnName, "sex")) {
         if (StringUtils.endsWithIgnoreCase(columnName, "file")) {
            column.setHtmlType("upload");
         } else if (StringUtils.endsWithIgnoreCase(columnName, "content")) {
            column.setHtmlType("summernote");
         }
      } else {
         column.setHtmlType("select");
      }

   }

   public static boolean arraysContains(String[] arr, String targetValue) {
      return Arrays.asList(arr).contains(targetValue);
   }

   public static String getModuleName(String packageName) {
      int lastIndex = packageName.lastIndexOf(".");
      int nameLength = packageName.length();
      return StringUtils.substring(packageName, lastIndex + 1, nameLength);
   }

   public static String getBusinessName(String tableName) {
      int lastIndex = tableName.lastIndexOf("_");
      int nameLength = tableName.length();
      return StringUtils.substring(tableName, lastIndex + 1, nameLength);
   }

   public static String convertClassName(String tableName) {
      boolean autoRemovePre = GenConfig.getAutoRemovePre();
      String tablePrefix = GenConfig.getTablePrefix();
      if (autoRemovePre && StringUtils.isNotEmpty(tablePrefix)) {
         String[] searchList = StringUtils.split(tablePrefix, ",");
         tableName = replaceFirst(tableName, searchList);
      }

      return StringUtils.convertToCamelCase(tableName);
   }

   public static String replaceFirst(String replacementm, String[] searchList) {
      String text = replacementm;
      String[] var3 = searchList;
      int var4 = searchList.length;

      for(int var5 = 0; var5 < var4; ++var5) {
         String searchString = var3[var5];
         if (replacementm.startsWith(searchString)) {
            text = replacementm.replaceFirst(searchString, "");
            break;
         }
      }

      return text;
   }

   public static String replaceText(String text) {
      return RegExUtils.replaceAll(text, "(?:表|若依)", "");
   }

   public static String getDbType(String columnType) {
      return StringUtils.indexOf(columnType, "(") > 0 ? StringUtils.substringBefore(columnType, "(") : columnType;
   }

   public static Integer getColumnLength(String columnType) {
      if (StringUtils.indexOf(columnType, "(") > 0) {
         String length = StringUtils.substringBetween(columnType, "(", ")");
         return Integer.valueOf(length);
      } else {
         return 0;
      }
   }
}
