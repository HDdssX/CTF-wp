package main

import (
	"fmt"
	"math/rand"
	"os"
	"os/signal"
	"time"
)

func RandStr(length int) string {
	str := "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()-_=+[]{}|;:,.<>/?"
	bytes := []byte(str)
	result := []byte{}
	rand.Seed(time.Now().UnixNano() + int64(rand.Intn(100)))
	for i := 0; i < length; i++ {
		result = append(result, bytes[rand.Intn(len(bytes))])
	}
	return string(result)
}

func main() {

	_ = InitJWTSecret()
	_, err := InitDatabase("data/monitor.db")
	if err != nil {
		fmt.Println(err)
		return
	}
	go Monitor()

	adminName := "admin"
	adminPassword := RandStr(16)
	fmt.Println(adminName, adminPassword)
	_, _ = CreateUser(adminName, adminPassword)
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c
	_ = os.RemoveAll("data")
}
