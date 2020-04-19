#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import re
import os,sys,platform
from datetime import datetime


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
}

proxies = {
    'http': 'socks5://127.0.0.1:1080',
    'https': 'socks5://127.0.0.1:1080',
}

def now():
    return str(datetime.now().strftime("%Y%m%d%H") + str(datetime.now().microsecond)[-4:])

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        print("------------------- mkdir -------------------")
        os.makedirs(path)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        domain = "https://y4er.com/"
    else:
        domain = sys.argv[1]
    print("------------------- start -------------------")
    githubusercontent = r'(!\[.*\]\((.*githubusercontent.*\.(gif|png|jpg)).*\))'
    qiita = r'(!\[.*\]\((.*qiita-image-store.*amazonaws.*\.(gif|png|jpg)).*\))'
    postdir = './content/post/'
    try:
        for post in os.listdir(postdir):
            if post[-2:] == 'md':
                f = open(postdir+post, 'r', encoding='utf8')
                content = f.read()
                f.close()
                imgs = None
                if 'githubusercontent.com' in content:
                    imgs = re.findall(githubusercontent, content)
                elif 'qiita-image-store' in content:
                    imgs = re.findall(qiita, content)
                else:
                    print("[*][{}] \t not found.".format(post))
                    continue
                for markdown, img, suffix in imgs:
                    # 保存图片
                    imgcontent = None
                    if platform.system() == "Windows" and os.environ['USERNAME'] == 'Y4er':
                        imgcontent = requests.get(img, headers=headers, proxies=proxies).content
                    else:
                        imgcontent = requests.get(img, headers=headers).content
                    mkdir("static/img/uploads/")
                    filename = 'img/uploads/' + now() +'.'+ suffix
                    with open('static/'+filename, 'wb+') as mark:
                        mark.write(imgcontent)
                        print("[!][{}] \t {} \t {}".format(post,img, filename))
                    # 替换文章markdown链接
                    markdown_str = markdown
                    markdown = markdown.replace(img, domain + filename)
                    content = content.replace(markdown_str, markdown)
                    with open(postdir+post, 'w', encoding='utf8') as file:
                        file.write(content)
        print("------------------- over! -------------------")
    except Exception as e:
        print("------------------- error -------------------")
        print("[x]error: {}".format(e))
        print("------------------- error -------------------")
