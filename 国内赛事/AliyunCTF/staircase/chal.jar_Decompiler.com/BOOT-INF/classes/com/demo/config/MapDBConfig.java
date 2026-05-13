package com.demo.config;

import org.mapdb.DB;
import org.mapdb.DBMaker;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MapDBConfig {
   @Bean
   public DB mapDB() {
      return DBMaker.tempFileDB().fileMmapEnable().closeOnJvmShutdown().transactionEnable().make();
   }
}
