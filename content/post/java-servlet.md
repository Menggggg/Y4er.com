---
title: "Java Web之Servlet"
date: 2018-12-16T14:31:11+08:00
categories: ['代码审计']
tags: ['Java','web']
---

两周的Java实训结束了，学了一个`servlet`做接口，给前端提供数据支持，记下笔记，免得以后忘了。

<!--more-->

## Java知识

1. 标识符 关键字
2. 变量 数据类型
3. 运算符
4. 控制流程
5. 面向对象

标识符是自己能够定义的东西，关键字是系统定义好的东西。

变量是存放数据的容器，数据类型有基本数据类型和引用数据类型

基本数据类型如下：

![基本数据类型](https://y4er.com/img/uploads/20190509166803.jpg "基本数据类型")

引用数据类型：

类、接口类型、数组类型、枚举类型、注解类型。

运算符：

算术、赋值、关系、逻辑、位、三目运算符

控制流程：

顺序、选择、循环

面向对象：

封装、继承、多态

## MySQL回顾

MySQL是一个关系型的数据库，一个MySQL可以有多个库，库中可以有多个表，表中可以有多个字段。如下图：

![数据库结构](https://y4er.com/img/uploads/20190509160082.jpg "数据库结构")

![数据表结构](https://y4er.com/img/uploads/20190509160217.jpg "数据表结构")

记录下MySQL的一些命令：

![基本命令](https://y4er.com/img/uploads/20190509160771.jpg "基本命令")

![基本命令](https://y4er.com/img/uploads/20190509167263.jpg "基本命令")

![基本命令](https://y4er.com/img/uploads/20190509165130.jpg "基本命令")

那么Java怎么去链接数据库呢?

## JDBC建立数据库链接

![](https://y4er.com/img/uploads/20190509160694.jpg)

那么JDBC的增删改查如何进行?

![JDBC查询](https://y4er.com/img/uploads/20190509165760.jpg "查询")

![JDBC增加](https://y4er.com/img/uploads/20190509161480.jpg "增加")

在进行`select`查询的时候返回的是一个`ResultSet`结果集，其他的`insert`、`update`、`delete`语句返回的就是影响的行数（`int`）

在建立数据库链接之后我们来了解下tomcat这个web应用服务器
## tomcat
![tomcat](https://y4er.com/img/uploads/20190509166994.jpg "tomcat")
其中的s1、s2就是一个一个的web应用，在我们实训中用到的就是servlet了

tomcat的目录结构如下图：
![tomcat目录结构](https://y4er.com/img/uploads/20190509160628.jpg "tomcat目录结构")

了解完我们服务端的tomcat之后，我们需要去了解客户端和服务端之间的通信
## 客服？
客户端：和用户交互的那端，即PC端
服务端：和服务器、数据库等进行交互的那端，给前端提供数据支持

在B/S架构中 Browser就是我们的客户端
Browser/server

而在C/S架构 Client就是客户端
Client/server

那么B/S和C/S架构的区别就在于客户所使用的请求方式，举个简单的例子：
网页版的微信就是B/S架构
而手机APP的微信就是C/S架构
一个是通过浏览器发起请求，而另一个是通过APP发起请求。

那么我们实训中用到的就是B/S架构的方式，我们用一张图来理解：
![B/S架构](https://y4er.com/img/uploads/20190509167356.jpg "B/S架构")
简单的解释下，客户端发起请求`request`，这个请求可能会有参数、cookie等，服务端接受到请求之后去处理，到数据库中拿到数据，然后返回给客户端一个`response`

那么这就是一个简单的客户端和服务端的请求过程。
因为我们实训写的是一个接口，给前端提供数据支持，所以说我们需要了解一下json和xml
## Json or Xml
json是一种数据交换格式，易于人阅读，易于机器去解析拿到数据。xml类似。
那么我们来看下两种格式的结构
![json](https://y4er.com/img/uploads/20190509162321.jpg "json")
![xml](https://y4er.com/img/uploads/20190509168926.jpg "xml")

xml相对臃肿，而在web开发中，流量就是钱，很多人为了几K的流量头疼不已，所以我们选择更为轻量的json。
那么数据转为json的方案有很多，我们选择了谷歌的jar包`Gson.toJson()`
介绍完这些之后，我们来把所有的部分揉合到一起。
## 微票
![微票](https://y4er.com/img/uploads/20190509161847.jpg "微票的项目结构")
这是整个项目结构
五个`package`，其中bean、servlet、biz对应的就是web开发中常见的mvc结构的模型、视图、控制器，而dao是真正的一个数据交互层，util则是为了减少代码量，拿出来了数据库打开关闭的部分。
## 豆瓣电影
豆瓣电影和微票原理结构一样，区别就在于我们把数据库配置单独拿了出来写成了`PropertiesUtil`类
![PropertiesUtil](https://y4er.com/img/uploads/20190509166075.jpg "PropertiesUtil")
![jdbc.properties](https://y4er.com/img/uploads/20190509169853.jpg "jdbc.properties")

## 后记
两周Java实训收获颇多，当然最重要的是学到了web开发的一个设计思想和设计模式。比如mvc、分层还有就是代码的解耦和。对于一个开发新人来说，算是树立了一个开发基础思想。也感谢我们的实训老师 - 铁雪亮老师。