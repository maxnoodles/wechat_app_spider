# -*- encoding=utf8 -*-
__author__ = "Administrator"
import itertools
import traceback

from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
import redis
import pymongo
import pandas as pd

import helper


class AirTestSpider:
    """
    airtest 抓取文本信息和触发点击事件，mitmproxy 抓取相关网络信息，通过 redis 通信
    """

    def __init__(self, device_host):
        auto_setup(__file__)

        self.device_1 = connect_device(f'android:///{device_host}?cap_method=javacap&touch_method=adb')
        self.device_name = 'xiaoyao'
        self.poco = AndroidUiautomationPoco(self.device_1, screenshot_each_action=False)

        self.client = pymongo.MongoClient()
        self.dp_db = self.client['DianPing']

        self.wechat_db = self.client['WeChatOfficialAccount']
        self.wechat_col = self.wechat_db['wechat_search_info']
        self.pandas_col = self.wechat_db['pandas_info']

        self.redis_cli = redis.StrictRedis(decode_responses=True)
        self.biz_queue = f'{self.device_name}_wechat_biz'
        self.url_queue = f'{self.device_name}_article_url'

        self.wx_package_name = 'com.tencent.mm'
        self.city_en_list = ['guangzhou', 'dongguan', 'foshan', 'huizhou', 'zhongshan', 'zhuhai']

        self.count = 0

    def to_search_entrance(self):
        """
        进入微信搜索入口
        :return:
        """
        try:
            # 点击首页搜索图标
            self.poco("com.tencent.mm:id/jb").click()
            # 搜索项选择公众号
            self.poco(text="公众号").click()
        except Exception as e:
            print('进入搜索入口失败')
            traceback.print_exc()

    def get_item_info(self, keyword):
        """
        获取搜索的公众号基础信息，不包括 biz 和 第一篇文章 url
        :param keyword:
        :return:
        """
        # 清空输入框
        self.poco("com.tencent.mm:id/l3").set_text('')
        # 点击输入框
        self.poco("com.tencent.mm:id/l3").click()
        # 输入关键词
        text(keyword, search=True)
        sleep(3)
        # 出现微信推荐搜索时，点击进入仍然搜索页面
        still_search_button = self.poco(nameMatches='.*?仍然搜索.*?')
        if still_search_button.exists():
            print('进入点击')
            still_search_button.click()
        # 搜集搜索项
        nodes = self.poco(name="搜一搜").children()
        if len(nodes) > 2:
            item_info_dict = self.parse_nodes(nodes)
            return item_info_dict

    @staticmethod
    def parse_nodes(nodes):
        """
        :param nodes:
        :return:
        """
        # compress 过滤出迭代元素中 True 的元素
        search_result = itertools.compress(nodes, [node.attr('touchable') for node in nodes])
        search_result = [i.get_name() for i in search_result][1:]
        for i in search_result:
            # 去除干扰项
            if i in ['正在搜索', '没有更多的搜索结果', '3f5d81b43a891e3abe270d49cd6ce850']:
                search_result.remove(i)
        dic_list = helper.parse_search_list(search_result)
        return dic_list[0]

    def click_article(self):
        """
        点击公众号和首条文章
        :return:
        """
        # 点击第一个搜索项
        # self.poco("android.webkit.WebView").child('搜一搜').child('android.view.View')[0].click()
        self.poco("搜一搜").children()[1].click()
        # 验证公众号是否包含一篇及以上文章
        article = self.poco('com.tencent.mm:id/b3q')
        biz, article_url = '', ''
        if article.exists():
            article.click()
            sleep(2)
            biz = self.from_redis_get_info(self.biz_queue)
            article_url = self.from_redis_get_info(self.url_queue)
            if biz is None:
                print('找不到 biz ,请查看具体情况')
            else:
                # blpop 取出来是一个元祖，需取第一个元素
                biz = biz[1]
                article_url = article_url[1]
            sleep(0.5)
            # 点击关闭文章按钮
            self.poco("com.tencent.mm:id/kx").click()
        kf = self.poco("com.tencent.mm:id/kf")
        if kf.exists():
            kf.click()
        else:
            self.poco("com.tencent.mm:id/kx").click()
        return biz, article_url

    def from_redis_get_info(self, name):
        info = self.redis_cli.blpop(name, timeout=3)
        return info

    def restart_app_to_search(self):
        stop_app(self.wx_package_name)
        start_app(self.wx_package_name)
        sleep(3)
        self.to_search_entrance()

    def inspect_current_page(self):
        """
        检测当前页面
        :return:
        """
        if self.poco("当前所在页面,与的聊天").exists():
            print('现在 app 在首页位置，准备进入搜索入口')
            self.to_search_entrance()
        elif self.poco("当前所在页面,搜一搜").exists():
            print('现在 app 在搜索入口，准备进行搜索')
        elif self.poco('com.tencent.mm:id/b1o').exists():
            print('现在在公众号信息页面，准备返回搜索入口')
            self.poco("com.tencent.mm:id/kb").click()
        else:
            print('app 页面未检测到，准备重启')
            self.restart_app_to_search()
        return

    def search_and_click(self, name):
        """
        完整流程
        :param name:
        :return:
        """
        print('准备搜索公众号: ', name)
        try:
            item_info_dic = self.get_item_info(name)
            if item_info_dic:
                # 保存搜索名字
                item_info_dic['search_name'] = name
                biz, article_url = self.click_article()
                if biz and article_url:
                    item_info_dic['biz'] = biz
                    item_info_dic['article_url'] = article_url
            else:
                item_info_dic = {'search_name': name}
            return item_info_dic
        except Exception as e:
                traceback.print_exc()
                self.inspect_current_page()

    def mongo_run(self):
        self.inspect_current_page()

        for city_en in self.city_en_list:
            col = self.dp_db[f'dp_{city_en}_mall']
            mall_names = [mall.get('fullName') for mall in list(col.find())]
            for mall_name in mall_names:
                mall_wechat_info = self.wechat_col.find_one({'search_name': mall_name})
                if mall_name and not mall_wechat_info:

                    # if self.count == 200:
                    #     self.count = 0
                    #     time.sleep(3600)
                    # else:
                    #     self.count += 1

                    item_info_dic = self.search_and_click(mall_name)
                    if item_info_dic:
                        print(item_info_dic)
                        self.wechat_col.update_one({'search_name': item_info_dic['search_name']}, {'$set': item_info_dic}, True)

        print('数据抓取结束')

    def pandas_run_help(self, data):
        if self.pandas_col.find_one({'微信': data['微信']}):
            return
        item_info_dic = self.search_and_click(data['微信'])
        if item_info_dic:
            data['gzh_id'] = item_info_dic.get('biz')
            data['wechat_name'] = item_info_dic.get('wechat_name')
            data['wechat_url'] = item_info_dic.get('article_url')
        self.pandas_col.update_one({'微信': data['微信']}, {'$set': data.to_dict()}, True)
        print(data.to_dict())
        return

    def pandas_run(self):
        path = r'C:Users\Administrator\Desktop\test_brand.xls'
        df = pd.read_excel(path)
        df.apply(lambda x: self.pandas_run_help(x), axis=1)

    def test_run(self):
        # 测试出现任然搜索的情况
        self.search_and_click('beceas')


def main():
    device_host = '127.0.0.1:21503'
    air_spider = AirTestSpider(device_host)
    air_spider.mongo_run()
    # air_spider.pandas_run()
    # air_spider.test_run()


if __name__ == '__main__':
    main()
