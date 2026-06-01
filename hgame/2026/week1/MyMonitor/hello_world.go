package main

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
)

// 定义接收 JSON 数据的结构体
type LoginRequest struct {
	User     string `json:"user" binding:"required"`
	Password string `json:"password" binding:"required"`
}

func main() {
	// 1. 初始化引擎
	r := gin.Default()

	// 2. 加载 HTML 模板
	// 为了演示，这里直接嵌入 HTML 字符串，实际开发中会用 r.LoadHTMLGlob("templates/*")
	// 你可以把这段 HTML 放到 main.go 同级目录的 index.html 中，然后用 r.LoadHTMLFiles("index.html")
	r.SetHTMLTemplate(template())

	// ==================== 路由部分 ====================

	// 一个最简单的 GET 路由，返回 HTML 页面
	r.GET("/", func(c *gin.Context) {
		// 渲染名为 "index" 的模板，并传入数据
		c.HTML(http.StatusOK, "index", gin.H{
			"title": "Gin Hello World",
		})
	})

	// JSON API 路由
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "pong",
		})
	})

	// 接收 POST 参数的路由
	r.POST("/login", func(c *gin.Context) {
		var json LoginRequest
		// 绑定 JSON 数据到结构体
		if err := c.ShouldBindJSON(&json); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		if json.User == "admin" && json.Password == "123456" {
			c.JSON(http.StatusOK, gin.H{"status": "you are logged in"})
		} else {
			c.JSON(http.StatusUnauthorized, gin.H{"status": "unauthorized"})
		}
	})

	// 路由参数 /user/john
	r.GET("/user/:name", func(c *gin.Context) {
		name := c.Param("name")
		message := name + " is here"
		c.String(http.StatusOK, message)
	})

	// 3. 启动服务，默认监听 0.0.0.0:8080
	fmt.Println("Server is running at http://localhost:8080")
	r.Run()
}

// 模拟 HTML 模板内容
// 在 Go 中，HTML 模板使用 {{ .VariableName }} 来取值
import "html/template"

func template() *template.Template {
	t := template.New("index")
	t.Parse(`
<!DOCTYPE html>
<html>
<head>
    <title>{{ .title }}</title>
</head>
<body>
    <h1>Hello, {{ .title }}!</h1>
    <p>Try sending a request to <a href="/ping">/ping</a></p>
    <p>Try sending a request to <a href="/user/Guest">/user/Guest</a></p>
</body>
</html>
`)
	return t
}
