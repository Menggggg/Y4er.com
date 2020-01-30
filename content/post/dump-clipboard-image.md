---
title: "使用powershell导出剪切板图片"
date: 2019-07-30T08:57:16+08:00
draft: false
tags: ['powershell']
categories: ['瞎折腾']
---

怎么导出QQ截图的图片到指定位置呢？powershell来帮你

<!--more-->
我是一个喜欢记笔记写文章的菜鸡，而使用markdown记笔记最蛋疼的就是图片的存储问题，刚开始使用的是[PicGo](https://github.com/Molunerfinn/PicGo)，可以直接截图然后粘贴就是markdown的图片语法，但是使用的是第三方的图床。

而我自己原来用第三方图床也就是新浪的图床，后来新浪一波防盗链把我搞得~~骂骂咧咧~~措手不及，想了想，图片还是掌握在自己手中比较好，于是就有了本文。

## 借助PicGo搞插件？

刚好自己搭了一个图床http://static.chabug.org/ ，想着参考PicGo的思路，自己写一个插件，然后实现截图 快捷键 粘贴 一套操作，岂不是美滋滋？后来看到了PicGo需要装nodejs才能用插件，再想想nodejs的依赖和蛇皮语法，直接实力劝退，不了了之。

## python自己造轮子

国光师傅写过一篇 [Python 编写一个免费简单的图床上传工具二](https://www.sqlsec.com/2018/06/img.html) ，但是编写思路是采用`xclip`来操作`ubuntu`下的剪切板，而苦逼windows党不配这样操作。随卒。

## 参考PicGo自己撸

研究到这一步，实际上最关键的问题在于win下怎么去导出剪切板中的图片。百度谷歌了很多文章，发现都是牛头不照马尾，在此过程中我把PicGo作者的博客翻烂了，发现PicGo作者获取剪切板的图片采用的是命令行调用 https://github.com/PicGo/PicGo-Core/blob/dev/src/utils/clipboard/windows10.ps1 这个脚本。在第一行定义了最关键的项目 https://github.com/octan3/img-clipboard-dump 。这个就是我们想要的东西！

那么我们的问题就解决了！

看下**dump-clipboard-png.ps1**

```powershell
Add-Type -Assembly PresentationCore
$img = [Windows.Clipboard]::GetImage()
if ($img -eq $null) {
    Write-Host "Clipboard contains no image."
    Exit
}

$fcb = new-object Windows.Media.Imaging.FormatConvertedBitmap($img, [Windows.Media.PixelFormats]::Rgb24, $null, 0)
$file = "{0}\clipboard-{1}.png" -f [Environment]::GetFolderPath('MyPictures'),((Get-Date -f s) -replace '[-T:]','')
Write-Host ("`n Found picture. {0}x{1} pixel. Saving to {2}`n" -f $img.PixelWidth, $img.PixelHeight, $file)

$stream = [IO.File]::Open($file, "OpenOrCreate")
$encoder = New-Object Windows.Media.Imaging.PngBitmapEncoder
$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($fcb))
$encoder.Save($stream)
$stream.Dispose()

& explorer.exe /select,$file
```

首先获取剪切板的图片，如果没图片就exit，然后新建一个位图对象，新建一个file变量当作文件名，从环境变量中拿到MyPictures的路径，然后写入图片。

相对我们想实现的效果还差一步就是直接向剪切板写入markdown格式的图片链接。我在这放出来我修改之后的脚本。(注意修改路径)

```powershell
Add-Type -Assembly PresentationCore
$img = [Windows.Clipboard]::GetImage()
if ($img -eq $null) {
    Write-Host "Clipboard contains no image."
    Exit
}

$fcb = new-object Windows.Media.Imaging.FormatConvertedBitmap($img, [Windows.Media.PixelFormats]::Rgb24, $null, 0)
$filename = ((Get-Date -f s) -replace '[-T:]','')
$file = "E:/work/myblog/static/img/uploads/{0}.png" -f $filename
Write-Host ("`n Found picture. {0}x{1} pixel. Saving to {2}`n" -f $img.PixelWidth, $img.PixelHeight, $file)

$stream = [IO.File]::Open($file, "OpenOrCreate")
$encoder = New-Object Windows.Media.Imaging.PngBitmapEncoder
$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($fcb))
$encoder.Save($stream)
$stream.Dispose()

$str =  "![{0}](/img/uploads/{1}.png)" -f $filename,$filename
[Windows.Clipboard]::SetText($str)
```

然后把`dump-clipboard-png.cmd`改名为`png.cmd`和`png.ps1`放到环境变量里，截图，cmd运行`png`，那么你的剪切板就会写入一个markdown格式的图片咯。并且图片保存在了你的本地。
## 进一步操作
到现在我们基本的效果已经实现了，不过还是差一点，怎么去实现按下快捷键就导出图片到我们指定的位置呢？参考国光师傅的代码已经写的很清楚了。

https://github.com/sqlsec/imageMD/blob/master/imageMD.py

**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**