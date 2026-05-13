package com.ruoyi.generator.service.impl;

import com.ruoyi.common.core.text.Convert;
import com.ruoyi.generator.domain.GenTableColumn;
import com.ruoyi.generator.mapper.GenTableColumnMapper;
import com.ruoyi.generator.service.IGenTableColumnService;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class GenTableColumnServiceImpl implements IGenTableColumnService {
   @Autowired
   private GenTableColumnMapper genTableColumnMapper;

   public List<GenTableColumn> selectGenTableColumnListByTableId(GenTableColumn genTableColumn) {
      return this.genTableColumnMapper.selectGenTableColumnListByTableId(genTableColumn);
   }

   public int insertGenTableColumn(GenTableColumn genTableColumn) {
      return this.genTableColumnMapper.insertGenTableColumn(genTableColumn);
   }

   public int updateGenTableColumn(GenTableColumn genTableColumn) {
      return this.genTableColumnMapper.updateGenTableColumn(genTableColumn);
   }

   public int deleteGenTableColumnByIds(String ids) {
      return this.genTableColumnMapper.deleteGenTableColumnByIds(Convert.toLongArray(ids));
   }
}
