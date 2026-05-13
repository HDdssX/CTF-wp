/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  io.jsonwebtoken.Claims
 *  io.jsonwebtoken.Jws
 *  io.jsonwebtoken.JwtException
 *  io.jsonwebtoken.Jwts
 *  io.jsonwebtoken.SignatureAlgorithm
 */
package com.ctf;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import javax.crypto.spec.SecretKeySpec;

public class JwtUtil {
    private static final Key key = new SecretKeySpec("secret-secret-secret-secret-secret-secret-secret-secret-secret-secret-secret".getBytes(StandardCharsets.UTF_8), SignatureAlgorithm.HS256.getJcaName());
    private static final long EXPIRATION = 1800000L;

    public static String generateToken(String username) {
        return Jwts.builder().setSubject(username).setExpiration(new Date(System.currentTimeMillis() + 1800000L)).signWith(key).compact();
    }

    public static String validateToken(String token) {
        try {
            Jws claims = Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return ((Claims)claims.getBody()).getSubject();
        }
        catch (JwtException e) {
            return null;
        }
    }
}
