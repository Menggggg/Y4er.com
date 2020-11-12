---
title: "Windows网络认证NTLM&Net-NTLM Hash"
date: 2020-11-12T11:32:07+08:00
draft: false
tags:
- NTLM
series:
- Windows协议
categories:
- 渗透测试
---

继续学
<!--more-->
Net-NTLM Hash 通常是指网络环境下NTLM认证中的Hash，比如在工作组环境中，共享资料通过net use来建立smb共享。早期smb传输明文口令，后来用LM，现在用NTLM。

NTLM使用在Windows NT和Windows 2000 Server（or later）工作组环境中（Kerberos用在域模式下）。在AD域环境中，如果需要认证Windows NT系统，也必须采用NTLM。较之Kerberos，基于NTLM的认证过程要简单很多。NTLM采用一种质询/应答（Challenge/Response）消息交换模式。

NTLM是只能镶嵌在上层协议里面，消息的传输依赖于使用NTLM的上层协议。比如镶嵌在SMB协议。

# 简述NTLM
NTLM认证采用质询/应答（Challenge/Response）的消息交换模式，流程如下：

NTLM协议的认证过程分为三步：

- 协商 主要用于确认双方协议版本(NTLM v1/NTLM V2)
- 质询 就是挑战（Challenge）/响应（Response）认证机制起作用的范畴。
- 验证 验证主要是在质询完成后，验证结果，是认证的最后一步。


整个流程图如下

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b89b03f9-2fd2-0903-b913-2c043fe09839.png)

使用net use模拟流量请求,因为net use是建立在smb上的，所以会有smb的流量。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/48f4ea48-cc6b-6e47-f887-3b759f5eea5e.png)


13-22请求包为net use的包，**其中13-16为smb的包，17-20为NTLM认证的包**，一个一个看

# SMB
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/12a2c124-512a-ea57-4ac4-8fa9e9255d4c.png)

客户端向服务器发送smb协商1，请求包中包含客户端支持的smb协议版本

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/74deb70d-47df-ef8b-c5d4-113f6ad9f050.png)

服务端返回smb Response 1，包含它所支持的smb版本

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/52a5b0ac-0808-1502-c3f9-4467b3fc6e4a.png)

然后客户端根据服务端返回的smb版本选择一个两者通用的发送协商smb Request 2

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/5a27be59-addd-2d29-a6c7-b434ad0ac0d4.png)

服务端回应smb Response 2

这里我其实没弄明白为什么要发四个包，按理说前两个包已经拿到了客户端和服务端支持的smb版本，第三个包直接认证就行了，但是还进行了smb Request2，不是脱裤子放屁吗？

然后我对比了两个Request和respons，发现在两个Response中的 Dialect 字段不太一样。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b4923b22-9cbc-7287-7787-311554c14c3b.png)

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/ad2874cb-2b5a-f44f-720b-42d01db06459.png)

再仔细看Request2中只发送了两个smb版本
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/128cb862-aad1-6f29-5895-b9d4ade61b4a.png)

大胆猜测 

1. smb req 1 发送所有支持的协议版本
2. smb resp 1 返回期望的smb版本 即上图中Dialect字段 SMB2 wildcard
3. smb req 2 客户端发现本地有两个smb V2的版本，得重新协商用哪个，就把本地所有的smb V2的版本全发过去
4. smb resp 2 就高不就低 服务端返回 SMB 2.1

# NTLM认证

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/98b1f4c0-7d32-688b-e681-f0faa602a562.png)

NTLMSSP_NEGOTIATE Request 发送一些版本信息给服务端协商协议版本

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c1655bce-c926-492a-c7a1-6fb5d333dc07.png)

NTLMSSP_NEGOTIATE Response 返回 NTLMSSP_Challenge 包含一个16位随机数Challenge。

客户端接收到Challenge之后，使用用户NTLM Hash与Challenge进行加密运算得到Response，将Response,username,Challenge发给服务器。消息中的Response是最关键的部分，因为它向服务器证明客户端用户已经知道帐户密码。

**其中，经过NTLM Hash加密Challenge的结果在网络协议中称之为Net NTLM Hash。**

继续第三个请求包

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/6eac6973-9106-3861-4f12-6db98abadf87.png)

客户端发送刚才加密计算的Response,username,Challenge给服务端，这里的Challenge是客户端重新生成的一个随机的nonce，不同于上一个相应包中的Challenge。

MIC是校验和，设计MIC主要是为了防止这个包中途被修改。session_key是在要求进行签名的时候用的，用来进行协商加密密钥。


![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/3ee56872-6d2a-2c75-ec5c-131c6f930429.png)

