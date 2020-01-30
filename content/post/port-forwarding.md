---
title: "各种端口转发工具的使用方法"
date: 2019-07-23T10:40:37+08:00
draft: false
tags: ['portforward']
categories: ['渗透测试']
---

科普转发工具的用法

<!--more-->

本文主要介绍几种内网中常用的端口转发以代理的几种姿势。阅读本文前请看到每个阶段的网络环境，对理解本文有重要帮助。

我们在这里用三台实验机

client ：172.16.1.1

attacker：172.16.2.18 172.16.1.144

server：172.16.2.8

我们的目的是从我们的client就可以连接上 win2008 的远程桌面。

## LCX

lcx.exe有两大功能

1. 端口转发 slave和listen成对使用
2. 端口映射 tran

### slave listen

server执行

```powershell
lcx.exe -s 172.16.2.18 5555 127.0.0.1 3389
```

这句话的意思是把本机的3389端口转发到172.16.2.18的5555端口

在attacker执行

```powershell
lcx.exe -l 5555 4444
```

这句是把本机5555接收到的数据转发到本机的4444端口

现在就可以在client上 mstsc 连接attacker的4444端口，或者直接在attacker中连接`127.0.0.1:4444`

整个数据的流向

client <-> 4444 attacker 5555 <->3389 server

### tran

如果server中有防火墙不允许3389出站，那么可以用tran将3389映射到防火墙允许出站的端口，比如53端口。

server执行

```powershell
lcx -t 53 172.16.2.8 3389
```

直接连接server:53

数据流向

server 3389 <-> 53 <->attacker

## Earthworm

EW 是一套便携式的网络穿透工具，具有 SOCKS v5 服务架设和端口转发两大核心功能。该工具能够以 “正向”、“反向”、“多级级联” 等方式打通一条网络隧道，直达网络深处，用蚯蚓独有的手段突破网络限制，给防火墙松土。工具包中提供了多种可执行文件，以适用不同的操作系统，Linux、Windows、MacOS、Arm-Linux 均被包括其内, 强烈推荐使用。官方地址：http://rootkiter.com/EarthWorm

该工具共有 6 种命令格式：ssocksd、rcsocks、rssocks、lcx_slave、lcx_listen、lcx_tran

### 正向socks5

attacker:

```powershell
ew -s ssocksd -l 1080
```

client:

```powershell
C:\Users\Y4er>curl http://172.16.2.8 -x socks5://172.16.1.144:1080
I am 172.16.2.8
```

数据流向

client <-> attacker 1080 <-> server

### 反向socks5

attacker执行，监听8888端口转发到1080端口

```powershell
ew -s rcsocks -l 1080 -e 8888
```

在server中启动socks5服务，并且反弹到attacker的8888端口

```powershell
ew -s rssocks -d 172.16.2.18 -e 8888
```

在client中就可以用这个代理了

```powershell
curl http://172.16.2.8 -x socks5://172.16.1.144:1080
```

client <-> attacker 1080 <-> attacker 8888 <-> server

### 端口转发

这里着重说一下`lcx_tran`、`lcx_listen`、`lcx_slave`的用法。

案例一：

在attacker中启动一个socks5代理，端口是9999

```powershell
ew -s ssocksd -l 9999
```

**然后通过`lcx_tran`来转发9999到1080**

```powershell
ew.exe -s lcx_tran -l 1080 -f 127.0.0.1 -g 9999
```

然后就能从client访问server了

```powershell
curl http://172.16.2.8 -x socks5://172.16.1.144:1080
```

实际上还是用attacker搭了一个socks5代理，**这个例子主要说的是lcx_tran的使用方法**。

 案例二：
attacker:

```powershell
ew.exe -s lcx_listen -l 1234 -e 8888
```
server: 
```powershell
ew.exe -s lcx_slave -d 192.168.1.100 -e 8888 -f 127.0.0.1 -g 3389
```

原理和lcx一样

### 多级级联

假如我们当前的网络环境如下

```powershell
a: 192.168.1.100
b: 192.168.1.101,10.0.0.1
c: 10.0.0.2,172.16.0.1
d: 172.16.0.2
```
那么我们怎么做才能让a访问到d的资源呢？

ew提供了多级级联

```powershell
a: ew.exe -s lcx_listen -l 1080 -e 8888
b: ew.exe -s lcx_slave -d 192.168.1.100 -e 8888 -f 10.0.0.2  -g 9999
c: ew.exe -s lcx_tran -l 9999 -f 172.16.0.2 -g 3389
```

数据流向

a 1080 <-> a 8888 <-> b 9999 <-> c 9999 <-> d 3389

## netsh

