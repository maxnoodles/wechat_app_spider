import re

import mitmproxy.http
from mitmproxy import ctx
import redis


class Counter:
    def __init__(self):

        self.device_name = 'xiaoyao'
        self.redis_cli = redis.StrictRedis(decode_responses=True)
        self.biz_queue = f'{self.device_name}_wechat_biz'
        self.url_queue = f'{self.device_name}_article_url'

    def inspect_redis_queue(self, name):
        queue_len = self.redis_cli.llen(name)
        if queue_len != 0:
            self.redis_cli.delete(name)

    def request(self, flow: mitmproxy.http.HTTPFlow):
        biz = re.search(r'https://mp.weixin.qq.com/mp/geticon\?__biz=(.*?)&', flow.request.url)
        if biz:
            referer = flow.request.headers['referer']
            print(referer)
            biz = biz.group(1)
            self.inspect_redis_queue(self.biz_queue)
            self.inspect_redis_queue(self.url_queue)
            self.redis_cli.lpush(self.biz_queue, biz)
            self.redis_cli.lpush(self.url_queue, referer)
            ctx.log.info(f"the biz is: {biz}")


addons = [
    Counter()
]