package com.ruoyi.generator.util;

import com.alibaba.fastjson.JSONObject;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.generator.config.GenConfig;
import com.ruoyi.generator.domain.GenTable;
import com.ruoyi.generator.domain.GenTableColumn;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import org.apache.velocity.VelocityContext;

public class VelocityUtils {
   private static final String PROJECT_PATH = "main/java";
   private static final String MYBATIS_PATH = "main/resources/mapper";
   private static final String TEMPLATES_PATH = "main/resources/templates";
   private static final String DEFAULT_PARENT_MENU_ID = "3";

   public static VelocityContext prepareContext(GenTable genTable) {
      String moduleName = genTable.getModuleName();
      String businessName = genTable.getBusinessName();
      String packageName = genTable.getPackageName();
      String tplCategory = genTable.getTplCategory();
      String functionName = genTable.getFunctionName();
      VelocityContext velocityContext = new VelocityContext();
      velocityContext.put("tplCategory", genTable.getTplCategory());
      velocityContext.put("tableName", genTable.getTableName());
      velocityContext.put("functionName", StringUtils.isNotEmpty(functionName) ? functionName : "【请填写功能名称】");
      velocityContext.put("ClassName", genTable.getClassName());
      velocityContext.put("className", StringUtils.uncapitalize(genTable.getClassName()));
      velocityContext.put("moduleName", genTable.getModuleName());
      velocityContext.put("businessName", genTable.getBusinessName());
      velocityContext.put("basePackage", getPackagePrefix(packageName));
      velocityContext.put("packageName", packageName);
      velocityContext.put("author", genTable.getFunctionAuthor());
      velocityContext.put("datetime", DateUtils.getDate());
      velocityContext.put("pkColumn", genTable.getPkColumn());
      velocityContext.put("importList", getImportList(genTable));
      velocityContext.put("permissionPrefix", getPermissionPrefix(moduleName, businessName));
      velocityContext.put("columns", genTable.getColumns());
      velocityContext.put("table", genTable);
      setMenuVelocityContext(velocityContext, genTable);
      if ("tree".equals(tplCategory)) {
         setTreeVelocityContext(velocityContext, genTable);
      }

      if ("sub".equals(tplCategory)) {
         setSubVelocityContext(velocityContext, genTable);
      }

      return velocityContext;
   }

   public static void setMenuVelocityContext(VelocityContext context, GenTable genTable) {
      String options = genTable.getOptions();
      JSONObject paramsObj = JSONObject.parseObject(options);
      String parentMenuId = getParentMenuId(paramsObj);
      context.put("parentMenuId", parentMenuId);
   }

   public static void setTreeVelocityContext(VelocityContext context, GenTable genTable) {
      String options = genTable.getOptions();
      JSONObject paramsObj = JSONObject.parseObject(options);
      String treeCode = getTreecode(paramsObj);
      String treeParentCode = getTreeParentCode(paramsObj);
      String treeName = getTreeName(paramsObj);
      context.put("treeCode", treeCode);
      context.put("treeParentCode", treeParentCode);
      context.put("treeName", treeName);
      context.put("expandColumn", getExpandColumn(genTable));
      if (paramsObj.containsKey("treeParentCode")) {
         context.put("tree_parent_code", paramsObj.getString("treeParentCode"));
      }

      if (paramsObj.containsKey("treeName")) {
         context.put("tree_name", paramsObj.getString("treeName"));
      }

   }

   public static void setSubVelocityContext(VelocityContext context, GenTable genTable) {
      GenTable subTable = genTable.getSubTable();
      String subTableName = genTable.getSubTableName();
      String subTableFkName = genTable.getSubTableFkName();
      String subClassName = genTable.getSubTable().getClassName();
      String subTableFkClassName = StringUtils.convertToCamelCase(subTableFkName);
      context.put("subTable", subTable);
      context.put("subTableName", subTableName);
      context.put("subTableFkName", subTableFkName);
      context.put("subTableFkClassName", subTableFkClassName);
      context.put("subTableFkclassName", StringUtils.uncapitalize(subTableFkClassName));
      context.put("subClassName", subClassName);
      context.put("subclassName", StringUtils.uncapitalize(subClassName));
      context.put("subImportList", getImportList(genTable.getSubTable()));
   }

   public static List<String> getTemplateList(String tplCategory) {
      List<String> templates = new ArrayList();
      templates.add("vm/java/domain.java.vm");
      templates.add("vm/java/mapper.java.vm");
      templates.add("vm/java/service.java.vm");
      templates.add("vm/java/serviceImpl.java.vm");
      templates.add("vm/java/controller.java.vm");
      templates.add("vm/xml/mapper.xml.vm");
      if ("crud".equals(tplCategory)) {
         templates.add("vm/html/list.html.vm");
      } else if ("tree".equals(tplCategory)) {
         templates.add("vm/html/tree.html.vm");
         templates.add("vm/html/list-tree.html.vm");
      } else if ("sub".equals(tplCategory)) {
         templates.add("vm/html/list.html.vm");
         templates.add("vm/java/sub-domain.java.vm");
      }

      templates.add("vm/html/add.html.vm");
      templates.add("vm/html/edit.html.vm");
      templates.add("vm/sql/sql.vm");
      return templates;
   }