> netsh(Network Shell) 是一个windows系统本身提供的功能强大的网络配置命令行工具。
>
> https://docs.microsoft.com/zh-cn/windows-server/networking/technologies/netsh/netsh-contexts

netsh添加规则

```powershell
netsh interface portproxy set v4tov4 listenaddress=172.16.1.144  listenport=4444 connectaddress=172.16.2.8 connectport=3389
```

将172.16.1.144的4444端口映射到172.16.2.8的3389

查看规则

```powershell
C:\Users\Administrator\Desktop>netsh interface portproxy show all

侦听 ipv4:                 连接到 ipv4:

地址            端口        地址            端口
--------------- ----------  --------------- ----------
172.16.1.144    4444        172.16.2.8      3389
```

删除规则

```powershell
netsh interface portproxy delete v4tov4 listenaddress=172.16.1.144 listenport=4444
```

关闭防火墙

```powershell
netsh firewall set opmode disabled
```

## sSocks

> sSocks是一个socks代理工具套装，可用来开启socks代理服务，支持socks5验证，支持IPV6和UDP，并提供反向socks代理服务，即将远程计算机作为socks代理服务端，反弹回本地，极大方便内网的渗透测试。官方地址：http://sourceforge.net/projects/ssocks/

使用方法类似ew

attacker

```bash
rcsocks -l 4444 -p 5555 -vv
```

server

```bash
rssocks –vv –s 172.16.2.8:5555
```

client

```bash
curl 172.16.2.8 -x socks5://172.16.1.144:4444
```

## portfwd

> portfwd是一款强大的端口转发工具，支持TCP，UDP，支持IPV4--IPV6的转换转发。

portfwd是meterpreter中内置的功能，也有单机exe版本的https://github.com/rssnsj/portfwd

较为简单，不举例了。

---

以上我们将的都是win平台下的tcp端口转发，接下来我们看Linux平台下的。

改变下我们当前的网络结构

win10 client:172.16.1.1

kali attacker:172.16.1.141 172.16.2.19

win2008 server:172.16.2.8

我们现在的目的是通过kali的转发来使client连接到server的3389

---

## socat

> socat是一个多功能的网络工具，名字来由是” Socket CAT”，可以看作是netcat的N倍加强版，socat的官方网站：http://www.dest-unreach.org/socat/

socat的主要特点就是在两个数据流之间建立通道，且支持众多协议和链接方式：`ip, tcp, udp, ipv6, pipe,exec,system,open,proxy,openssl,socket`等。

### 端口转发

```bash
socat TCP4-LISTEN:4444 TCP4:172.16.2.8:3389
```

client连接172.16.1.141:4444就是连接server的3389

如果需要使用并发连接，则加一个fork,如下:

```
socat TCP4-LISTEN:4444,fork TCP4:172.16.2.8:3389
```

### 端口映射

在一个NAT环境，如何从外部连接到内部的一个端口呢？只要能够在内部运行socat就可以了。

attacker
```bash
socat tcp-listen:1234 tcp-listen:3389 
```
server
```bash
socat tcp:172.16.2.19:1234 tcp:172.16.2.8:3389
```
这样，你外部机器上的3389就映射在内部网172.16.2.8的3389端口上。

mstsc 172.16.1.141:3389

参考倾旋师傅的文章https://payloads.online/tools/socat 

---

我们再来看看基于ssh协议的端口转发，环境跟上文一样。

---

## ssh

> SSH 会自动加密和解密所有 SSH 客户端与服务端之间的网络数据。但是，SSH 还同时提供了一个非常有用的功能，这就是端口转发。它能够将其他 TCP 端口的网络数据通过 SSH 链接来转发，并且自动提供了相应的加密及解密服务。
>
> https://www.ibm.com/developerworks/cn/linux/l-cn-sshforward/index.html

 SSH 端口转发能够提供两大功能：

1. 加密 SSH Client 端至 SSH Server 端之间的通讯数据。
2. 突破防火墙的限制完成一些之前无法建立的 TCP 连接。

参数：

-C Enable compression. 

压缩数据传输。

-N Do not execute a shell or command. 
不执行脚本或命令，通常与-f连用。

-g Allow remote hosts to connect to forwarded ports. 
在-L/-R/-D参数中，允许远程主机连接到建立的转发的端口，如果不加这个参数，只允许本地主机建立连接。

-f Fork into background after authentication. 
后台认证用户/密码，通常和-N连用，不用登录到远程主机。

### 本地端口转发

所谓本地端口转发，就是**将发送到本地端口的请求，转发到目标端口**。这样，就可以通过访问本地端口，来访问目标端口的服务。

