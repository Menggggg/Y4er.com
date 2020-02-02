---
title: "搜书大师去启动屏广告小记"
date: 2019-07-02T14:56:03+08:00
draft: false
tags: ['app','reverse']
categories: ['APP相关']
---

前几天手机上用的很舒服的搜书大师，被自动更新了...

<!--more-->

那么更新后迎来的就是满屏的广告，我是真的服。

启动电脑吧！去广告的apk链接在文后。

## 反编译

AndroidKiller反编译拿到smali源代码。

名称：搜书大师

包名：com.flyersoft.seekbooks

入口：com.flyersoft.WB.SplashActivity

版本信息：Ver：v16.7(160701) SDK：16 TargetSDK：26

启动屏的广告就是程序入口，在com.flyersoft.WB.SplashActivity中。

![](https://y4er.com/img/uploads/20190702151102.png)

smali的代码像屎一样，我们用dex2jar来转换成java代码看。

## java源码

将apk改名为zip，然后用压缩软件打开后把classes.dex拖出来放到dex2jar的文件夹下。

运行命令`d2j-dex2jar.bat classes.dex --force`然后生成了classes-dex2jar.jar这个新文件

然后用jd-gui打开新生成的文件看到源代码。

定位到文件

![](https://y4er.com/img/uploads/20190702150917.png)

## 去广告思路

先来谈谈我是怎么定位到调用广告的代码片段的：在启动屏中有关键字`跳过`，全局搜索就能定位到片段。

然后搜书大师的代码经过了混淆，命名乱七八糟，那么为了提高效率我们需要先来了解一下安卓开发的生命周期。

![](https://y4er.com/img/uploads/20190702151649.png)

程序会按照图上的流程来走，那么首先就是`onCreate()`方法。

```java
protected void onCreate(Bundle paramBundle)
{
    e.a(new Object[] { "=Splash:onCreate" });
    super.onCreate(paramBundle);
    paramBundle = SeekBooksApplication.a;
    if ((paramBundle != null) && (paramBundle.contains("UnsatisfiedLinkError")))
    {
        ...省略...
    }
    setContentView(2131427359);
    this.b = ((ViewGroup)findViewById(2131297135));
    this.d = ((AlphaImageView)findViewById(2131297136));
    this.e = ((AlphaImageView)findViewById(2131296361));
    this.c = ((TextView)findViewById(2131297117));
    a(0);
    c();
    this.g = System.currentTimeMillis();
    if (getIntent().getBooleanExtra("showBookCover", false))
    {
        ...省略...
    }
    this.h = getIntent().getBooleanExtra("directShow", false);
    ActivityMain.h = d();
    if ((!this.h) && ((e.va) || (!ActivityMain.a())))
    {
        a();
        return;
    }
    a(this, this.b, this.c, "1106419620", "8090057339034822", this, 0);
}
```

可以发现多次调用`a()`方法，而`a`又有好几种重载。

我在这直接说下我的几种方法

### finish()

让广告的Activity直接退出，但是这样有bug，会导致启动的时候需要点两次才能正常启动。

### 替换他的广告id

经过我多次编译测试

```java
a(this, this.b, this.c, "1106419620", "8090057339034822", this, 0);
```

里面的两个string参数应该是传的广告联盟的id和key，那么我们把他改成错误的就拉不出来广告了。

这种方法没有bug，完美。

### 更改广告的加载时间

在`onADTick()`方法中，广告时间是由下面的代码控制的，稍加修改就行了。

```java
public void onADTick(long paramLong)
{
    StringBuilder localStringBuilder = new StringBuilder();
    localStringBuilder.append("SplashADTick ");
    localStringBuilder.append(paramLong);
    localStringBuilder.append("ms");
    Log.i("MR2", localStringBuilder.toString());
    a(Math.round((float)paramLong / 1000.0F));
}
```

`paramLong`是取得`System.currentTimeMillis()`是5

那么我们可以将被除数1000.0F改大一点，让他`Math.round()`之后为0就可以了。

## 更改smali

我用的是第二种方法，更改掉他的广告id和key

`SplashActivity.smali`1060行

```c
const-string v4, "1106419620"

const-string v5, "8090057339034822"
```

改为

```c
const-string v4, "0"

const-string v5, "0"
```

保存

## 重新编译

之前用AndroidKiller反编译之后重新编译为apk是一直报错

```
>brut.androlib.AndrolibException: brut.androlib.AndrolibException: brut.common.BrutException: could not exec (exit code = 1): 
...
APK 编译失败，无法继续下一步签名!
```

然后我就用apktool重新来了一遍

```bash
C:\Users\Y4er\Downloads>java -jar apktool.jar -r d com.flyersoft.seekbooks.apk
I: Using Apktool 2.4.0 on com.flyersoft.seekbooks.apk
I: Copying raw resources...
I: Baksmaling classes.dex...
I: Copying assets and libs...
I: Copying unknown files...
I: Copying original files...
```

注意**-r**参数，已经确认是**-r**参数导致的

修改smali代码之后保存

```bash
C:\Users\Y4er\Downloads>java -jar apktool.jar b com.flyersoft.seekbooks
I: Using Apktool 2.4.0
I: Checking whether sources has changed...
I: Checking whether resources has changed...
I: Building apk file...
I: Copying unknown files/dir...
I: Built apk...

C:\Users\Y4er\Downloads>
```

然后你会在`com.flyersoft.seekbooks\dist`目录下找到你编译好的apk

## 签名

生成签名

```bash
keytool -genkey -keystore bookapk.keystore -keyalg RSA -validity 10000 -alias book
```

给apk签名

```
jarsigner -verbose -keystore bookapk.keystore -signedjar book1.apk book.apk book
```

最后的`book`就是`-alias`后面带的，必须保持一致

然后就能给手机装上你的`book1.apk`来尽情看小说了

链接: https://pan.baidu.com/s/1_j1WNl0nglJ2uY9LU833BA 提取码: 6dvi 

## 写在文后

这篇文章也算是自己对安卓逆向的一篇水文把，主要还是记录一下命令和思路。不过顺手挖了一个短信轰炸，一百多条短信给我炸的懵逼...

顺便记下我谷歌的一些资料。

[吾爱破解-教我兄弟学Android逆向系列课程+附件导航帖](https://www.52pojie.cn/thread-742703-1-1.html)

[apktool参数文档](https://ibotpeaches.github.io/Apktool/documentation/)

[详解Android中Activity的生命周期](https://blog.csdn.net/android_tutor/article/details/5772285)