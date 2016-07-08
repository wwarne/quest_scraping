from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from .models import SvExitCity, SvExitQuest, SvExitQuestImage, db_connect, create_svexit_tables
from pomp.core.base import BasePipeline


class SvExitCityPipeline(BasePipeline):
    """
    Pipeline for storing scraped city items in the database
    """
    Session = None

    def start(self, crawler):
        engine = db_connect()
        create_svexit_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def process(self, crawler, item):
        session = self.Session()
        # Check is it Quest or QuestImage
        try:
            city_in_base = session.query(SvExitCity).filter(SvExitCity.url == item.url).one()
        except NoResultFound:
            city_in_base = SvExitCity()

        city_in_base.name = item.name
        city_in_base.url = item.url
        city_in_base.crawled = item.crawled
        try:
            session.add(city_in_base)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        return item

    def stop(self, crawler):
        print('Stop called')


class SvExitQuestPipeline(BasePipeline):

    Session = None

    def start(self, crawler):
        engine = db_connect()
        create_svexit_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def process(self, crawler, item):
        """
        Check every element for existence in DB before saving.
        If an element exist - update its properties.
        """
        session = self.Session()
        try:
            quest_in_base = session.query(SvExitQuest).filter(SvExitQuest.url == item.url).one()
        except NoResultFound:
            quest_in_base = SvExitQuest()
        quest_in_base.url = item.url
        quest_in_base.city_id = item.city_id
        quest_in_base.name = item.name
        quest_in_base.min_age = item.min_age or 0
        quest_in_base.address = item.address
        quest_in_base.phone = item.phone
        quest_in_base.min_players = item.min_players or 0
        quest_in_base.max_players = item.max_players or 0
        quest_in_base.time = item.time or 0
        quest_in_base.description = item.description
        quest_in_base.crawled = item.crawled
        quest_in_base.status = item.status
        try:
            session.add(quest_in_base)
            session.commit()
        except:
            session.rollback()
            session.close()
            raise
        if item.images:
            for image in item.images:
                instance = session.query(SvExitQuestImage).filter_by(url=image, quest=quest_in_base).first()
                if instance:
                    continue
                else:
                    temp = SvExitQuestImage(
                        url=image,
                        quest=quest_in_base
                    )
                    try:
                        session.add(temp)
                    except:
                        session.rollback()
                        session.close()
                        raise
        session.commit()
        session.close()
        print('Successfully added {}'.format(item))

    def stop(self, crawler):
        pass
