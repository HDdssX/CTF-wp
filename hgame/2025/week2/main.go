package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"sync"
)

type DBConfig struct {
	Host     string `json:"host" binding:"required"`
	Port     string `json:"port" binding:"required"`
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type ImportConfig struct {
	RemoteHost     string `json:"remote_host" binding:"required"`
	RemotePort     string `json:"remote_port" binding:"required"`
	RemoteUsername string `json:"remote_username" binding:"required"`
	RemotePassword string `json:"remote_password" binding:"required"`
	RemoteDatabase string `json:"remote_database" binding:"required"`
	LocalDatabase  string `json:"local_database" binding:"required"`
}

type ConnectionManager struct {
	mu   sync.Mutex
	db   *sql.DB
	conf *DBConfig
}

var manager = &ConnectionManager{}
var localConfig DBConfig

func loadLocalConfig() error {
	configFile, err := os.Open("config.json")
	if err != nil {
		return fmt.Errorf("error opening config file: %v", err)
	}
	defer configFile.Close()

	decoder := json.NewDecoder(configFile)
	if err := decoder.Decode(&localConfig); err != nil {
		return fmt.Errorf("error decoding config file: %v", err)
	}

	return nil
}
func main() {
	if err := loadLocalConfig(); err != nil {
		log.Fatalf("Failed to load local configuration: %v", err)
	}
	r := gin.Default()

	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type"}
	r.Use(cors.New(config))
	r.LoadHTMLGlob("index.html")
	r.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index.html", nil)
	})
	r.GET("/flag", func(c *gin.Context) {
		data, err := ioutil.ReadFile("/flag")
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read /flag file"})
			return
		}
		c.String(http.StatusOK, string(data))
	})
	api := r.Group("/api")
	{
		api.GET("/databases", getDatabases)
		api.GET("/tables", getTables)
		api.GET("/data", getTableData)
		api.GET("/database", createDatabase)
		api.GET("/search", searchTableData)
		api.POST("/test-connection", testConnection)
		api.POST("/test-import-connection", testImportConnection)
		api.POST("/connect", connect)
		api.POST("/import", ImportData)

	}

	log.Printf("Server starting on http://localhost:9090")
	r.Run(":9090")
}

func testConnection(c *gin.Context) {
	dsn := buildDSN(localConfig)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to open connection: " + err.Error(),
		})
		return
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to connect: " + err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Connection successful",
	})
}

func testImportConnection(c *gin.Context) {
	var config ImportConfig
	if err := c.ShouldBindJSON(&config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Invalid request body: " + err.Error(),
		})
		return
	}

	if err := validateImportConfig(config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Invalid input: " + err.Error(),
		})
		return
	}

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s",
		sanitizeInput(config.RemoteUsername),
		config.RemotePassword,
		sanitizeInput(config.RemoteHost),
		config.RemotePort,
		sanitizeInput(config.RemoteDatabase),
	)

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to open connection: " + err.Error(),
		})
		return
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to connect: " + err.Error(),
		})
		return
	}

	var dbExists bool
	err = db.QueryRow("SELECT COUNT(*) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = ?",
		config.RemoteDatabase).Scan(&dbExists)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to verify database: " + err.Error(),
		})
		return
	}

	if !dbExists {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Remote database does not exist",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Connection successful",
	})
}

func connect(c *gin.Context) {
	var config DBConfig
	manager.mu.Lock()
	defer manager.mu.Unlock()

	if manager.db != nil {
		manager.db.Close()
	}
	dsn := buildDSN(localConfig)
	db, _ := sql.Open("mysql", dsn)

	if err := db.Ping(); err != nil {
		db.Close()
		return
	}

	manager.db = db
	manager.conf = &config
	c.JSON(http.StatusBadRequest, gin.H{
		"success": true,
		"message": "Connected To Database",
	})
	return
}

func getDatabases(c *gin.Context) {
	manager.mu.Lock()
	defer manager.mu.Unlock()

	if manager.db == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "No active connection",
		})
		return
	}

	rows, err := manager.db.Query("SHOW DATABASES")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to fetch databases: " + err.Error(),
		})
		return
	}
	defer rows.Close()

	var databases []string
	for rows.Next() {
		var dbName string
		if err := rows.Scan(&dbName); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to scan database name: " + err.Error(),
			})
			return
		}
		if dbName != "information_schema" && dbName != "mysql" &&
			dbName != "performance_schema" && dbName != "sys" {
			databases = append(databases, dbName)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    databases,
	})
}

