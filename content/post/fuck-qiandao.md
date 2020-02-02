---
title: "指点天下Python签到脚本"
date: 2018-12-23T22:44:13+08:00
categories: ['代码片段']
tags: ['code']
---

学校每天晚上让用一个垃圾app签到就寝，没办法，写了个脚本来解放双手。

<!--more-->

## 思路

抓手机app的签到包

## 代码

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author:Y4er

import requests
import json
import hashlib

def getToken(phone,password):
	url = 'http://app.zhidiantianxia.cn/api/Login/pwd'
	headers = {
	'Host': 'app.zhidiantianxia.cn',
	'Content-Type': 'application/x-www-form-urlencoded',
	'User-Agent': 'okhttp/3.10.0'
	}
	params = {
		'phone': phone,
		'password': password,
		'mobileSystem': '8.1.0',
		'appVersion': '1.1.4',
		'mobileVersion': 'MI 6X',
		'deviceToken': '1507bfd3f7ec78ab60e'
	}
	token = requests.post(url,params=params,headers=headers).json()['data']
	return token

def qianDao(phone,token):
	url = 'http://zzrvtc.zhidiantianxia.cn/applets/signin/sign'
	headers = {
		'axy-phone': phone,
		'axy-token': token,
		'Content-Type': 'application/json',
		'user-agent': 'MI 6X(Android/8.1.0) (com.axy.zhidian/1.1.4) Weex/0.18.0 1080x2030',
		'Host': 'zzrvtc.zhidiantianxia.cn'
	}
	payload = {"lat":"34.794349","lng":"113.887287","signInId":1562}
	res = requests.post(url,headers=headers,data=json.dumps(payload)).json()['msg']
	print("手机号:{0} 签到结果:{1}".format(phone,res))

def getPhoneAndPass():
	results = []
	with open('password.txt','r',encoding='utf-8') as f:
		for line in f.readlines():
			line = line.strip('\n')
			phone = line.split('|')[0]
			password = line.split('|')[1]
			m = hashlib.md5()
			m.update(b"axy_" + bytes(password,encoding = "utf8"))
			password = m.hexdigest()
			results.append([phone,password])
		f.close()
	return results

if __name__ == '__main__':

	results = getPhoneAndPass()
	for phone,password in results:
		token = getToken(phone, password)
		qianDao(phone,token)
```

因为前天搞得签到需要自行获取`signInId`，这次更新了下，直接代码获取

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author:Y4er

import requests
import json
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def mailTome():
	# 第三方 SMTP 服务
	mail_host="smtp.ym.163.com"  #设置服务器
	mail_user="smtp@user.com"    #用户名
	mail_pass="smtppassword"   #口令 
	sender = 'service@chabug.org'
	receivers = ['your@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
	message = MIMEText('指点天下签到完毕,请自行查看结果', 'plain', 'utf-8')
	message['From'] = Header("smtp@user.com", 'utf-8')
	message['To'] =  Header("指点天下签到完毕,请自行查看结果", 'utf-8')
	subject = '指点天下签到完毕,请自行查看结果'
	message['Subject'] = Header(subject, 'utf-8')
	try:
	    smtpObj = smtplib.SMTP() 
	    smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
	    smtpObj.login(mail_user,mail_pass)
	    smtpObj.sendmail(sender, receivers, message.as_string())
	    print ("邮件发送成功")
	except smtplib.SMTPException:
	    print ("Error: 无法发送邮件")

def getToken(phone,password):
	url = 'http://app.zhidiantianxia.cn/api/Login/pwd'
	headers = {
	'Host': 'app.zhidiantianxia.cn',
	'Content-Type': 'application/x-www-form-urlencoded',
	'User-Agent': 'okhttp/3.10.0'
	}
	params = {
		'phone': phone,
		'password': password,
		'mobileSystem': '8.1.0',
		'appVersion': '1.1.4',
		'mobileVersion': 'MI 6X',
		'deviceToken': '1507bfd3f7ec78ab60e'
	}
	token = requests.post(url,params=params,headers=headers).json()['data']
	return token

def getsignInId(phone,token):
	url = 'http://zzrvtc.zhidiantianxia.cn/applets/signin/my'
	headers = {
		'axy-phone': phone,
		'axy-token': token,
		'user-agent': 'MI 6X(Android/8.1.0) (com.axy.zhidian/1.1.4) Weex/0.18.0 1080x2030',
		'Host': 'zzrvtc.zhidiantianxia.cn'
	}
	params = {
		'page': '0',
		'size': '10'
	}
	signInId = requests.get(url,headers=headers,params=params).json()['data']['content'][0]['id']
	return signInId

def qianDao(phone,token):
	url = 'http://zzrvtc.zhidiantianxia.cn/applets/signin/sign'
	headers = {
		'axy-phone': phone,
		'axy-token': token,
		'Content-Type': 'application/json',
		'user-agent': 'MI 6X(Android/8.1.0) (com.axy.zhidian/1.1.4) Weex/0.18.0 1080x2030',
		'Host': 'zzrvtc.zhidiantianxia.cn'
	}
	payload = {"lat":"34.794349","lng":"113.887287","signInId":getsignInId(phone,token)}
	res = requests.post(url,headers=headers,data=json.dumps(payload)).json()['msg']
	print("手机号:{0} 签到结果:{1}".format(phone,res))

def getPhoneAndPass():
	results = []
	with open('password.txt','r',encoding='utf-8') as f:
		for line in f.readlines():
			line = line.strip('\n')
			phone = line.split('|')[0]
			password = line.split('|')[1]
			m = hashlib.md5()
			m.update(b"axy_" + bytes(password,encoding = "utf8"))
			password = m.hexdigest()
			results.append([phone,password])
		f.close()
	return results

if __name__ == '__main__':
	results = getPhoneAndPass()
	for phone,password in results:
		token = getToken(phone, password)
		qianDao(phone,token)
	mailTome()
```