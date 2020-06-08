import sys, urllib.parse, urllib.request, urllib.parse, urllib.error, time, base64
import xbmcgui, xbmcplugin, xbmcaddon, xbmc

from resources.lib import utils
from resources.lib import redbulltv_client as redbulltv

class RedbullTV(object):
    def __init__(self):
        self.id = 'plugin.video.redbulltv'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        self.args = urllib.parse.parse_qs(sys.argv[2][1:])
        xbmcplugin.setContent(self.addon_handle, 'videos')
        self.redbulltv_client = redbulltv.RedbullTVClient(self.addon.getSetting('video.resolution'))
        self.default_view_mode = 55 # Wide List

    @staticmethod
    def get_keyboard(default="", heading="", hidden=False):
        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return str(urllib.parse.quote_plus(keyboard.getText()))
        return default

    def navigation(self):
        url = base64.b64decode(self.args.get("api_url")[0]).decode() if self.args.get("api_url") else None
        is_stream = self.args.get('is_stream', [False])[0] == "True"

        if url and "search?q=" in url:
            url += self.get_keyboard()

        # If Stream url is available
        if is_stream:
            self.play_stream(url)
            return

        try:
            items = self.redbulltv_client.get_items(url)
        except IOError:
            # Error getting data from Redbull server
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30020), self.addon.getLocalizedString(30021), self.addon.getLocalizedString(30022))
            return

        if not items:
            # No results found
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30023), self.addon.getLocalizedString(30024), self.addon.getLocalizedString(30025))
            return
        elif items[0].get("event_date"):
            # Scheduled Event Time
            xbmcgui.Dialog().ok(
                self.addon.getLocalizedString(30026),
                self.addon.getLocalizedString(30027),
                items[0].get("event_date") + " (GMT+" + str(time.timezone / 3600 * -1) + ")"
            )
            return
        else:
            self.add_items(items)

        xbmc.executebuiltin('Container.SetViewMode(%d)' % self.default_view_mode)
        xbmcplugin.endOfDirectory(self.addon_handle)

    def add_items(self, items):
        for item in items:
            params = {
                'api_url': base64.b64encode(item["url"].encode()).decode(),
                }

            if "is_content" in item:
                params['is_stream'] = item["is_content"]

            url = utils.build_url(self.base_url, params)
            list_item = xbmcgui.ListItem(item.get("title"))
            list_item.setArt({"thumb": item['landscape'] if 'landscape' in item else self.icon})

            if 'fanart' in item: 
                list_item.setArt({"fanart": item['fanart']})
            if 'landscape' in item:
                list_item.setArt({"landscape": item['landscape']})
            if 'banner' in item:
                list_item.setArt({"banner": item['banner']})
            if 'poster' in item:
                list_item.setArt({"poster": item['poster']})
            
            infoLabels = {
                "title": item["title"], 
                "plot": item.get("summary", None), 
                "genre": item.get("subheading", None), 
                "duration": item.get("duration")
            }
            list_item.setInfo(type="Video", infoLabels=infoLabels)
            if item.get("is_content"):
                list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url, listitem=list_item, isFolder=(not item["is_content"]))

    def play_stream(self, streams_url):
        stream_url = self.redbulltv_client.get_stream_url(streams_url)
        item = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=item)

if __name__ == '__main__':
    RedbullTV().navigation()
