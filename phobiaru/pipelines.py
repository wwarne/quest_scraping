from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from .models import PhobiaCity, PhobiaQuest, PhobiaQuestImage, db_connect, create_phobia_tables
from pomp.core.base import BasePipeline


class PhobiaCityPipeline(BasePipeline):

    Session = None

    def start(self, crawler):
        engine = db_connect()
        create_phobia_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def process(self, crawler, item):
        session = self.Session()
        try:
            city_in_base = session.query(PhobiaCity).filter(PhobiaCity.url == item.url).one()
        except NoResultFound:
            city_in_base = PhobiaCity()
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


class PhobiaQuestPipeline(BasePipeline):

    Session = None

    def start(self, crawler):
        engine = db_connect()
        create_phobia_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def process(self, crawler, item):
        session = self.Session()
        try:
            quest_in_base = session.query(PhobiaQuest).filter(PhobiaQuest.url == item.url).one()
        except NoResultFound:
            quest_in_base = PhobiaQuest()

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
        quest_in_base.age_with_parents = item.age_with_parents or 0
        quest_in_base.address_notes = item.address_notes
        quest_in_base.email = item.email

        try:
            session.add(quest_in_base)
            session.commit()
        except:
            session.rollback()
            session.close()
            raise
        if item.images:
            for image in item.images:
                try:
                    image_in_base = session.query(PhobiaQuestImage).filter_by(url=image, quest=quest_in_base).one()
                except NoResultFound:
                    image_in_base = PhobiaQuestImage()
                image_in_base.url = image
                image_in_base.quest = quest_in_base
                session.add(image_in_base)
            try:
                session.commit()
            except:
                session.rollback()
                session.close()
                raise
        session.close()
        print('Successfully added {s} ({s.name})'.format(s=item))
