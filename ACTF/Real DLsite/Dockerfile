FROM debian:forky-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git apache2 libapache2-mod-fcgid fcgiwrap spawn-fcgi supervisor sqlite3 cron php8.4-fpm php8.4-sqlite3 util-linux gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*
RUN a2enmod rewrite proxy_fcgi proxy_http

# Ancient repos always have good reputation :)
RUN cd /var/www/html && \
    rm -rf ./* && \
    git clone --depth=1 https://github.com/mnihyc/dlsite.git . && \
    touch index.html && \
    sed -i '9 i Your site is working normally! Access data at <a href="/data/">/data</a>, or new site at <a href="/new/#/_/test">/new</a>' dl/index.html && \
    ln -s /app/data/local/test dl/data && \
    sqlite3 db.sqlite "CREATE TABLE CONFIG(NAME NTEXT NOT NULL,TYPE NTEXT NOT NULL,VALUE NTEXT NOT NULL,PRIMARY KEY (NAME,TYPE));" && \
    chown -R root:www-data . && \
    find . -type d -exec chmod 1775 {} + && \
    find . -type f -exec chmod 0664 {} +

RUN cat > /etc/apache2/sites-available/000-default.conf <<'EOF'
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html

    RewriteEngine On
    RewriteCond %{REQUEST_URI} !^/(main\.php|assets/|favicon\.ico$|robots\.txt$|new(?:/|$)|ancient(?:/|$))
    RewriteRule ^ /main.php [L]

    <Directory /var/www/html>
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php-fpm.sock|fcgi://localhost"
    </FilesMatch>

    <Directory /app/data/local/test>
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    ProxyPreserveHost On
    <LocationMatch "^/ancient$">
        SetHandler "proxy:unix:/run/apache2/ancient.sock|fcgi://localhost"
        ProxyFCGIBackendType GENERIC
        ProxyFCGISetEnvIf "true" SCRIPT_FILENAME "/app/data/local/test/index.cgi"
        ProxyFCGISetEnvIf "true" SCRIPT_NAME "/ancient"
    </LocationMatch>
    Alias /ancient/ /app/data/local/test/

    ProxyPass /new http://127.0.0.1:8089/new
    ProxyPassReverse /new http://127.0.0.1:8089/new

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF

RUN cat > /etc/php/8.4/fpm/conf.d/99-override.ini <<'EOF'
allow_url_fopen = Off
allow_url_include = Off
display_errors = Off
error_reporting = 0
expose_php = Off
max_execution_time = 5
memory_limit = 256M
open_basedir = /var/www/html:/tmp:/app/data/local/test
disable_classes = InternalIterator,Generator,WeakReference,WeakMap,Attribute,ReturnTypeWillChange,AllowDynamicProperties,SensitiveParameter,SensitiveParameterValue,Fiber,stdClass,DateTime,DateTimeImmutable,DateTimeZone,DateInterval,DatePeriod,OpenSSLCertificate,OpenSSLCertificateSigningRequest,OpenSSLAsymmetricKey,InflateContext,DeflateContext,CurlHandle,CurlMultiHandle,CurlShareHandle,CURLFile,CURLStringFile,Dom\AdjacentPosition,dom\domexception,DOMImplementation,Dom\Implementation,DOMNode,Dom\Node,DOMNameSpaceNode,Dom\NamespaceInfo,DOMDocumentFragment,Dom\DocumentFragment,Dom\Document,DOMDocument,Dom\HTMLDocument,Dom\XMLDocument,DOMNodeList,Dom\NodeList,DOMNamedNodeMap,Dom\NamedNodeMap,Dom\DtdNamedNodeMap,Dom\HTMLCollection,DOMCharacterData,Dom\CharacterData,DOMAttr,Dom\Attr,DOMElement,Dom\Element,Dom\HTMLElement,DOMText,Dom\Text,DOMComment,Dom\Comment,DOMCdataSection,Dom\CDATASection,DOMDocumentType,Dom\DocumentType,DOMNotation,Dom\Notation,DOMEntity,Dom\Entity,DOMEntityReference,Dom\EntityReference,DOMProcessingInstruction,Dom\ProcessingInstruction,DOMXPath,Dom\XPath,Dom\TokenList,finfo,HashContext,RecursiveIteratorIterator,IteratorIterator,FilterIterator,RecursiveFilterIterator,CallbackFilterIterator,RecursiveCallbackFilterIterator,ParentIterator,LimitIterator,CachingIterator,RecursiveCachingIterator,NoRewindIterator,AppendIterator,InfiniteIterator,RegexIterator,RecursiveRegexIterator,EmptyIterator,RecursiveTreeIterator,ArrayObject,ArrayIterator,RecursiveArrayIterator,SplFileInfo,DirectoryIterator,FilesystemIterator,RecursiveDirectoryIterator,GlobIterator,SplFileObject,SplTempFileObject,SplDoublyLinkedList,SplQueue,SplStack,SplHeap,SplMinHeap,SplMaxHeap,SplPriorityQueue,SplFixedArray,SplObjectStorage,MultipleIterator,SessionHandler,PDO,PDOStatement,PDORow,Pdo\Sqlite,__PHP_Incomplete_Class,RoundingMode,php_user_filter,StreamBucket,Directory,Random\Engine\Mt19937,Random\Engine\PcgOneseq128XslRr64,Random\Engine\Xoshiro256StarStar,Random\Engine\Secure,Random\Randomizer,Random\IntervalBoundary,Reflection,ReflectionFunctionAbstract,ReflectionFunction,ReflectionGenerator,ReflectionParameter,ReflectionType,ReflectionNamedType,ReflectionUnionType,ReflectionIntersectionType,ReflectionMethod,ReflectionClass,ReflectionObject,ReflectionProperty,ReflectionClassConstant,ReflectionExtension,ReflectionZendExtension,ReflectionReference,ReflectionAttribute,ReflectionEnum,ReflectionEnumUnitCase,ReflectionEnumBackedCase,ReflectionFiber,ReflectionConstant,PropertyHookType,Phar,PharData,PharFileInfo,SimpleXMLElement,SimpleXMLIterator,PhpToken,XMLParser
disable_functions = iconv,pcntl_wait,curl_close,curl_init,proc_get_status,curl_strerror,ini_restore,curl_share_setopt,curl_escape,socket_listen,gethostbynamel,syslog,pcntl_wifexited,socket_connect,socket_send,curl_reset,pcntl_wstopsig,socket_create,pcntl_sigprocmask,gc_collect_cycles,pcntl_signal_dispatch,imap_open,curl_unescape,proc_open,fsockopen,popen,debug_print_backtrace,curl_getinfo,curl_pause,error_reporting,pcntl_alarm,curl_errno,glob,pcntl_signal_get_handler,system,socket_recv,rmdir,socket_close,stream_socket_client,getmxrr,apache_setenv,curl_multi_setopt,stream_socket_enable_crypto,pcntl_wifstopped,posix_kill,socket_create_listen,stream_socket_server,pcntl_wexitstatus,curl_multi_errno,curl_share_close,curl_multi_getcontent,curl_multi_close,mail,curl_multi_add_handle,proc_terminate,pcntl_getpriority,pcntl_waitpid,pcntl_signal,shell_exec,curl_multi_remove_handle,socket_sendto,pcntl_async_signals,set_include_path,pcntl_wifsignaled,linkinfo,link,curl_exec,stream_socket_pair,passthru,socket_accept,error_log,readlink,pcntl_wtermsig,debug_backtrace,spl_autoload_register,stream_socket_accept,curl_multi_exec,curl_multi_init,gethostbyname,unlink,symlink,socket_recvfrom,putenv,socket_bind,curl_upkeep,socket_shutdown,socket_create_pair,ini_alter,dl,proc_nice,curl_copy_handle,gethostbyaddr,curl_setopt_array,imap_mail,curl_error,curl_setopt,curl_multi_strerror,dns_get_record,pcntl_get_last_error,stream_socket_sendto,pcntl_setpriority,pfsockopen,pcntl_sigwaitinfo,curl_share_init,array_merge_recursive,proc_close,exec,curl_file_create,pcntl_sigtimedwait,socket_write,pcntl_wifcontinued,mb_send_mail,rename,curl_multi_info_read,copy,pcntl_fork,curl_share_errno,socket_read,ini_set,chdir,curl_version,chroot,pcntl_strerror,checkdnsrr,curl_multi_select,curl_share_strerror,pcntl_exec
EOF

RUN cat > /etc/php/8.4/fpm/pool.d/www.conf <<'EOF'
[www]
user = www-data
group = www-data
listen = /run/php/php-fpm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
clear_env = yes
chdir = /var/www/html
EOF

# Internet legacies demand extraordinary protection!
RUN echo '<?php if(!function_exists("ini_set")) { function ini_set($a, $b) {}; } ?>' > /tmp/preload.php
RUN echo '\nphp_admin_value[auto_prepend_file] = /tmp/preload.php\n' >> /etc/php/8.4/fpm/pool.d/www.conf

RUN useradd -Ms /bin/bash app

# We're moving towards modernization absolutely :)
RUN set -e; \
    TAG=v0.12.0; \
    arch=amd64; \
    name=go-drive_linux_${arch}; \
    file=/tmp/${name}.tar.gz; \
    url=https://github.com/devld/go-drive/releases/download/${TAG}/${name}.tar.gz; \
    echo downloading ${url} ; \
    mkdir /app; cd /app; \
    curl -sL -o ${file} ${url} && \
    tar xf ${file} && \
    rm ${file} && \
    mv ${name}/* . && \
    rmdir ${name} && \
    mv go-drive /usr/sbin && \
    mkdir data && \
    chown -R root:app . && \
    find . -type d -exec chmod 1775 {} + && \
    find . -type f -exec chmod 0664 {} + && \
    sed 's/data-dir: .\//data-dir: \/app\/data/; s/web-dir: .\/web/web-dir: \/app\/web/; s/lang-dir: .\/lang/lang-dir: \/app\/lang/; s/api-path: ""/api-path: "\/new"/; s/web-path: ""/web-path: "\/new"/' -i config.yml

RUN mkdir -p /app/data/local/test
RUN echo hello > /app/data/local/test/hello.txt
RUN mkdir -p /app/data/local/test/【18+】禁断の氟拉格~被还原前的最后一分钟
RUN ln -s /root/flag /app/data/local/test/【18+】禁断の氟拉格~被还原前的最后一分钟/f13g

# Keep some backward-compatibility as best as we could :)
RUN curl -fsSL https://raw.githubusercontent.com/rocksclusters/roll-server/master/index.cgi -o /app/data/local/test/index.cgi && \
    sed -i "/^try:/,/^\tpass/c\\dir = '/app/data/local/test'" /app/data/local/test/index.cgi && \
    sed -i -E "1s|.*|#!/usr/bin/env python3|; s|out \\+= '<body>'|out += '<head><base href=\"/ancient/\"></head>'\\nout += '<body>'|; s/^print 'Content-length: %d' % \\(len\\(out\\)\\)$/print('Content-length: %d' % (len(out)))/; s/^print '([^']*)'$/print('\\1')/; s/^print out$/print(out)/" /app/data/local/test/index.cgi && \
    chown root:root /app/data/local/test/index.cgi && \
    chmod 0755 /app/data/local/test/index.cgi

RUN cat > /usr/local/bin/go-drive-bootstrap.sh <<'EOF'
#!/bin/bash
set -euo pipefail

CFG=/app/config.yml
DB=/app/data/data.db
BOOT_LOG=/tmp/go-drive-bootstrap.log

cleanup_bootstrap() {
    if [ -n "${BOOT_PID:-}" ] && kill -0 "${BOOT_PID}" 2>/dev/null; then
        kill "${BOOT_PID}" 2>/dev/null || true
        wait "${BOOT_PID}" 2>/dev/null || true
    fi
}

db_ready() {
    [ -f "${DB}" ] && \
    [ "$(sqlite3 "${DB}" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='drives';" 2>/dev/null || echo 0)" = "1" ]
}

if ! db_ready; then
    /usr/sbin/go-drive -c "${CFG}" >"${BOOT_LOG}" 2>&1 &
    BOOT_PID=$!
    trap cleanup_bootstrap EXIT

    for _ in $(seq 1 100); do
        if db_ready; then
            break
        fi

        if ! kill -0 "${BOOT_PID}" 2>/dev/null; then
            wait "${BOOT_PID}" || true
            cat "${BOOT_LOG}" >&2 || true
            exit 1
        fi

        sleep 0.2
    done

    if ! db_ready; then
        cat "${BOOT_LOG}" >&2 || true
        exit 1
    fi

    cleanup_bootstrap
    trap - EXIT
fi

sqlite3 "${DB}" <<'SQL'
INSERT INTO drives(name, enabled, type, config)
SELECT 'test', 1, 'fs', '{"path":"test"}'
WHERE NOT EXISTS (
    SELECT 1 FROM drives WHERE name = 'test'
);
SQL

exec /usr/sbin/go-drive -c "${CFG}"
EOF

RUN chmod +x /usr/local/bin/go-drive-bootstrap.sh

RUN cat > /etc/supervisor/conf.d/services.conf <<'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/tmp/supervisord.log
pidfile=/run/supervisord.pid

[program:php-fpm]
command=/usr/local/bin/no_priv /bin/sh -lc 'install -d -m 0755 -o www-data -g www-data /run/php && rm -f /run/php/php-fpm.sock && exec /usr/sbin/php-fpm8.4 -F'
priority=10
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:ancient]
command=/bin/sh -lc 'install -d -m 0755 /run/apache2 && rm -f /run/apache2/ancient.sock && exec spawn-fcgi -n -s /run/apache2/ancient.sock -M 0660 -G www-data -- /bin/su -s /bin/sh www-data -c "exec /usr/sbin/fcgiwrap"'
priority=15
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:apache2]
command=/bin/sh -lc 'install -d -m 0755 /var/run/apache2 /var/lock/apache2 && exec /usr/sbin/apache2ctl -D FOREGROUND'
priority=20
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:go-drive]
command=/usr/local/bin/no_priv /usr/local/bin/go-drive-bootstrap.sh
directory=/app
user=app
priority=30
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

[program:cron]
command=/usr/sbin/cron -f
priority=40
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
EOF

# Just in case... that your 0day shall best not work.
RUN cat > /usr/local/bin/no_priv.c <<'EOF'
#define _GNU_SOURCE
#include <errno.h>
#include <stddef.h>
#include <unistd.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>

#define DENY(x) (SECCOMP_RET_ERRNO | ((x) & SECCOMP_RET_DATA))
#define X32_SYSCALL_BIT 0x40000000U

int main(int argc, char **argv) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JSET | BPF_K, X32_SYSCALL_BIT, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 512, 0, 2),
        BPF_JUMP(BPF_JMP | BPF_JGT | BPF_K, 547, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_io_uring_setup, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_io_uring_enter, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_io_uring_register, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_link, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_linkat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_symlink, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_symlinkat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, DENY(EACCES)),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = { sizeof(filter) / sizeof(filter[0]), filter };
    if (argc < 2) return 127;
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) return 126;
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)) return 126;
    execvp(argv[1], argv + 1);
    return 127;
}
EOF
RUN gcc -O2 -Wall -Wextra -o /usr/local/bin/no_priv /usr/local/bin/no_priv.c && \
    rm /usr/local/bin/no_priv.c

RUN cat > /box.c <<'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <pwd.h>
#include <limits.h>
#include <errno.h>
#include <stdlib.h>
#include <dirent.h>

static const char *bn(const char *p){ const char *q=strrchr(p,'/'); return q&&q[1]?q+1:p; }
static int wr(int fd,const char *b,size_t n){ ssize_t r; while(n){ r=write(fd,b,n); if(r<=0) return -1; b+=r; n-=r; } return 0; }
static int reg(int fd,int root){ struct stat st; return fstat(fd,&st)||!S_ISREG(st.st_mode)||(root&&st.st_uid)?(errno=EPERM,-1):0; }
static int ch(int fd,uid_t u,gid_t g,mode_t m){ return fchown(fd,u,g)||fchmod(fd,m)?-1:0; }
static int home(const char *h,const char *p){ size_t n=strlen(h); return !strncmp(h,p,n)&&(p[n]=='/'||!p[n]); }
static int ok(const char *p){
    const char *s=bn(p); size_t i=0;
    if(!*s||!strcmp(s,".")||!strcmp(s,"..")||!strcmp(s,"secrets")||!strcmp(s,"disabled")) return 0;
    for(;s[i];i++){ unsigned char c=s[i]; if(i>=64) return 0;
        if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='.'||c=='_'||c=='-')) return 0;
    } return 1;
}
static int ain(const char *h,const char *p,char *a){ return ok(p)&&realpath(p,a)&&home(h,a); }
static int aout(const char *h,const char *p,char *a){
    char d[PATH_MAX],t[PATH_MAX],*q; const char *b=bn(p);
    if(!ok(p)||strlen(p)>=sizeof d) return 0;
    strcpy(d,p); q=strrchr(d,'/'); if(q){ *q=0; if(!*d) strcpy(d,"/"); } else strcpy(d,".");
    return realpath(d,t)&&snprintf(a,PATH_MAX,"%s/%s",t,b)<PATH_MAX&&home(h,a);
}
static int udir(uid_t u,gid_t g){
    char n[64]; int r,d; struct stat st;
    snprintf(n,sizeof n,"%u-%u",(unsigned)u,(unsigned)g);
    if((r=open("/root",O_RDONLY|O_DIRECTORY))<0) return -1;
    d=openat(r,n,O_RDONLY|O_DIRECTORY);
    if(d<0&&errno==ENOENT){
        if(mkdirat(r,n,0700)<0&&errno!=EEXIST){ close(r); return -1; }
        d=openat(r,n,O_RDONLY|O_DIRECTORY);
    }
    close(r);
    if(d<0||fstat(d,&st)||!S_ISDIR(st.st_mode)||st.st_uid){ if(d>=0) close(d); errno=EPERM; return -1; }
    return d;
}
static int dis(int d){ struct stat st; return fstatat(d,"disabled",&st,AT_SYMLINK_NOFOLLOW)==0?1:errno==ENOENT?0:-1; }
static int rsec(int d,char *s,size_t n){
    int f=openat(d,"secrets",O_RDONLY),r;
    if(f<0) return errno==ENOENT?-1:-2;
    if(reg(f,1)<0){ close(f); return -2; }
    r=read(f,s,n-1); close(f); if(r<0) return -2;
    s[r]=0; while(r&&(s[r-1]=='\n'||s[r-1]=='\r')) s[--r]=0; return r;
}
static int wsec(int d,const char *s){
    int f=openat(d,"secrets",O_WRONLY|O_CREAT|O_TRUNC,0400);
    if(f<0||reg(f,0)<0||ch(f,0,0,0400)<0) return f>=0?close(f),1:1;
    if(wr(f,s,strlen(s))<0) return perror("write"),close(f),1;
    return close(f),0;
}
static int put1(int d,const char *src){
    char b[8192]; ssize_t r; int i,o; const char *n=bn(src);
    i=open(src,O_RDONLY);
    if(i<0||reg(i,0)<0) return perror(src),i>=0?close(i),1:1;
    o=openat(d,n,O_WRONLY|O_CREAT|O_TRUNC,0400);
    if(o<0||reg(o,0)<0||ch(o,0,0,0400)<0) return perror(n),close(i),o>=0?close(o),1:1;
    while((r=read(i,b,sizeof b))>0) if(wr(o,b,r)<0) return perror("write"),close(i),close(o),1;
    if(r<0) perror("read");
    close(i); close(o); return r<0;
}
static int get1(int d,uid_t u,gid_t g,const char *dst){
    char b[8192]; ssize_t r; int i,o; const char *n=bn(dst); struct stat st;
    i=openat(d,n,O_RDONLY);
    if(i<0||reg(i,1)<0) return perror(n),i>=0?close(i),1:1;
    if(!lstat(dst,&st)){ if(!S_ISREG(st.st_mode)) return fprintf(stderr,"bad path: %s\n",dst),close(i),1; unlink(dst); }
    o=open(dst,O_WRONLY|O_CREAT|O_EXCL,0600);
    if(o<0||reg(o,0)<0||ch(o,u,g,0600)<0) return perror(dst),close(i),o>=0?close(o),1:1;
    while((r=read(i,b,sizeof b))>0) if(wr(o,b,r)<0) return perror("write"),close(i),close(o),1;
    if(r<0) perror("read");
    close(i); close(o); return r<0;
}
static int list1(int d){
    DIR *p; struct dirent *e; int x=0,fd=dup(d);
    if(fd<0||(p=fdopendir(fd))==NULL) return fd>=0?close(fd),1:1;
    while((e=readdir(p))) if(strcmp(e->d_name,".")&&strcmp(e->d_name,"..")&&strcmp(e->d_name,"secrets")&&strcmp(e->d_name,"disabled")) puts(e->d_name),x=1;
    closedir(p); return 0;
}
static const char *cursec(void){
    const char *s = getenv("APP_SECRET");
    return (s && *s) ? s : NULL;
}

int main(int c,char **v){
    struct passwd *pw; uid_t u=getuid(); gid_t g=getgid(); int d,i,r=0,x; char h[PATH_MAX],p[PATH_MAX],sec[4096]; const char *es;
    if(geteuid()!=0) return fprintf(stderr,"need suid-root\n"),1;
    if(u>1000) return fprintf(stderr,"forbidden\n"),1;
    if(!(pw=getpwuid(u))||!pw->pw_dir||!realpath(pw->pw_dir,h)) return fprintf(stderr,"no home\n"),1;
    if(c<2) return fprintf(stderr,"use: %s put <files...> | get <paths...> | list | secret <new|->\n",v[0]),1;
    if((d=udir(u,g))<0) return perror("userdir"),1;
    x=dis(d); if(x<0) return perror("disabled"),close(d),1;
    if(x) return fprintf(stderr,"disabled\n"),close(d),1;
    x=rsec(d,sec,sizeof sec); if(x==-2) return perror("secrets"),close(d),1;
    if(x>=0){ es=cursec(); if(!es || strcmp(sec,es)) return fprintf(stderr,"bad secret\n"),close(d),1;}

    if(!strcmp(v[1],"put")){
        if(c<3) r=1;
        else for(i=2;i<c;i++) if(!ain(h,v[i],p)) fprintf(stderr,"bad path: %s\n",v[i]),r=1; else r|=put1(d,p);
    }else if(!strcmp(v[1],"get")){
        i=2;
        if(i>=c) r=1; else for(;i<c;i++) if(!aout(h,v[i],p)) fprintf(stderr,"bad path: %s\n",v[i]),r=1; else r|=get1(d,u,g,p);
    }else if(!strcmp(v[1],"list")){
        r=list1(d);
    }else if(!strcmp(v[1],"secret")){
        if(c!=3) r=1;
        else if(!strcmp(v[2],"-")){ if(unlinkat(d,"secrets",0)<0&&errno!=ENOENT) perror("secrets"),r=1; }
        else r=wsec(d,v[2]);
    }else r=1;

    close(d);
    return r;
}
EOF

RUN gcc -O2 -o /box /box.c && \
    rm /box.c && \
    chown root:root /box && \
    chmod 6755 /box && \
    mv /box /usr/sbin/StorageBox

RUN cat > /etc/cron.d/backup <<'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

*/5 * * * * root APP_SECRET="$(cat /run/secrets/www)" exec su -s /bin/bash -p www-data -c 'StorageBox put /var/www/html/db.sqlite'
EOF
RUN chown root:root /etc/cron.d/backup && chmod 0600 /etc/cron.d/backup

RUN cat > /start.sh <<'EOF'
#!/bin/bash
rm -f /start.sh

echo "flag{dummy}" > /root/flag
# Protect our precious flag from any unauthorized access
StorageBox put /root/flag
rm -f /root/flag
unset FLAG

install -d -m 0700 -o root -g root /run/secrets
head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n' > /run/secrets/www
head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n' > /run/secrets/root
chown -R root:root /run/secrets; chmod -R 0600 /run/secrets

su -s /bin/bash -p www-data -c "StorageBox secret '$(cat /run/secrets/www)'"
StorageBox secret "$(cat /run/secrets/root)"

exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/services.conf
EOF

CMD ["bash", "/start.sh"]
EXPOSE 80
