from phobiaru.downloader import PhantomDownloader, PhantomWorker
from phobiaru.crawlers import PhobiaCityCrawler, PhobiaQuestCrawler
from phobiaru.pipelines import PhobiaCityPipeline, PhobiaQuestPipeline
from phobiaru.middleware import StatisticMiddleware
from phobiaru.models import PhobiaCity, db_connect
from sqlalchemy.orm import sessionmaker
from pomp.core.engine import Pomp
from datetime import datetime
from collections import deque
from selenium import webdriver

# On windows the subprocesses will import (i.e. execute) the main module at start.
# so we need to protect the main code with 'if __name__ == '__main__':'
# to avoid creating subprocesses recursively:
if __name__ == '__main__':
    pool_size = 2
    start_time = datetime.now()
    # start phantomjs nodes
    ph_drivers = deque(
        [
            webdriver.PhantomJS() for _ in range(pool_size)
            ]
    )
    # Grab URLs of all cities
    city_pomp = Pomp(
        downloader=PhantomDownloader(
            pool_size=2,
            worker_class=PhantomWorker,
            phantom_drivers=ph_drivers,
        ),
        pipelines=[PhobiaCityPipeline()]
    )
    city_pomp.pump(PhobiaCityCrawler())

    engine = db_connect()
    Session = sessionmaker(bind=engine)
    se = Session()
    all_cities = [(city.id, city.url) for city in se.query(PhobiaCity).all()]
    se.close()

    statistics = StatisticMiddleware()

    for city_id, city_url in all_cities:
        quest_pomp = Pomp(
            downloader=PhantomDownloader(
                pool_size=2,
                worker_class=PhantomWorker,
                phantom_drivers=ph_drivers,
            ),
            middlewares=[statistics],
            pipelines=[PhobiaQuestPipeline()]
        )

        print('--- Parsing {} ---'.format(city_url))
        quest_pomp.pump(PhobiaQuestCrawler(
            start_url=city_url,
            city_id=city_id
        ))
    print('------------------ Total time -------------')
    t = datetime.now() - start_time
    print('It has took {} seconds'.format(t.seconds))
    print("Statistics: \n {}".format(statistics))
    print('----------- RPS (Requests per second)--------')
    print(statistics.requests / t.seconds)

    for driver in ph_drivers:
        driver.close()
        driver.quit()
