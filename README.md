# 微信公众号Python-SDK

作者: [@jeff_kit](http://twitter.com/jeff_kit)

本SDK支持微信公众号以及企业号的上行消息及OAuth接口。本文档及SDK假设使用者已经具备微信公众号开发的基础知识，及有能力通过微信公众号、企业号的文档来查找相关的接口详情。


## 1. 安装

### pip
	
	pip install wechat

### 源码安装

	git clone git@github.com:jeffkit/wechat.git
	cd wechat
	python setup.py install
	
	
## 2. 用户上行消息处理框架

对于微信用户在公众号内发送的上行消息，本sdk提供了一个微型处理框架，开发者只需继承wechat.official.WxApplication类, 实现各种消息对应的方法，然后把该类与自己熟悉的web框架结合起来使用即可。

WxApplication内部会实现请求的合法性校验以及消息的分发等功能，还对上行消息对行了结构化，开发者把精力放到业务逻辑的编写即可。

下面先看看一个WxApplication的示例代码：

	from wechat.official import WxApplication, WxTextResponse, WxMusic,\
		WxMusicResponse
	
	class WxApp(WxApplication):
	
    	SECRET_TOKEN = 'test_token'
	    WECHAT_APPID = 'wx1234556'
	    WECHAT_APPSECRET = 'sevcs0j'

    	def on_text(self, text):
        	return WxTextResponse(text.Content, text)
        
       	def on_image(self, image):
       		return WxTextResponse(image.Url, image)

	    def on_click(self, click):
    	    return WxMusicResponse(
    	    	WxMusic(Title='hey jude',
    	    			Description='dont make it bad',
    	    			PicUrl='http://heyjude.com/logo.png',
    	    			Url='http://heyjude.com/mucis.mp3'), 
    	    	click)
    	
需要配置几个类参数，几个参数均可在公众号管理后台的开发者相关页面找到：
	
- SECRET_TOKEN: 微信公众号回调的TOKEN
- APP_ID: 微信公众号的应用ID
- ENCODING_AES_KEY: (可选)，加密用的SECRET，如您的公众号未采取加密传输，不需填。
- UNSUPPORT_TXT:(可选)，收到某种不支持类型的消息时自动响应给用户的文本消息。
- WELCOME_TXT:(可选), 新关注时默认响应的文本消息。

然后，您需要逐一实现WxApplication的各个on_xxxx函数。不同类型的上行消息及事件均有对应的on_xxx函数

### on_xxx函数


所有的on_xxx函数列举如下：

- on_text, 响应用户文本
- on_link，响应用户上行的链接
- on_image，响应用户上行图片
- on_voice，响应用户上行语音
- on_video，响应用户上行视频
- on_location，响应用户上行地理位置
- on_subscribe，响应用户关注事件
- on_unsubscribe，响应用户取消关注事件
- on_click，响应用户点击自定义菜单事件
- on_scan，响应用户扫描二维码事件
- on_location_update，响应用户地理位置变更事件
- on_view，响应用户点击自定义菜单访问网页事件
- on_scancode_push
- on_scancode_waitmsg
- on_pic_sysphoto
- on_pic_photo_or_album
- on_pic_weixin
- on_location_select

on_xxx函数的定义如下：

	def on_xxx(self, req):
		return WxResponse()

on_xxx函数，接受一个WxRequest参数req，返回一个WxResponse的子类实例。

#### WxRequest

req是一个代表用户上行消息的WxRequest实例。其属性与消息的XML属性一一对应，不同的消息有几个相同的属性：

- ToUserName
- FromUserName
- CreateTime
- MsgType
- MsgId

不同的消息类型对应有各自的属性，属性名与消息的xml标签名保一致。如MsgType为text的的req，有一个Content属怀，而MsgType为image的req，则有PicUrl及MediaId两个属性。更多消息详情请查看微信公众号[官方文档](http://mp.weixin.qq.com/wiki/10/79502792eef98d6e0c6e1739da387346.html)。

#### WxResponse

on_xxx函数需要返回一个WxResponse的子类实例。WxResponse的子类有：

##### WxTextResponse, 文本消息

 	WxTextResponse("hello", req)
	
##### WxImageResponse, 图片消息

	WxImageResponse(WxImage(MediaId='xxyy'),req)
	
##### WxVoiceResponse, 语音消息

	WxVoiceResponse(WxVoice(MediaId='xxyy'),req)
	
##### WxVideoResponse, 视频消息

	WxVideoResponse(WxVideo(MediaId='xxyy', Title='video', Description='test'),req)
	
##### WxMusicResponse, 音乐消息

	WxMusicResponse(WxMusic(Title='hey jude', 
		Description='dont make it bad', 
		PicUrl='http://heyjude.com/logo.png', 
		Url='http://heyjude.com/mucis.mp3'), req)

##### WxNewsResponse, 图文消息

	WxNewsResponse(WxArticle(Title='test news', 
		Description='this is a test', 
		Picurl='http://smpic.com/pic.jpg', 
		Url='http://github.com/jeffkit'), req)
##### WxEmptyResponse, 无响应
	
	WxEmptyResponse(req)

### 在web中使用WxApplication

编写完成WxApplication后，将其应用于您熟悉的web框架当中即可。关键是在web程序里调用WxApplication的process方法，后续的事情交给SDK来处理。

#### process(params, xml)

WxApplication的process函数，接受两个必须的参数：

- params, url参数字典，需要解析自微信回调的url的querystring。
- xml, 微信回调时post的xml内容。

process最后返回一串文本(xml或空字符串)。


下面以Django为例说明，实现一个微信回调的功能(view)，利用上面示例代码中的WxApp：
	
	from django.http import HttpResponse

	def wechat(request):
		app = WxApp()
		result = app.process(request.GET, request.body)
		return HttpResponse(result)

配置 urls.py:
	
	urlpatterns = patterns('',
    	url(r'^wechat/', 'myapp.views.wechat'),
	)

OK.就这么多，WxApplication本身与web框架无关，不管你使用哪个Framework都可以享受到它带来的便利。

## 3. OAuth API

OAuth API目前仅支持下列常用接口：

- 发送消息
- 用户管理
- 自定义菜单管理
- 多媒体上传下载
- 二维码

其他接口拟于未来的版本中支持，同时欢迎大家来增补。

