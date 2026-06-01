package main

import (
	"fmt"
	"os/exec"
	"sync"

	"github.com/gin-gonic/gin"
)

type UserStruct struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type MonitorStruct struct {
	Cmd  string `json:"cmd" binding:"required"`
	Args string `json:"args"`
}

var MonitorPool = &sync.Pool{
	New: func() any {
		return &MonitorStruct{}
	},
}

func (m *MonitorStruct) reset() {
	m.Cmd = ""
	m.Args = ""
	fmt.Println("reset")
}

func AdminCmd(c *gin.Context) {
	monitor := MonitorPool.Get().(*MonitorStruct)
	defer MonitorPool.Put(monitor)
	if err := c.ShouldBindJSON(monitor); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	fmt.Println(monitor)
	defer monitor.reset()
	fullCommand := fmt.Sprintf("%s %s", monitor.Cmd, monitor.Args)
	output, err := exec.Command("bash", "-c", fullCommand).CombinedOutput()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error(), "output": string(output)})
		return
	}
	c.JSON(200, gin.H{"output": string(output)})
	return
}

func UserCmd(c *gin.Context) {
	monitor := MonitorPool.Get().(*MonitorStruct)
	defer MonitorPool.Put(monitor)
	if err := c.ShouldBindJSON(monitor); err != nil {
		fmt.Println(monitor)
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	fmt.Println(monitor)
	defer monitor.reset()
	if monitor.Cmd != "status" {
		c.JSON(403, gin.H{"response": "No permission to execute this command"})
		return
	}
	c.JSON(400, gin.H{"response": "Not implemented yet :("})
	return
}

func Login(c *gin.Context) {
	var user UserStruct
	if err := c.ShouldBindJSON(&user); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	var userFromDB UserStruct
	sql, err := SearchUserByUsername(user.Username)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	err = sql.Scan(&userFromDB.Username, &userFromDB.Password)
	if err != nil {
		c.JSON(400, gin.H{"response": "User does not exist"})
		return
	}
	fmt.Println(userFromDB)
	if user.Password != userFromDB.Password {
		c.JSON(400, gin.H{"response": "Incorrect password"})
		return
	}
	jwt, err := SignJWT(user.Username)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"response": "Login successful", "Authorization": jwt})
	return
}

func Register(c *gin.Context) {
	var user UserStruct
	if err := c.ShouldBindJSON(&user); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	res, err := CreateUser(user.Username, user.Password)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	if res == nil {
		c.JSON(400, gin.H{"response": "User already exists"})
		return
	}
	cnt, err := res.RowsAffected()

	if cnt == 0 {
		c.JSON(400, gin.H{"response": "User already exists"})
		return
	}
	jwt, err := SignJWT(user.Username)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"response": "User registered successfully", "Authorization": jwt})
	return
}
