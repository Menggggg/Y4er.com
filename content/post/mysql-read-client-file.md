---
title: "Mysql Read Client's File"
date: 2019-05-23T20:31:28+08:00
draft: false
tags: ['mysql']
categories: ['渗透测试']
---

连我MySQL拿你文件系列

<!--more-->

我们可以伪造一个 MySQL 的服务端，甚至不需要实现 MySQL 的任何功能（除了向客户端回复 greeting package），当有客户端连接上这个假服务端的时候，我们就可以任意读取客户端的一个文件，当然前提是运行客户端的用户具有读取该文件的权限。

这个问题主要是出在`LOAD DATA INFILE`这个语法上，这个语法主要是用于读取一个文件的内容并且放到一个表中。通常有两种用法，分别是：

```mysql
load data infile "/data/data.csv" into table TestTable;
load data local infile "/home/data.csv" into table TestTable;
```

一个是读服务器本地上的文件，另一个是读client客户端的文件。

我们这次要利用的也就是`LOAD DATA LOCAL INFILE`这种形式。

>  正如官方文档中提出的安全风险，"In theory, a patched server could be built that would tell the client program to transfer a file of the server's choosing rather than the file named by the client in the LOAD DATA statement."

可以看到，客户端读取哪个文件其实并不是自己说了算的，是服务端说了算的，形象一点的说就是下面这个样子：

- 客户端：hi~ 我将把我的 data.csv 文件给你插入到 test 表中！
- 服务端：OK，读取你本地 data.csv 文件并发给我！
- 客户端：这是文件内容：balabal！

正常情况下，这个流程不会有什么问题，但是如果我们制作了恶意的客户端，并且回复服务端任意一个我们想要获取的文件，那么情况就不一样了。

- 客户端：hi~ 我将把我的 data.csv 文件给你插入到 test 表中！
- 服务端：OK，读取你本地的 / etc/passwd 文件并发给我！
- 客户端：这是文件内容：balabal（/etc/passwd 文件的内容）！

以上摘取[lightless师傅](<https://lightless.me/archives/read-mysql-client-file.html>)，读取客户端任意文件的原理在师傅的文章中讲的很明白。

那么具体的利用你可以用<https://github.com/allyshka/Rogue-MySql-Server>工具，下面是演示视频。

<div class="bilibili" style="position: relative; padding-bottom: 56.25%; padding-top: 30px; height: 0; overflow: hidden;">
    <iframe src="//player.bilibili.com/player.html?aid=53371772" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>

对于这种攻击的防御，说起来比较简单，首先一点就是客户端要避免使用 LOCAL 来读取本地文件。但是这样并不能避免连接到恶意的服务器上，如果想规避这种情况，可以使用`--ssl-mode=VERIFY_IDENTITY`来建立可信的连接。

当然最靠谱的方式还是要从配置文件上根治，关于配置上的防御问题，可以参考[这篇文档](https://dev.mysql.com/doc/refman/8.0/en/load-data-local.html)进行设置。

参考文档

- https://lightless.me/archives/read-mysql-client-file.html

- https://xz.aliyun.com/t/3973