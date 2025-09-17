package com.ruoyi.generator.mapper;

import com.ruoyi.generator.domain.GenTableColumn;
import java.util.List;

public interface GenTableColumnMapper {
   List<GenTableColumn> selectDbTableColumnsByName(String var1);

   List<GenTableColumn> selectGenTableColumnListByTableId(GenTableColumn var1);

   int insertGenTableColumn(GenTableColumn var1);

   int updateGenTableColumn(GenTableColumn var1);

   int deleteGenTableColumns(List<GenTableColumn> var1);

   int deleteGenTableColumnByIds(Long[] var1);
}
