package com.ruoyi.generator.domain;

import com.ruoyi.common.constant.GenConstants;
import com.ruoyi.common.core.domain.BaseEntity;
import com.ruoyi.common.utils.StringUtils;
import java.util.List;
import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import org.apache.commons.lang3.ArrayUtils;

public class GenTable extends BaseEntity {
   private static final long serialVersionUID = 1L;
   private Long tableId;
   @NotBlank(
      message = "表名称不能为空"
   )
   private String tableName;
   @NotBlank(
      message = "表描述不能为空"
   )
   private String tableComment;
   private String subTableName;
   private String subTableFkName;
   @NotBlank(
      message = "实体类名称不能为空"
   )
   private String className;
   private String tplCategory;
   @NotBlank(
      message = "生成包路径不能为空"
   )
   private String packageName;
   @NotBlank(
      message = "生成模块名不能为空"
   )
   private String moduleName;
   @NotBlank(
      message = "生成业务名不能为空"
   )
   private String businessName;
   @NotBlank(
      message = "生成功能名不能为空"
   )
   private String functionName;
   @NotBlank(
      message = "作者不能为空"
   )
   private String functionAuthor;
   private String genType;
   private String genPath;
   private GenTableColumn pkColumn;
   private GenTable subTable;
   @Valid
   private List<GenTableColumn> columns;
   private String options;
   private String treeCode;
   private String treeParentCode;
   private String treeName;
   private String parentMenuId;
   private String parentMenuName;

   public Long getTableId() {
      return this.tableId;
   }

   public void setTableId(Long tableId) {
      this.tableId = tableId;
   }

   public String getTableName() {
      return this.tableName;
   }

   public void setTableName(String tableName) {
      this.tableName = tableName;
   }

   public String getTableComment() {
      return this.tableComment;
   }

   public void setTableComment(String tableComment) {
      this.tableComment = tableComment;
   }

   public String getSubTableName() {
      return this.subTableName;
   }

   public void setSubTableName(String subTableName) {
      this.subTableName = subTableName;
   }

   public String getSubTableFkName() {
      return this.subTableFkName;
   }

   public void setSubTableFkName(String subTableFkName) {
      this.subTableFkName = subTableFkName;
   }

   public String getClassName() {
      return this.className;
   }

   public void setClassName(String className) {
      this.className = className;
   }

   public String getTplCategory() {
      return this.tplCategory;
   }

   public void setTplCategory(String tplCategory) {
      this.tplCategory = tplCategory;
   }

   public String getPackageName() {
      return this.packageName;
   }

   public void setPackageName(String packageName) {
      this.packageName = packageName;
   }

   public String getModuleName() {
      return this.moduleName;
   }

   public void setModuleName(String moduleName) {
      this.moduleName = moduleName;
   }

   public String getBusinessName() {
      return this.businessName;
   }

   public void setBusinessName(String businessName) {
      this.businessName = businessName;
   }

   public String getFunctionName() {
      return this.functionName;
   }

   public void setFunctionName(String functionName) {
      this.functionName = functionName;
   }

   public String getFunctionAuthor() {
      return this.functionAuthor;
   }

   public void setFunctionAuthor(String functionAuthor) {
      this.functionAuthor = functionAuthor;
   }

   public String getGenType() {
      return this.genType;
   }

   public void setGenType(String genType) {
      this.genType = genType;
   }

   public String getGenPath() {
      return this.genPath;
   }

   public void setGenPath(String genPath) {
      this.genPath = genPath;
   }

   public GenTableColumn getPkColumn() {
      return this.pkColumn;
   }

   public void setPkColumn(GenTableColumn pkColumn) {
      this.pkColumn = pkColumn;
   }

   public GenTable getSubTable() {
      return this.subTable;
   }

   public void setSubTable(GenTable subTable) {
      this.subTable = subTable;
   }

   public List<GenTableColumn> getColumns() {
      return this.columns;
   }

   public void setColumns(List<GenTableColumn> columns) {
      this.columns = columns;
   }

   public String getOptions() {
      return this.options;
   }

   public void setOptions(String options) {
      this.options = options;
   }

   public String getTreeCode() {
      return this.treeCode;
   }

   public void setTreeCode(String treeCode) {
      this.treeCode = treeCode;
   }

   public String getTreeParentCode() {
      return this.treeParentCode;
   }

   public void setTreeParentCode(String treeParentCode) {
      this.treeParentCode = treeParentCode;
   }

   public String getTreeName() {
      return this.treeName;
   }

   public void setTreeName(String treeName) {
      this.treeName = treeName;
   }

   public String getParentMenuId() {
      return this.parentMenuId;
   }

   public void setParentMenuId(String parentMenuId) {
      this.parentMenuId = parentMenuId;
   }

   public String getParentMenuName() {
      return this.parentMenuName;
   }

   public void setParentMenuName(String parentMenuName) {
      this.parentMenuName = parentMenuName;
   }

   public boolean isSub() {
      return isSub(this.tplCategory);
   }

   public static boolean isSub(String tplCategory) {
      return tplCategory != null && StringUtils.equals("sub", tplCategory);
   }

   public boolean isTree() {
      return isTree(this.tplCategory);
   }

   public static boolean isTree(String tplCategory) {
      return tplCategory != null && StringUtils.equals("tree", tplCategory);
   }

   public boolean isCrud() {
      return isCrud(this.tplCategory);
   }

   public static boolean isCrud(String tplCategory) {
      return tplCategory != null && StringUtils.equals("crud", tplCategory);
   }

   public boolean isSuperColumn(String javaField) {
      return isSuperColumn(this.tplCategory, javaField);
   }

   public static boolean isSuperColumn(String tplCategory, String javaField) {
      return isTree(tplCategory) ? StringUtils.equalsAnyIgnoreCase(javaField, (CharSequence[])ArrayUtils.addAll(GenConstants.TREE_ENTITY, GenConstants.BASE_ENTITY)) : StringUtils.equalsAnyIgnoreCase(javaField, GenConstants.BASE_ENTITY);
   }
}
