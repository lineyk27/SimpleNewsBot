from newsapi import newsapi_client
import constant
from time import sleep
import db_funcs
from tokens import *

client = newsapi_client.NewsApiClient(TOKEN_NEWS)


def get_urls(news_dict):
    # Return list of urls from dictionary returned by newsapi
    return [i['url'] for i in news_dict['articles']]


def notifier_news(callback):
    # This function work all time, and callback(send news) if last news was changed
    while True:
        for i in constant.CATEGORIES:
            for j in constant.COUNTRIES:
                news_dict = client.get_top_headlines(country=constant.COUNTRIES[j],
                                                     category=i,
                                                     page_size=1)

                news_urls = get_urls(news_dict)
                if news_urls[0] != db_funcs.get_last_news(i, j):
                    callback(i, j, news_urls[0])
                    db_funcs.change_last_news(i, j, news_urls[0])
        sleep(7200)  # 2 hours


def search_news(query, count=10):
    # This function search news by query sorted by last time
    try:
        res = client.get_everything(q=query,
                                    page_size=count,
                                    sort_by='publishedAt'
                                    )
    except newsapi_client.NewsAPIException:
        return None
    urls = [i['url'] for i in res['articles']]
    if not bool(urls):
        return None
    return urls
