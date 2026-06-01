package main

import (
	"context"
	"database/sql"
	"os"
	"time"

	_ "modernc.org/sqlite"
)

var DB *sql.DB

func InitDatabase(path string) (*sql.DB, error) {
	// 确保目录存在
	if err := os.MkdirAll("data", 0o755); err != nil {
		return nil, err
	}

	// 打开数据库（driver 名称为 "sqlite"）
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}

	// 限制打开连接数（根据需要调整）
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(time.Hour)

	// 使用上下文执行初始化语句
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 简单的 PRAGMA 设置
	pragmas := []string{
		"PRAGMA journal_mode=WAL;",
		"PRAGMA synchronous=NORMAL;",
		"PRAGMA foreign_keys=ON;",
	}
	for _, p := range pragmas {
		if _, err := db.ExecContext(ctx, p); err != nil {
			db.Close()
			return nil, err
		}
	}

	// Ping 确认可用
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, err
	}

	// 简单迁移：users 和 commands 表（根据需要调整字段）
	schema := []string{
		`CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		);`,
		`CREATE TABLE IF NOT EXISTS commands (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			cmd TEXT NOT NULL,
			args TEXT,
			output TEXT,
			error TEXT,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		);`,
	}
	for _, s := range schema {
		if _, err := db.ExecContext(ctx, s); err != nil {
			db.Close()
			return nil, err
		}
	}

	// 全局保存并返回
	DB = db
	return db, nil
}

func CountUsersByUsername(username string) (int64, error) {
	var cnt int64
	err := DB.QueryRow("SELECT COUNT(1) FROM users WHERE username = ?", username).Scan(&cnt)
	if err != nil {
		return 0, err
	}
	return cnt, nil
}

func CreateUser(username, password string) (sql.Result, error) {
	cnt, err := CountUsersByUsername(username)
	if err != nil {
		return nil, err
	}
	if cnt > 0 {
		return nil, nil
	}
	result, err := DB.Exec("INSERT INTO users (username, password) VALUES (?, ?)", username, password)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func SearchUserByUsername(username string) (*sql.Row, error) {
	row := DB.QueryRow("SELECT username, password FROM users WHERE username = ?", username)
	return row, nil
}
