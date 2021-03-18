# coding=gbk
import scrapy
from re import match, findall
from time import time
from json import loads
from requests import get

from NewsCrawler.items import NewsItem
from NewsCrawler.utils.validate_published import validate_replace


class SinaSpider(scrapy.Spider):
    """����7*24Сʱȫ��ʵʱ�ƾ�����ֱ��"""
    name = 'sina'
    allowed_domains = ['sina.com.cn']

    base_url = 'http://zhibo.sina.com.cn/api/zhibo/feed?page=%(page)s&page_size=20&zhibo_id=152&tag_id=0&dire=f&dpc=1&_=%(time_stamp)s'
    start_urls = [base_url % {'page': 1, 'time_stamp': str(time()).replace('.', '')[:-4]}]

    def parse(self, response):
        item = NewsItem()
        data = loads(response.text)
        data_list = data['result']['data']['feed']['list']
        for i in data_list:
            item['news_id'] = i['id']
            original_content = i['rich_text'].strip().replace('\r\n', '')
            pattern = match('��(.*?)��', original_content)
            if pattern:
                pattern2 = findall('��(.*?)��(.*)', original_content)
                item['content'] = pattern2[0][1].strip()
                item['title'] = pattern2[0][0].strip()
            else:
                item['title'] = i['rich_text'].strip()
                item['content'] = i['rich_text'].strip()
            item['link'] = i['docurl']
            item['published'] = validate_replace(i['update_time'])
            item['nav_name'] = [tag['name'] for tag in i['tag']]
            media = i['multimedia']
            if media:
                item['images'] = [get(url).content for url in media['img_url']]
            else:
                item['images'] = None
            yield item
        # parse page
        page_info = data['result']['data']['feed']['page_info']
        next_page = page_info['nextPage']
        if not page_info['totalPage'] == page_info['page']:
            yield scrapy.Request(
                self.base_url % {'page': next_page, 'time_stamp': str(time()).replace('.', '')[:-4]},
                callback=self.parse,
            )
        else:
            print('��ȡ���')
