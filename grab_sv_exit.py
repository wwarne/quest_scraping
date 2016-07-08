from svexitru.downloader import RequestDownloader
from svexitru.crawlers import SvExitCityCrawler, SvExitQuestCrawler
from svexitru.pipelines import SvExitCityPipeline, SvExitQuestPipeline
from svexitru.middleware import StatisticMiddleware, ErrorReportingMiddleware
from svexitru.models import SvExitCity, db_connect, create_svexit_tables
from sqlalchemy.orm import sessionmaker
from pomp.core.engine import Pomp
from datetime import datetime

start_time = datetime.now()
# Grab URLs of all cities
city_pomp = Pomp(
    downloader=RequestDownloader(),
    pipelines=[SvExitCityPipeline()]
)
city_pomp.pump(SvExitCityCrawler())


engine = db_connect()
# create_svexit_tables(engine)
Session = sessionmaker(bind=engine)
se = Session()
all_city_info = se.query(SvExitCity).all()
all_cities = [(city.id, city.url) for city in all_city_info]
dont_parse = [city.url for city in all_city_info]
se.close()

statistics = StatisticMiddleware()
quest_pomp = Pomp(
    downloader=RequestDownloader(),
    middlewares=[statistics, ErrorReportingMiddleware()],
    pipelines=[SvExitQuestPipeline()]
)

for city_id, city_url in all_cities:
    print('---Parsing {}---'.format(city_url))
    quest_pomp.pump(SvExitQuestCrawler(
        start_url=city_url,
        city_id=city_id,
        dont_parse_urls=dont_parse
    ))
print('------------------ Total time -------------')
t = datetime.now() - start_time
print('It has took {} seconds'.format(t.seconds))
print("Statistics: \n {}".format(statistics))
print('----------- RPS (Requests per second)--------')
print(statistics.requests / t.seconds)