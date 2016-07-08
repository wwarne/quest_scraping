from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from svexitru import db_settings

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using settings from db_settings.py
    :return: SQLAlchemy engine instance
    """
    return create_engine(URL(**db_settings.DATABASE))


def create_svexit_tables(engine):
    DeclarativeBase.metadata.create_all(engine)
    # Create tables.
    # Will not attempt to recreate tables already present in the target database.


class SvExitCity(DeclarativeBase):
    """
    SQLAlchemy PhobiaCity model
    """
    __tablename__ = 'sv_exit_cities'

    id = Column(Integer, primary_key=True)
    name = Column('name', String)
    url = Column('url', String)
    crawled = Column('crawled', DateTime)


class SvExitQuest(DeclarativeBase):
    """
    SQLAlchemy PhobiaQuest model
    """
    __tablename__ = 'sv_exit_quests'

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey('sv_exit_cities.id'))
    city = relationship(SvExitCity)
    name = Column('name', String)
    url = Column('url', String, unique=True)
    min_age = Column('min_age', Integer, nullable=True)
    address = Column('address', String, nullable=True)
    phone = Column('phone', String, nullable=True)
    min_players = Column('min_players', Integer, nullable=True)
    max_players = Column('max_players', Integer, nullable=True)
    time = Column('time', Integer, nullable=True)
    description = Column('description', String, nullable=True)
    crawled = Column('crawled', DateTime)
    status = Column('status', String, nullable=True)
    images = relationship('PhobiaQuestImage', back_populates='quest', cascade='all, delete-orphan')


class SvExitQuestImage(DeclarativeBase):
    """
    SQLAlchemy PhobiaQuestImage model
    """
    __tablename__ = 'sv_exit_images'

    id = Column(Integer, primary_key=True)
    url = Column('url', String)
    quest_id = Column(Integer, ForeignKey('sv_exit_quests.id', ondelete='CASCADE'))
    quest = relationship('PhobiaQuest', back_populates='images')
