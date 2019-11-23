# -*- coding: utf-8 -*-
import urllib2,urllib,re,os,string,time,base64,datetime
from urlparse import urlparse
import aes
try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from stats import *
import xbmcplugin,xbmcgui,xbmcaddon
__baseurl__ = 'http://novaplus.nova.cz'
__dmdbase__ = 'http://iamm.uvadi.cz/xbmc/voyo/'
_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
addon = xbmcaddon.Addon('plugin.video.dmd-czech.novaplus')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
__settings__ = xbmcaddon.Addon(id='plugin.video.dmd-czech.novaplus')
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )

#Nacteni informaci o doplnku
__addon__      = xbmcaddon.Addon()
__addonname__  = __addon__.getAddonInfo('name')
__addonid__    = __addon__.getAddonInfo('id')
__cwd__        = __addon__.getAddonInfo('path').decode("utf-8")
__language__   = __addon__.getLocalizedString

def log(msg):
    xbmc.log(("### [%s] - %s" % (__addonname__.decode('utf-8'), msg.decode('utf-8'))).encode('utf-8'), level=xbmc.LOGDEBUG)

def OBSAH():
    addDir('Seriály a pořady','http://novaplus.nova.cz/porady/',5,icon,1)
    addDir('Televizní noviny','http://novaplus.nova.cz/porad/televizni-noviny',2,icon,1)
    addDir('TOP pořady','http://novaplus.nova.cz',9,icon,1)
    addDir('Poslední díly','http://novaplus.nova.cz',8,icon,1)
    addDir('Nejsledovanější','http://novaplus.nova.cz',6,icon,1)
    addDir('Doporučujeme','http://novaplus.nova.cz',7,icon,1)

def HOME_NEJSLEDOVANEJSI(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles b-section-articles-primary my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Nejsledovanější':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_DOPORUCUJEME(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Doporučujeme':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_POSLEDNI(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section b-section-articles my-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'Poslední díly':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title1 = article.h3.getText(" ").encode('utf-8')
                title2 = article.find('span', 'e-text').getText(" ").encode('utf-8')
                title = str(title1) + ' - ' + str(title2)
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,3,thumb,1)

def HOME_TOPPORADY(url,page):
    doc = read_page(url)

    for section in doc.findAll('section', 'b-main-section my-sm-5'):
        if section.div.h3.getText(" ").encode('utf-8') == 'TOP pořady':
            for article in section.findAll('article'):
                url = article.a['href'].encode('utf-8')
                title = article.a['title'].encode('utf-8')
                thumb = article.a.div.img['data-original'].encode('utf-8')
                addDir(title,url,2,thumb,1)

def CATEGORIES(url,page):
    print 'CATEGORIES *********************************' + str(url)
    doc = read_page(url)

    for article in doc.findAll('article'):
        url, title, thumb = None, None, None

        if article.a is not None:
          url = article.a['href'].encode('utf-8')
          title = article.a['title'].encode('utf-8')
          #title = article.a['title'].encode('utf-8') + ' ' + str(url)
          thumb = article.a.div.img['data-original'].encode('utf-8')
          addDir(title,url,2,thumb,1)

def VIDEOLINK(url,name):
    print 'VIDEOLINK *********************************' + str(url)

    doc = read_page(url)

    # nalezeni hlavniho article
    article = doc.find('article', 'b-article b-article-main')

    # pokud hlavni article neexistuje, jsme na specialni strance a prejdeme na odkaz "Cele dily"
    if article is None:
      nav = doc.find('nav', 'sub-nav')
      if nav != None and nav.ul != None:
        for li in nav.ul.findAll('li'):
          if li.a != None and li.a['title'] != None and li.a['title'].encode('utf-8') == 'Celé díly':
            url = li.a['href']
            doc = read_page(url)
            article = doc.find('article', 'b-article b-article-main')

    # pokud stale hlavni article neexistuje, chyba
    if article is None:
      xbmcgui.Dialog().ok("Nova Plus TV Archiv", "Na stránce nenalezena sekce s videi. Program nebude fungovat správně.", url)

    # nazev
    try:
      name = article.find('h3').getText(" ").encode('utf-8')
    except:
      name = 'Jméno pořadu nenalezeno';

    # popis (nemusi byt vzdy uveden)
    try:
      desc = article.find('div', 'e-description').getText(" ").encode('utf-8')
    except:
      desc = ''

    # nalezeni iframe
    main = doc.find('main')
    url = main.find('iframe')['src']
    print ' - iframe src ' + url

    # nacteni a zpracovani iframe
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()

    httpdata   = httpdata.replace("\r","").replace("\n","").replace("\t","")

    thumb = re.compile('<meta property="og:image" content="(.+?)">').findall(httpdata)
    thumb = thumb[0] if len(thumb) > 0 else ''

    renditions = re.compile('renditions: \[(.+?)\]').findall(httpdata)
    if len(renditions) > 0:
      renditions = re.compile('[\"](.+?)[\"]').findall(renditions[0])

    bitrates = re.compile('src = {(.+?)\[(.+?)\]').findall(httpdata);
    if len(bitrates) > 0:
      urls = re.compile('[\'\"](.+?)[\'\"]').findall(bitrates[0][1])

      for num, url in enumerate(urls):
        if num < len(renditions):
          addLink('[B]' + renditions[num] + ' - ' + name + '[/B]',url,thumb,desc)
        else:
          addLink(name,url,thumb,desc)
    else:
      xbmcgui.Dialog().ok('Chyba', 'Video nelze přehrát', '', '')

    # dalsi dily poradu
    for article in doc.findAll('article', 'b-article-news'):
        url = article.a['href'].encode('utf-8')
        title = article.a['title'].encode('utf-8')
        thumb = article.a.img['data-original'].encode('utf-8')
        addDir(title,url,3,thumb,1)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]

        return param

def addLink(name,url,iconimage,popis):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": popis} )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,page):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+str(page)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=get_params()
url=None
name=None
thumb=None
mode=None
page=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Page: "+str(page)

if mode==None or url==None or len(url)<1:
        STATS("OBSAH", "Function")
        OBSAH()

elif mode==6:
        STATS("HOME_NEJSLEDOVANEJSI", "Function")
        HOME_NEJSLEDOVANEJSI(url,page)

elif mode==7:
        STATS("HOME_DOPORUCUJEME", "Function")
        HOME_DOPORUCUJEME(url,page)

elif mode==8:
        STATS("HOME_POSLEDNI", "Function")
        HOME_POSLEDNI(url,page)

elif mode==9:
        STATS("HOME_TOPPORADY", "Function")
        HOME_TOPPORADY(url,page)

elif mode==5:
        STATS("CATEGORIES", "Function")
        CATEGORIES(url,page)

elif mode==2:
        STATS("EPISODES", "Function")
        #EPISODES(url,page)
        VIDEOLINK(url,page)

elif mode==3:
        STATS("VIDEOLINK", "Function")
        VIDEOLINK(url,page)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
