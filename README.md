# Wechat SDK
An UnOfficial WeChat python SDK. For the primal version, the SDK support the `Official Account` only.

Author: [@jeff_kit](http://twitter.com/jeff_kit)

# Getting start

Before getting start, you should have learnt what wechat official account is, and have registed acccount. if you don't, click [here](http://mp.weixin.qq.com) to learn more.

Now, we are going to create an echo robot, the robot will send back what you sent to the official account. ps. I use Django web framework for the example.

## 1. install Wechat sdk

	git clone git@github.com:jeffkit/wechat.git
	cd wechat
	python setup.py install

## 2. setup your web server
You can use any webframework you like for the response server, just set it up and have it run. 

Your offical account should turn into develop mode, and config the interface url and token.

For example, start a Django project and config a view to interactive with Official account.
	
	django-admin.py startproject demo
	cd demo
	python manage.py startapp echo
	
modify demo/settings.py, append echo to INSTALLED_APPS:

	INSTALLED_APPS = (
	    'django.contrib.auth',
    	'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'django.contrib.sites',
	    'django.contrib.messages',
	    'django.contrib.staticfiles',
	    'echo',
	)
add view for official account interface. edit echo/views.py:
	
	from django.http import HttpResponse

	def wechat(request):
		return HttpResponse('hello wechat')

config urls.py:
	
	urlpatterns = patterns('',
    	url(r'^wechat/', 'echo.views.wechat'),
	)


## 3.Warm up
Let's get familar with Official account objects.
### WxClient
WxClient use to check if the request is valid.

	from wechat.official import WxClient
	cli = WxClient('your official account token')  # init with you official token
	status, content = cli.is_valid_params(params)  # params is a dict, which represent the http querty params.

### WxRequest
A WxRequest instance represent an incoming wechat message. One message is piece of xml. WxRequest map elements of xml to it's own attributes, so you can access the message directly. for more information, see [this link](http://mp.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E6%8E%A5%E5%8F%A3%E6%8C%87%E5%8D%97#.E6.B6.88.E6.81.AF.E6.8E.A8.E9.80.81).
	
	from wechat.official import WxRequest
	wxreq = WxRequest(req.body)  # init with a xml string. The req is a django HttpRequest instance
	wxreq.MsgType  # text, image, location, event, link
	wxreq.Content  # if it's a text message

### WxResponse
A WxResponse instance represent and outgoing wechat message. One message is piece of xml too. there are now three types of Outgoing message: text, link, news. so, there are three WxResponse subclasses for you. 

#### WxTextResponse
	from wechat.official import WxTextResponse
	resp = WxTextResponse("hello world", wxreq).as_xml()

#### WxMusicResponse

	from wechat.official import WxMusicResponse, WxMusic
	resp = WxMusicResponse(WxMusic(Title="hey jude", Description="2012 London", 
									MusicUrl="http://yourhost.com/jude.mp3", 
									HQMusicUrl="http://yourhost.com/jude.hd.mp3"), wxreq).as_xml()

#### WxNewsResponse
	from wechat.official import WxNewsResponse, WxArticle
	resp = WxNewsResponse([WxArticle(Title="iPhone 6 is here!",
							Description="It is not a joke",
							Url="http://jeffkit.info",
							PicUrl="http://jeffkit.info/avatar.jpg")], wxreq).as_xml()

## 4.Build the Robot

The robot's code is simple. edit the echo/views.py:

	from django.http import HttpResponse
	from wechat.official import WxRequest, WxTextResponse
	from wechat.official import WxClient


	def wechat(request):
    	cli = WxClient("your official account token")
	    ret = cli.is_valid_params(request.GET)  # validate the request
	    if not ret:
    	    return HttpResponse('invalid request')
	    if request.method == 'GET':
	        return HttpResponse(ret[1])  # for interface validation
	    else:
    	    req = WxRequest(request.body)
        	if req.MsgType == 'text':
            	return HttpResponse(WxTextResponse(req.Content, req).as_xml())
	        elif req.MsgType == 'event' and req.Event == 'subscribe':
	            return HttpResponse(WxTextResponse('welcome to echo bot!',
    	                                           req).as_xml())
        	else:
            	return HttpResponse(WxTextResponse('support text only',
                	                               req).as_xml())

## 5.deploy 
That's all. deploy you web application, and have fun!

