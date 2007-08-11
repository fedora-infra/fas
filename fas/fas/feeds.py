import urllib
from xml.dom import minidom


class Koji:
    def __init__(self, userName, url='http://publictest8/koji/recentbuilds?user='):
        buildFeed = minidom.parse(urllib.urlopen(url + userName))
        try:
            self.userLink = buildFeed.getElementsByTagName('link')[0].childNodes[0].data
            self.builds = {}
            for build in buildFeed.getElementsByTagName('item'):
                link = build.getElementsByTagName('link')[0].childNodes[0].data
                self.builds[link] = {}
                self.builds[link]['title'] = build.getElementsByTagName('title')[0].childNodes[0].data
                self.builds[link]['pubDate'] = build.getElementsByTagName('pubDate')[0].childNodes[0].data
        except IndexError:
            return