第四个请求包表示验证通过。当使用错误的用户名密码net use时，会验证失败。如图

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/a85261a7-9ff5-e246-e07f-bea86f10e11a.png)

# Net-NTLM Hash
在请求包19中的Response根据系统版本被分为六种响应类型

1. LM(LAN Manager)响应 - 由大多数较早的客户端发送，这是“原始”响应类型。
2. NTLMv1响应 - 这是由基于NT的客户端发送的，包括Windows 2000和XP。
3. NTLMv2响应 - 在Windows NT Service Pack 4中引入的一种较新的响应类型。它替换启用了NTLMv2的系统上的NTLM响应。
4. LMv2响应 - 替代NTLMv2系统上的LM响应。
5. NTLM2会话响应 - 用于在没有NTLMv2身份验证的情况下协商NTLM2会话安全性时，此方案会更改LM NTLM响应的语义。
6. 匿名响应 - 当匿名上下文正在建立时使用; 没有提供实际的证书，也没有真正的身份验证。

这六种使用的加密流程一样，都是前面我们说的 Challenge/Response 验证机制,区别在Challenge和加密算法不同。

- Challage:NTLM v1的Challenge有8位，NTLM v2的Challenge为16位。
- Net-NTLM Hash:NTLM v1的主要加密算法是DES，NTLM v2的主要加密算法是HMAC-MD5。

根据LmCompatibilityLevel的安全设置来决定发送哪个响应，默认如下

1. Windows 2000 以及 Windows XP: 发送 LM & NTLM 响应
2. Windows Server 2003: 仅发送 NTLM 响应
3. Windows Vista、Windows Server 2008、Windows 7 以及 Windows Server 2008 R2及以上: 仅发送 NTLMv2 响应

Net-NTLM Hash v1的格式为：

```
username::hostname:LM Response:NTLM Response:Challenge
```

Net-NTLM Hash v2的格式为：

```
username::domain:Challenge:HMAC-MD5:blob
```

**Challenge为NTLM Server Challenge**，domian由数据包内容获得(IP或者机器名)，HMAC-MD5对应数据包中的NTProofStr。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/8ed4ac46-6730-3a11-2046-40d003cc03b5.png)

blob对应数据包中Response去掉NTProofStr的后半部分，拼接NTLM v2 Hash为

```
administrator::test:bb7e0cce5b7a719c:40426e2eaa7d7b467855be0881b5d069:01010000000000001111f0f6ae9ed60161e75abd99c8fd2b0000000002000800540045005300540001000400440043000400140074006500730074002e006c006f00630061006c0003001a00440043002e0074006500730074002e006c006f00630061006c000500140074006500730074002e006c006f00630061006c00070008001111f0f6ae9ed601060004000200000008003000300000000000000000000000003000007276a9639bd6e10c91bbc264a284d542e7acb37803ef6a3bf7e3eb9cbf82a2d20a001000000000000000000000000000000000000900200063006900660073002f003100370032002e00310036002e00330033002e003300000000000000000000000000
```

Hashcat破解就行了。

```
hashcat -m 5600 administrator::test:bb7e0cce5b7a719c:40426e2eaa7d7b467855be0881b5d069:01010000000000001111f0f6ae9ed60161e75abd99c8fd2b0000000002000800540045005300540001000400440043000400140074006500730074002e006c006f00630061006c0003001a00440043002e0074006500730074002e006c006f00630061006c000500140074006500730074002e006c006f00630061006c00070008001111f0f6ae9ed601060004000200000008003000300000000000000000000000003000007276a9639bd6e10c91bbc264a284d542e7acb37803ef6a3bf7e3eb9cbf82a2d20a001000000000000000000000000000000000000900200063006900660073002f003100370032002e00310036002e00330033002e003300000000000000000000000000 /tmp/password.list --force
```

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/85f44e08-48ba-937a-0f8a-e2174da8507e.png)



# 参考
1. https://payloads.online/archivers/2018-11-30/1
2. https://daiker.gitbook.io/windows-protocol/NTLM-pian/4
3. [Windows下的密码hash——NTLM hash和Net-NTLM hash介绍](https://3gstudent.github.io/Windows%E4%B8%8B%E7%9A%84%E5%AF%86%E7%A0%81hash-NTLM-hash%E5%92%8CNet-NTLM-hash%E4%BB%8B%E7%BB%8D/)
4. http://davenport.sourceforge.net/NTLM.html
5. https://www.cnblogs.com/artech/archive/2011/01/25/NTLM.html
6. https://www.cnblogs.com/yuzly/p/10480438.html


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**