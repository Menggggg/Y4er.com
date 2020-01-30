---
title: "搞了一个图床"
date: 2019-07-07T17:31:13+08:00
draft: false
tags: ['图床']
categories: ['瞎折腾']
---

昨天把chabug弄炸了，然后图片有的也炸了...

<!--more-->

> 今天看到之前用的很多的图片都是新浪图床的链接，自从新浪加上防盗链之后，博客的图片挂了一大波，之前也写过脚本来处理([这篇文章](https://y4er.com/post/downimg2local/))，但是总不是很满意，因为图片现在是放到了GitHub，速度不行，然后在网上找了很多的图床，都不太稳，不然就是不太方便。然后我在GitHub上找到了一个好东西😁

## AUXPI

Github：[AUXPI 集合多家 API 的新一代图床](https://github.com/aimerforreimu/auxpi)

![](https://y4er.com/img/uploads/20190707173858.png)

## 功能特色

- 支持 web 上传图片
- 支持 API 上传图片
- 支持分发，控制反转

前台上传是不支持分发图片的。

后台中上传图片是支持分发的。

## 分发原理

![](https://y4er.com/img/uploads/20190707173944.png)

## 搭建好的成品

https://static.chabug.org

所有图片均存储在各大图床网站，**本地不存储任何图片。**

欢迎使用🙂

有上传API哦，自行挖掘利用🤭