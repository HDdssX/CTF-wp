@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Building Executable JAR package...
echo ========================================

REM 检查Java是否安装
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Java is not installed or not in PATH
    pause
    exit /b 1
)

REM 创建输出目录
if not exist "dist" mkdir dist
if not exist "dist\lib" mkdir dist\lib

echo.
echo Step 1: Downloading Tomcat Embedded dependencies...

REM 下载Tomcat Embed Core
if not exist "dist\lib\tomcat-embed-core-9.0.80.jar" (
    echo Downloading tomcat-embed-core...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/embed/tomcat-embed-core/9.0.80/tomcat-embed-core-9.0.80.jar' -OutFile 'dist\lib\tomcat-embed-core-9.0.80.jar'}"
)

if not exist "dist\lib\tomcat-annotations-api-9.0.80.jar" (
    echo Downloading tomcat-annotations-api...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/tomcat-annotations-api/9.0.80/tomcat-annotations-api-9.0.80.jar' -OutFile 'dist\lib\tomcat-annotations-api-9.0.80.jar'}"
)

echo.
echo Step 2: Copying existing dependencies...
if exist "WEB-INF\lib\" (
    copy /Y "WEB-INF\lib\*.jar" "dist\lib\" >nul
)

echo.
echo Step 3: Creating executable JAR...

REM 创建临时目录
if exist "temp_jar" rmdir /S /Q temp_jar
mkdir temp_jar
mkdir temp_jar\com\ctf
mkdir temp_jar\css
mkdir temp_jar\js
mkdir temp_jar\META-INF

REM 复制编译的class文件
echo Copying compiled classes...
if exist "WEB-INF\classes\com\ctf\*.class" (
    copy /Y "WEB-INF\classes\com\ctf\*.class" "temp_jar\com\ctf\" >nul 2>&1
) else (
    echo No compiled class files found, copying source files...
    copy /Y "WEB-INF\classes\com\ctf\*.java" "temp_jar\com\ctf\"
)

REM 复制资源文件
echo Copying web resources...
if exist "css" xcopy /E /I /Y css temp_jar\css >nul
if exist "js" xcopy /E /I /Y js temp_jar\js >nul
if exist "*.html" copy /Y *.html temp_jar\ >nul

REM 复制WEB-INF
mkdir temp_jar\WEB-INF
if exist "WEB-INF\web.xml" copy /Y "WEB-INF\web.xml" "temp_jar\WEB-INF\" >nul

REM 创建MANIFEST.MF
echo Manifest-Version: 1.0 > temp_jar\META-INF\MANIFEST.MF
echo Main-Class: com.ctf.Main >> temp_jar\META-INF\MANIFEST.MF

REM 构建classpath字符串
set CP=
for %%f in (dist\lib\*.jar) do (
    if defined CP (
        set CP=!CP! lib/%%~nxf
    ) else (
        set CP=lib/%%~nxf
    )
)
if defined CP (
    echo Class-Path: !CP! >> temp_jar\META-INF\MANIFEST.MF
)
echo. >> temp_jar\META-INF\MANIFEST.MF

REM 打包JAR
cd temp_jar
echo Creating JAR file...
jar cfm ..\dist\app.jar META-INF\MANIFEST.MF .
cd ..

REM 清理临时文件
rmdir /S /Q temp_jar

echo.
echo ========================================
echo Build Successful!
echo ========================================
echo.
echo Output:
echo   - dist\app.jar (Main application JAR)
echo   - dist\lib\*.jar (All dependencies)
echo.
echo To run the application:
echo   java -jar dist\app.jar [port]
echo.
echo Default port: 8080
echo Example: java -jar dist\app.jar 9090
echo ========================================
echo.
pause
