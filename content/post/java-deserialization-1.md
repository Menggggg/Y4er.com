---
title: "Java 反序列化基础"
date: 2019-10-14T20:55:59+08:00
draft: false
tags: []
categories: ['代码审计']
---

又臭又长🙃

<!--more-->

## java反序列化学习
序列化是将面向对象中的对象转化为文件的过程，通过在流中使用文件可以实现对象的持久存储。 和PHP一样，java中也有序列化和反序列化，先来看下最基本的反序列化代码。
## 反序列化demo
```java
import java.io.*;

interface Animal {
    public void eat();
}

class Ani implements Serializable {
    public String name;

    private void readObject(java.io.ObjectInputStream in) throws IOException, ClassNotFoundException {
        //执行默认的readObject()方法
        in.defaultReadObject();
        //执行打开计算器程序命令
        Runtime.getRuntime().exec("calc");
    }
}

class Cat extends Ani implements Animal {
    @Override
    public void eat() {
        System.out.println("cat eat.");
    }
}

public class Test {

    public static void main(String[] args) throws IOException, ClassNotFoundException {
        Ani cat = new Cat();
        cat.name = "tom";
        FileOutputStream fos = new FileOutputStream("obj");
        ObjectOutputStream os = new ObjectOutputStream(fos);
        os.writeObject(cat);
        os.close();
        //从文件中反序列化obj对象
        FileInputStream fis = new FileInputStream("obj");
        ObjectInputStream ois = new ObjectInputStream(fis);
        //恢复对象
        Cat objectFromDisk = (Cat) ois.readObject();
        System.out.println(objectFromDisk.name);
        ois.close();
    }
}

```
在java中，反序列化对象是通过继承`Serializable`接口来实现的，只要一个类实现了java.io.Serializable接口，那么它就可以被序列化。

在上面这段代码中，创建了一个`Ani`父类和一个`Cat`子类，以及一个`Animal`接口，在子类中通过重写接口的eat方法来实现猫吃饭的功能。

在main方法中，我们创建了一个cat对象，通过文件流的形式来**将对象写入到磁盘中实现持久性存储**，这个写入的过程就是序列化的过程。

反序列化的过程是从文件`obj`中读取输入流，然后通过`ObjectInputStream`将输入流中的字节码反序列化为对象，最后通过`ois.readObject()`将对象恢复为类的实例。

`readObject()`是干什么吃的呢？

我们知道，在php序列化的过程中，会判断是否有`__sleep()`魔术方法，如果存在这个魔术方法，会先执行这个方法，反序列`unserialize()`的时候先执行的是`__wakeup()`魔术方法。

java同理，`readObject()`=`__wakeup()`，还有一个`writeObject()`=`__sleep()`，这两个方法默认是可以不写的，我在上面的代码中重写了`readObject()`方法，通过自定义的`writeObject()`和`readObject()`方法可以允许用户控制序列化的过程，比如可以在序列化的过程中动态改变序列化的数值。

那么写到这里差不多就明了了，`cat`对象在反序列化的时候会自动自动调用`readObject()`方法，导致执行命令。

但是你肯定会问，真正开发的时候谁会这么写啊，这不是故意写bug吗？确实，开发人员不会这么写，但是在重写`readObject()`方法时会写一些正常的操作，我们这个时候就要提到反射了，关于更多java反序列化的问题请移步 [深入分析Java的序列化与反序列化](https://www.hollischuang.com/archives/1140)。

在java中，反序列化很大部分是通过反射来构造pop链。

## 反射
什么是反射？反射之中包含了一个「反」字，所以想要解释反射就必须先从「正」开始解释。

我们先来看一段代码
```java
fanshe testObj = new fanshe();
testObj.setPrice(5);
```
很简单，就是通过new创建了一个`fanshe`类的对象`testObj`，这是[正射]。在这个实例化的过程中，我们需要知道类名，那么实际开发中如果我们不确定类名的话就没办法`new`一个实例了，为此java搞了一个反射出来。

所以反射就是在运行时才知道要操作的类是什么，并且可以在运行时获取类的完整构造，并调用对应的方法，来看例子
```java
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

public class fanshe {
    private String name;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }


    public static void main(String[] args) throws Exception {
        //正常的调用
        fanshe testObj = new fanshe();
        testObj.setName("tom");
        System.out.println("Obj name:" + testObj.getName());
        //使用反射调用
        Class clz = Class.forName("fanshe");
        Method setNameMethod = clz.getMethod("setName", String.class);
        Constructor testConstructor = clz.getConstructor();
        Object testObj1 = testConstructor.newInstance();
        setNameMethod.invoke(testObj1, "tom");
        Method getNameMethod = clz.getMethod("getName");
        System.out.println("Obj name:" + getNameMethod.invoke(testObj1));
    }
}
```
在这段代码中我们使用了两种方式来创建实例，第一种就是正常的new，第二种是使用反射来创建，我们主要看反射部分的。

首先使用`Class.forName()`来加载`fanshe`类，然后通过`getMethod()`来拿到`fanshe`类下的`setName`的方法和参数，通过`getConstructor()`拿到类的完整构造，通过`testConstructor.newInstance()`创建新实例，也就是new一个对象，最后通过`setNameMethod.invoke(testObj1, "tom")`来调用`testObj`对象的`setName()`方法赋值为"tom"。

两种方法的运行结果是一样的。

再来捋一下，正射是直接new，反射是invoke回调。个人理解，反射等同于php中的回调函数。

更多反射相关移步 [大白话说Java反射：入门、使用、原理](https://www.cnblogs.com/chanshuyi/p/head_first_of_reflection.html)




**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**