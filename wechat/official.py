#encoding=utf-8
from xml.dom import minidom
import collections
import time
from hashlib import sha1


def kv2element(key, value, doc):
    ele = doc.createElement(key)
    if isinstance(value, str) or isinstance(value, unicode):
        data = doc.createCDATASection(value)
        ele.appendChild(data)
    else:
        text = doc.createTextNode(str(value))
        ele.appendChild(text)
    return ele


def fields2elements(tupleObj, enclose_tag=None, doc=None):
    if enclose_tag:
        xml = doc.createElement(enclose_tag)
        for key in tupleObj._fields:
            ele = kv2element(key, getattr(tupleObj, key), doc)
            xml.appendChild(ele)
        return xml
    else:
        return [kv2element(key, getattr(tupleObj, key), doc)
                for key in tupleObj._fields]


class WxRequest(object):

    def __init__(self, xml):
        doc = minidom.parseString(xml)
        params = [ele for ele in doc.childNodes[0].childNodes
                  if isinstance(ele, minidom.Element)]
        for param in params:
            if param.childNodes:
                text = param.childNodes[0]
                self.__dict__.update({param.tagName: text.data})
            else:
                self.__dict__.update({param.tagName: ''})


class WxResponse(object):

    def __init__(self, request):
        self.CreateTime = long(time.time())
        self.FuncFlag = 0
        self.ToUserName = request.FromUserName
        self.FromUserName = request.ToUserName

    def as_xml(self):
        doc = minidom.Document()
        xml = doc.createElement('xml')
        doc.appendChild(xml)
        xml.appendChild(kv2element('ToUserName', self.ToUserName, doc))
        xml.appendChild(kv2element('FromUserName', self.FromUserName, doc))
        xml.appendChild(kv2element('CreateTime', self.CreateTime, doc))
        xml.appendChild(kv2element('MsgType', self.MsgType, doc))
        contents = self.content_nodes(doc)
        if isinstance(contents, list) or isinstance(contents, tuple):
            for content in contents:
                xml.appendChild(content)
        else:
            xml.appendChild(contents)
        xml.appendChild(kv2element('FuncFlag', self.FuncFlag, doc))
        return doc.toxml()


WxMusic = collections.namedtuple('WxMusic',
                                 'Title Description MusicUrl HQMusicUrl')
WxArticle = collections.namedtuple('WxArticle',
                                   'Title Description PicUrl Url')
WxLink = collections.namedtuple('WxLink', 'Title Description Url')


class WxTextResponse(WxResponse):

    MsgType = 'text'

    def __init__(self, text, request):
        super(WxTextResponse, self).__init__(request)
        self.text = text

    def content_nodes(self, doc):
        return kv2element('Content', self.text, doc)


class WxMusicResponse(WxResponse):

    MsgType = 'music'

    def __init__(self, music, request):
        super(WxMusicResponse, self).__init__(request)
        self.music = music

    def content_nodes(self, doc):
        return fields2elements(self.music, 'Music', doc)


class WxNewsResponse(WxResponse):

    MsgType = 'news'

    def __init__(self, articles, request):
        super(WxNewsResponse, self).__init__(request)
        if isinstance(articles, list) or isinstance(articles, tuple):
            self.articles = articles
        else:
            self.articles = [articles]

    def content_nodes(self, doc):
        count = kv2element('ArticleCount', len(self.articles), doc)
        articles = doc.createElement('Articles')
        for article in self.articles:
            articles.appendChild(fields2elements(article, 'item', doc))
        return count, articles


class WxApplication(object):

    UNSUPPORT_TXT = u'暂不支持此类型消息'
    WELCOME_TXT = u'你好！感谢您的关注！'
    SECRET_TOKEN = None

    def is_valid_params(self, params):
        timestamp = params.get('timestamp', '')
        nonce = params.get('nonce', '')
        signature = params.get('signature', '')
        echostr = params.get('echostr', '')

        sign_ele = [self.token, timestamp, nonce]
        sign_ele.sort()
        if(signature == sha1(''.join(sign_ele)).hexdigest()):
            return True, echostr
        else:
            return None

    def process(self, auth_params, xml=None, token=None):
        self.token = token if token else self.SECRET_TOKEN
        assert self.token is not None

        ret = self.is_valid_params(auth_params)

        if not ret:
            return 'invalid request'
        if not xml:
            # 微信开发者设置的调用测试
            return ret[1]

        req = WxRequest(xml)
        self.wxreq = req
        func = self.handler_map().get(req.MsgType, None)
        if not func:
            return WxTextResponse(self.UNSUPPORT_TXT, req)
        self.pre_process()
        rsp = func(req)
        self.post_process(rsp)
        return rsp.as_xml()

    def on_text(self, text):
        return WxTextResponse(self.UNSUPPORT_TXT, text)

    def on_link(self, link):
        return WxTextResponse(self.UNSUPPORT_TXT, link)

    def on_image(self, image):
        return WxTextResponse(self.UNSUPPORT_TXT, image)

    def on_location(self, loc):
        return WxTextResponse(self.UNSUPPORT_TXT, loc)

    def on_event(self, event):
        if event.Event == 'subscribe':
            return self.on_subscribe(event)
        elif event.Event == 'unsubscribe':
            return self.on_unsubscribe(event)
        else:
            return self.on_click(event)

    def on_subscribe(self, sub):
        return WxTextResponse(self.WELCOME_TXT, sub)

    def on_unsubscribe(self, unsub):
        return WxTextResponse(self.UNSUPPORT_TXT, unsub)

    def on_click(self, click):
        return WxTextResponse(self.UNSUPPORT_TXT, click)

    def handler_map(self):
        return {
            'text': self.on_text,
            'link': self.on_link,
            'image': self.on_image,
            'location': self.on_location,
            'event': self.on_event,
        }

    def pre_process(self):
        pass

    def post_process(self, rsp):
        pass
