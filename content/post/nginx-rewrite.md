---
title: "Nginx URL Rewrite"
date: 2019-07-07T18:27:56+08:00
draft: false
tags: ['nginx']
categories: ['瞎折腾']
---
总结下nginx的重写规则用法。
<!--more-->
url重写是指通过配置conf文件，以让网站的url中达到某种状态时则定向/跳转到某个规则，比如常见的伪静态、301重定向、浏览器定向等。

conf配置文件的路径可以通过命令来查看
```bash
[root@VM_100_94_centos ~]# nginx -t
nginx: the configuration file /www/server/nginx/conf/nginx.conf syntax is ok
nginx: configuration file /www/server/nginx/conf/nginx.conf test is successful
```
但是如果你有多个conf文件，这个命令并不适用。

在宝塔面板中conf是在`/www/server/panel/vhost/nginx`路径下。
## rewrite
```bash
server {
    rewrite 规则 定向路径 重写类型;
}
```
1. 规则：可以是字符串或者正则来表示想匹配的目标url
2. 定向路径：表示匹配到规则后要定向的路径，如果规则里有正则，则可以使用$index来表示正则里的捕获分组
3. 重写类型：
    - last：相当于Apache里德(L)标记，表示完成rewrite，浏览器地址栏URL地址不变
    - break：本条规则匹配完成后，终止匹配，不再匹配后面的规则，浏览器地址栏URL地址不变
    - redirect：返回302临时重定向，浏览器地址会显示跳转后的URL地址
    - permanent：返回301永久重定向，浏览器地址栏会显示跳转后的URL地址

看一个例子
```bash
server {
    # 访问 /last.html 的时候，页面内容重写到 /index.html 中
    rewrite /last.html /index.html last;
    # 访问 /break.html 的时候，页面内容重写到 /index.html 中，并停止后续的匹配
    rewrite /break.html /index.html break;
    # 访问 /redirect.html 的时候，页面直接302定向到 /index.html中
    rewrite /redirect.html /index.html redirect;
    # 访问 /permanent.html 的时候，页面直接301定向到 /index.html中
    rewrite /permanent.html /index.html permanent;
    # 把 /html/*.html => /post/*.html ，301定向
    rewrite ^/html/(.+?).html$ /post/$1.html permanent;
    # 把 /search/key => /search.html?keyword=key
    rewrite ^/search\/([^\/]+?)(\/|$) /search.html?keyword=$1 permanent;
}
```

last和break的区别
因为301和302不能简单的只返回状态码，还必须有重定向的URL，这就是return指令无法返回301,302的原因了。这里 last 和 break 区别有点难以理解：

+ last一般写在server和if中，而break一般使用在location中
+ last不终止重写后的url匹配，即新的url会再从server走一遍匹配流程，而break终止重写后的匹配
+ break和last都能组织继续执行后面的rewrite指令

在`location`里一旦返回`break`则直接生效并**停止后续的匹配**`location`

```bash
server {
    location / {
        rewrite /last/ /q.html last;
        rewrite /break/ /q.html break;
    }
    location = /q.html {
        return 400;
    }
}
```
- 访问/last/时重写到/q.html，然后使用新的uri再匹配，正好匹配到locatoin = /q.html然后返回了400
- 访问/break时重写到/q.html，由于返回了break，则直接停止了

## if判断
只是上面的简单重写很多时候满足不了需求，比如需要判断当文件不存在时、当路径包含xx时等条件，则需要用到if
当表达式只是一个变量时，如果值为空或任何以0开头的字符串都会当做false
直接比较变量和内容时，使用=或!=
~正则表达式匹配，~*不区分大小写的匹配，!~区分大小写的不匹配
一些内置的条件判断：

- -f和!-f用来判断是否存在文件
- -d和!-d用来判断是否存在目录
- -e和!-e用来判断是否存在文件或目录
- -x和!-x用来判断文件是否可执行

内置的全局变量
```bash
$args ：这个变量等于请求行中的参数，同$query_string
$content_length ： 请求头中的Content-length字段。
$content_type ： 请求头中的Content-Type字段。
$document_root ： 当前请求在root指令中指定的值。
$host ： 请求主机头字段，否则为服务器名称。
$http_user_agent ： 客户端agent信息
$http_cookie ： 客户端cookie信息
$limit_rate ： 这个变量可以限制连接速率。
$request_method ： 客户端请求的动作，通常为GET或POST。
$remote_addr ： 客户端的IP地址。
$remote_port ： 客户端的端口。
$remote_user ： 已经经过Auth Basic Module验证的用户名。
$request_filename ： 当前请求的文件路径，由root或alias指令与URI请求生成。
$scheme ： HTTP方法（如http，https）。
$server_protocol ： 请求使用的协议，通常是HTTP/1.0或HTTP/1.1。
$server_addr ： 服务器地址，在完成一次系统调用后可以确定这个值。
$server_name ： 服务器名称。
$server_port ： 请求到达服务器的端口号。
$request_uri ： 包含请求参数的原始URI，不包含主机名，如：”/foo/bar.php?arg=baz”。
$uri ： 不带请求参数的当前URI，$uri不包含主机名，如”/foo/bar.html”。
$document_uri ： 与$uri相同。
```

