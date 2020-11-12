---
title: "Windows本地认证NTLM Hash&LM Hash"
date: 2020-11-12T11:29:48+08:00
draft: false
tags:
- NTLM
series:
- Windows协议
categories:
- 渗透测试
---

Windows本地认证
<!--more-->

# 基础
Windows本地认证采用sam hash比对的形式来判断用户密码是否正确，计算机本地用户的所有密码被加密存储在`%SystemRoot%\system32\config\sam`文件中，这个文件更像是一个存储用户密码的数据库。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/05292947-64cd-bfa1-6118-07182e3c1400.png)

本地认证的过程其实就是Windows把用户输入的密码凭证和sam里的加密hash比对的过程。

Windows对用户的密码凭证有两种加密算法，也就是本文写的ntlm和lm。在使用QuarksPwDump抓密码的时候经常看到形如这样的hash

```text
admin:1003:AAD3B435B51404EEAAD3B435B51404EE:111F54A2A4C0FB3D7CD9B19007809AD6:::
Guest:501:AAD3B435B51404EEAAD3B435B51404EE:31D6CFE0D16AE931B73C59D7E0C089C0:::
Administrator:500:AAD3B435B51404EEAAD3B435B51404EE:58EC08167E274AD52D1849DA7A3E9A81:::
```
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/6050b180-c13c-74dc-ba24-56364de231c9.png)

其中冒号分割的前半段`AAD3B435B51404EEAAD3B435B51404EE`是lm hash，后半段`111F54A2A4C0FB3D7CD9B19007809AD6`是ntlm hash。前半段放到cmd5解密会发现是空密码，那是因为Windows版本的原因。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/93c10772-7664-430a-a471-1f189675e77e.png)

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/9dc978b4-1bca-a900-8192-c650ce01b7e9.png)

也就是说从Windows Vista 和 Windows Server 2008开始，默认情况下只存储NTLM Hash，LM Hash将不再存在。

接下来介绍下这两种协议的认证过程和加密算法。

# LM Hash
全称是`LAN Manager Hash`, windows最早用的加密算法，由IBM设计。

LM Hash的计算:

1. 用户的密码转换为大写，密码转换为16进制字符串，不足14字节将会用0来再后面补全。
2. 密码的16进制字符串被分成两个7byte部分。每部分转换成比特流，并且长度位56bit，长度不足使用0在左边补齐长度
3. 再分7bit为一组,每组末尾加0，再组成一组
4. 上步骤得到的二组，分别作为key 为 `KGS!@#$%`进行DES加密。
5. 将加密后的两组拼接在一起，得到最终LM HASH值。

python脚本计算

```python
#coding=utf-8
import re
import binascii
from pyDes import *
def DesEncrypt(str, Des_Key):
    k = des(binascii.a2b_hex(Des_Key), ECB, pad=None)
    EncryptStr = k.encrypt(str)
    return binascii.b2a_hex(EncryptStr)

def group_just(length,text):
    # text 00110001001100100011001100110100001101010011011000000000
    text_area = re.findall(r'.{%d}' % int(length), text) # ['0011000', '1001100', '1000110', '0110011', '0100001', '1010100', '1101100', '0000000']
    text_area_padding = [i + '0' for i in text_area] #['00110000', '10011000', '10001100', '01100110', '01000010', '10101000', '11011000', '00000000']
    hex_str = ''.join(text_area_padding) # 0011000010011000100011000110011001000010101010001101100000000000
    hex_int = hex(int(hex_str, 2))[2:].rstrip("L") #30988c6642a8d800
    if hex_int == '0':
        hex_int = '0000000000000000'
    return hex_int

def lm_hash(password):
    # 1. 用户的密码转换为大写，密码转换为16进制字符串，不足14字节将会用0来再后面补全。
    pass_hex = password.upper().encode("hex").ljust(28,'0') #3132333435360000000000000000
    print(pass_hex) 
    # 2. 密码的16进制字符串被分成两个7byte部分。每部分转换成比特流，并且长度位56bit，长度不足使用0在左边补齐长度
    left_str = pass_hex[:14] #31323334353600
    right_str = pass_hex[14:] #00000000000000
    left_stream = bin(int(left_str, 16)).lstrip('0b').rjust(56, '0') # 00110001001100100011001100110100001101010011011000000000
    right_stream = bin(int(right_str, 16)).lstrip('0b').rjust(56, '0') # 00000000000000000000000000000000000000000000000000000000
    # 3. 再分7bit为一组,每组末尾加0，再组成一组
    left_stream = group_just(7,left_stream) # 30988c6642a8d800
    right_stream = group_just(7,right_stream) # 0000000000000000
    # 4. 上步骤得到的二组，分别作为key 为 "KGS!@#$%"进行DES加密。
    left_lm = DesEncrypt('KGS!@#$%',left_stream) #44efce164ab921ca
    right_lm = DesEncrypt('KGS!@#$%',right_stream) # aad3b435b51404ee
    # 5. 将加密后的两组拼接在一起，得到最终LM HASH值。
    return left_lm + right_lm

if __name__ == '__main__':
    hash = lm_hash("123456")
```

lm协议的脆弱之处在于

1. des的key是固定的
2. 可以根据hash判断密码长度是否大于7位，如果密码强度是小于7位，那么第二个分组加密后的结果肯定是aad3b435b51404ee
3. 密码不区分大小写并且长度最大为14位
4. 7+7字符分开加密明显复杂度降低14个字符整体加密 95<sup>7</sup>+ 95<sup>7</sup> <95 <sup>14</sup>

# NTLM Hash
LM Hash 的脆弱性显而易见，所以微软于1993年在Windows NT 3.1中引入了NTLM协议。

加密算法如下：

1. 先将用户密码转换为十六进制格式。
2. 将十六进制格式的密码进行Unicode编码。
3. 使用MD4摘要算法对Unicode编码数据进行Hash计算

python计算

```python
import hashlib,binascii
print binascii.hexlify(hashlib.new("md4", "123456".encode("utf-16le")).digest())
```

# 认证过程
本地认证过程都是一样的，算法不一样。

winlogon.exe -> 接收用户密码 -> lsass.exe -> 比对sam表

winlogon就是登陆界面，接受用户密码之后会发送明文到lsass.exe，lsass.exe会存储一份明文，然后加密明文和sam表的hash做比对，判断是否可以登陆。

Windows Logon Process(即 winlogon.exe)，是Windows NT 用户登陆程序，用于管理用户登录和退出。LSASS用于微软Windows系统的安全机制。它用于本地安全和登陆策略。

下一篇写NTLM网络认证

# 参考
1. https://payloads.online/archivers/2018-11-30/1
2. https://daiker.gitbook.io/windows-protocol/NTLM-pian/4
3. [Windows下的密码hash——NTLM hash和Net-NTLM hash介绍](https://3gstudent.github.io/Windows%E4%B8%8B%E7%9A%84%E5%AF%86%E7%A0%81hash-NTLM-hash%E5%92%8CNet-NTLM-hash%E4%BB%8B%E7%BB%8D/)
4. http://davenport.sourceforge.net/NTLM.html
5. https://www.cnblogs.com/artech/archive/2011/01/25/NTLM.html
6. https://www.cnblogs.com/yuzly/p/10480438.html


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**