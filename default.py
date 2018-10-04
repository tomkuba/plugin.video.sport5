# -*- coding: utf-8 -*-
""" KODI addon for Sport5.cz    """

import urllib, urllib2, re, xbmcplugin, xbmcgui, os


def get_web_page(url):
    """    Sport5 web pages downloader    """
    req = urllib2.Request(url)
    req.add_header('User-Agent',
                   'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    web_page = response.read()
    web_page = web_page.decode('utf-8')
    response.close()
    return web_page


def get_shows():
    """    Create list of all shows    """
    link = get_web_page('http://sport5.cz/archiv/')

    # strip unneeded html code so we can better regex needed data
    match = re.compile('div>(<div class="row">.*)', re.MULTILINE | re.DOTALL).findall(link)

    # use regex to find data; it is faster than bs4 on slower devices such as RaspberryPI
    match = re.compile('<div class="row">.+?href=\"(?P<programme_url>\/.+?\/)\" class="archive-.*?src="(?P<thumbnail>.+?png)" alt="(?P<title>.+?)"',
                       re.MULTILINE | re.DOTALL).findall(match[0])

    for programme_url, thumbnail, title in match:
        programme_url = "http://sport5.cz" + programme_url
        thumbnail = thumbnail
        print "Sport5LOG: programme_url: {0}, thumbnail: {1}, title: {2}".format(str(programme_url), str(thumbnail), str(title))
        add_dir(title.encode('utf-8'), programme_url, 1, thumbnail)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_episodes_of_show(programme_url):
    """    Create list of episodes    """
    link = get_web_page(programme_url)

    match = re.compile(ur'bind="(?P<thumbnail>.+?)" alt="(?P<title>.+?)".+?href="(?P<episode_url>.+?)"',
                       re.MULTILINE | re.DOTALL).findall(link)

    for thumbnail, title, episode_url in match:
        thumbnail = thumbnail
        title = title.encode('utf-8')
        print "Sport5LOG: thumbnail: {0}, title: {1}, episode_url: {2}".format(str(thumbnail), str(title), str(episode_url))
        add_link(title, episode_url, 2, thumbnail)

    # Find the url of the right-angle link: ">"
    paging = re.compile(ur'.*href="(?P<next_page_url>.+?)"><i class="fa fa-fw fa-angle-right">', re.UNICODE).findall(link)

    for next_page_url in paging:
        plugin_id = 'plugin.video.sport5'
        media_url = 'special://home/addons/{0}/resources/media/'.format(plugin_id)
        next_icon_path = media_url + "next.png"
        add_dir("[B]Další[/B]", next_page_url, 1, next_icon_path)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_video_link(episode_url):
    """ Download episode web page and parse stream url (one mp4 url)    """
    xbmc.log("url:" + str(episode_url), level=xbmc.LOGNOTICE)
    link = get_web_page(episode_url)
    match = re.compile('source src="(?P<stream_url>.+?)"').findall(link)
    xbmc.log("url:" + str(match[0].encode('utf-8')), level=xbmc.LOGNOTICE)
    return match[0]


def get_params():
    """ Loads plugin parameters    """
    param = {'url': None,'mode': None,'name': None}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


def add_link(name, url, mode, iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    liz.setMimeType('application/dash+xml')
    liz.setContentLookup(False)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def add_dir(name, url, mode, iconimage):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

# MAIN EVENT PROCESSING STARTS HERE
url = None
name = None
mode = None

params = get_params()

if params["url"]:
    url = urllib.unquote_plus(params["url"])
if params["name"]:
    name = urllib.unquote_plus(params["name"])
if params["mode"]:
    mode = int(params["mode"])

print "Sport5LOG: Mode: {0}, URL: {1}, Name: {2}".format(str(mode), str(url), str(name))

if mode is None:  # List all shows
    get_shows()

elif mode == 1:  # List episodes of selected show
    get_episodes_of_show(url)

elif mode == 2:  # Get stream url of episode and start player
    stream_url = str(get_video_link(url))
    list_item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)