   public static String getFileName(String template, GenTable genTable) {
      String fileName = "";
      String packageName = genTable.getPackageName();
      String moduleName = genTable.getModuleName();
      String className = genTable.getClassName();
      String businessName = genTable.getBusinessName();
      String javaPath = "main/java/" + StringUtils.replace(packageName, ".", "/");
      String mybatisPath = "main/resources/mapper/" + moduleName;
      String htmlPath = "main/resources/templates/" + moduleName + "/" + businessName;
      if (template.contains("domain.java.vm")) {
         fileName = StringUtils.format("{}/domain/{}.java", new Object[]{javaPath, className});
      }

      if (template.contains("sub-domain.java.vm") && StringUtils.equals("sub", genTable.getTplCategory())) {
         fileName = StringUtils.format("{}/domain/{}.java", new Object[]{javaPath, genTable.getSubTable().getClassName()});
      } else if (template.contains("mapper.java.vm")) {
         fileName = StringUtils.format("{}/mapper/{}Mapper.java", new Object[]{javaPath, className});
      } else if (template.contains("service.java.vm")) {
         fileName = StringUtils.format("{}/service/I{}Service.java", new Object[]{javaPath, className});
      } else if (template.contains("serviceImpl.java.vm")) {
         fileName = StringUtils.format("{}/service/impl/{}ServiceImpl.java", new Object[]{javaPath, className});
      } else if (template.contains("controller.java.vm")) {
         fileName = StringUtils.format("{}/controller/{}Controller.java", new Object[]{javaPath, className});
      } else if (template.contains("mapper.xml.vm")) {
         fileName = StringUtils.format("{}/{}Mapper.xml", new Object[]{mybatisPath, className});
      } else if (template.contains("list.html.vm")) {
         fileName = StringUtils.format("{}/{}.html", new Object[]{htmlPath, businessName});
      } else if (template.contains("list-tree.html.vm")) {
         fileName = StringUtils.format("{}/{}.html", new Object[]{htmlPath, businessName});
      } else if (template.contains("tree.html.vm")) {
         fileName = StringUtils.format("{}/tree.html", new Object[]{htmlPath});
      } else if (template.contains("add.html.vm")) {
         fileName = StringUtils.format("{}/add.html", new Object[]{htmlPath});
      } else if (template.contains("edit.html.vm")) {
         fileName = StringUtils.format("{}/edit.html", new Object[]{htmlPath});
      } else if (template.contains("sql.vm")) {
         fileName = businessName + "Menu.sql";
      }

      return fileName;
   }

   public static String getProjectPath() {
      String packageName = GenConfig.getPackageName();
      StringBuffer projectPath = new StringBuffer();
      projectPath.append("main/java/");
      projectPath.append(packageName.replace(".", "/"));
      projectPath.append("/");
      return projectPath.toString();
   }

   public static String getPackagePrefix(String packageName) {
      int lastIndex = packageName.lastIndexOf(".");
      return StringUtils.substring(packageName, 0, lastIndex);
   }

   public static HashSet<String> getImportList(GenTable genTable) {
      List<GenTableColumn> columns = genTable.getColumns();
      GenTable subGenTable = genTable.getSubTable();
      HashSet<String> importList = new HashSet();
      if (StringUtils.isNotNull(subGenTable)) {
         importList.add("java.util.List");
      }

      Iterator var4 = columns.iterator();

      while(true) {
         while(var4.hasNext()) {
            GenTableColumn column = (GenTableColumn)var4.next();
            if (!column.isSuperColumn() && "Date".equals(column.getJavaType())) {
               importList.add("java.util.Date");
               importList.add("com.fasterxml.jackson.annotation.JsonFormat");
            } else if (!column.isSuperColumn() && "BigDecimal".equals(column.getJavaType())) {
               importList.add("java.math.BigDecimal");
            }
         }

         return importList;
      }
   }

   public static String getPermissionPrefix(String moduleName, String businessName) {
      return StringUtils.format("{}:{}", new Object[]{moduleName, businessName});
   }

   public static String getParentMenuId(JSONObject paramsObj) {
      return StringUtils.isNotEmpty(paramsObj) && paramsObj.containsKey("parentMenuId") && StringUtils.isNotEmpty(paramsObj.getString("parentMenuId")) ? paramsObj.getString("parentMenuId") : "3";
   }

   public static String getTreecode(JSONObject paramsObj) {
      return paramsObj.containsKey("treeCode") ? StringUtils.toCamelCase(paramsObj.getString("treeCode")) : "";
   }

   public static String getTreeParentCode(JSONObject paramsObj) {
      return paramsObj.containsKey("treeParentCode") ? StringUtils.toCamelCase(paramsObj.getString("treeParentCode")) : "";
   }

   public static String getTreeName(JSONObject paramsObj) {
      return paramsObj.containsKey("treeName") ? StringUtils.toCamelCase(paramsObj.getString("treeName")) : "";
   }

   public static int getExpandColumn(GenTable genTable) {
      String options = genTable.getOptions();
      JSONObject paramsObj = JSONObject.parseObject(options);
      String treeName = paramsObj.getString("treeName");
      int num = 0;
      Iterator var5 = genTable.getColumns().iterator();

      while(var5.hasNext()) {
         GenTableColumn column = (GenTableColumn)var5.next();
         if (column.isList()) {
            ++num;
            String columnName = column.getColumnName();
            if (columnName.equals(treeName)) {
               break;
            }
         }
      }

      return num;
   }
}
