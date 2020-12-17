import codecs, json
import os

from datetime import date, datetime, timedelta
from time import mktime, gmtime
from msedge.selenium_tools import Edge, EdgeOptions

class ChannelScrape:
    """
    Constructors:
    __init__()


    Methods:

    toFile(), getUpcomingId(), getLiveId()
    """
    options_edge = EdgeOptions()
    options_edge.use_chromium = True
    options_edge.add_argument('--ignore-certificate-errors')
    options_edge.add_argument('--ignore-ssl-errors')  
    options_edge.add_argument('--mute-audio')  


    def __init__(self, channelId: str, headless = True, executable_path = None):
        # Searches for webdriver on each dir from PATH environment variables
        # Currently untested in linux
        if executable_path == None:
            for p in os.environ['PATH'].split(";"):
                if os.path.isfile(p+"\msedgedriver.exe"):
                    self.path_dir = p + "\msedgedriver.exe" 

        # Setup driver
        self.options_edge.headless = headless
        self.driver = Edge(options=self.options_edge, executable_path=self.path_dir)

        # JSON collecting process
        url = 'https://www.youtube.com/channel/' + channelId
        self.driver.get(url)
        self.jsonData = self.driver.execute_script('return ytInitialData')
        self.driver.quit()


    def toFile(self, output_file: str):
        """
        Output the collected json data to a file
        output_file: Output file name. File extension will be added automatically
        """
        with codecs.open(output_file + '.json', 'w', encoding='utf-8') as jsonFile:
            json.dump(self.jsonData, jsonFile, ensure_ascii=False, indent=1)


    def getUpcomingId(self, dayDelta = 14):
        """
        Returns a list of upcoming livestream(s) video ID
        dayDelta: If the upcoming livestream delta is more than the provided argument,
                the livestream Id will not be added to the return list 
        """

        # Personal note:
        # The base for calculating dates is 31-12-1969 (UNIX epoch time)
        # Which is then counted to the used date by seconds
        dateFilter=timedelta(days=dayDelta)
        dateThreshold = datetime.now() + dateFilter

        content = self.jsonData['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][1]['itemSectionRenderer']['contents'][0]['shelfRenderer']['content']
        collectedContents = []
        # Only one upcoming livestream
        # This shouldn't need to use for loop assuming that there is always one item in items key
        # But items is still an array, so just in case
        if "expandedShelfContentsRenderer" in content:
            for item in content['expandedShelfContentsRenderer']['items']:
                liveDateEpoch = item['videoRenderer']['upcomingEventData']['startTime']
                liveDate = datetime.fromtimestamp(mktime(gmtime(liveDateEpoch)))
                if item['videoRenderer']['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['style'] == "UPCOMING" and liveDate < dateThreshold:
                    collectedContents.append(item['videoRenderer']['videoId'])

        # Multiple upcoming livestreams
        elif "horizontalListRenderer" in content:
            for item in content['horizontalListRenderer']['items']:
                liveDateEpoch = item['videoRenderer']['upcomingEventData']['startTime']
                liveDate = datetime.fromtimestamp(mktime(gmtime(liveDateEpoch)))
                if item['gridVideoRenderer']['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['style'] == "UPCOMING" and liveDate < dateThreshold:
                    collectedContents.append(item['gridVideoRenderer']['videoId'])

        return collectedContents
    

    def getLiveId(self):
        # Returns a list of the current livestreams video Id, if any
        # It is unlikely that there are multiple livestreams in the same channel,
        # but the possibility is there, therefore it returns a list instead of a single item

        content = self.jsonData['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]
        collectedContents = []
        if "channelFeaturedContentRenderer" in content:
            for videoItem in content['channelFeaturedContentRenderer']['items']:
                if videoItem['videoRenderer']['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['style'] == "LIVE":
                    collectedContents.append(videoItem['videoRenderer']['videoId'])
        
        return collectedContents