from lxml import html
from pomp.core.base import BaseCrawler
from .items import PhobiaCityItem, PhobiaQuestItem
from .downloader import PhantomDownloader, PhantomRequest
from urllib.parse import urljoin
from datetime import datetime
import re


class PhobiaCityCrawler(BaseCrawler):
    CITY_PATH = '//li[contains(concat(" ", @class, " "), " city ")]/a'
    ENTRY_REQUESTS = PhantomRequest('http://phobia.ru/cities/')

    def extract_items(self, response):
        tree = html.fromstring(response.content)
        for city in tree.xpath(self.CITY_PATH):
            city_item = PhobiaCityItem()
            city_item.name = ''.join(city.xpath('text()'))
            partial_url = ''.join(city.xpath('@href'))
            city_item.url = urljoin(response.req.url, partial_url)
            city_item.crawled = datetime.now()
            yield city_item


class PhobiaQuestCrawler(BaseCrawler):
    # на титульной странице города
    # выбираем все квесты, которые работают! (В разработке не берём)
    # те, которые работают имеют класс enabled
    ALL_QUESTS_IN_CITY = '//*[@id="quests_tab"]/div/div[contains(@class, "enabled")]'
    ALL_QUEST_SITE_VER2 = './/div[@class="quest"]//div[@class="right_side"]/a'
    ALL_QUEST_SITE_VER3 = './/div[@class="quest_list"]//div[@class="right_side"]/a'
    # на странице с квестом
    QUEST_NAME = '//*[@id="qi-name"]/text()'
    QUEST_GAMERS = '//*[@id="qi-gamers"]/text()'
    QUEST_TIME = '//*[@id="qi-duration"]/text()'
    QUEST_DESCRIPTION = '//*[@id="qi-description"]/text()'
    QUEST_PHONE = '//*[@id="qi-phone"]/text()'
    QUEST_EMAIL = '//*[@id="qi-email"]/a/text()'
    QUEST_ADDRESS = '//*[@id="qi-address"]/text()'
    QUEST_ADDRESS_NOTES = '//*[@id="qi-address-desc"]/text()'
    QUEST_AGE = '//*[@id="qi-age"]/text()'

    def __init__(self, start_url, city_id):
        self.city = city_id
        self.ENTRY_REQUESTS = PhantomRequest(start_url)
        # превращает строку типа 'ш34л 4d' в список ['34', '4']
        self.gamers = re.compile('(\d+)')
        super().__init__()

    def extract_items(self, response):
        tree = html.fromstring(response.content)
        quest_name = tree.xpath(self.QUEST_NAME)
        all_q = tree.xpath(self.ALL_QUESTS_IN_CITY)
        all_q_ver2 = tree.xpath(self.ALL_QUEST_SITE_VER2)

        if quest_name:
            quest = PhobiaQuestItem()
            quest.time = ''.join(tree.xpath(self.QUEST_TIME)).strip()
            if 'минут' in quest.time:
                quest.time = quest.time.split(' ')[0]
            try:
                quest.time = int(quest.time)
            except ValueError:
                quest.time = 0
            quest.name = ''.join(tree.xpath(self.QUEST_NAME))
            quest.url = response.req.url
            quest.address = ''.join(tree.xpath(self.QUEST_ADDRESS))
            quest.address_notes = ''.join(tree.xpath(self.QUEST_ADDRESS_NOTES))
            quest.city_id = self.city
            quest.description = ''.join(tree.xpath(self.QUEST_DESCRIPTION)).strip()
            quest.email = ''.join(tree.xpath(self.QUEST_EMAIL))
            quest.phone = ''.join(tree.xpath(self.QUEST_PHONE))
            # Количество игроков указано - строкой - от 2 до 4, к примеру. Поэтому выцепляем
            # регуляркой цифры из этой строки
            players = [int(num) for num in self.gamers.findall(''.join(tree.xpath(self.QUEST_GAMERS)))]
            quest.min_players = players[0]
            quest.max_players = players[-1]
            # Возраст тоже пишется строкой -
            # Минимальный возраст участников: от 8 лет с родителями, от 14 без
            # Поэтому используя ту-же самую регулярку, выцепляю эти два возраста
            ages = [int(age) for age in self.gamers.findall(''.join(tree.xpath(self.QUEST_AGE)))]
            quest.age = max(ages)
            quest.age_with_parents = min(ages)
            # У квестов, которые в разработке даже нет страниц, так что
            quest.status = True
            if response.images:
                quest.images = response.images
            quest.crawled = datetime.now()
            yield quest
        # Если мы на титульной странице города
        if all_q:
            for one_quest in all_q:
                _url = ''.join(one_quest.xpath('div[2]/h2/a/@href'))
                next_url = urljoin(response.req.url, _url)
                yield PhantomRequest(url=next_url)
        if all_q_ver2:
            # Второй вариант главной страницы сайта
            for one_quest in all_q_ver2:
                _url = ''.join(one_quest.xpath('@href'))
                next_url = urljoin(response.req.url, _url)
                yield PhantomRequest(url=next_url)

        if not quest_name and not all_q and not all_q_ver2:
            all_q_ver3 = tree.xpath(self.ALL_QUEST_SITE_VER3)
            if all_q_ver3:
                # Третий вариант главной страницы сайта
                for one_quest in all_q_ver3:
                    _url = ''.join(one_quest.xpath('@href'))
                    next_url = urljoin(response.req.url, _url)
                    yield PhantomRequest(url=next_url)
            else:
                print('Unknown page on {}'.format(response.req.url))
