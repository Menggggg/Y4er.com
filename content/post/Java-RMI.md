---
title: "Java RMI原理及反序列化学习"
date: 2020-02-15T23:11:20+08:00
draft: false
tags:
- Java
- RMI
- 反序列化
- ysoserial
series:
-
categories:
- 代码审计
---

RMI 远程方法调用
<!--more-->

## RMI简介
Java远程方法调用，即Java RMI（Java Remote Method Invocation）是Java编程语言里，一种用于实现远程过程调用的应用程序编程接口。它使客户机上运行的程序可以调用远程服务器上的对象。远程方法调用特性使Java编程人员能够在网络环境中分布操作。RMI全部的宗旨就是尽可能简化远程接口对象的使用。

接口的两种常见实现方式是：最初使用JRMP（Java Remote Message Protocol，Java远程消息交换协议）实现；此外还可以用与CORBA兼容的方法实现。RMI一般指的是编程接口，也有时候同时包括JRMP和API（应用程序编程接口），而RMI-IIOP则一般指RMI接口接管绝大部分的功能，以支持CORBA的实现。

最初的RMI API设计为通用地支持不同形式的接口实现。后来，CORBA增加了传值（pass by value）功能，以实现RMI接口。然而RMI-IIOP和JRMP实现的接口并不完全一致。

