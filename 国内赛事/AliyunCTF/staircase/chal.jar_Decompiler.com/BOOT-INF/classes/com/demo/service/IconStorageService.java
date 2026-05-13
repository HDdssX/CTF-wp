package com.demo.service;

import java.util.Base64;
import org.mapdb.DB;
import org.mapdb.HTreeMap;
import org.mapdb.Serializer;
import org.springframework.stereotype.Service;

@Service
public class IconStorageService {
   private final DB mapDB;
   private final HTreeMap iconMap;
   private static final String iconKey = "icon";
   public static final byte[] defaultIcon = Base64.getDecoder().decode("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAATUlEQVR4nGP8//8/AyWAiSLdDAwMLOgC7s1bCTppZ603I1YXuBOhGV0dE6ma0dUzMVAImEYNYBhOYbATKXkSA2DqUVxArCHI6hgpzc4AMPAaG7S7LBoAAAAASUVORK5CYII=");

   public IconStorageService(DB mapDB) {
      this.mapDB = mapDB;
      this.iconMap = mapDB.hashMap("icons").keySerializer(Serializer.STRING).valueSerializer(Serializer.JAVA).createOrOpen();
      this.iconMap.put("icon", defaultIcon);
      mapDB.commit();
   }

   public void storeIcon(byte[] iconBytes) {
      if (iconBytes != null && iconBytes.length != 0) {
         if (iconBytes.length > 324) {
            throw new IllegalArgumentException("icon size cannot exceed 18x18");
         } else {
            this.iconMap.put("icon", iconBytes);
            this.mapDB.commit();
         }
      } else {
         throw new IllegalArgumentException("icon data cannot be empty");
      }
   }

   public byte[] getIcon() {
      return (byte[])this.iconMap.get("icon");
   }
}
