---
title: "Bypass JEP290"
date: 2020-05-29T11:27:08+08:00
draft: false
tags:
- java
- 反序列化
series:
-
categories:
- 代码审计
---

本文学习如何绕过JEP290反序列化限制
<!--more-->
## 关于JEP290
JEP290是Java底层为了缓解反序列化攻击提出的一种解决方案，主要做了以下几件事

1. 提供一个限制反序列化类的机制，白名单或者黑名单。
2. 限制反序列化的深度和复杂度。
3. 为RMI远程调用对象提供了一个验证类的机制。
4. 定义一个可配置的过滤机制，比如可以通过配置properties文件的形式来定义过滤器。

## JEP290的实际限制
写一个RMIServer

RMIServer.java

```java
package org.chabug.rmi.server;

import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class RMIServer {
    public static String HOST = "127.0.0.1";
    public static int PORT = 1099;
    public static String RMI_PATH = "/hello";
    public static final String RMI_NAME = "rmi://" + HOST + ":" + PORT + RMI_PATH;

    public static void main(String[] args) {
        try {
            // 注册RMI端口
            LocateRegistry.createRegistry(PORT);
            // 创建一个服务
            Hello hello = new HelloImpl();
            // 服务命名绑定
            Naming.rebind(RMI_NAME, hello);

            System.out.println("启动RMI服务在" + RMI_NAME);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

HelloImpl.java

```java
package org.chabug.rmi.server;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class HelloImpl extends UnicastRemoteObject implements Hello {
    protected HelloImpl() throws RemoteException {
    }

    public String hello() throws RemoteException {
        return "hello world";
    }

    public String hello(String name) throws RemoteException {
        return "hello" + name;
    }

    public String hello(Object object) throws RemoteException {
        System.out.println(object);
        return "hello "+object.toString();
    }
}
```

Hello.java

```java
package org.chabug.rmi.server;


import java.rmi.Remote;
import java.rmi.RemoteException;

public interface Hello extends Remote {
    String hello() throws RemoteException;
    String hello(String name) throws RemoteException;
    String hello(Object object) throws RemoteException;
}
```
使用JDK7u21打Commonscollections1，成功弹出calc。
![image.png](https://y4er.com/img/uploads/20200529110235.png)

使用JDK8u221启动RMIServer攻击失败
![image.png](https://y4er.com/img/uploads/20200529113177.png)
报错显示

```
ObjectInputFilter REJECTED: class sun.reflect.annotation.AnnotationInvocationHandler, array length: -1, nRefs: 8, depth: 2, bytes: 298, ex: n/a
```
## JEP290的过滤机制
在上文的报错中可见`sun.reflect.annotation.AnnotationInvocationHandler`被拒绝，跟一下RMI的过程，看下在哪里过滤了，JEP290又是怎么实现的。以下使用JDK8U221调试

首先我们要清楚RMI的实现流程
![image.png](https://y4er.com/img/uploads/20200529118617.png)
在远程引用层中客户端服务端两个交互的类分别是`RegistryImpl_Stub`和`RegistryImpl_Skel`，在服务端的`RegistryImpl_Skel`类中，向注册中心进行bind、rebind操作时均进行了readObject操作以此拿到Remote远程对象引用。
![image.png](https://y4er.com/img/uploads/20200529113113.png)

跟进63行进入到`java.io.ObjectInputStream#readObject`，然后进入`readObject0()`
![image.png](https://y4er.com/img/uploads/20200529117657.png)
在readObject0()之中进入readOrdinaryObject()
![image.png](https://y4er.com/img/uploads/20200529111407.png)
继续进入readClassDesc()
![image.png](https://y4er.com/img/uploads/20200529116825.png)
进入readProxyDesc()
![image.png](https://y4er.com/img/uploads/20200529118768.png)

在readProxyDesc()中有filterCheck
![image.png](https://y4er.com/img/uploads/20200529117829.png)

先检查其所有接口，然后检查对象自身。进入filterCheck()之后
![image.png](https://y4er.com/img/uploads/20200529113824.png)
调用了serialFilter.checkInput()，最终来到`sun.rmi.registry.RegistryImpl#registryFilter`
![image.png](https://y4er.com/img/uploads/20200529116979.png)

```java
return String.class != var2 && !Number.class.isAssignableFrom(var2) && !Remote.class.isAssignableFrom(var2) && !Proxy.class.isAssignableFrom(var2) && !UnicastRef.class.isAssignableFrom(var2) && !RMIClientSocketFactory.class.isAssignableFrom(var2) && !RMIServerSocketFactory.class.isAssignableFrom(var2) && !ActivationID.class.isAssignableFrom(var2) && !UID.class.isAssignableFrom(var2) ? Status.REJECTED : Status.ALLOWED;
```

![image.png](https://y4er.com/img/uploads/20200529116890.png)
没有给`AnnotationInvocationHandler`白名单，所以返回REJECTED。

## 绕过JEP290
在RMI远程方法调用过程中，方法参数需要先序列化，从本地JVM发送到远程JVM，然后在远程JVM上反序列化，执行完后，将结果序列化，发送回本地JVM，而在本地的参数是我们可以控制的，如果向参数中注入gadget会怎么样？

我在HelloImpl实现了三个hello()方法，分别是void、string、Object类型的参数
![image.png](https://y4er.com/img/uploads/20200529119249.png)

在客户端我向Object参数类型注入cc5的gadget
![image.png](https://y4er.com/img/uploads/20200529118670.png)

运行成功弹出calc
![image.png](https://y4er.com/img/uploads/20200529110642.png)

也就是说：如果目标的RMI服务暴漏了Object参数类型的方法，我们就可以注入payload进去。

那么别的参数类型呢？在sun.rmi.server.UnicastRef#unmarshalValue中判断了远程调用方法的参数类型
![image.png](https://y4er.com/img/uploads/20200529113622.png)
如果不是基本类型，就进入readObject，之后的流程也走了filterCheck过滤
![image.png](https://y4er.com/img/uploads/20200529110830.png)
不过在`sun.rmi.transport.DGCImpl#checkInput`这里ObjID是在白名单中的，所以可以被反序列化。

那这个只是object类型的参数可以，其他的参数类型呢？

由于攻击者可以完全控制客户端，因此他可以用恶意对象替换从Object类派生的参数（例如String）有几种方法：

1. 将java.rmi软件包的代码复制到新软件包，然后在其中更改代码
2. 将调试器附加到正在运行的客户端，并在序列化对象之前替换对象
3. 使用Javassist之类的工具更改字节码
4. 通过实现代理来替换网络流上已经序列化的对象

afanti师傅用的是通过RASP hook住`java.rmi.server.RemoteObjectInvocationHandler`类的`InvokeRemoteMethod`方法的第三个参数非Object的改为Object的gadget。他的项目地址在[RemoteObjectInvocationHandler](https://github.com/Afant1/RemoteObjectInvocationHandler)。

修改`src\main\java\afanti\rasp\visitor\RemoteObjectInvocationHandlerHookVisitor.java`的dnslog地址，然后打包出来在RMIClient运行前加上`-javaagent:e:/rasp-1.0-SNAPSHOT.jar`

虽然报错参数类型不匹配
![image.png](https://y4er.com/img/uploads/20200529110171.png)

但是dnslog已经收到请求了。

![image.png](https://y4er.com/img/uploads/20200529117757.png)


## 参考
1. https://mogwailabs.de/blog/2019/03/attacking-java-rmi-services-after-jep-290/
2. https://www.anquanke.com/post/id/200860
3. https://github.com/Afant1/RemoteObjectInvocationHandler
4. https://paper.seebug.org/454/


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**