func getTables(c *gin.Context) {
	dbName := c.Query("database")
	if dbName == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Database name is required",
		})
		return
	}

	manager.mu.Lock()
	defer manager.mu.Unlock()

	if manager.db == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "No active connection",
		})
		return
	}

	if _, err := manager.db.Exec("USE `" + dbName + "`"); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to switch database: " + err.Error(),
		})
		return
	}

	rows, err := manager.db.Query("SHOW TABLES")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to fetch tables: " + err.Error(),
		})
		return
	}
	defer rows.Close()

	var tables []string
	for rows.Next() {
		var tableName string
		if err := rows.Scan(&tableName); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to scan table name: " + err.Error(),
			})
			return
		}
		tables = append(tables, tableName)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tables,
	})
}

func getTableData(c *gin.Context) {
	dbName := c.Query("database")
	tableName := c.Query("table")
	page := c.DefaultQuery("page", "0")
	size := c.DefaultQuery("size", "0")

	if dbName == "" || tableName == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Database and table names are required",
		})
		return
	}

	manager.mu.Lock()
	defer manager.mu.Unlock()

	if manager.db == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "No active connection",
		})
		return
	}

	if _, err := manager.db.Exec(fmt.Sprintf("USE `%s`", dbName)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to switch database: " + err.Error(),
		})
		return
	}

	columns, err := getTableColumns(manager.db, tableName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to get table structure: " + err.Error(),
		})
		return
	}

	var total int
	sumQuery := fmt.Sprintf("SELECT COUNT(*) FROM `%s`.`%s`", dbName, tableName)
	if err := manager.db.QueryRow(sumQuery).Scan(&total); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to get total count: " + err.Error(),
		})
		return
	}

	var query string
	if page != "0" && size != "0" {
		pageNum, err1 := strconv.Atoi(page)
		pageSize, err2 := strconv.Atoi(size)
		if err1 != nil || err2 != nil || pageNum < 1 || pageSize < 1 {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"message": "Invalid page or size parameter",
			})
			return
		}

		offset := (pageNum - 1) * pageSize
		query = fmt.Sprintf("SELECT * FROM `%s`.`%s` LIMIT %d OFFSET %d",
			dbName, tableName, pageSize, offset)
	} else {
		query = fmt.Sprintf("SELECT * FROM `%s`.`%s` LIMIT 10", dbName, tableName)
	}

	rows, err := manager.db.Query(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to fetch data: " + err.Error(),
		})
		return
	}
	defer rows.Close()

	var results []map[string]interface{}
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to scan row: " + err.Error(),
			})
			return
		}

		row := make(map[string]interface{})
		for i, col := range columns {
			val := values[i]
			if b, ok := val.([]byte); ok {
				row[col] = string(b)
			} else {
				row[col] = val
			}
		}
		results = append(results, row)
	}

	if err = rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Error iterating rows: " + err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"records": results,
			"total":   total,
		},
	})
}

