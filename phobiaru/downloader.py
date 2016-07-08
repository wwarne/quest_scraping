from pomp.core.base import BaseHttpRequest, BaseHttpResponse, BaseDownloadWorker, BaseCrawlException
from pomp.contrib.concurrenttools import ConcurrentDownloader
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time


class PhantomRequest(BaseHttpRequest):
    def __init__(self, url):
        self.url = url
        self.driver_url = None

    def __str__(self):
        return '<{s.__class__.__name__} url: {s.url}> ' \
               'wdriver: {s.driver_url}'.format(s=self)


class PhantomResponse(BaseHttpResponse):
    def __init__(self, req, body, images=None):
        self.req = req
        self.content = body
        if images:
            self.images = images

    @property
    def request(self):
        return self.req


class PhantomWorker(BaseDownloadWorker):
    def __init__(self):
        self.pid = 'windows'
        # on linux
        # self.pid = os.getpid()

    def get_one(self, request):
        # attach webdriver to already started phantomjs node
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/39.0.2171.95 Safari/537.36'
        )
        dcap = DesiredCapabilities.PHANTOMJS.copy()
        dcap['phantomjs.page.settings.userAgent'] = user_agent
        driver = webdriver.Remote(
            command_executor=request.driver_url,
            desired_capabilities=dcap,
        )
        driver.get(request.url)
        # wait untill JS renders the page
        try:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, './/*[@id="footer"]')
                )
            )
        except TimeoutException:
            print(request.url + ' не загрузился')
            return BaseCrawlException(request=request, exception=TimeoutException)
        image_elements = []

        try:
            # Этот элемент появляется на иностранных сайтах, и на некоторых русских.
            # Берлин, Дубай, Минск, Майами, Самара, Саратов, Чебоксары
            element = driver.find_element_by_xpath('.//*[@id="lang_select"]')
            if element:
                opt_ru, opt_en = None, None
                for option in element.find_elements_by_tag_name('option'):
                    if option.text == 'Ru':
                        opt_ru = option
                    elif option.text == 'En':
                        opt_en = option
                if opt_ru:
                    opt_ru.click()
                    time.sleep(3)
                elif opt_en:
                    opt_en.click()
                    time.sleep(3)
            # if element:
            #     select = Select(element)
            #     select.deselect_all()
            #     select.select_by_visible_text('En')
            #     select.deselect_all()
            #     select.select_by_visible_text('Ru')

        except NoSuchElementException:
            pass

        try:
            if driver.find_element_by_xpath('.//*[@id="quest-image"]'):
                current_image = 'n/a'
                while current_image not in image_elements:
                    """ Картинки на сайте переключаются нажатием на картинку стрелочки.
                    через JS изменяется стиль элемента - меняется адрес картинки.
                    Перебираем картинки и записываем их в list до тех пор, пока не начнут повторяться.
                    И заодно обрезаем слева текст `background-image: url(` и справа `);`
                    """
                    current_image = driver.find_element_by_xpath('.//*[@id="quest-image"]').get_attribute('style')[22:][:-2]
                    image_elements.append(current_image)
                    driver.find_element_by_xpath('.//*[@id="next_img"]').click()
                    driver.implicitly_wait(4)
                    # time.sleep(1)
                    current_image = driver.find_element_by_xpath('.//*[@id="quest-image"]').get_attribute('style')[22:][:-2]
        except NoSuchElementException:
            pass

        # finish - get current document body
        body = driver.execute_script('return document.documentElement.outerHTML;')
        return PhantomResponse(request, body, image_elements)


class PhantomDownloader(ConcurrentDownloader):

    def __init__(self, phantom_drivers, *args, **kwargs):
        self.drivers = phantom_drivers
        super().__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)

    def get(self, requests):
        # associate each request with phantomjs node
        def _associate_driver_url(request):
            request.driver_url = self.drivers[0].command_executor._url
            self.drivers.rotate(1)
            return request

        return super().get(
            map(_associate_driver_url, requests)
        )

    def stop(self):
        super().stop()
        # for driver in self.drivers:
        #     driver.close()
        #     driver.quit()
            # for linux
            # pid = driver.service.process.pid
            # HACK - phantomjs does not exited after close and quit
            # try:
            #     os.kill(pid, signal.SIGTERM)
            # except ProcessLookupError:
            #     pass
