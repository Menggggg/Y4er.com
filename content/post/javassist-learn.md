---
title: "Javassist 学习"
date: 2020-04-20T11:21:05+08:00
draft: false
tags:
- java
series:
-
categories:
- 代码审计
---

由上文引出的Javassist学习
<!--more-->

## 前言
Java中所有的类都被编译为class文件来运行，在编译完class文件之后，类不能再被显示修改，而`Javassist`就是用来处理编译后的class文件，它可以用来修改方法或者新增方法，并且不需要深入了解字节码，还可以生成一个新的类对象。

## 创建class
创建maven项目，引入Javassist库

```xml
<!-- https://mvnrepository.com/artifact/javassist/javassist -->
        <dependency>
            <groupId>javassist</groupId>
            <artifactId>javassist</artifactId>
            <version>3.12.1.GA</version>
        </dependency>
```
使用javassist来创建一个Person类

```java
package com.y4er.learn;

import javassist.*;


public class CreateClass {
    public static void main(String[] args) throws Exception {
        // 获取javassist维护的类池
        ClassPool pool = ClassPool.getDefault();

        // 创建一个空类com.y4er.learn.Person
        CtClass ctClass = pool.makeClass("com.y4er.learn.Person");

        // 给ctClass类添加一个string类型的字段为name
        CtField name = new CtField(pool.get("java.lang.String"), "name", ctClass);

        // 设置private权限
        name.setModifiers(Modifier.PRIVATE);

        // 初始化name字段为zhangsan
        ctClass.addField(name, CtField.Initializer.constant("zhangsan"));

        // 生成get、set方法
        ctClass.addMethod(CtNewMethod.getter("getName",name));
        ctClass.addMethod(CtNewMethod.setter("setName",name));

        // 添加无参构造函数
        CtConstructor ctConstructor = new CtConstructor(new CtClass[]{}, ctClass);
        ctConstructor.setBody("{name=\"xiaoming\";}");
        ctClass.addConstructor(ctConstructor);

        // 添加有参构造
        CtConstructor ctConstructor1 = new CtConstructor(new CtClass[]{pool.get("java.lang.String")}, ctClass);
        ctConstructor1.setBody("{$0.name=$1;}");
        ctClass.addConstructor(ctConstructor1);

        // 创建一个public方法printName() 无参无返回值
        CtMethod printName = new CtMethod(CtClass.voidType, "printName", new CtClass[]{}, ctClass);
        printName.setModifiers(Modifier.PUBLIC);
        printName.setBody("{System.out.println($0.name);}");
        ctClass.addMethod(printName);

        // 写入class文件
        ctClass.writeFile();
        ctClass.detach();
    }
}
```

执行完之后生成了Person.class
![image.png](https://y4er.com/img/uploads/20200424097089.png)

## 使用方法
从上文的demo中可以看到部分使用方法，在javassist中CtClass代表的就是类class，ClassPool就是CtClass的容器，ClassPool维护了所有创建的CtClass对象，需要注意的是当CtClass数量过大会占用大量内存，需要调用CtClass.detach()释放内存。

ClassPool重点有以下几个方法：
1. getDefault() 单例获取ClassPool
2. appendClassPath() 将目录添加到ClassPath
3. insertClassPath() 在ClassPath插入jar
4. get() 根据名称获取CtClass对象
5. toClass() 将CtClass转为Class 一旦被转换则不能修改
6. makeClass() 创建新的类或接口

更多移步官方文档：http://www.javassist.org/html/javassist/ClassPool.html

CtClass需要关注的方法：
1. addConstructor() 添加构造函数
2. addField() 添加字段
3. addInterface() 添加接口
4. addMethod​() 添加方法
5. freeze() 冻结类使其不能被修改
6. defrost() 解冻使其能被修改
7. detach() 从ClassPool中删除类
8. toBytecode() 转字节码
9. toClass() 转Class对象
10. writeFile() 写入.class文件
11. setModifiers​() 设置修饰符

移步：http://www.javassist.org/html/javassist/CtClass.html

CtMethod继承CtBehavior，需要关注的方法：
1. insertBefore 在方法的起始位置插入代码
2. insterAfter 在方法的所有 return 语句前插入代码
3. insertAt 在指定的位置插入代码
4. setBody 将方法的内容设置为要写入的代码，当方法被 abstract修饰时，该修饰符被移除
5. make 创建一个新的方法

更多移步：http://www.javassist.org/html/javassist/CtBehavior.html

在setBody()中我们使用了`$`符号代表参数

```java
// $0代表this $1代表第一个传入的参数 类推
printName.setBody("{System.out.println($0.name);}");
```

## 使用CtClass生成对象
上文我们生成了一个ctClass对象对应的是Person.class，怎么调用Person类生成对象、调用属性或方法？

三种方法：
1. 反射方式调用
2. 加载class文件
3. 通过接口

### 反射调用

```java
// 实例化
Object o = ctClass.toClass().newInstance();
Method setName = o.getClass().getMethod("setName", String.class);
setName.invoke(o,"Y4er");
Method printName1 = o.getClass().getMethod("printName");
printName1.invoke(o);
```
### 加载class文件

```java
ClassPool pool = ClassPool.getDefault();
pool.appendClassPath("E:\\code\\java\\javassist-learn\\com\\y4er\\learn");
CtClass PersonClass = pool.get("com.y4er.learn.Person");
Object o = PersonClass.toClass().newInstance();
//接下来反射调用
```
### 通过接口调用
新建一个接口IPerson，将Person类的方法全部抽象出来

```java
package com.y4er.learn;

public interface IPerson {
    String getName();

    void setName(String name);

    void printName();
}
```

```java
ClassPool pool = ClassPool.getDefault();
pool.appendClassPath("E:\\code\\java\\javassist-learn\\com\\y4er\\learn\\Person.class");

CtClass IPerson = pool.get("com.y4er.learn.IPerson");
CtClass Person = pool.get("com.y4er.learn.Person");
Person.defrost();
Person.setInterfaces(new CtClass[]{IPerson});

IPerson o = (IPerson) Person.toClass().newInstance();
o.setName("aaa");
System.out.println(o.getName());
o.printName();
```
将Person类实现IPerson接口，然后创建实例时直接强转类型，就可以直接调用了。

## 修改现有的类
javassist大多数情况下用户修改已有的类，比如常见的日志切面。我仍然使用Person类来讲解：

```java
//
// Source code recreated from a .class file by IntelliJ IDEA
// (powered by Fernflower decompiler)
//

package com.y4er.learn;

public class Person implements IPerson {
    private String name = "zhangsan";

    public String getName() {
        return this.name;
    }

    public void setName(String var1) {
        this.name = var1;
    }

    public Person() {
        this.name = "xiaoming";
    }

    public Person(String var1) {
        this.name = var1;
    }

    public void printName() {
        System.out.println(this.name);
    }
}

```
此时我想在printName方法的执行效果如下

```text
------ printName start ------
xiaoming
------ printName  over ------
```
写一下代码：

```java
pool.appendClassPath("E:\\code\\java\\javassist-learn\\com\\y4er\\learn\\Person.class");
CtClass Person = pool.get("com.y4er.learn.Person");
Person.defrost();

CtMethod printName1 = Person.getDeclaredMethod("printName", null);
printName1.insertBefore("System.out.println(\"------ printName start ------\");");
printName1.insertAfter("System.out.println(\"------ printName  over ------\");");

Object o = Person.toClass().newInstance();
Method printName2 = o.getClass().getMethod("printName");
printName2.invoke(o, null);
```
很轻松实现了切面
![image.png](https://y4er.com/img/uploads/20200424092505.png)


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**