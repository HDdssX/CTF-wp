package com.ruoyi.generator.controller;

import com.alibaba.druid.DbType;
import com.alibaba.druid.sql.SQLUtils;
import com.alibaba.druid.sql.ast.SQLStatement;
import com.alibaba.druid.sql.dialect.mysql.ast.statement.MySqlCreateTableStatement;
import com.alibaba.fastjson.JSON;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.CxSelect;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.text.Convert;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.security.PermissionUtils;
import com.ruoyi.common.utils.sql.SqlUtil;
import com.ruoyi.generator.domain.GenTable;
import com.ruoyi.generator.domain.GenTableColumn;
import com.ruoyi.generator.service.IGenTableColumnService;
import com.ruoyi.generator.service.IGenTableService;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import javax.servlet.http.HttpServletResponse;
import org.apache.commons.io.IOUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.apache.shiro.authz.annotation.RequiresRoles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.ModelMap;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@RequestMapping({"/tool/gen"})
public class GenController extends BaseController {
   private String prefix = "tool/gen";
   @Autowired
   private IGenTableService genTableService;
   @Autowired
   private IGenTableColumnService genTableColumnService;

   @RequiresPermissions({"tool:gen:view"})
   @GetMapping
   public String gen() {
      return this.prefix + "/gen";
   }

   @RequiresPermissions({"tool:gen:list"})
   @PostMapping({"/list"})
   @ResponseBody
   public TableDataInfo genList(GenTable genTable) {
      this.startPage();
      List<GenTable> list = this.genTableService.selectGenTableList(genTable);
      return this.getDataTable(list);
   }

   @RequiresPermissions({"tool:gen:list"})
   @PostMapping({"/db/list"})
   @ResponseBody
   public TableDataInfo dataList(GenTable genTable) {
      this.startPage();
      List<GenTable> list = this.genTableService.selectDbTableList(genTable);
      return this.getDataTable(list);
   }

   @RequiresPermissions({"tool:gen:list"})
   @PostMapping({"/column/list"})
   @ResponseBody
   public TableDataInfo columnList(GenTableColumn genTableColumn) {
      TableDataInfo dataInfo = new TableDataInfo();
      List<GenTableColumn> list = this.genTableColumnService.selectGenTableColumnListByTableId(genTableColumn);
      dataInfo.setRows(list);
      dataInfo.setTotal((long)list.size());
      return dataInfo;
   }

   @RequiresPermissions({"tool:gen:list"})
   @GetMapping({"/importTable"})
   public String importTable() {
      return this.prefix + "/importTable";
   }

   @GetMapping({"/createTable"})
   public String createTable() {
      return this.prefix + "/createTable";
   }

