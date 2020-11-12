---
title: "Kerberos协议之PAC及MS14-068"
date: 2020-11-12T11:39:57+08:00
draft: false
tags:
- Kerberos
series:
- Windows协议
categories:
- 渗透测试
---


<!--more-->

# PAC介绍
介绍PAC之前，先重新捋一捋Kerberos协议的流程

1. AS_REQ Client使用自己的hash加密时间戳发送给kdc请求TGT
2. AS_REP kdc使用Client Hash解密验证时间戳，如果正确则就返回用krbtgt hash加密的TGT票据
3. TGS_REQ Client使用TGT票据向KDC发起针对指定服务的TGS_REQ请求
4. TGS_REP KDC使用krbtgt hash解密tgt票据，如果解密正确则返回特定服务hash加密的tgs票据
5. AP_REQ Client使用TGS票据请求特定服务
6. AP_REP 特定服务使用自己的hash解密，如果验证正确向KDC发送TGS票据询问该Client是否有权限访问自身服务。

PAC在其中出现的节点为AS_REP和AP_REP。在AS_REP中，KDC返回的tgt票据中包含了PAC。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/d1a181f6-d90d-8df7-2da7-1b28070386cc.png)

在AP_REP中，服务解密验证正确后将PAC发送给KDC，KDC根据PAC的值来判断用户是否有权限访问该服务。

**而在TGS_REP中，不管Client是否有权限访问特殊服务，只要Client发送的TGT票据是正确的，那么就会返回服务hash加密的tgs票据，这也是kerberoating利用的原因。换而言之，不管你是什么用户，只要你的hash正确，那么就能请求域内任意服务的TGS票据。**

krbtgt服务的密码是随机生成的，就别想了。

PAC的结构看不懂，见daiker师傅文章吧。这里介绍下因为pac引发的高危漏洞MS14-068

# MS14-068

以下内容摘抄自[《深入解读MS14-068漏洞：微软精心策划的后门？》](https://www.freebuf.com/vuls/56081.html)

1. 在KDC机构对PAC进行验证时，对于PAC尾部的签名算法，虽然原理上规定必须是带有Key的签名算法才可以，但微软在实现上，却允许任意签名算法，只要客户端指定任意签名算法，KDC服务器就会使用指定的算法进行签名验证。
2. PAC没有被放在TGT中，而是放在了TGS_REQ数据包的其它地方。但可笑的是，KDC在实现上竟然允许这样的构造，也就是说，KDC能够正确解析出没有放在其它地方的PAC信息。
3. 只要TGS_REQ按照刚才漏洞要求设置，KDC服务器会做出令人吃惊的事情：它不仅会从Authenticator中取出来subkey把PAC信息解密并利用客户端设定的签名算法验证签名，同时将另外的TGT进行解密得到SessionKeya-kdc；
4. 在验证成功后，把解密的PAC信息的尾部，重新采用自身Server_key和KDC_key生成一个带Key的签名，把SessionKeya-kdc用subkey加密，从而组合成了一个新的TGT返回给Client-A

## kekeo
直接打，需要一个域账户。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/fec91b68-b9e8-6c70-7a36-e7c83cfdc781.png)

## impacket
goldenPac.py windows的在 https://github.com/maaaaz/impacket-examples-windows 下载
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/e6e940a4-5b87-45d8-34b1-12433d707d0a.png)

## pykek
https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS14-068

exe和python版本，演示py的版本。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/bb165a46-3a43-c70c-dc41-ce583624f8c2.png)

拼接domain sid和域用户id

```
S-1-5-21-514356739-3204155868-1239341419-1111
```
生成tgt票据
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/a84fa640-4975-d56b-b28e-cfd1c0dfc9ca.png)
ptt过去
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/db4b7bff-8120-7c43-e64f-d61c0e0fac78.png)

# 参考
1. https://daiker.gitbook.io/windows-protocol/kerberos/3
2. https://github.com/SecWiki/windows-kernel-exploits/tree/master/MS14-068
3. https://github.com/mubix/pykek
4. https://gist.github.com/TarlogicSecurity/2f221924fef8c14a1d8e29f3cb5c5c4a


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**