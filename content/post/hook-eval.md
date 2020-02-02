---
title: "通过hook eval解密混淆的PHP文件"
date: 2020-02-02T21:11:52+08:00
draft: false
tags:
- PHP
- shell
series:
-
categories:
- 二进制
---

扒开加密shell的底裤。

<!--more-->

想找一款好用的大马，还得分析分析有没有后门，但很多大马都是加密的，于是想试试能不能解密这些鬼代码，遂有此文。

## PHP混淆原理
一般来讲，混淆分为两种
1. 利用拓展进行加密
2. 不需要拓展，单文件加密

本文主要针对第二种，而单文件加密的一般都是对源码进行字符串操作，比如对字符串移位、拼接，或者重新定义变量，重新赋值数组，总之就是尽可能减少程序可读性。但是所有加密过的代码都会经过多次eval来重新还原为php代码执行，所以我们可以hook PHP中的eval函数来输出经过eval函数的参数，参数就是源码。

## hook eval
PHP中的eval函数在Zend里需要调用zend_compile_string函数，我们写一个拓展直接hook这个函数就行了。不过我不会写c代码，所以参考网上的文章，在GitHub中找到了现成的一个拓展库。

https://github.com/bizonix/evalhook 需要编译，不过我在文末提供了编译好的so文件。

修改 evalhook.c 中这部分代码，否则只能在命令行中使用。

![image](https://y4er.com/img/uploads/20200202214739.png)

```c
static zend_op_array *evalhook_compile_string(zval *source_string, char *filename TSRMLS_DC)
{
        int c, len, yes;
        char *copy;

        /* Ignore non string eval() */
        if (Z_TYPE_P(source_string) != IS_STRING) {
                return orig_compile_string(source_string, filename TSRMLS_CC);
        }

        len  = Z_STRLEN_P(source_string);
        copy = estrndup(Z_STRVAL_P(source_string), len);
        if (len > strlen(copy)) {
                for (c=0; c<len; c++) if (copy[c] == 0) copy[c] == '?';
        }
        php_printf("\n--------- Decrypt start ------------\n");
        php_printf(copy);
        php_printf("\n--------- Decrypt done ------------\n");
        return orig_compile_string(source_string, filename TSRMLS_CC);

}
```
centos php5.6+apache 然后运行
```
yum install http://rpms.remirepo.net/enterprise/remi-release-7.rpm
yum install --enablerepo=remi --enablerepo=remi-php56 php-devel
phpize && ./configure && make
```
将 evalhook/modules/evalhook.so 拷贝到 php 的拓展目录下，并且向php.ini中添加

```
extension=evalhook.so
```

重新启动apache之后，可以通过web访问php文件，会直接打印出源码。

拿一个大马举例，没加拓展之前访问。

![image](https://y4er.com/img/uploads/20200202217147.png)

加了拓展之后

![image](https://y4er.com/img/uploads/20200202211173.png)

## 参考链接
[解密混淆的PHP程序](http://weaponx.site/2018/04/27/%E8%A7%A3%E5%AF%86%E6%B7%B7%E6%B7%86%E7%9A%84PHP%E7%A8%8B%E5%BA%8F/)
http://blog.evalbug.com/2017/09/21/phpdecode_01/
https://www.leavesongs.com/PENETRATION/unobfuscated-phpjiami.html
https://github.com/bizonix/evalhook
[放一个我基于PHP 5.6.40编译好的so文件](https://gitee.com/Y4er/static/raw/master/hook.so)

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**