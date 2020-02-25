---
title: "C# Shellcode Loader"
date: 2020-02-25T23:46:39+08:00
draft: false
tags:
- shellcode
series:
-
categories:
- 渗透测试
- 代码片段
---

静态免杀
<!--more-->

## 项目地址

https://github.com/Y4er/shellcode-loader

## shellcode loader

csharp 5632 byte xor 静态免杀,过Windows defender.

## 免杀效果

测试于 2020/2/24 23:30

http://r.virscan.org/language/zh-cn/report/5583273543afd24b387833e86c22a798 0/49

![](https://y4er.com/img/uploads/20200226002209.png)

https://www.virustotal.com/gui/file/08d02c54c910ad9d26d4f42aa59f785aad9468c3687be4d2b3575c689c18102c/detection 2/69

![](https://y4er.com/img/uploads/20200226002776.png)

## 使用方法

cobalt strike 或者 metasploit 生成 csharp 的 payload ,先使用 enloader 加密,再使用 loader.exe 执行.

**注意不同位数的 payload 请使用相应的 loader**
**注意不同位数的 payload 请使用相应的 loader**
**注意不同位数的 payload 请使用相应的 loader**
**注意不同位数的 payload 请使用相应的 loader**
**编译时请注意针对目标机器的.net版本对应编译**
**编译时请注意针对目标机器的.net版本对应编译**
**编译时请注意针对目标机器的.net版本对应编译**
**编译时请注意针对目标机器的.net版本对应编译**

1. enloader.exe 生成加密payload
2. cmd /c loader.exe payload


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**