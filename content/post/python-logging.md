---
title: "Python模块学习之Logging日志模块"
date: 2019-01-13T12:17:40+08:00
tags: ['python','logging']
categories: ['代码片段']
---

最近一直想自己的批量框架，参考了POC-T框架和sqlmap的框架结构，发现logging模块被大量用来处理控制台输出以及日志记录，鉴于我自己也要写框架，那么本文就记录下我的logging模块学习记录。

<!--more-->

## 为什么需要logging

在开发过程中，如果程序出现了问题，我们可以使用编辑器的Debug模式来检查bug，但是在发布之后，我们的程序相当于在一个黑盒状态去运行，我们只能看到运行效果，可是程序难免出错，这种情况的话我们就需要日志模块来记录程序当前状态、时间状态、错误状态、标准输出等，这样不论是正常运行还是出现报错，都有记录，我们可以针对性的快速排查问题。

因此，日志记录对于程序的运行状态以及debug都起到了很高效的作用。如果一个程序没有标准的日志记录，就不能算作一个合格的开发者。

## logging和print的对比

- logging对输出进行了分级，print没有
- logging具有更灵活的格式化功能，比如运行时间、模块信息
- print输出都在控制台上，logging可以输出到任何位置，比如文件甚至是远程服务器

## logging的结构拆分

|      模块      |                             用途                             |
| :------------: | :----------------------------------------------------------: |
|     Logger     | 记录日志时创建的对象，调用其方法来传入日志模板和信息生成日志记录 |
|   Log Record   |                  Logger对象生成的一条条记录                  |
|    Handler     |              处理日志记录，输出或者存储日志记录              |
|   Formatter    |                        格式化日志记录                        |
|     Filter     |                          日志过滤器                          |
| Parent Handler |                   Handler之间存在分层关系                    |

## 简单的实例

```python
import logging

logger = logging.getLogger("Your Logger")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("this is info msg")
logger.debug("this is debug msg")
logger.warning("this is warn msg")
logger.error("this is error msg")
```

输出

```html
2019/01/13 13:21:17 - Your Logger - INFO - this is info msg
2019/01/13 13:21:17 - Your Logger - DEBUG - this is debug msg
2019/01/13 13:21:17 - Your Logger - WARNING - this is warn msg
2019/01/13 13:21:17 - Your Logger - ERROR - this is error msg
```



我们来理解下这个实例。

首先创建了一个`logger`对象作为生成日志记录的对象，然后设置输出级别为`DEBUG`，然后创建了一个`StreamHandler`对象`handler`，来处理日志，随后创建了一个`formatter`对象来格式化输出日志记录，然后把`formatter`赋给`handler`，最后把`handler`处理器添加到我们的`logger`对象中，完成了整个处理流程。

知道整个流程之后我们来看一些细的东西。

### Level

`logging`模块中自带了几个日志级别

|   等级   | 数值 |          对应方法          |
| :------: | :--: | :------------------------: |
| CRITICAL |  50  |   logger.critical("msg")   |
|  FATAL   |  50  |    logger.fatal("msg")     |
|  ERROR   |  40  |    logger.error("msg")     |
| WARNING  |  30  |   logger.warning("msg")    |
|   WARN   |  30  | ~~logger.warn("msg")~~废弃 |
|   INFO   |  20  |     logger.info("msg")     |
|  DEBUG   |  10  |    logger.debug("msg")     |
|  NOTSET  |  0   |             无             |

在我们的实例中我们设置了输出级别为`DEBUG`

```python
logger.setLevel(logging.DEBUG)
```

那么在`DEBUG`级别之下的也就是`NOTSET`级别的不会被输出。

如果我们把级别设置为`INFO`，那么我们实例的输出应该是

```python
2019/01/13 13:21:17 - Your Logger - INFO - this is info msg
2019/01/13 13:21:17 - Your Logger - WARNING - this is warn msg
2019/01/13 13:21:17 - Your Logger - ERROR - this is error msg
```

只会输出比INFO级别高的日志。

### Handler

logging提供的Handler有很多，我简单列举几种

|     种类      |              位置              | 用途                                                 |
| :-----------: | :----------------------------: | ---------------------------------------------------- |
| StreamHandler |     logging.StreamHandler      | 日志输出到流，可以是 sys.stderr，sys.stdout 或者文件 |
|  FileHandler  |      logging.FileHandler       | 日志输出到文件                                       |
|  SMTPHandler  |  logging.handlers.SMTPHandler  | 远程输出日志到邮件地址                               |
| SysLogHandler | logging.handlers.SysLogHandler | 日志输出到syslog                                     |
|  HTTPHandler  |  logging.handlers.HTTPHandler  | 通过”GET”或者”POST”远程输出到HTTP服务器              |

### Formatter

fmt参数和datefmt两个参数分别对应日志记录的格式化和时间的格式化。

