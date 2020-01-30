---
title: "Thinkphp错误使用Upload类导致getshell"
date: 2019-10-23T20:58:17+08:00
draft: false
tags: []
categories: ['代码审计']
series:
- ThinkPHP
---

对tp的错误使用导致的。

<!--more-->

本文来自RoarCTF的 [simple_upload](https://github.com/berTrAM888/RoarCTF-Writeup-some-Source-Code/tree/master/Web/simple_upload) 

源代码

```php
<?php
namespace Home\Controller;

use Think\Controller;

class IndexController extends Controller
{
    public function index()
    {
        show_source(__FILE__);
    }
    public function upload()
    {
        $uploadFile = $_FILES['file'] ;

        if (strstr(strtolower($uploadFile['name']), ".php") ) {
            return false;
        }

        $upload = new \Think\Upload();// 实例化上传类
        $upload->maxSize  = 4096 ;// 设置附件上传大小
        $upload->allowExts  = array('jpg', 'gif', 'png', 'jpeg');// 设置附件上传类型
        $upload->rootPath = './Public/Uploads/';// 设置附件上传目录
        $upload->savePath = '';// 设置附件上传子目录
        $info = $upload->upload() ;
        if(!$info) {// 上传错误提示错误信息
          $this->error($upload->getError());
          return;
        }else{// 上传成功 获取上传文件信息
          $url = __ROOT__.substr($upload->rootPath,1).$info['file']['savepath'].$info['file']['savename'] ;
          echo json_encode(array("url"=>$url,"success"=>1));
        }
    }
} 
```

源码中限制了$_FILES[file]文件名不能是.php文件，得想办法绕过。 **$upload->allowExts** 并不是 **Think\Upload** 类的正确用法，所以 **allowexts** 后缀名限制是无效的。 

熟悉 **thinkphp** 的应该知道， **upload()** 函数不传参时为多文件上传，整个 **$_FILES** 数组的文件都会上传保存。

题目中只限制了 **$_FILES[file]** 的上传后缀，也只给出 **$_FILES[file]** 上传后的路径，那我们上传多文件就可以绕过 **php** 后缀限制。

![20191023211558](https://y4er.com/img/uploads/20191023211558.png)

 下一步就是要知道上传后的php文件名。看一下 **think\upload** 类是怎么生成文件名的

 https://github.com/berTrAM888/RoarCTF-Writeup-some-Source-Code/blob/master/Web/simple_upload/docker/html/ThinkPHP/Library/Think/Upload.class.php#L27 
```php
'saveName'     => array('uniqid', ''), //上传文件命名规则，[0]-函数名，[1]-参数，多个参数使用数组 
```

可以看到使用的是uniqid来生成文件名，同时上传txt文件跟php文件，txt上传后的文件名跟php的文件名非常接近。我们只需要构造Burp包，遍历爆破txt文件名后三位 **0-9 a-f** 的文件名，就能猜出php的文件名。

 把 **$upload->allowExts** 替换成 **$upload->exts** 就可以修补这个漏洞了。 



**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**