func getTableColumns(db *sql.DB, tableName string) ([]string, error) {
	rows, err := db.Query("SHOW COLUMNS FROM `" + tableName + "`")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var columns []string
	for rows.Next() {
		var field, typ, null, key, default_value, extra sql.NullString
		if err := rows.Scan(&field, &typ, &null, &key, &default_value, &extra); err != nil {
			return nil, err
		}
		columns = append(columns, field.String)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return columns, nil
}
func createDatabase(c *gin.Context) {
	databaseName := c.Query("db")
	query := fmt.Sprintf("CREATE DATABASE IF NOT EXISTS `%s`", databaseName)
	_, err := manager.db.Exec(query)
	if err != nil {
		c.JSON(http.StatusOK, gin.H{"success": "false", "message": err})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": "true", "message": "创建数据库" + databaseName + "成功"})
	return
}
func createdb(dbname string) error {
	query := fmt.Sprintf("CREATE DATABASE IF NOT EXISTS `%s`", dbname)
	_, err := manager.db.Exec(query)
	return err
}

func buildDSN(config DBConfig) string {
	return config.Username + ":" + config.Password + "@tcp(" + config.Host + ":" + config.Port + ")/"
}
func ImportData(c *gin.Context) {
	var config ImportConfig
	if err := c.ShouldBindJSON(&config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Invalid request body: " + err.Error(),
		})
		return
	}
	if err := validateImportConfig(config); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Invalid input: " + err.Error(),
		})
		return
	}

	config.RemoteHost = sanitizeInput(config.RemoteHost)
	config.RemoteUsername = sanitizeInput(config.RemoteUsername)
	config.RemoteDatabase = sanitizeInput(config.RemoteDatabase)
	config.LocalDatabase = sanitizeInput(config.LocalDatabase)
	if manager.db == nil {
		dsn := buildDSN(localConfig)
		db, err := sql.Open("mysql", dsn)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to connect to local database: " + err.Error(),
			})
			return
		}

		if err := db.Ping(); err != nil {
			db.Close()
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to ping local database: " + err.Error(),
			})
			return
		}

		manager.db = db
	}
	if err := createdb(config.LocalDatabase); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to create local database: " + err.Error(),
		})
		return
	}
	//Never able to inject shell commands,Hackers can't use this,HaHa
	command := fmt.Sprintf("/usr/local/bin/mysqldump -h %s -u %s -p%s %s |/usr/local/bin/mysql -h 127.0.0.1 -u %s -p%s %s",
		config.RemoteHost,
		config.RemoteUsername,
		config.RemotePassword,
		config.RemoteDatabase,
		localConfig.Username,
		localConfig.Password,
		config.LocalDatabase,
	)
	fmt.Println(command)
	cmd := exec.Command("sh", "-c", command)
	if err := cmd.Run(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to import data: " + err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Data imported successfully",
	})
}
func sanitizeInput(input string) string {
	reg := regexp.MustCompile(`[;&|><\(\)\{\}\[\]\\` + "`" + `]`)
	return reg.ReplaceAllString(input, "")
}
func searchTableData(c *gin.Context) {
	dbName := c.Query("database")
	tableName := c.Query("table")
	keyword := c.Query("keyword")
	page := c.DefaultQuery("page", "1")
	size := c.DefaultQuery("size", "10")

	if dbName == "" || tableName == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "Database and table names are required",
		})
		return
	}

	manager.mu.Lock()
	defer manager.mu.Unlock()

	if manager.db == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"message": "No active connection",
		})
		return
	}

	if _, err := manager.db.Exec(fmt.Sprintf("USE `%s`", dbName)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to switch database: " + err.Error(),
		})
		return
	}

	columns, err := getTableColumns(manager.db, tableName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to get table structure: " + err.Error(),
		})
		return
	}

	var whereClause string
	var args []interface{}
	if keyword != "" {
		var conditions []string
		for _, col := range columns {
			conditions = append(conditions, fmt.Sprintf("`%s` LIKE ?", col))
			args = append(args, "%"+keyword+"%")
		}
		whereClause = " WHERE " + strings.Join(conditions, " OR ")
	}

	var total int
	countQuery := fmt.Sprintf("SELECT COUNT(*) FROM `%s`%s", tableName, whereClause)
	if err := manager.db.QueryRow(countQuery, args...).Scan(&total); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to get total count: " + err.Error(),
		})
		return
	}

	pageNum, _ := strconv.Atoi(page)
	pageSize, _ := strconv.Atoi(size)
	offset := (pageNum - 1) * pageSize

	query := fmt.Sprintf("SELECT * FROM `%s`%s LIMIT ? OFFSET ?", tableName, whereClause)
	args = append(args, pageSize, offset)

	rows, err := manager.db.Query(query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to fetch data: " + err.Error(),
		})
		return
	}
	defer rows.Close()

	var results []map[string]interface{}
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"message": "Failed to scan row: " + err.Error(),
			})
			return
		}

		row := make(map[string]interface{})
		for i, col := range columns {
			val := values[i]
			if b, ok := val.([]byte); ok {
				row[col] = string(b)
			} else {
				row[col] = val
			}
		}
		results = append(results, row)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"records": results,
			"total":   total,
		},
	})
}
func validateImportConfig(config ImportConfig) error {
	if config.RemoteHost == "" ||
		config.RemoteUsername == "" ||
		config.RemoteDatabase == "" ||
		config.LocalDatabase == "" {
		return fmt.Errorf("missing required fields")
	}

	if match, _ := regexp.MatchString(`^[a-zA-Z0-9\.\-]+$`, config.RemoteHost); !match {
		return fmt.Errorf("invalid remote host")
	}

	if match, _ := regexp.MatchString(`^[a-zA-Z0-9_]+$`, config.RemoteUsername); !match {
		return fmt.Errorf("invalid remote username")
	}

	if match, _ := regexp.MatchString(`^[a-zA-Z0-9_]+$`, config.RemoteDatabase); !match {
		return fmt.Errorf("invalid remote database name")
	}

	if match, _ := regexp.MatchString(`^[a-zA-Z0-9_]+$`, config.LocalDatabase); !match {
		return fmt.Errorf("invalid local database name")
	}

	return nil
}
