---
title: "Python保存图床图片到本地"
date: 2019-05-09T17:34:21+08:00
draft: false
tags: ['图床','python']
categories: ['代码片段']
---

新浪图床挂了之后我的博客图片挂了一大堆，今天写了个脚本来解决下。

<!--more-->

```python
import requests
import re
import os
from datetime import datetime

COUNT = 0


def getimg(post, rule):
    with open(post, 'r', encoding='utf-8') as f:
        content = f.read()
        imgs = re.findall(rule, content)
        for markdown, img in imgs:
            r = requests.get(img).content
            filename = 'img/uploads/' + now() + '.jpg'
            with open(filename, 'wb+')as file:
                file.write(r)
                global COUNT
                COUNT += 1
                print(filename, img)
            markdown_str = markdown
            markdown = markdown.replace(img, 'https://y4er.com/' + filename)
            content = content.replace(markdown_str, markdown)
        with open(post, 'w', encoding='utf-8')as mark:
            mark.write(content)
            print(post + " over! replace "+str(COUNT)+"张!")
    return 0


def now():
    return str(datetime.now().strftime("%Y%m%d%H") + str(datetime.now().microsecond)[-4:])


if __name__ == '__main__':
    weibo = r'(!.*(https://.*sinaimg.*.jpg).*\))'
    smms = r'(!.*(https://.*loli.net.*.png).*\))'
    for post in os.listdir():
        if post[-2:] == 'md':
            with open(post, 'r', encoding='utf-8')as f:
                text = f.read()
                if 'sinaimg' in text:
                    getimg(post, weibo)
                elif 'loli.net' in text:
                    getimg(post, smms)
                else:
                    print(post+"没有图片")
```

