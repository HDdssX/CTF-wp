package main

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

func Cors() gin.HandlerFunc {
	return func(c *gin.Context) {
		method := c.Request.Method
		origin := c.Request.Header.Get("Origin")
		if origin != "" {
			c.Header("Access-Control-Allow-Origin", "*")
			c.Header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE, UPDATE")
			c.Header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization")
			c.Header("Access-Control-Expose-Headers", "Content-Length, Access-Control-Allow-Origin, Access-Control-Allow-Headers, Cache-Control, Content-Language, Content-Type")
			c.Header("Access-Control-Allow-Credentials", "true")
		}
		if method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
		}
		c.Next()
	}
}

func Monitor() {
	r := gin.Default()
	r.Use(Cors())
	r.LoadHTMLGlob("templates/*")
	api := r.Group("/api")
	{
		admin := api.Group("/admin", AuthAdminMiddleware())
		{
			admin.POST("/cmd", AdminCmd)
		}
		user := api.Group("/user", AuthMiddleware())
		{
			user.POST("/cmd", UserCmd)
		}

		account := api.Group("/account")
		{
			account.POST("/login", Login)
			account.POST("/register", Register)
		}
	}
	view := r.Group("/")
	{
		view.GET("/", func(c *gin.Context) {
			c.Redirect(http.StatusMovedPermanently, "/login")
		})
		view.GET("/login", func(c *gin.Context) {
			c.HTML(http.StatusOK, "login.html", nil)
		})
		view.GET("/register", func(c *gin.Context) {
			c.HTML(http.StatusOK, "register.html", nil)
		})
		view.GET("/user", func(c *gin.Context) {
			c.HTML(http.StatusOK, "user.html", nil)
		})
		view.GET("/admin", func(c *gin.Context) {
			c.HTML(http.StatusOK, "admin.html", nil)
		})
	}

	time.Sleep(time.Second * 5)

	r.Run(":8080")

}
