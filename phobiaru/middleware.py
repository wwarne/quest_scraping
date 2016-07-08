from pomp.core.base import BaseMiddleware


class StatisticMiddleware(BaseMiddleware):
    def __init__(self):
        self.requests = self.responses = self.exceptions = 0

    def process_request(self, request, crawler, downloader):
        self.requests += 1
        return request

    def process_response(self, response, crawler, downloader):
        self.responses += 1
        return response

    def process_exception(self, exception, crawler, downloader):
        self.exceptions += 1
        return exception

    def __str__(self):
        return 'requests/responses/exceptions ' \
            '= {s.requests}/{s.responses}/{s.exceptions}' \
            .format(s=self)


class ErrorReportingMiddleware(BaseMiddleware):

    def process_exception(self, exception, crawler, downloader):
        # exception is a BaseCrawlerExceprion(Request, exception)
        # so exception.exception.args[0] - it's a text from exception
        # print(exception.exception.args[0])
        # print(exception)
        return exception
