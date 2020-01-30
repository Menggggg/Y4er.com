---
title: "如何禁止PHP脚本跨站跨目录"
date: 2019-03-29T15:53:11+08:00
draft: false
tags: ['php']
categories: ['渗透测试']
---
昨天晚上一位朋友问到这个东西，就顺手查了下资料，这是笔记。

<!--more-->

## 前言

在一些渗透测试遇到的环境中，有的时候我们会发现shell所能访问的目录非常有限，可能只有当前网站的一个根路径，当我们需要从旁站拿目标站点的shell时往往被局限于此。这篇文章就是研究下php的防跨站跨目录的一个安全配置。

现在网络上大部分php的环境是lamp或者lnmp，那么防止跨站跨目录的方式大致分为两类：中间件的配置、php.ini的配置。本文将对这两种方法来进行讲解。

## 中间件

我们首先先从中间件的层面来看这个问题。

### apache

阿帕奇是比较成熟的中间件，我们可以通过修改apache安装目录下的`vhost.conf`来达到防止跨站跨目录的目的。在网站配置中加入以下代码

```
<VirtualHost *:80>
php_admin_value open_basedir "/www/wwwroot/:/tmp/:/proc/"
</VirtualHost>
```

需要把`/www/wwwroot/`改为你网站所在目录的绝对路径。

**值得注意的是如果使用这种方式，那么虚拟用户就不再自动继承`php.ini`中的`open_basedir`值了，这样会失去灵活性。**

### nginx

nginx也可以通过修改配置文件来达到防跨站跨目录的效果。

```ini
fastcgi_param  PHP_VALUE  "open_basedir=$document_root:/tmp/:/proc/";
```

通常nginx的站点配置文件里用了`include fastcgi.conf;`，我们可以把这行加在`fastcgi.conf`里就OK了。 
如果某个站点需要单独设置额外的目录，把上面的代码写在`include fastcgi.conf;`这行下面就OK了，会把`fastcgi.conf`中的设置覆盖掉。 
这种方式的设置需要重启nginx后生效。

## php.ini

实际上脱离中间件，我们完全可以通过php的配置文件来达到防跨站的效果。

在`php.ini`中修改`open_basedir`的值
```ini
open_basedir=/home/wwwroot/:/tmp/:/proc/
```

这样php只能访问到我们设置的目录。但是这种办法适用于你的网站根目录是/home/wwwroot，如果你的wwwroot目录下有多个网站并存，如下

| 域名  | 路径           |
| ----- | -------------- |
| a.com | /wwwroot/a.com |
| b.com | /wwwroot/b.com |

那么入侵者在拿下a.com的shell时仍然可以跨目录到b.com之下。怎么解决？

---

> 自 PHP 5.3.0 起，PHP 支持基于每个目录的 .htaccess 风格的 INI 文件。此类文件*仅*被 CGI／FastCGI SAPI 处理。此功能使得 PECL 的 htscanner 扩展作废。如果使用 Apache，则用 .htaccess 文件有同样效果。
>
> 除了主 php.ini 之外，PHP 还会在每个目录下扫描 INI 文件，从被执行的 PHP 文件所在目录开始一直上升到 web 根目录（[$_SERVER['DOCUMENT_ROOT']所指定的）。如果被执行的 PHP 文件在 web 根目录之外，则只扫描该目录。

也就是说我们可以通过`.user.ini`这种形式来对每一个网站甚至是每一个目录设置`open_basedir`属性值

首先修改`php.ini`，去掉`user_ini.filename`和`user_ini.cache_ttl`前面的分号。

```ini
;;;;;;;;;;;;;;;;;;;;
; php.ini Options  ;
;;;;;;;;;;;;;;;;;;;;
; Name for user-defined php.ini (.htaccess) files. Default is ".user.ini"
user_ini.filename = ".user.ini"

; To disable this feature set this option to empty value
;user_ini.filename =

; TTL for user-defined php.ini files (time-to-live) in seconds. Default is 300 seconds (5 minutes)
user_ini.cache_ttl = 300
```

在网站`a.com`根目录下创建`.user.ini`加入：

```ini
open_basedir=/home/wwwroot/a.com:/tmp/:/proc/
```

这样就可以确保每个网站的php文件只能访问`open_basedir`属性设置的目录范围了。

关于`.user.ini`文件的更多详细说明移步https://www.php.net/manual/zh/configuration.file.per-user.php

**特别注意，需要取消掉`.user.ini`文件的写权限，这个文件只让最高权限的管理员设置为只读。**

## 后记

通过学习apache、nginx和php的一些配置文件和属性来达到安全配置的目的，略有收获。推荐使用`.user.ini`来配置目录权限。