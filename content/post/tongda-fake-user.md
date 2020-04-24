---
title: "通达OA前台任意用户伪造登录分析"
date: 2020-04-24T09:35:02+08:00
draft: false
tags:
- 通达OA
series:
-
categories:
- 代码审计
---

通达OA又爆洞了
<!--more-->
## 环境
通达OA历史版本下载：https://cdndown.tongda2000.com/oa/2019/TDOA11.4.exe

解密工具：https://pan.baidu.com/s/1c14V6pi

## 复现
![image.png](https://y4er.com/img/uploads/20200424096776.png)

![image.png](https://y4er.com/img/uploads/20200424095006.png)

拿到UID为1及管理员的SESSION直接登陆
![image.png](https://y4er.com/img/uploads/20200424098163.png)

## 分析
![image.png](https://y4er.com/img/uploads/20200424095012.png)
在logincheck_code.php中UID可控，当UID为1时，用户默认为admin管理员。
![image.png](https://y4er.com/img/uploads/20200424098519.png)
在其后180行左右将信息保存到SESSION中。那么只要绕过了18行的exit()就可以了。

```php
$CODEUID = $_POST["CODEUID"];
$login_codeuid = TD::get_cache("CODE_LOGIN" . $CODEUID);
if (!isset($login_codeuid) || empty($login_codeuid)) {
	$databack = array("status" => 0, "msg" => _("参数错误！"), "url" => "general/index.php?isIE=0");
	echo json_encode(td_iconv($databack, MYOA_CHARSET, "utf-8"));
	exit();
}
```
login_codeuid 从redis缓存中`TD::get_cache()`获取`"CODE_LOGIN" . $CODEUID`，搜索下可不可控
![image.png](https://y4er.com/img/uploads/20200424090859.png)

跟进`general\login_code.php`

```php
<?php

include_once "inc/utility_all.php";
include_once "inc/utility_cache.php";
include_once "inc/phpqrcode.php";
$codeuid = $_GET["codeuid"];
$login_codeuid = TD::get_cache("CODE_LOGIN" . $codeuid);
$tempArr = array();
$login_codeuid = (preg_match_all("/[^a-zA-Z0-9-{}\/]+/", $login_codeuid, $tempArr) ? "" : $login_codeuid);

if (empty($login_codeuid)) {
	$login_codeuid = getUniqid();
}

$databack = array("codeuid" => $login_codeuid, "source" => "web", "codetime" => time());
$dataStr = td_authcode(json_encode($databack), "ENCODE");
$dataStr = "LOGIN_CODE" . $dataStr;
$data = QRcode::text($dataStr, false, "L", 4);
$data = serialize($data);
if (($data != "") && ($data != NULL)) {
	if (unserialize($data)) {
		$matrixPointSize = 1.5;
		QRimage::png(unserialize($data), false, $matrixPointSize);
	}
	else {
		$im = imagecreatefromstring($data);

		if ($im !== false) {
			header("Content-Type: image/png");
			imagepng($im);
		}
	}
}

TD::set_cache("CODE_LOGIN" . $login_codeuid, $login_codeuid, 120);
$databacks = array("status" => 1, "code_uid" => $login_codeuid);
echo json_encode(td_iconv($databacks, MYOA_CHARSET, "utf-8"));
echo "\r\n\r\n\r\n";

?>
```
当`$login_codeuid`为空时会`getUniqid()`生成一个存入redis缓存并且在最后echo出来。所以我们可以通过直接get请求`general\login_code.php`拿到`CODEUID`
![image.png](https://y4er.com/img/uploads/20200424093835.png)
使用之前的CODEUID即可绕过if条件的exit()。

## 总结
很蠢的错误。通达真的不考虑抛弃全局变量覆盖吗？

拓展下的话，尝试寻找下通过get_cache()获取的变量影响到sql语句什么的。另外不同版本可能有一些不一样，比如11.3根本没走redis验证- -。


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**