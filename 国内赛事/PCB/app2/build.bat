@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Building Executable JAR Package
echo ========================================

REM 检查Java是否安装
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Java is not installed or not in PATH
    pause
    exit /b 1
)

javac -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: javac is not installed or not in PATH
    pause
    exit /b 1
)

REM 创建输出目录
if not exist "dist" mkdir dist
if not exist "dist\lib" mkdir dist\lib
if not exist "temp_classes" mkdir temp_classes

echo.
echo [1/5] Downloading Tomcat Embedded...
if not exist "dist\lib\tomcat-embed-core-9.0.80.jar" (
    echo   - Downloading tomcat-embed-core...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/embed/tomcat-embed-core/9.0.80/tomcat-embed-core-9.0.80.jar' -OutFile 'dist\lib\tomcat-embed-core-9.0.80.jar'}" 2>nul
) else (
    echo   - tomcat-embed-core already exists
)

if not exist "dist\lib\tomcat-annotations-api-9.0.80.jar" (
    echo   - Downloading tomcat-annotations-api...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/tomcat-annotations-api/9.0.80/tomcat-annotations-api-9.0.80.jar' -OutFile 'dist\lib\tomcat-annotations-api-9.0.80.jar'}" 2>nul
) else (
    echo   - tomcat-annotations-api already exists
)

if not exist "dist\lib\tomcat-embed-jasper-9.0.80.jar" (
    echo   - Downloading tomcat-embed-jasper...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/embed/tomcat-embed-jasper/9.0.80/tomcat-embed-jasper-9.0.80.jar' -OutFile 'dist\lib\tomcat-embed-jasper-9.0.80.jar'}" 2>nul
) else (
    echo   - tomcat-embed-jasper already exists
)

if not exist "dist\lib\tomcat-embed-el-9.0.80.jar" (
    echo   - Downloading tomcat-embed-el...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/apache/tomcat/embed/tomcat-embed-el/9.0.80/tomcat-embed-el-9.0.80.jar' -OutFile 'dist\lib\tomcat-embed-el-9.0.80.jar'}" 2>nul
) else (
    echo   - tomcat-embed-el already exists
)

if not exist "dist\lib\ecj-3.26.0.jar" (
    echo   - Downloading Eclipse Java Compiler...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/3.26.0/ecj-3.26.0.jar' -OutFile 'dist\lib\ecj-3.26.0.jar'}" 2>nul
) else (
    echo   - ecj already exists
)

echo.
echo [2/5] Copying dependencies...
if exist "WEB-INF\lib\*.jar" (
    copy /Y "WEB-INF\lib\*.jar" "dist\lib\" >nul
    echo   - Copied existing dependencies from WEB-INF\lib
)

echo.
echo [3/5] Compiling Java source files...
REM 构建classpath
set CLASSPATH=dist\lib\*
javac -encoding UTF-8 -cp "!CLASSPATH!" -d temp_classes WEB-INF\classes\com\ctf\*.java
if %errorlevel% neq 0 (
    echo   - Compilation failed!
    pause
    exit /b 1
)
echo   - Compilation successful

echo.
echo [4/5] Creating JAR package...
REM 创建临时目录结构
if exist "temp_jar" rmdir /S /Q temp_jar
mkdir temp_jar\META-INF

REM 复制编译好的class文件
xcopy /E /I /Y temp_classes\* temp_jar\ >nul

REM 复制资源文件
if exist "css" xcopy /E /I /Y css temp_jar\css >nul
if exist "js" xcopy /E /I /Y js temp_jar\js >nul
if exist "*.html" copy /Y *.html temp_jar\ >nul

REM 复制WEB-INF配置
mkdir temp_jar\WEB-INF
if exist "WEB-INF\web.xml" copy /Y "WEB-INF\web.xml" "temp_jar\WEB-INF\" >nul

REM 创建MANIFEST.MF
echo Manifest-Version: 1.0 > temp_jar\META-INF\MANIFEST.MF
echo Main-Class: com.ctf.Main >> temp_jar\META-INF\MANIFEST.MF

REM 添加Class-Path
set CP=
for %%f in (dist\lib\*.jar) do (
    if defined CP (
        set CP=!CP! lib/%%~nxf
    ) else (
        set CP=lib/%%~nxf
    )
)
if defined CP (
    echo Class-Path: !CP!>> temp_jar\META-INF\MANIFEST.MF
)
echo.>> temp_jar\META-INF\MANIFEST.MF

REM 打包JAR
cd temp_jar
jar cfm ..\dist\app.jar META-INF\MANIFEST.MF .
cd ..
echo   - JAR created: dist\app.jar

echo.
echo [5/5] Cleaning up...
rmdir /S /Q temp_jar
rmdir /S /Q temp_classes
echo   - Temporary files removed

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output Files:
echo   Main JAR:  dist\app.jar
echo   Libraries: dist\lib\
echo.
echo Usage:
echo   java -jar dist\app.jar [port]
echo.
echo   Default port: 8080
echo   Example:      java -jar dist\app.jar 8080
echo ========================================
pause
