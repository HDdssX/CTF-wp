package com.rois.happy_shopping.util;

import java.util.Collections;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;

@Component
public class RedisLockUtil {
   @Autowired
   private RedisTemplate<String, Object> redisTemplate;
   private static final String LOCK_PREFIX = "lock:";
   private static final String UNLOCK_SCRIPT = "if redis.call('get', KEYS[1]) == ARGV[1] then     return redis.call('del', KEYS[1]) else     return 0 end";

   public boolean tryLock(String key, String value, long expireTime) {
      String lockKey = "lock:" + key;
      Boolean result = this.redisTemplate.opsForValue().setIfAbsent(lockKey, value, expireTime, TimeUnit.SECONDS);
      return Boolean.TRUE.equals(result);
   }

   public boolean unlock(String key, String value) {
      String lockKey = "lock:" + key;
      DefaultRedisScript<Long> script = new DefaultRedisScript();
      script.setScriptText("if redis.call('get', KEYS[1]) == ARGV[1] then     return redis.call('del', KEYS[1]) else     return 0 end");
      script.setResultType(Long.class);
      Long result = (Long)this.redisTemplate.execute(script, Collections.singletonList(lockKey), new Object[]{value});
      return Long.valueOf(1L).equals(result);
   }

   public String generateLockValue() {
      return Thread.currentThread().getId() + ":" + System.currentTimeMillis();
   }
}
