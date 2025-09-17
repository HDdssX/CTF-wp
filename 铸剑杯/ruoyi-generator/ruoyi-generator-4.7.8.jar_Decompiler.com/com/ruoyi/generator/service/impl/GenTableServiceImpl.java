package com.ruoyi.generator.service.impl;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.ruoyi.common.core.text.Convert;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.generator.domain.GenTable;
import com.ruoyi.generator.domain.GenTableColumn;
import com.ruoyi.generator.mapper.GenTableColumnMapper;
import com.ruoyi.generator.mapper.GenTableMapper;
import com.ruoyi.generator.service.IGenTableService;
import com.ruoyi.generator.util.GenUtils;
import com.ruoyi.generator.util.VelocityInitializer;
import com.ruoyi.generator.util.VelocityUtils;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.StringWriter;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.IOUtils;
import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.Velocity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GenTableServiceImpl implements IGenTableService {
   private static final Logger log = LoggerFactory.getLogger(GenTableServiceImpl.class);
   private static final Pattern UPDATE_INJECTION_PATTERN = Pattern.compile("(update|delete|drop|truncate|select|insert|alter|create|exec|declare|union|or|and|--|#|\\*|;|from|where|UPDATE|IN)");
   @Autowired
   private GenTableMapper genTableMapper;
   @Autowired
   private GenTableColumnMapper genTableColumnMapper;

   public static boolean isInjection(String input) {
      if (input != null && !input.isEmpty()) {
         Matcher matcher = UPDATE_INJECTION_PATTERN.matcher(input);
         return matcher.find();
      } else {
         return false;
      }
   }

   public GenTable selectGenTableById(Long id) {
      GenTable genTable = this.genTableMapper.selectGenTableById(id);
      this.setTableFromOptions(genTable);
      return genTable;
   }

   public List<GenTable> selectGenTableList(GenTable genTable) {
      return this.genTableMapper.selectGenTableList(genTable);
   }

   public List<GenTable> selectDbTableList(GenTable genTable) {
      return this.genTableMapper.selectDbTableList(genTable);
   }

   public List<GenTable> selectDbTableListByNames(String[] tableNames) {
      return this.genTableMapper.selectDbTableListByNames(tableNames);
   }

   public List<GenTable> selectGenTableAll() {
      return this.genTableMapper.selectGenTableAll();
   }

   @Transactional
   public void updateGenTable(GenTable genTable) {
      String options = JSON.toJSONString(genTable.getParams());
      genTable.setOptions(options);
      int row = this.genTableMapper.updateGenTable(genTable);
      if (row > 0) {
         Iterator var4 = genTable.getColumns().iterator();

         while(var4.hasNext()) {
            GenTableColumn genTableColumn = (GenTableColumn)var4.next();
            this.genTableColumnMapper.updateGenTableColumn(genTableColumn);
         }
      }

   }

   @Transactional
   public void deleteGenTableByIds(String ids) {
      this.genTableMapper.deleteGenTableByIds(Convert.toLongArray(ids));
      this.genTableColumnMapper.deleteGenTableColumnByIds(Convert.toLongArray(ids));
   }

   public boolean createTable(String sql) {
      if (isInjection(sql)) {
         System.out.println("输入 '" + sql + "' 包含SQL注入关键字！");
         return false;
      } else {
         System.out.println("输入 '" + sql + "' 是安全的。");
         return this.genTableMapper.createTable(sql) == 0;
      }
   }

   @Transactional
   public void importGenTable(List<GenTable> tableList, String operName) {
      try {
         Iterator var3 = tableList.iterator();

         while(true) {
            GenTable table;
            String tableName;
            int row;
            do {
               if (!var3.hasNext()) {
                  return;
               }

               table = (GenTable)var3.next();
               tableName = table.getTableName();
               GenUtils.initTable(table, operName);
               row = this.genTableMapper.insertGenTable(table);
            } while(row <= 0);

            List<GenTableColumn> genTableColumns = this.genTableColumnMapper.selectDbTableColumnsByName(tableName);
            Iterator var8 = genTableColumns.iterator();

            while(var8.hasNext()) {
               GenTableColumn column = (GenTableColumn)var8.next();
               GenUtils.initColumnField(column, table);
               this.genTableColumnMapper.insertGenTableColumn(column);
            }
         }
      } catch (Exception var10) {
         throw new ServiceException("导入失败：" + var10.getMessage());
      }
   }

   public Map<String, String> previewCode(Long tableId) {
      Map<String, String> dataMap = new LinkedHashMap();
      GenTable table = this.genTableMapper.selectGenTableById(tableId);
      this.setSubTable(table);
      this.setPkColumn(table);
      VelocityInitializer.initVelocity();
      VelocityContext context = VelocityUtils.prepareContext(table);
      List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory());
      Iterator var6 = templates.iterator();

      while(var6.hasNext()) {
         String template = (String)var6.next();
         StringWriter sw = new StringWriter();
         Template tpl = Velocity.getTemplate(template, "UTF-8");
         tpl.merge(context, sw);
         dataMap.put(template, sw.toString());
      }

      return dataMap;
   }

   public byte[] downloadCode(String tableName) {
      ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
      ZipOutputStream zip = new ZipOutputStream(outputStream);
      this.generatorCode(tableName, zip);
      IOUtils.closeQuietly(zip);
      return outputStream.toByteArray();
   }

   public void generatorCode(String tableName) {
      GenTable table = this.genTableMapper.selectGenTableByName(tableName);
      this.setSubTable(table);
      this.setPkColumn(table);
      VelocityInitializer.initVelocity();
      VelocityContext context = VelocityUtils.prepareContext(table);
      List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory());
      Iterator var5 = templates.iterator();

      while(var5.hasNext()) {
         String template = (String)var5.next();
         if (!StringUtils.contains(template, "sql.vm")) {
            StringWriter sw = new StringWriter();
            Template tpl = Velocity.getTemplate(template, "UTF-8");
            tpl.merge(context, sw);

            try {
               String path = getGenPath(table, template);
               FileUtils.writeStringToFile(new File(path), sw.toString(), "UTF-8");
            } catch (IOException var10) {
               throw new ServiceException("渲染模板失败，表名：" + table.getTableName());
            }
         }
      }

   }

   @Transactional
   public void synchDb(String tableName) {
      GenTable table = this.genTableMapper.selectGenTableByName(tableName);
      List<GenTableColumn> tableColumns = table.getColumns();
      Map<String, GenTableColumn> tableColumnMap = (Map)tableColumns.stream().collect(Collectors.toMap(GenTableColumn::getColumnName, Function.identity()));
      List<GenTableColumn> dbTableColumns = this.genTableColumnMapper.selectDbTableColumnsByName(tableName);
      if (StringUtils.isEmpty(dbTableColumns)) {
         throw new ServiceException("同步数据失败，原表结构不存在");
      } else {
         List<String> dbTableColumnNames = (List)dbTableColumns.stream().map(GenTableColumn::getColumnName).collect(Collectors.toList());
         dbTableColumns.forEach((column) -> {
            GenUtils.initColumnField(column, table);
            if (tableColumnMap.containsKey(column.getColumnName())) {
               GenTableColumn prevColumn = (GenTableColumn)tableColumnMap.get(column.getColumnName());
               column.setColumnId(prevColumn.getColumnId());
               if (column.isList()) {
                  column.setDictType(prevColumn.getDictType());
                  column.setQueryType(prevColumn.getQueryType());
               }

               if (StringUtils.isNotEmpty(prevColumn.getIsRequired()) && !column.isPk() && (column.isInsert() || column.isEdit()) && (column.isUsableColumn() || !column.isSuperColumn())) {
                  column.setIsRequired(prevColumn.getIsRequired());
                  column.setHtmlType(prevColumn.getHtmlType());
               }

               this.genTableColumnMapper.updateGenTableColumn(column);
            } else {
               this.genTableColumnMapper.insertGenTableColumn(column);
            }

         });
         List<GenTableColumn> delColumns = (List)tableColumns.stream().filter((column) -> {
            return !dbTableColumnNames.contains(column.getColumnName());
         }).collect(Collectors.toList());
         if (StringUtils.isNotEmpty(delColumns)) {
            this.genTableColumnMapper.deleteGenTableColumns(delColumns);
         }

      }
   }

   public byte[] downloadCode(String[] tableNames) {
      ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
      ZipOutputStream zip = new ZipOutputStream(outputStream);
      String[] var4 = tableNames;
      int var5 = tableNames.length;

      for(int var6 = 0; var6 < var5; ++var6) {
         String tableName = var4[var6];
         this.generatorCode(tableName, zip);
      }

      IOUtils.closeQuietly(zip);
      return outputStream.toByteArray();
   }

   private void generatorCode(String tableName, ZipOutputStream zip) {
      GenTable table = this.genTableMapper.selectGenTableByName(tableName);
      this.setSubTable(table);
      this.setPkColumn(table);
      VelocityInitializer.initVelocity();
      VelocityContext context = VelocityUtils.prepareContext(table);
      List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory());
      Iterator var6 = templates.iterator();

      while(var6.hasNext()) {
         String template = (String)var6.next();
         StringWriter sw = new StringWriter();
         Template tpl = Velocity.getTemplate(template, "UTF-8");
         tpl.merge(context, sw);

         try {
            zip.putNextEntry(new ZipEntry(VelocityUtils.getFileName(template, table)));
            IOUtils.write(sw.toString(), zip, "UTF-8");
            IOUtils.closeQuietly(sw);
            zip.flush();
            zip.closeEntry();
         } catch (IOException var11) {
            log.error("渲染模板失败，表名：" + table.getTableName(), var11);
         }
      }

   }

   public void validateEdit(GenTable genTable) {
      if ("tree".equals(genTable.getTplCategory())) {
         String options = JSON.toJSONString(genTable.getParams());
         JSONObject paramsObj = JSONObject.parseObject(options);
         if (StringUtils.isEmpty(paramsObj.getString("treeCode"))) {
            throw new ServiceException("树编码字段不能为空");
         }

         if (StringUtils.isEmpty(paramsObj.getString("treeParentCode"))) {
            throw new ServiceException("树父编码字段不能为空");
         }

         if (StringUtils.isEmpty(paramsObj.getString("treeName"))) {
            throw new ServiceException("树名称字段不能为空");
         }
      } else if ("sub".equals(genTable.getTplCategory())) {
         if (StringUtils.isEmpty(genTable.getSubTableName())) {
            throw new ServiceException("关联子表的表名不能为空");
         }

         if (StringUtils.isEmpty(genTable.getSubTableFkName())) {
            throw new ServiceException("子表关联的外键名不能为空");
         }
      }

   }

   public void setPkColumn(GenTable table) {
      Iterator var2 = table.getColumns().iterator();

      GenTableColumn column;
      while(var2.hasNext()) {
         column = (GenTableColumn)var2.next();
         if (column.isPk()) {
            table.setPkColumn(column);
            break;
         }
      }

      if (StringUtils.isNull(table.getPkColumn())) {
         table.setPkColumn((GenTableColumn)table.getColumns().get(0));
      }

      if ("sub".equals(table.getTplCategory())) {
         var2 = table.getSubTable().getColumns().iterator();

         while(var2.hasNext()) {
            column = (GenTableColumn)var2.next();
            if (column.isPk()) {
               table.getSubTable().setPkColumn(column);
               break;
            }
         }

         if (StringUtils.isNull(table.getSubTable().getPkColumn())) {
            table.getSubTable().setPkColumn((GenTableColumn)table.getSubTable().getColumns().get(0));
         }
      }

   }

   public void setSubTable(GenTable table) {
      String subTableName = table.getSubTableName();
      if (StringUtils.isNotEmpty(subTableName)) {
         table.setSubTable(this.genTableMapper.selectGenTableByName(subTableName));
      }

   }

   public void setTableFromOptions(GenTable genTable) {
      JSONObject paramsObj = JSONObject.parseObject(genTable.getOptions());
      if (StringUtils.isNotNull(paramsObj)) {
         String treeCode = paramsObj.getString("treeCode");
         String treeParentCode = paramsObj.getString("treeParentCode");
         String treeName = paramsObj.getString("treeName");
         String parentMenuId = paramsObj.getString("parentMenuId");
         String parentMenuName = paramsObj.getString("parentMenuName");
         genTable.setTreeCode(treeCode);
         genTable.setTreeParentCode(treeParentCode);
         genTable.setTreeName(treeName);
         genTable.setParentMenuId(parentMenuId);
         genTable.setParentMenuName(parentMenuName);
      }

   }

   public static String getGenPath(GenTable table, String template) {
      String genPath = table.getGenPath();
      return StringUtils.equals(genPath, "/") ? System.getProperty("user.dir") + File.separator + "src" + File.separator + VelocityUtils.getFileName(template, table) : genPath + File.separator + VelocityUtils.getFileName(template, table);
   }
}