fmt可用的占位符简单列举几种，更多请参考[这里](https://docs.python.org/3/library/logging.html?highlight=logging%20threadname#logrecord-attributes)

|     占位符      |                     作用                      |
| :-------------: | :-------------------------------------------: |
|  %(levelname)s  |              打印日志级别的名称               |
|  %(pathname)s   | 打印当前执行程序的路径，其实就是sys.argv[0]。 |
|  %(filename)s   |             打印当前执行程序名。              |
|  %(funcName)s   |             打印日志的当前函数。              |
|   %(lineno)d    |             打印日志的当前行号。              |
|   %(asctime)s   |               打印日志的时间。                |
|   %(thread)d    |                 打印线程ID。                  |
| %(threadName)s  |                打印线程名称。                 |
|   %(process)d   |                 打印进程ID。                  |
| %(processName)s |                打印线程名称。                 |
|   %(module)s    |                打印模块名称。                 |
|   %(message)s   |                打印日志信息。                 |

## 捕获Traceback

```python
try:
    result = 10 / 0
except Exception:
    logger.error('Faild to get result', exc_info=True)
    # 或者用下面这个
    # logging.exception('Error')
logger.info('Finished')
```

输出

```bash
2019/01/13 14:11:18 - Your Logger - ERROR - Faild to get result
Traceback (most recent call last):
  File "E:/Python/test.py", line 22, in <module>
    result = 10 / 0
ZeroDivisionError: division by zero
2019/01/13 14:11:18 - Your Logger - INFO - Finished
```

这样会更合理的捕获异常信息。

## 自定义日志级别

```python
import logging

INFO, WARN, ERROR, SUCCESS = range(1, 5)
# print(SYSINFO, WARN, ERROR, SUCCESS)
logging.addLevelName(INFO, '*')
logging.addLevelName(WARN, '!')
logging.addLevelName(ERROR, 'x')
logging.addLevelName(SUCCESS, '+')

logger = logging.getLogger('LOGGER')
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)

logger.log(INFO, "INFO")
logger.log(WARN, "WARN")
logger.log(ERROR, "ERROR")
logger.log(SUCCESS, "SUCCESS")
```

输出

```bash
2019/01/13 14:17:59 [*] INFO
2019/01/13 14:17:59 [!] WARN
2019/01/13 14:17:59 [x] ERROR
2019/01/13 14:17:59 [+] SUCCESS
```

先定义级别和数值，然后调用`addLevelName(级别名,'输出名')`。记得**数值不能小于等于0**，注意输出日志的级别。

## 给输出加上颜色

用到了一个第三方的脚本`ansistrm.py`，下载地址https://gist.github.com/Y4er/6300ccff3a6628ea7bda24e514013476 原作者脚本不支持win10，我修复了一下。

将这个脚本`ansistrm.py`和你的`log.py`放到同一目录，然后`log.py`如下内容

```python
#!/usr/bin/env python3 
# -*- coding: utf-8 -*- 
# @Time : 2019/1/12 21:01 
# @Author : Y4er 
# @Site : http://Y4er.com
# @File : log.py 


import logging

INFO, WARN, ERROR, SUCCESS = range(1, 5)
# print(SYSINFO, WARN, ERROR, SUCCESS)
logging.addLevelName(INFO, '*')
logging.addLevelName(WARN, '!')
logging.addLevelName(ERROR, 'x')
logging.addLevelName(SUCCESS, '+')

logger = logging.getLogger('YOUR LOGGER')
try:
    from ansistrm import ColorizingStreamHandler

    handle = ColorizingStreamHandler()
    handle.level_map[logging.getLevelName('*')] = (None, 'cyan', False)
    handle.level_map[logging.getLevelName('+')] = (None, 'green', False)
    handle.level_map[logging.getLevelName('x')] = (None, 'red', False)
    handle.level_map[logging.getLevelName('!')] = (None, 'yellow', False)
except Exception as e:
    print(e)
    handle = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - [%(levelname)s]  %(message)s', '%Y/%m/%d %H:%M:%S')
handle.setFormatter(formatter)
logger.addHandler(handle)
logger.setLevel(INFO)


class LOGGER:
    @staticmethod
    def info(msg):
        return logger.log(INFO, msg)

    @staticmethod
    def warning(msg):
        return logger.log(WARN, msg)

    @staticmethod
    def error(msg):
        return logger.log(ERROR, msg)

    @staticmethod
    def success(msg):
        return logger.log(SUCCESS, msg)


LOGGER.info("INFO msg")
LOGGER.warning("warning msg")
LOGGER.error("error msg")
LOGGER.success("success msg")
```

在这个脚本中，我写了一个类以及其下的四个静态方法，那么可以这么调用

```python
LOGGER.info("INFO msg")
LOGGER.warning("warning msg")
LOGGER.error("error msg")
LOGGER.success("success msg")
```

运行效果：

![](https://y4er.com/img/uploads/20190509162726.jpg)

## 写在文后

是时候抛弃`print`了！

参考链接

[Python中logging模块的基本用法 - 崔庆才老师](https://cuiqingcai.com/6080.html)

[原版ansistrm.py - vsajip](https://gist.github.com/vsajip/758430)

[修复ansistrm.py以支持win10](https://gist.github.com/vsajip/758430#gistcomment-2764744)