# encoding=utf-8
from xml.dom import minidom
import collections
import time
from hashlib import sha1
import requests
import simplejson as json


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

    def __init__(self, xml=None):
        if not xml:
            return
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

    def on_voice(self, voice):
        return WxTextResponse(self.UNSUPPORT_TXT, voice)

    def on_video(self, video):
        return WxTextResponse(self.UNSUPPORT_TXT, video)

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
        if getattr(self, 'handlers'):
            return self.handlers
        return {
            'text': self.on_text,
            'link': self.on_link,
            'image': self.on_image,
            'voice': self.on_voice,
            'video': self.on_video,
            'location': self.on_location,
            'event': self.on_event,
        }

    def pre_process(self):
        pass

    def post_process(self, rsp):
        pass


class APIError(object):

    def __init__(self, code, msg):
        self.code = code
        self.message = msg


class WxApi(object):

    API_PREFIX = 'https://api.weixin.qq.com/cgi-bin/'

    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self._access_token = None
        self.expires_in = time.time()

    @property
    def access_token(self):
        if (not self._access_token) or (
                self._access_token and time.time() > self.expires_in):
            self._access_token = None
            print 'get access token again'
            token, err = self.get_access_token()
            if not err:
                self._access_token = token['access_token']
                self.expires_in = time.time() + token['expires_in']
                print 'expires in %d' % self.expires_in
                return self._access_token
            else:
                return None
        return self._access_token

    def get_access_token(self):
        params = {'grant_type': 'client_credential', 'appid': self.appid,
                  'secret': self.appsecret}
        return self._get('token', params)

    def _process_response(self, rsp):
        if rsp.status_code != 200:
            return None, APIError(rsp.status_code, 'http error')
        try:
            content = rsp.json()
        except:
            return None, APIError(99999, 'invalid rsp')
        if 'errcode' in content and content['errcode'] != 0:
            return None, APIError(content['errcode'], content['errmsg'])
        return content, None

    def _get(self, path, params=None):
        if not params:
            params = {}
        if self._access_token:
            params['access_token'] = self._access_token
        rsp = requests.get(self.API_PREFIX + path, params=params)
        return self._process_response(rsp)

    def _post(self, path, data, ctype='json'):
        headers = {'Content-type': 'application/json', 'Accept': 'text/json'}
        path = self.API_PREFIX + path + '?access_token=' + self.access_token
        if ctype == 'json':
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        rsp = requests.post(path, data=data, headers=headers)
        return self._process_response(rsp)

    def user_info(self, user_id, lang='zh_CN'):
        return self._get('user/info', {'openid': user_id, 'lang': lang})

    def followers(self, next_id=''):
        return self._get('user/get', {'next_openid': next_id})

    def upload_media(self, mtype, filepath):
        # TODO, 对各种类型的文件作合法性校验
        path = self.API_PREFIX + 'media/upload?access_token=' \
            + self._access_token + '&type=' + mtype
        rsp = requests.post(path, files={'media': open(filepath, 'rb')})
        return self._process_response(rsp)

    def download_media(self,  media_id, to_path):
        rsp = requests.get(self.API_PREFIX + 'media/get',
                           {'media_ia': media_id})
        if rsp.status_code == 200:
            save_file = open(to_path, 'wb')
            save_file.write(rsp.content)
            save_file.close()
            return {'errcode': 0}, None
        else:
            return None, APIError(rsp.status_code, 'http error')

    def send_message(self, to_user, msg_type, content):
        func = {'text': self.send_text,
                'image': self.send_image,
                'voice': self.send_voice,
                'video': self.send_video,
                'music': self.send_music,
                'news': self.send_news}.get(msg_type, None)
        if func:
            return func(to_user, content)
        return None, None

    def send_text(self, to_user, content):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'text',
                           'text': {'content': content}})

    def send_image(self, to_user, media_id):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'image',
                           'image': {'media_id': media_id}})

    def send_voice(self, to_user, media_id):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'voice',
                           'voice': {'media_id': media_id}})

    def send_music(self, to_user, music):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'music',
                           'music': music})

    def send_video(self, to_user, video):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'video',
                           'video': video})

    def send_news(self, to_user, news):
        return self._post('message/custom/send',
                          {'touser': to_user, 'msgtype': 'news',
                           'news': news})

    def create_group(self, name):
        return self._post('groups/create',
                          {'group': {'name': name}})

    def groups(self):
        return self._get('groups/get')

    def update_group(self, group_id, name):
        return self._post('groups/update',
                          {'group': {'id': group_id, 'name': name}})

    def group_of_user(self, user_id):
        return self._get('groups/getid', {'openid': user_id})

    def move_user_to_group(self, user_id, group_id):
        return self._post('groups/members/update',
                          {'openid': user_id, 'to_groupid': group_id})

    def create_menu(self, menus):
        return self._post('menu/create', menus, ctype='text')

    def get_menu(self):
        return self._get('menu/get')

    def delete_menu(self):
        return self._get('menu/delete')
