package main

import (
	"fmt"
	"math/rand"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

var key []byte

func InitJWTSecret() []byte {
	// In a real application, use a secure method to generate and store the secret key
	key = make([]byte, 32)
	rand.Read(key)
	return key
}

func SignJWT(username string) (string, error) {
	claims := jwt.MapClaims{
		"username": username,
	}
	return GenerateJWT(claims)
}

func GenerateJWT(claims jwt.MapClaims) (string, error) {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(key)
}

func ValidateJWT(tokenString string) (*jwt.Token, error) {
	return jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, jwt.ErrSignatureInvalid
		}
		return key, nil
	})
}

func AuthAdminMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")

		token, err := ValidateJWT(tokenString)
		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(401, gin.H{"error": "Invalid token"})
			return
		}

		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			username, _ := claims["username"].(string)
			if username != "admin" {
				c.AbortWithStatusJSON(403, gin.H{"error": "No permission,please use admin account"})
				return
			}
		}
		c.Next()
	}
}

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")
		fmt.Println("Authorization Token:", tokenString)
		token, err := ValidateJWT(tokenString)
		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(401, gin.H{"error": "Invalid token"})
			return
		}
		c.Next()
	}
}
