---
title: "Hello World"
date: 2018-12-08T12:32:42+08:00
categories: ['瞎折腾']
tags: ['hugo']
---

本博客采用Hugo+GitHub搭建，生命在于折腾，记录学习和生活。

先在此记录下我自己踩过的坑

搭建方法自行移步：http://www.gohugo.org/doc/ 不在此赘述。
<!--more-->

## 主题选用

~~选择恐惧症，感觉哪个主题都好看，最后选用了[maupassant](https://github.com/Y4er/maupassant-hugo)。这个主题还算比较符合我的要求。贴上我修改完主题之后的[Github](https://github.com/Y4er/maupassant-hugo/)，欢迎issue、pr、star。~~

换主题了，用的[even](https://github.com/olOwOlo/hugo-theme-even)，还算好看。

## 更换字体

主题自带的字体太费眼了，改了下`style.css`

## 添加灯箱

采用lightgallery

hugo采用的是markdown来渲染文章，而图片在前端渲染出来的都是img标签，这没办法去控制他渲染的标签class，但是经过我不懈百度，各种看文档，发现hugo支持模板中采用正则表达式查找替换。那么就很简单了。我直接贴上我写的代码。

在主题的`layouts/_default/single.html`中默认是

```html
<div class="post-content">
{{ .Content }}
</div>
```

我通过正则去查找替换了渲染之后的img标签和结构，而且顺手就给图片加上了`class="lazyload"`来实现我们的懒加载效果

```html
<div class="post-content">
                            {{ $reAltIn := "<img src=\"([^\"]+)\" alt=\"([^\"]+)?\" />" }}
                            {{ $reAltOut := "<figure><img src=\"/images/ring.svg\" data-sizes=\"auto\" data-src=\"$1\" alt=\"$2\" class=\"lazyload\"><figcaption class=\"image-caption\">$2</figcaption></figure>" }}
                            {{ $altContent := .Content | replaceRE $reAltIn $reAltOut | safeHTML }}
                            {{ $reAltTitleIn := "<img src=\"([^\"]+)\" alt=\"([^\"]+)?\" title=\"([^\"]+)?\" />" }}
                            {{ $reAltTitleOut :=  "<figure><img src=\"/images/ring.svg\" data-src=\"$1\" data-sizes=\"auto\" alt=\"$2\" title=\"$3\" class=\"lazyload\"><figcaption class=\"image-caption\">$2</figcaption></figure>" }}
                            {{ $finalContent := $altContent | replaceRE $reAltTitleIn $reAltTitleOut | safeHTML }}
                            {{ $finalContent }}
                        </div>
```



## 添加懒加载

https://github.com/aFarkas/lazysizes 贴上文档

## 添加文章版权

修改`layouts/partials/related.html`

```html
 <blockquote>
 <div class="post-copyright">
     {{ with .Site.Params.author }} 
     <p class="copyright-item">
         <span>本文作者:</span>
         <span>{{ . }} </span>
         </p>
     {{ end }}
 
      {{ with .Permalink }} 
     <p class="copyright-item">
             <span>本文链接:</span>
             <a href={{ . }}>{{ . }}</a>
     </p>
     {{ end }}
 
      <p class="copyright-item lincese">
     	<span>许可协议:</span>
     	<a rel="license" href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" title="Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)">署名-非商业性使用-禁止演绎 4.0 国际</a>
     </p>
 
      <p>
     	<b>转载请保留原文链接及作者。</b>
     </p>
 </div>
 </blockquote>
```



## 添加GoogleAnalytics

hugo本身就支持GoogleAnalytics，直接在config.toml中配置

```toml
GoogleAnalytics = "UA-555555555-1"
```

这个配置最好放在配置文件的上方，要不然不会生效。**坑**

## 修改摘要方式

原主题不支持`<!--more-->`的方式显示摘要，发现是因为他在模板中写死了

```html
{{ .Content | markdownify | truncate 100 }}
```

显示内容的前100个字符。

我们需要改成

```html
{{ .Summary | markdownify | safeHTML }}
```

这样就支持`<!--more-->`的方式显示摘要了，当然如果不加，会自动截取前70个字符作为摘要。

## 添加shortcode

bilibili

```toml
{{ if .IsNamedParams }}
<div class="bilibili" style="position: relative; padding-bottom: 56.25%; padding-top: 30px; height: 0; overflow: hidden;">
    <iframe src="//player.bilibili.com/player.html?aid={{ .Get "av"}}" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>

{{ else }}

<div class="bilibili" style="position: relative; padding-bottom: 56.25%; padding-top: 30px; height: 0; overflow: hidden;">
    <iframe src="//player.bilibili.com/player.html?aid={{ .Get 0}}" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>

{{ end }}
```

网易云音乐

```html
{{/* DEFAULTS */}}
{{ $auto := "0" }}

{{ if .IsNamedParams }}

  <iframe
    class="music163"
    frameborder="no"
    border="0"
    marginwidth="0"
    marginheight="0"
    width="330"
    height="86"
    src="//music.163.com/outchain/player?type=2&id={{ .Get "id" }}&auto={{ or (.Get "auto") $auto }}&height=66">
  </iframe>

{{ else }}

  <iframe
    class="music163"
    frameborder="no"
    border="0"
    marginwidth="0"
    marginheight="0"
    width="330"
    height="86"
    src="//music.163.com/outchain/player?type=2&id={{ .Get 0 }}&auto={{ if isset .Params 1 }}{{ .Get 1 }}{{ else }}{{ $auto }}{{ end }}&height=66">
  </iframe>

{{ end }}
```

腾讯视频

```html
{{ if .IsNamedParams }}
<div class="qqvideo" style="position: relative; padding-bottom: 56.25%; padding-top: 30px; height: 0; overflow: hidden;">
		<iframe frameborder="0" src="//v.qq.com/txp/iframe/player.html?vid={{ .Get "vid"}}" allowFullScreen="true"  style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
</div>

{{ else }}

<div class="qqvideo" style="position: relative; padding-bottom: 56.25%; padding-top: 30px; height: 0; overflow: hidden;">
		<iframe frameborder="0" src="//v.qq.com/txp/iframe/player.html?vid={{ .Get 0 }}" allowFullScreen="true"  style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
</div>

{{ end }}
```



踩坑结束。