举个例子
```shell
# 如果文件不存在则返回400
if (!-f $request_filename) {
    return 400;
}
# 如果host不是example.com，则301到example.com中
if ( $host != 'example.com' ){
    rewrite ^/(.*)$ https://example.com/$1 permanent;
}
# 如果请求类型不是POST则返回405
if ($request_method = POST) {
    return 405;
}
# 如果参数中有 a=1 则301到指定域名
if ($args ~ a=1) {
    rewrite ^ http://example.com/ permanent;
}
```
## location

在server块中使用，如：
```shell
server {
    location 表达式 {
    }
}
```
location表达式类型

- 如果直接写一个路径，则匹配该路径下的
- ~ 表示执行一个正则匹配，区分大小写
- ~* 表示执行一个正则匹配，不区分大小写
- ^~ 表示普通字符匹配。使用前缀匹配。如果匹配成功，则不再匹配其他location。
- = 进行普通字符精确匹配。也就是完全匹配。
优先级
1. 等号类型（=）的优先级最高。一旦匹配成功，则不再查找其他匹配项。
2. ^~类型表达式。一旦匹配成功，则不再查找其他匹配项。
3. 正则表达式类型（~ ~*）的优先级次之。如果有多个location的正则能匹配的话，则使用正则表达式最长的那个。
4. 常规字符串匹配类型。按前缀匹配。

例子 - 假地址掩饰真地址
```shell
server {
    # 用 test_admin 来掩饰 admin
    location / {
        # 使用break拿一旦匹配成功则忽略后续location
        rewrite /test_admin /admin break;
    }
    # 访问真实地址直接报没权限
    location /admin {
        return 403;
    }
}
```
## 实际应用
在上篇文章中auxpi图床直接访问是本地的图床，而且在后台即使关闭本地图床，也仍然会显示在首页，用户直接上传会报错，那么我们要做的就是让访问的时候跳转到别的图床。

要求

- 直接访问 https://static.chabug.org/ 跳转到 https://static.chabug.org/Ali
- 别的url例如https://static.chabug.org/Jd 不跳转
- 不能更改网页的其他url地址。

直接放上我的配置文件
```bash
server
{
    listen 80;
    listen 443 ssl http2;
    server_name static.chabug.org;
    index index.php index.html index.htm default.php default.htm default.html;
    root /www/wwwroot/static.chabug.org;
    rewrite "^/$" https://static.chabug.org/Ali break;
    #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
    #error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END
    ssl_certificate    /www/server/panel/vhost/cert/static.chabug.org/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/static.chabug.org/privkey.pem;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    error_page 497  https://$host$request_uri;

    #SSL-END
    
    #ERROR-PAGE-START  错误页配置，可以注释、删除或修改
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END
    
    #PHP-INFO-START  PHP引用配置，可以注释或修改
    #清理缓存规则
    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/static.chabug.org_purge_cache.log;
    }
	#引用反向代理规则，注释后配置的反向代理将无效
	include /www/server/panel/vhost/nginx/proxy/static.chabug.org/*.conf;

	#include enable-php-00.conf;
    #PHP-INFO-END
    
    #REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效
    #include /www/server/panel/vhost/rewrite/static.chabug.org.conf;
    #REWRITE-END
    
    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }
    
    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }
    
    access_log  /www/wwwlogs/static.chabug.org.log;
    error_log  /www/wwwlogs/static.chabug.org.error.log;
}
```
重点就在于`rewrite "^/$" https://static.chabug.org/Ali break;` break的使用

本文参考链接:

- [使用宝塔进行安装auxpi图床](https://github.com/aimerforreimu/auxpi/wiki/%E4%BD%BF%E7%94%A8%E5%AE%9D%E5%A1%94%E8%BF%9B%E8%A1%8C%E5%AE%89%E8%A3%85)
- http://www.linuxeye.com/configuration/2657.html
- http://seanlook.com/2015/05/17/nginx-location-rewrite/