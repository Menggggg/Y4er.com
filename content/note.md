---
title: "笔记"
enableComment: false
hideToc : true
---


## 打包

```bash
"C:/Program Files/7-Zip/7z.exe" a D:\upload\2020\7\13\www.zip C:\inetpub\wwwroot\ -r -x!*.zip -x!*.7z -v200m
Rar.exe a -r -v500m -X*.rar -X*.zip sst.rar D:\wwwroot\sq\
tar -zcvf /tmp/www.tar.gz --exclude=upload --exclude *.png --exclude *.jpg --exclude *.gif --exclude *.mp* --exclude *.flv --exclude *.m4v --exclude *.pdf --exclude *.*tf --ignore-case /www/ | split -b 100M -d -a - www.tar.gz.
```

```php
<?php
function addFileToZip($path,$zip){
    $handler=opendir($path); //打开当前文件夹由$path指定。
    while(($filename=readdir($handler))!==false){
        if($filename != "." && $filename != ".."){//文件夹文件名字为'.'和‘..’，不要对他们进行操作
            if(is_dir($path."/".$filename)){// 如果读取的某个对象是文件夹，则递归
                addFileToZip($path."/".$filename, $zip);
            }else{ //将文件加入zip对象
                $zip->addFile($path."/".$filename);
            }
        }
    }
    @closedir($path);
}
$zip=new ZipArchive();

if($zip->open('/tmp/backup.zip', ZipArchive::OVERWRITE)=== TRUE){
    addFileToZip('/www/wwwroot/', $zip); //调用方法，对要打包的根目录进行操作，并将ZipArchive的对象传递给方法
    $zip->close(); //关闭处理的zip文件
    echo 1;
}
```