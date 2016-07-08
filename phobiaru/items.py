from datetime import datetime
from pomp.contrib.item import Item, Field


class PhobiaQuestItem(Item):
    """
    A model used by crawler
    """
    city = Field()
    name = Field()
    url = Field()
    min_age = Field()
    address = Field()
    phone = Field()
    min_players = Field()
    max_players = Field()
    time = Field()
    description = Field()
    crawled = Field()
    status = Field()
    images = Field()
    age_with_parents = Field()
    address_notes = Field()
    email = Field()

    def __init__(self):
        super().__init__()
        if not self.crawled:
            self.crawled = datetime.now()

    def __str__(self):
        return 'QuestItem from {url}. ' \
               'Photos: {ph_count}'.format(url=self.url,
                                           ph_count=len(self.images) if self.images else 'N/A')


class PhobiaCityItem(Item):
    name = Field()
    url = Field()
    crawled = Field()

    def __str__(self):
        return 'City from {}'.format(self.url)
