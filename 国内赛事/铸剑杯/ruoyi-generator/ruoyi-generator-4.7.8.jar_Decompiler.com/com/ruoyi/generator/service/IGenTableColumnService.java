package com.ruoyi.generator.service;

import com.ruoyi.generator.domain.GenTableColumn;
import java.util.List;

public interface IGenTableColumnService {
   List<GenTableColumn> selectGenTableColumnListByTableId(GenTableColumn var1);

   int insertGenTableColumn(GenTableColumn var1);

   int updateGenTableColumn(GenTableColumn var1);

   int deleteGenTableColumnByIds(String var1);
}
