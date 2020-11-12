---
title: "Kerberos协议之AS_REQ & AS_REP"
date: 2020-11-12T11:34:09+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---

Kerberos是一种由MIT（麻省理工大学）提出的一种网络身份验证协议。
<!--more-->
# 简述Kerberos
Kerberos是一种由MIT（麻省理工大学）提出的一种网络身份验证协议。它旨在通过使用密钥加密技术为客户端/服务器应用程序提供强身份验证。

在Kerberos协议中主要是有三个角色的存在：

1. 访问服务的Client(以下表述为Client 或者用户)
2. 提供服务的Server(以下表述为服务)
3. KDC（Key Distribution Center）密钥分发中心 kerberos 测试工具介绍

其中KDC服务默认会安装在一个域的域控中，而Client和Server为域内的用户或者是服务，如HTTP服务，SQL服务。在Kerberos中Client是否有权限访问Server端的服务由KDC发放的票据来决定。

kerberos的简化认证认证过程如下图
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/4bd27682-030a-578e-0714-0fae3534032e.png)

1. AS_REQ: Client向KDC发起AS_REQ,请求凭据是Client hash加密的时间戳
2. AS_REP: KDC使用Client hash进行解密，如果结果正确就返回用krbtgt hash加密的TGT票据，TGT里面包含PAC,PAC包含Client的sid，Client所在的组。
3. TGS_REQ: Client凭借TGT票据向KDC发起针对特定服务的TGS_REQ请求
4. TGS_REP: KDC使用krbtgt hash进行解密，如果结果正确，就返回用服务hash 加密的TGS票据(这一步不管用户有没有访问服务的权限，只要TGT正确，就返回TGS票据)
5. AP_REQ: Client拿着TGS票据去请求服务
6. AP_REP: 服务使用自己的hash解密TGS票据。如果解密正确，就拿着PAC去KDC那边问Client有没有访问权限，域控解密PAC。获取Client的sid，以及所在的组，再根据该服务的ACL，判断Client是否有访问服务的权限。

本文注重前两个

# AS_REQ
用daiker师傅的工具来发Kerberos包。

配置域账户
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/1aff1f2f-2986-7d88-dd07-c3af837465cb.png)

勾上`PAPAC_REQUEST`、`ENCTIMESTAMP`、`etypes`里的`rc4hmac`加密。发包

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f6f6700c-dbbe-4ecd-2ccf-3e3c770452ff.png)

抓包可见两个请求包AS-REQ AS-REP
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/85e201b1-aa32-05cb-1bed-792e07e5bf24.png)

AS-REQ中各个字段
1. pvno Kerberos版本
2. msg-type Kerberos类型 0x0a对应krb-as-req
3. padata 存放了PA-ENC-TIMESTAMP和PA-PAC-REQUEST
3.1 PA-ENC-TIMESTAMP是预认证，使用用户hash加密时间戳，AS存放了用户的hash，AS用用户hash解密获得时间戳。如果时间戳在某一个时间则认证成功。
3.2 PA-PAC-REQUEST是微软引入的PAC拓展，include-pac=true，KDC会根据include的值来判断返回的票据中是否携带PAC。
4. req-body
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/33a02077-0f2b-4807-261e-91a3f60c209a.png)
4.1 cname
PrincipalName 类型。PrincipalName包含type和value。
KRB_NT_PRINCIPAL = 1 意思是只用用户名就行，比如`admin@test.local`这个域用户，只需要填admin
KRB_NT_SRV_INST = 2 service and other unique instance (krbtgt) 这个一般指服务账户名
KRB_NT_ENTERPRISE_PRINCIPAL = 10 `admin@test.local`用户全称。
4.2 sname PrincipalName 类型 在AS_REQ里面sname是krbtgt，类型是KRB_NT_SRV_INST
4.3 till 到期时间
4.4 nonce 随机数
4.5 etype hash加密类型

# AS-REP
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/779b9952-c190-8091-ae35-04cf6f1854f3.png)

KDC使用用户hash解密，如果结果正确返回用krbtgt hash加密的TGT票据。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/a19226a2-5be3-189c-ab08-55f438188efb.png)

各个字段的含义
1. msg-type krb-as-rep 对应的是0x0b
2. crealm 域名
3. cname 用户类型和用户名
4. ticket tgt票据 这里存在黄金票据的问题，因为返回的tgt是通过krbtgt的hash加密的，如果知道krbtgt的hash，则可以伪造任意用户。
5. enc-part 这部分可以用daiker师傅的工具解密。key是用户hash，解密后得到Encryptionkey。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/86399362-c950-4d63-fdf2-0c4a74cad4b3.png)

# 参考
1. https://daiker.gitbook.io/windows-protocol/kerberos/1
2. https://github.com/daikerSec/windows_protocol/tree/master/tools

吹爆daiker师傅


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**