from lxml import html
from pomp.core.base import BaseCrawler
from svexitru.items import SvExitCityItem, SvExitQuestItem
from svexitru.downloader import ReqRequest
from urllib.parse import urljoin
from datetime import datetime


class SvExitCityCrawler(BaseCrawler):
    """
    Example of city html element
    <a id="bx_3094277961_2876" href="http://abakan.sv-exit.ru/">
    <span class="name">Абакан</span>
    2 КВЕСТА, 0 В РАЗРАБОТКЕ
    </a>
    """
    ENTRY_REQUESTS = ['http://msk.sv-exit.ru/']
    SVEXIT_TOWNS_XPATH = '//ul[@class="town"]/li/a'

    def extract_items(self, response):
        if response.status_code == 200:
            converted = response.content.decode('utf-8')
            tree = html.fromstring(converted)
            for city in tree.xpath(self.SVEXIT_TOWNS_XPATH):
                item = SvExitCityItem()
                item.name = ''.join(city.xpath('span/text()'))
                item.url = ''.join(city.xpath('@href'))
                if not item.url:
                    item.url = response.request.url
                item.crawled = datetime.now()
                yield item
        else:
            print('Error on page {}, status code {}'.format(response.req.url, response.status_code))


class SvExitQuestCrawler(BaseCrawler):
    # xpath for city main page
    ALL_QUESTS_IN_CITY = './/*[@id="quests"]/div[2]/a'

    # xpaths for retrieve one quest information
    QUEST_NAME = './/body/div[2]/div/div[1]/h1/text()'
    QUEST_MIN_AGE = '//span[@class="age_max_big"]/text()'
    QUEST_ADDRESS = '/tr[1]/td[2]/div[@class="name"]/text()'
    QUEST_PHONE = '//span[@class="phone"]/text()'
    QUEST_MIN_PLAYERS = './/*[@id="mincountplayer"]/text()'
    QUEST_MAX_PLAYERS = './/*[@id="maxcountplayer"]/text()'
    QUEST_TIME = './/div[@class="name"]/text()'
    QUEST_DESCRIPTION = './/*[@id="scrollbar2"]/div[1]/div/text()'
    QUEST_IMAGES = './/body/div[2]/div/div[2]/div/img/@src'
    QUEST_STATUS = '//span[contains(concat(" ", @class , " "), " time ")]'

    def __init__(self, start_url, dont_parse_urls, city_id):
        """

        :param start_url: The city's main page
        :param dont_parse_urls: A list of all cities main pages. For example - on Moscow page there is a
                                link 'Quests in Balashikha'. It is decorated like a normal link to a quest.
                                So if we found a link to a different city in a quest's link area - we'll ignore it.
        :param city_id: An ID of the current city we parse. Without it it's impossible to save data
                        in database properly.
        """
        self.city = city_id
        self._parsed_urls = dont_parse_urls
        self.ENTRY_REQUESTS = ReqRequest(start_url)
        super().__init__()

    def extract_items(self, response):
        if response.status_code != 200:
            print('Error on page {}, status code {}'.format(response.req.url, response.status_code))
            return
        converted = response.content.decode('utf-8')
        tree = html.fromstring(converted)
        quest_name = tree.xpath(self.QUEST_NAME)
        all_q = tree.xpath(self.ALL_QUESTS_IN_CITY)

        if all_q:
            # we on the city's main page (with a list of quests in this city)
            for one_link in all_q:
                new_url = ''.join(one_link.xpath('@href'))
                next_url = urljoin(response.req.url, new_url)
                if next_url not in self._parsed_urls:
                    self._parsed_urls.append(next_url)
                    yield ReqRequest(next_url)

        if quest_name:
            # We are on Quest's single page
            quest = SvExitQuestItem()
            quest.city_id = self.city
            quest.url = response.req.url
            quest.name = ''.join(quest_name)
            quest.min_age = ''.join(tree.xpath(self.QUEST_MIN_AGE))

            # Sometimes there are few elements on a page that looks like an address.
            # Usually the address is the longest one.
            quest.address = ''
            for addr in tree.xpath(self.QUEST_ADDRESS):
                if len(addr.strip()) > len(quest.address):
                    quest.address = addr.strip()

            quest.phone = ''.join(tree.xpath(self.QUEST_PHONE))
            quest.min_players = ''.join(tree.xpath(self.QUEST_MIN_PLAYERS))
            quest.max_players = ''.join(tree.xpath(self.QUEST_MAX_PLAYERS))

            for item in tree.xpath(self.QUEST_TIME):
                if 'МИНУТ' in item:
                    quest.time = item.split(' ')[0]
            if quest.time is None:
                quest.time = 0

            quest.description = ''.join(tree.xpath(self.QUEST_DESCRIPTION)).strip()
            quest.city = self.city
            images_urls = tree.xpath(self.QUEST_IMAGES)
            if images_urls:
                quest.images = []
                for image in images_urls:
                    quest.images.append(urljoin(quest.url, image))
            if tree.xpath(self.QUEST_STATUS):
                quest.status = False
                # it's 'coming soon' quest
            else:
                quest.status = True
                # it's an active quest
            quest.crawled = datetime.now()
            yield quest

        if not all_q and not quest_name:
            print('Unknown page on {}'.format(response.req.url))
