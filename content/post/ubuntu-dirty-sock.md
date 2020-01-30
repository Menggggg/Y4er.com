---
title: "Ubuntu Dirty Sock 本地权限提升"
date: 2019-02-16T14:55:14+08:00
draft: false
categories: ['漏洞复现']
tags: ['CVE','ubuntu']
---

在2019年1月，由于snapd API中的错误，多个版本的Ubuntu被发现本地权限提升漏洞。

<!--more-->

## 漏洞原因

默认情况下，Ubuntu附带了snapd，但是如果安装了这个软件包，任何发行版都应该可利用。运行以下命令，如果你`snapd`是2.37.1或更高，你是安全的。

```bash
$ snap version
snap    2.34.2
snapd   2.34.2
series  16
ubuntu  16.04
kernel  4.15.0-29-generic
```

![](https://y4er.com/img/uploads/20190509169857.jpg)

## 影响版本

- Ubuntu 18.10
- Ubuntu 18.04 LTS
- Ubuntu 16.04 LTS
- Ubuntu 14.04 LTS

## 漏洞利用

poc链接：https://github.com/initstring/dirty_sock

### 方法一

先在[Ubuntu SSO](https://login.ubuntu.com/)创建账号，然后本地生成密钥：

```bash
ssh-keygen -t rsa -C "<you email>"
```

![](https://y4er.com/img/uploads/20190509167767.jpg)

然后把当前用户下`/.ssh/`目录下的`id_rsa.pub`（公钥）拷到你账户的[ssh-keys](https://login.ubuntu.com/ssh-keys)中。

![](https://y4er.com/img/uploads/20190509168919.jpg)

执行第一个poc

```bash
python3 dirty_sockv1.py -u "you@yourmail.com" -k "id_rsa的路径"
```

![](https://y4er.com/img/uploads/20190509164951.jpg)

出现错误，因为没有开启ssh服务。

```bash
sudo apt install openssh-server
```

重新执行下

![](https://y4er.com/img/uploads/20190509166652.jpg)

如果成功，`sudo -i`即可获取root权限。

### 方法二

直接执行poc

```bash
python3 ./dirty_sockv2.py
```

![](https://y4er.com/img/uploads/20190509169281.jpg)

如果成功，会创建一个账号密码都为`dirty_sock`的用户，su命令切换过去，然后通过sudo就可以切换为root了。

如果遇到了`No passwd entry for user 'dirty_sock'`的问题，则查看下图中的任务进度，等到doing任务执行完之后再进行尝试，如果仍不行，请使用方法一。

![](https://y4er.com/img/uploads/20190509169720.jpg)

## 参考链接

https://usn.ubuntu.com/3887-1/

https://wiki.ubuntu.com/SecurityTeam/KnowledgeBase/SnapSocketParsing

https://github.com/initstring/dirty_sock