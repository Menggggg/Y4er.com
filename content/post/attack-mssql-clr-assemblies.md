---
title: "MSSQL使用CLR程序集来执行命令"
date: 2019-10-23T21:26:20+08:00
lastmod: 2019-10-23T21:26:20+08:00
draft: true
tags: []
categories: ['渗透测试']
comment: true
---

使用mssql中的clr程序集来执行命令

<!--more-->

在我们拿到一个mssql的可堆叠注入时，可能第一时间想到的就是使用 `xp_cmdshell` 和 `sp_OACreate` 来执行命令、反弹shell等等，然而很多时候这两个存储过程不是被删就是被拦截，各种各样的因素导致我们不能执行系统命令，本文就来解决这个问题。

# 什么是CLR

CLR微软官方把他称为**公共语言运行时**，从 SQL Server 2005 开始，SQL Server 集成了用于 Microsoft Windows 的 .NET Framework 的公共语言运行时 (CLR) 组件。 这意味着现在可以使用任何 .NET Framework 语言（包括 Microsoft Visual Basic .NET 和 Microsoft Visual C#）来编写存储过程、触发器、用户定义类型、用户定义函数、用户定义聚合和流式表值函数。 

换言之，可以使用CLR导入.net的dll，那么我们可以通过导入我们的恶意dll来使用SQL执行命令。

# WarSQLKit



**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**