更多参考 [JAVA RPC：从上手到爱不释手](https://www.jianshu.com/p/362880b635f0)

## RMI架构
RMI分为三部分
1. Registry 类似网关
2. Server 服务端提供服务
3. Client 客户端调用

实现RMI所需的API几乎都在：
- java.rmi：提供客户端需要的类、接口和异常；
- java.rmi.server：提供服务端需要的类、接口和异常；
- java.rmi.registry：提供注册表的创建以及查找和命名远程对象的类、接口和异常；

上代码，服务端
```java
package com.test.rmi;

import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class RMIServer {
    public static String HOST = "127.0.0.1";
    public static int PORT = 8989;
    public static String RMI_PATH = "/hello";
    public static final String RMI_NAME = "rmi://" + HOST + ":" + PORT + RMI_PATH;

    public static void main(String[] args) {
        try {
            // 注册RMI端口
            LocateRegistry.createRegistry(PORT);

            // 创建一个服务
            RMIInterface rmiInterface = new RMIImpl();

            // 服务命名绑定
            Naming.rebind(RMI_NAME, rmiInterface);

            System.out.println("启动RMI服务在" + RMI_NAME);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
```
上述代码中，在8989端口起了RMI服务，以键值对的形式存储了RMI_PATH和rmiInterface的对应关系，也就是`rmi://127.0.0.1:8989/hello`对应一个RMIImpl类实例，然后通过`Naming.rebind(RMI_NAME, rmiInterface)`绑定对应关系。再来看RMIInterface.java
```java
package com.test.rmi;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface RMIInterface extends Remote {
    String hello() throws RemoteException;
}
```
定义了RMIInterface接口，继承自Remote，然后定义了一个hello()方法作为接口。注意需要抛出RemoteException异常。继续看实现真正功能的类RMIImpl.java
```java
package com.test.rmi;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class RMIImpl extends UnicastRemoteObject implements RMIInterface {
    protected RMIImpl() throws RemoteException {
        super();
    }

    @Override
    public String hello() throws RemoteException {
        System.out.println("call hello().");
        return "this is hello().";
    }

}
```
继承自UnicastRemoteObject类，并且实现之前定义的RMIInterface接口的hello()方法。UnicastRemoteObject类提供了很多支持RMI的方法，具体来说，这些方法可以通过JRMP协议导出一个远程对象的引用，并通过动态代理构建一个可以和远程对象交互的Stub对象。现在就定义好了Server端，来看Client
```java
package com.test.rmi;

import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

import static com.test.rmi.RMIServer.RMI_NAME;

public class RMIClient {
    public static void main(String[] args) {
        try {
            // 获取服务注册器
            Registry registry = LocateRegistry.getRegistry("127.0.0.1", 8989);
            // 获取所有注册的服务
            String[] list = registry.list();
            for (String i : list) {
                System.out.println("已经注册的服务：" + i);
            }

            // 寻找RMI_NAME对应的RMI实例
            RMIInterface rt = (RMIInterface) Naming.lookup(RMI_NAME);

            // 调用Server的hello()方法,并拿到返回值.
            String result = rt.hello();

            System.out.println(result);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
我们可以通过Registry拿到所有已经注册的服务，其中就包括我们注册的hello。然后可以通过Naming.lookup(RMI_NAME)去寻找对应的hello实例，这样就拿到了远程对象，可以直接通过对象来调用hello()方法。

在Java 1.4及 以前的版本中需要手动建立Stub对象，通过运行rmic命令来生成远程对象实现类的Stub对象，但是在Java 1.5之后可以通过动态代理来完成，不再需要这个过程了。运行Server之后再运行Client输出结果
```
Server
启动RMI服务在rmi://127.0.0.1:8989/hello
call hello().

Client
已经注册的服务：hello
this is hello().
```
那么Registry去哪了？通常在新建一个RMI Registry的时候，都会直接绑定一个对象在上面，也就是说我们示例代码中的Server其实包含了Registry和Server两部分。我们用一张图来解释下。

![image](https://y4er.com/img/uploads/20200216017286.png)

## RMI的通信模型
上一部分我提到了Stub对象，是因为RMI底层通讯采用了Stub(运行在客户端)和Skeleton(运行在服务端)机制，真正的调用过程如图所示。

![image](https://y4er.com/img/uploads/20200216011185.png)

Client调用远程方法时，会先创建Stub(sun.rmi.registry.RegistryImpl_Stub)对象，然后将Remote对象传递给远程引用层(java.rmi.server.RemoteRef)并创建java.rmi.server.RemoteCall(远程调用)对象，RemoteCall序列化服务名和Remote对象，RemoteRef将序列化之后的数据通过socket传输到Server的RemoteRef。

Server的RemoteRef收到远程调用请求之后，将数据传递给Skeleton(sun.rmi.registry.RegistryImpl_Skel#dispatch)，Skeleton调用RemoteCall反序列化传过来的数据，Skeleton处理客户端请求如：bind、list、lookup、rebind、unbind，如果是lookup则查找RMI服务名绑定的接口对象，序列化该对象并通过RemoteCall传输到Client。

Client反序列化Server返回的序列化数据从而获得远程对象的引用。然后Client调用远程方法，Server反射执行对应方法并将结果序列化传输给Client，Client反序列化结果，整个过程结束。

## RMI需要解决的问题
其实很明显的有两大问题
1. 数据的传递问题
2. 远程对象如何发现

### 数据传递
Java中是存在引用类型的，当引用类型的变量作为参数被传递时，传递的不是值，而是内存地址，而对于一台机器上的同一个Java虚拟机来讲，引用传递当然没有问题，而对于分布式的RPC调用，引用传递的内存地址在两个Java虚拟机中并不对等，所以怎么解决呢？

1. 使用序列化传递
2. 仍然用引用传递，每当远程主机调用本地主机方法时，该调用还要通过本地主机查询该引用对应的对象

RMI中的参数传递和结果返回可以使用的三种机制（取决于数据类型）：

简单类型：按值传递，直接传递数据拷贝；
远程对象引用（实现了Remote接口）：以远程对象的引用传递；
远程对象引用（未实现Remote接口）：按值传递，通过序列化对象传递副本，本身不允许序列化的对象不允许传递给远程方法

### 远程对象发现
RMI解决方式就是类似于域名对应IP的解决方式，`rmi://host:port/name`，不同的name对应不同的远程对象，注意主机和端口都是可选的，如果省略主机，则默认运行在本地；如果端口也省略，则默认端口是1099。

## RMI的序列化和反序列化
在RMI的通信过程中，用到了很多的序列化和反序列化，而在Java中，只要进行反序列化操作就可能有漏洞。RMI通过序列化传输Remote对象，那么我们可以构造恶意的Remote对象，当服务端反序列化传输过来的数据时，就会触发反序列化。

利用的话我们可以使用ysoserial，如图
![image](https://y4er.com/img/uploads/20200216016965.png)

客户端在sun.rmi.registry.RegistryImpl_Stub#bind中进行了序列化，这个类是动态生成的，所以在源码中找不到这个类。
![image](https://y4er.com/img/uploads/2020021601567.png)

服务端在sun.rmi.registry.RegistryImpl_Skel#dispatch 进行反序列化，同样是动态生成类。
![image](https://y4er.com/img/uploads/20200216014183.png)

## RMI-JRMP反序列化
JRMP接口的两种常见实现方式：
1. JRMP协议(Java Remote Message Protocol)，RMI专用的Java远程消息交换协议。
2. IIOP协议(Internet Inter-ORB Protocol) ，基于 CORBA 实现的对象请求代理协议。

JRMP在传输过程中也会自动序列化和反序列化，利用过程和RMI一样，不再此赘述。

## 参考链接
1. https://javasec.org/javase/RMI/
2. https://blog.csdn.net/lmy86263/article/details/72594760
3. https://www.cnblogs.com/afanti/p/10256840.html
4. https://xz.aliyun.com/t/5392
5. https://blog.51cto.com/guojuanjun/1423392
6. https://blog.hufeifei.cn/2017/12/14/Java/RMI%E5%8E%9F%E7%90%86%E8%A7%A3%E6%9E%90/
7. https://www.jianshu.com/p/362880b635f0
8. https://www.anquanke.com/post/id/197829
9. https://xz.aliyun.com/t/2223 [这篇很清晰]

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**