   @RequiresPermissions({"tool:gen:list"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.IMPORT
   )
   @PostMapping({"/importTable"})
   @ResponseBody
   public AjaxResult importTableSave(String tables) {
      String[] tableNames = Convert.toStrArray(tables);
      List<GenTable> tableList = this.genTableService.selectDbTableListByNames(tableNames);
      String operName = Convert.toStr(PermissionUtils.getPrincipalProperty("loginName"));
      this.genTableService.importGenTable(tableList, operName);
      return AjaxResult.success();
   }

   @RequiresPermissions({"tool:gen:edit"})
   @GetMapping({"/edit/{tableId}"})
   public String edit(@PathVariable("tableId") Long tableId, ModelMap mmap) {
      GenTable table = this.genTableService.selectGenTableById(tableId);
      List<GenTable> genTables = this.genTableService.selectGenTableAll();
      List<CxSelect> cxSelect = new ArrayList();
      Iterator var6 = genTables.iterator();

      while(true) {
         GenTable genTable;
         do {
            if (!var6.hasNext()) {
               mmap.put("table", table);
               mmap.put("data", JSON.toJSON(cxSelect));
               return this.prefix + "/edit";
            }

            genTable = (GenTable)var6.next();
         } while(StringUtils.equals(table.getTableName(), genTable.getTableName()));

         CxSelect cxTable = new CxSelect(genTable.getTableName(), genTable.getTableName() + '：' + genTable.getTableComment());
         List<CxSelect> cxColumns = new ArrayList();
         Iterator var10 = genTable.getColumns().iterator();

         while(var10.hasNext()) {
            GenTableColumn tableColumn = (GenTableColumn)var10.next();
            cxColumns.add(new CxSelect(tableColumn.getColumnName(), tableColumn.getColumnName() + '：' + tableColumn.getColumnComment()));
         }

         cxTable.setS(cxColumns);
         cxSelect.add(cxTable);
      }
   }

   @RequiresPermissions({"tool:gen:edit"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.UPDATE
   )
   @PostMapping({"/edit"})
   @ResponseBody
   public AjaxResult editSave(@Validated GenTable genTable) {
      this.genTableService.validateEdit(genTable);
      this.genTableService.updateGenTable(genTable);
      return AjaxResult.success();
   }

   @RequiresPermissions({"tool:gen:remove"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.DELETE
   )
   @PostMapping({"/remove"})
   @ResponseBody
   public AjaxResult remove(String ids) {
      this.genTableService.deleteGenTableByIds(ids);
      return AjaxResult.success();
   }

   @RequiresRoles({"admin"})
   @Log(
      title = "创建表",
      businessType = BusinessType.OTHER
   )
   @PostMapping({"/createTable"})
   @ResponseBody
   public AjaxResult create(String sql) {
      try {
         SqlUtil.filterKeyword(sql);
         List<SQLStatement> sqlStatements = SQLUtils.parseStatements(sql, DbType.mysql);
         List<String> tableNames = new ArrayList();
         Iterator var4 = sqlStatements.iterator();

         while(var4.hasNext()) {
            SQLStatement sqlStatement = (SQLStatement)var4.next();
            if (sqlStatement instanceof MySqlCreateTableStatement) {
               MySqlCreateTableStatement createTableStatement = (MySqlCreateTableStatement)sqlStatement;
               if (this.genTableService.createTable(createTableStatement.toString())) {
                  String tableName = createTableStatement.getTableName().replaceAll("`", "");
                  tableNames.add(tableName);
               }
            }
         }

         List<GenTable> tableList = this.genTableService.selectDbTableListByNames((String[])tableNames.toArray(new String[tableNames.size()]));
         String operName = Convert.toStr(PermissionUtils.getPrincipalProperty("loginName"));
         this.genTableService.importGenTable(tableList, operName);
         return AjaxResult.success();
      } catch (Exception var8) {
         this.logger.error(var8.getMessage(), var8);
         return AjaxResult.error("创建表结构异常");
      }
   }

   @RequiresPermissions({"tool:gen:preview"})
   @GetMapping({"/preview/{tableId}"})
   @ResponseBody
   public AjaxResult preview(@PathVariable("tableId") Long tableId) throws IOException {
      Map<String, String> dataMap = this.genTableService.previewCode(tableId);
      return AjaxResult.success(dataMap);
   }

   @RequiresPermissions({"tool:gen:code"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.GENCODE
   )
   @GetMapping({"/download/{tableName}"})
   public void download(HttpServletResponse response, @PathVariable("tableName") String tableName) throws IOException {
      byte[] data = this.genTableService.downloadCode(tableName);
      this.genCode(response, data);
   }

   @RequiresPermissions({"tool:gen:code"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.GENCODE
   )
   @GetMapping({"/genCode/{tableName}"})
   @ResponseBody
   public AjaxResult genCode(@PathVariable("tableName") String tableName) {
      this.genTableService.generatorCode(tableName);
      return AjaxResult.success();
   }

   @RequiresPermissions({"tool:gen:edit"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.UPDATE
   )
   @GetMapping({"/synchDb/{tableName}"})
   @ResponseBody
   public AjaxResult synchDb(@PathVariable("tableName") String tableName) {
      this.genTableService.synchDb(tableName);
      return AjaxResult.success();
   }

   @RequiresPermissions({"tool:gen:code"})
   @Log(
      title = "代码生成",
      businessType = BusinessType.GENCODE
   )
   @GetMapping({"/batchGenCode"})
   @ResponseBody
   public void batchGenCode(HttpServletResponse response, String tables) throws IOException {
      String[] tableNames = Convert.toStrArray(tables);
      byte[] data = this.genTableService.downloadCode(tableNames);
      this.genCode(response, data);
   }

   private void genCode(HttpServletResponse response, byte[] data) throws IOException {
      response.reset();
      response.setHeader("Content-Disposition", "attachment; filename=\"ruoyi.zip\"");
      response.addHeader("Content-Length", "" + data.length);
      response.setContentType("application/octet-stream; charset=UTF-8");
      IOUtils.write(data, response.getOutputStream());
   }
}
