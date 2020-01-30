import requests
import re
import os
from datetime import datetime


def now():
    return str(datetime.now().strftime("%Y%m%d%H") + str(datetime.now().microsecond)[-4:])


headers = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
}

proxies = {
    'http': 'socks5://127.0.0.1:1080',
    'https': 'socks5://127.0.0.1:1080',
}

if __name__ == '__main__':
    githubusercontent = r'(!.*(https://.*github.*.png).*\))'
    postdir = './content/post/'
    for post in os.listdir(postdir):
        if post[-2:] == 'md':
            f = open(postdir+post, 'r', encoding='utf8')
            content = f.read()
            f.close()
            if 'user-images.githubusercontent.com' in content:
                print("[!]found {} exist github image".format(post))
                imgs = re.findall(githubusercontent, content)
                for markdown, img in imgs:
                    # 保存图片
                    imgcontent = requests.get(img, headers=headers, proxies=proxies).content
                    filename = 'img/uploads/' + now() + '.png'
                    with open('static/'+filename, 'wb+') as mark:
                        mark.write(imgcontent)
                        print("[!]save {} image {} over".format(post, filename))
                    # 替换文章markdown链接
                    markdown_str = markdown
                    markdown = markdown.replace(
                        img, 'https://y4er.com/' + filename)
                    content = content.replace(markdown_str, markdown)
                    with open(postdir+post, 'w', encoding='utf8') as file:
                        file.write(content)
                print("[!]replace {} over".format(post))
            else:
                print("[*]{} not found github image".format(post))
