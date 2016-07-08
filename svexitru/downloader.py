# downloader fetching data by requests package.
import random
import requests as requestlib

from pomp.core.base import BaseHttpRequest, BaseHttpResponse, BaseDownloader, BaseCrawlException

from .user_agents import user_agents


class ReqRequest(BaseHttpRequest):
    def __init__(self, url):
        self.url = url


class ReqResponse(BaseHttpResponse):
    def __init__(self, req, resp):
        self.req = req
        if not isinstance(resp, Exception):
            self.content = resp.content
            self.status_code = resp.status_code
            self.headers = resp.headers

    @property
    def request(self):
        return self.req


class RequestDownloader(BaseDownloader):
    # Share Session between get calls.
    _connection_session = None

    @property
    def session(self):
        if self._connection_session is None:
            self._connection_session = requestlib.Session()
        return self._connection_session

    def get(self, requests):
        responses = []
        for request in requests:
            response = self._fetch(request)
            responses.append(response)
        return responses

    def _fetch(self, request):
        agent = random.choice(list(user_agents.values()))
        headers = {'user-agent': agent}
        if isinstance(request, str):
            request = ReqRequest(request)
        try:
            res = self.session.get(request.url, headers=headers, timeout=5)

            if res.status_code == 200:
                return ReqResponse(request, res)
            elif res.status_code in (401, 403):
                return BaseCrawlException(request,
                                          exception=Exception(
                                              'Access forbidden to site {} ({})'.format(request.url,
                                                                                        res.status_code)))
            elif 400 <= res.status_code < 500:
                return BaseCrawlException(request,
                                          exception=Exception(
                                              'Assuming unrestricted access {} ({})'.format(request.url,
                                                                                            res.status_code)))
            elif res.status_code >= 500:
                return BaseCrawlException(request,
                                          exception=Exception(
                                              'Remote server returned ServerError {} ({})'.format(request.url,
                                                                                                  res.status_code)))
            else:
                return BaseCrawlException(request,
                                          exception=Exception(
                                              'Remote server returned status {} ({})'.format(request.url,
                                                                                             res.status_code)))
        except Exception as e:
            return BaseCrawlException(request, exception=e)
