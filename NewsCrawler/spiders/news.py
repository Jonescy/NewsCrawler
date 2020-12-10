import scrapy
import requests
import time
import json
from ..items import NewsCrawlerItem
from urllib.parse import urljoin


class NewsSpider(scrapy.Spider):
    """新华网财经频道"""
    name = 'news'
    timestamp = str(time.time()).replace('.', '')[:-4]
    base_url = 'http://da.wa.news.cn/nodeart/page?nid=11214126&pgnum=%(page)s&cnt=20&attr=&tp=1&orderby=1&_=%(timestamp)s'

    def start_requests(self):

        start_urls = ['http://www.xinhuanet.com/whxw.htm']
        for url in start_urls:
            yield scrapy.Request(url=url, dont_filter=True)
        yield scrapy.Request(self.base_url % {'page': 1, 'timestamp': self.timestamp},
                             callback=self.parse_central_file,
                             dont_filter=True)

    def parse(self, response):
        item = NewsCrawlerItem()
        li_list = response.xpath('//ul[@class="dataList"]/li')
        for li in li_list:
            item['title'] = li.xpath('./h3/a/text()').extract_first()
            detail_link = li.xpath('./h3/a/@href').extract_first()

            # print(detail_link)
            if detail_link:
                item['detail_link'] = detail_link
                # print(detail_link)
                yield scrapy.Request(url=detail_link, meta={'item': item}, callback=self.parse_detail)

    def parse_detail(self, response):
        item = response.meta['item']
        source = response.xpath('//div[@class="h-info"]/span[2]/text()').extract_first().replace('\r\n', '').strip()
        if len(source) > 4:
            item['source'] = source
        else:
            source2 = response.xpath('//em[@id="source"]/text()').extract_first()
            if source2:

                item['source'] = source2.replace('\r\n', '').strip()
        item['published'] = response.xpath('//div[@class="h-info"]/span[1]/text()').extract_first()
        item['img'] = []
        item['content'] = []

        p_list = response.xpath('//div[@id="p-detail"]/p')

        for p in p_list:
            p_img = p.xpath('.//img')
            if p_img:
                img_src = urljoin(response.url, p_img.xpath('./@src').extract_first())
                item['content'].append(img_src)
                img_content = requests.get(img_src).content
                item['img'].append(img_content)
            else:
                text = p.xpath('.//text()').extract_first()
                if text:
                    item['content'].append(text.strip())
        yield item

    def parse_central_file(self, response):
        item = NewsCrawlerItem()
        json_str = json.loads(response.text)

        data_list = json_str['data']['list']
        for data in data_list:
            item['news_id'] = data['DocID']
            item['published'] = data['PubTime']
            item['title'] = data['Title']
            item['abstract'] = data['Abstract']
            item['source'] = data['SourceName']
            item['detail_link'] = data['LinkUrl']
            item['keywords'] = data['keyword']

            yield scrapy.Request(url=item['detail_link'], meta={'item': item}, callback=self.parse_file_detail)
        total_news = int(json_str['totalnum'])
        if total_news > 20:
            page = total_news // 20
            for i in range(2, page + 2):
                yield scrapy.Request(url=self.base_url % {'page': i, 'timestamp': self.timestamp}, callback=self.parse_central_file)

    def parse_file_detail(self, response):
        item = response.meta['item']

        p_list = response.xpath('//div[@class="xlcontent"]/p')
        item['content'] = []
        item['img'] = []
        for p in p_list:
            p_img = p.xpath('./img')
            if p_img:
                img_link = urljoin(response.url, p_img.xpath('./@src').extract_first())
                item['content'].append(img_link)
                img_content = requests.get(img_link).content
                item['img'].append(img_content)
            elif p.xpath('./strong'):
                sub = p.xpath('./strong/text()').extract_first()
                if sub:
                    item['content'].append(sub.strip())
            else:
                text = p.xpath('./text()').extract_first()
                if text:
                    item['content'].append(text.strip())
        yield item
