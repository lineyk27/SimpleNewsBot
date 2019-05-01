from newsapi import newsapi_client
import constant
from time import sleep
import db_funcs

client = newsapi_client.NewsApiClient(constant.TOKEN_NEWS)


def get_urls(news_dict):
    return [i['url'] for i in news_dict['articles']]


def notifier_news(callback):
    countries = [i for i in constant.COUNTRIES]
    categories = constant.CATEGORIES

    while True:
        for i in categories:
            for j in countries:
                news_dict = client.get_top_headlines(country=constant.COUNTRIES[j],
                                                     category=i,
                                                     page_size=7)
                news_urls = get_urls(news_dict)

                #  k = 0
                #  while news_urls[k] != db_funcs.get_last_news(i, j):
                callback(i, j, news_urls[0])
                #  k += 1
                db_funcs.change_last_news(i, j, news_urls[0])

        sleep(1000)
        #  2 hours and 58 min. and 40 secs.
        # TODO: need to change, need calculate average needed time


def search_news(query, count=10):
    try:
        res = client.get_everything(q=query, page_size=count, sort_by='publishedAt')
    except newsapi_client.NewsAPIException:
        return None
    urls = [i['url'] for i in res['articles']]
    if not bool(urls):
        return None
    return urls
