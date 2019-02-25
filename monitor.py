import time

import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.request import Request, urlopen


client = MongoClient('localhost', 27017)
db = client['prices']
entries = db['entries']
metrics = db['metrics']


def create_entry(item_name):
    if not entries.find_one({'name': item_name}):
        entries.insert_one(create_entry_garage(item_name))
    else:
        print('Item already present.')


def create_entry_garage(item_name):
    brand_page = 'https://www.pcgarage.ro/cauta/'
    query_style = '+'.join(item_name.split(' '))
    req = Request(brand_page + query_style, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    soup = BeautifulSoup(webpage, 'html.parser')
    first_res = soup.find('div', {'class': 'product-list-container'}).findChild()

    item = {}
    item['name'] = item_name
    item['link'] = first_res.find('div', {'class': 'product-box'}).findChild().findChild()['href']
    return item


def update_entry_garage(entry):
    req = Request(entry['link'], headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    soup = BeautifulSoup(webpage, 'html.parser')

    item = {}
    item['name'] = entry['name']
    item['price'] = soup.find('meta', {'itemprop': 'price'})['content']
    item['date'] = datetime.datetime.now()
    return item


def update_entries(pause):
    lst = []
    for document in entries.find():
        lst.append(document)

    while lst:
        metrics.insert_one(update_entry_garage(lst.pop()))
        print('Sleeping {} seconds.'.format(pause))
        time.sleep(pause)

    print('End of one update.')


if __name__ == '__main__':
    sec = 7200
    # item_name = 'Memorie HyperX Fury Black 8GB DDR4 2400MHz CL15 1.2v'
    # create_entry(item_name)
    count = entries.count()
    update_entries(sec//count)