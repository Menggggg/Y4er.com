---
title: "Kerberos协议之TGS_REQ & TGS_REP"
date: 2020-11-12T11:37:42+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---

继续Kerberos协议
<!--more-->

# 接上文
前面解释了AS_REQ & AS_REP，在AS_REP中，kdc返回了使用krbtgt hash加密的tgt票据。在TGS_REQ & TGS_REP阶段，就是client拿着AS_REP获得的tgt票据去KDC换可以访问具体服务的tgs票据，然后再使用TGS票据去访问具体的服务。这一阶段，微软引进了两个扩展S4U2SELF和S4U2PROXY。

配置以下Kerberos发包工具。把AS_REP的票据导入，同样勾上RC4加密。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/990fd2e3-b4fa-7b56-c0e6-bdc3dd4b13ce.png)

发包
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/5373b549-86e3-6b01-0acf-891aef0b4257.png)

# TGS_REQ
在TGS_REQ请求中需要ap-req字段
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/3fb73bd7-aeae-a929-23db-b2ea1d698c69.png)
这部分包含了tgt里的信息，kdc以此校验tgt，正确则返回tgs票据。

PA_FOR_USER字段
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/1af91904-3ea6-f991-2bca-72a607e0a6dd.png)

类型是S4U2SELF，值是一个唯一的标识符，该标识符指示用户的身份。该唯一标识符由用户名和域名组成。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/a544d342-a8ed-c6de-a452-6591fdaff815.png)
S4U2proxy 必须扩展PA_FOR_USER结构，指定服务代表某个用户(图片里面是administrator)去请求针对服务自身的kerberos服务票据。

PA_PAC_OPTIONS字段
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/197e048f-009f-813d-d319-0728f09d078d.png)

类型是 PA_PAC_OPTIONS，值是以下flag的组合

1. Claims(0)
2. Branch Aware(1)
3. Forward to Full DC(2)
4. Resource-based Constrained Delegation (3)

微软的MS-SFU 2.2.5， S4U2proxy 必须扩展PA-PAC-OPTIONS结构。
如果是基于资源的约束委派，就需要指定Resource-based Constrained Delegation(RBCD)位。

req-body
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c16f90e8-6994-e26c-2331-2792d6a978b0.png)

sname指要请求的服务名，tgs的票据是由该服务用户的hash加密的。如果该服务名为krbtgt，那么tgs的票据可以当tgt用。

AddtionTicket：附加票据，在S4U2proxy请求里面，既需要正常的TGT，也需要S4U2self阶段获取到的TGS，那么这个TGS就添加到AddtionTicket里面。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/24d527ec-3096-82f9-36df-cdeb5a9d5dd6.png)

# TGS_REP
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/7c70b0cf-36f6-6f11-04d6-61dd72228780.png)

ticket字段是tgs票据，用于下一步的AP_REQ认证。ticket中的enc_part是使用服务账户的hash加密的，如果有服务账户的hash，就可以自己签发一个给任意用户的tgs票据(白银票据)。

最后一个enc_part可以解密，其中的session_key用作下一阶段的认证密钥。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/440c529b-37d8-4ac8-74c7-942ec5907555.png)


挖坑，S4U2SELF、S4U2PROXY和委派暂时放后面说。(等我看懂)

# 参考
1. https://daiker.gitbook.io/windows-protocol/kerberos/2


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**