client(win10有ssh命令)

```bash
ssh -CfNg -L 4444:172.16.2.8:3389 root@172.16.1.141
```

此时client去连接localhost:4444就是server:3389

### 远程端口转发

所谓远程端口转发，就是**将发送到远程端口的请求，转发到目标端口**。这样，就可以通过访问远程端口，来访问目标端口的服务。

client

```bash
ssh -CfNg -R 4444:172.16.1.1:3389 root@172.16.1.141
```

此时client去连接localhost:4444就是server:3389

### 本地转发与远程转发的对比

首先，SSH 端口转发自然需要 SSH 连接，而 SSH 连接是有方向的，从 SSH Client 到 SSH Server 。而我们的应用也是有方向的，比如需要连接远程桌面时，远程桌面自然就是 Server 端，我们应用连接的方向也是从应用的 Client 端连接到应用的 Server 端。如果这两个连接的方向一致，那我们就说它是本地转发。而如果两个方向不一致，我们就说它是远程转发。

总的思路是通过将 TCP 连接转发到 SSH 通道上以解决数据加密以及突破防火墙的种种限制。对一些已知端口号的应用，例如 Telnet/LDAP/SMTP，我们可以使用本地端口转发或者远程端口转发来达到目的。

如果你对ssh转发还有问题的话，推荐阅读以下文章

- [SSH隧道与端口转发及内网穿透](https://blog.creke.net/722.html)
- [实战 SSH 端口转发](https://www.ibm.com/developerworks/cn/linux/l-cn-sshforward/index.html)
- [玩转SSH端口转发](https://blog.fundebug.com/2017/04/24/ssh-port-forwarding/)

### ssh架设socks代理

client

```bash
ssh -qTfnN -D 1080 172.16.1.141
```

client上架设socks，端口1080，数据通过attacker转发到内网。

## dnscat2
> dnscat2 是一款基于 DNS 协议的代理隧道。不仅支持端口转发，另外还有执行命令，文件传输等功能。其原理与 DNS Log 类似, 分为直连和中继两种模式, 前者直接连接服务端的 53 端口, 速度快, 但隐蔽性差, 后者通过对所设置域名的递归查询进行数据传输, 速度慢, 但隐蔽性好。

创建一条端口转发

```powershell
(the security depends on the strength of your pre-shared secret!)
This is a command session!

That means you can enter a dnscat2 command such as
'ping'! For a full list of clients, try 'help'.

command (LAPTOP) 1> listen 1234 127.0.0.1:3389
Listening on 0.0.0.0:1234, sending connections to 127.0.0.1:3389
command (LAPTOP) 1> 
```

这个我没有测试，这个参考 @X1r0z 的文章 [dnscat2 tunnel](https://exp10it.cn/dnscat2-tunnel.html)

至于更多用法请参阅 [README.MD](https://github.com/iagox86/dnscat2/blob/v0.07/README.md)

## HTTP/HTTPS隧道

http隧道较为简单，在这里举几个有名的http隧道（或是基于http包装的tcp隧道）

1. https://github.com/sensepost/reGeorg
2. https://github.com/nccgroup/ABPTTS 目前不支持PHP
3. https://github.com/SECFORCE/Tunna
4. https://github.com/sensepost/reDuh

## 如何使用socks代理？

1. shadowsocks
2. sockcap64 windows
3. Proxifier
4. proxychains

## 踩过的坑

1. win2008 远程桌面黑屏鼠标没反应可能是因为你登录的用户已经登录了。
2. 连不上3389需要先关防火墙。
3. socat尽量用fork，不然一次会话结束后就会断。

## 写在文后

文章中的很多东西网上都有，端口转发实际上只要明白原理和数据的流向，就很明了了。

但是对于杀软来说，像lcx这种工具传上去就被杀掉了，所以推荐golang自写端口转发工具，当然你也可以在GitHub找一些少见的自写的端口转发工具来规避杀软。比如https://github.com/tavenli/port-forward

参考链接：

- https://micro8.gitbook.io/micro8/contents#91-100-ke
- [SSH隧道与端口转发及内网穿透](https://blog.creke.net/722.html)
- [实战 SSH 端口转发](https://www.ibm.com/developerworks/cn/linux/l-cn-sshforward/index.html)
- [玩转SSH端口转发](https://blog.fundebug.com/2017/04/24/ssh-port-forwarding/)
- [socat 使用手册](https://payloads.online/tools/socat)
- [Web狗要懂的内网端口转发](https://xz.aliyun.com/t/1862)
- [内网端口转发及穿透](https://hatboy.github.io/2018/08/28/内网端口转发及穿透/)

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**