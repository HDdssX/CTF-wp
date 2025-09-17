package com.rois.happy_shopping.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.util.Date;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class JwtUtil {
   @Value("${jwt.secret}")
   private String secret;
   @Value("${jwt.expiration}")
   private Long expiration;

   public String generateToken(String username, String userId) {
      Date now = new Date();
      Date expiryDate = new Date(now.getTime() + this.expiration * 1000L);
      return Jwts.builder().setSubject(username).claim("userId", userId).setIssuedAt(now).setExpiration(expiryDate).signWith(SignatureAlgorithm.HS512, this.secret).compact();
   }

   public String getUsernameFromToken(String token) {
      Claims claims = this.getClaimsFromToken(token);
      return claims.getSubject();
   }

   public String getUserIdFromToken(String token) {
      Claims claims = this.getClaimsFromToken(token);
      return (String)claims.get("userId", String.class);
   }

   public Boolean validateToken(String token) {
      try {
         Claims claims = this.getClaimsFromToken(token);
         return !this.isTokenExpired(claims);
      } catch (Exception var3) {
         return false;
      }
   }

   private Claims getClaimsFromToken(String token) {
      return (Claims)Jwts.parser().setSigningKey(this.secret).parseClaimsJws(token).getBody();
   }

   private Boolean isTokenExpired(Claims claims) {
      Date expiration = claims.getExpiration();
      return expiration.before(new Date());
   }
}
