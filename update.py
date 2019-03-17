import time
import datetime
#import dryscrape
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.request import Request, urlopen


client = MongoClient('localhost', 27017)
db = client['prices']
entries = db['entries']
metrics = db['metrics']


def update_entries(pause):
    lst = []
    for document in entries.find():
        lst.append(document)

    while lst:
        element = lst.pop()
        if element['store'] == 'PcGarage':
            metrics.insert_one(update_entry_garage(element))
        elif element['store'] == 'Emag':
            metrics.insert_one(update_entry_mag(element))
        print('Sleeping {} seconds.'.format(pause))
        time.sleep(pause)

    print('End of one update.')


# PCGARAGE
def update_entry_garage(entry):
    req = Request(entry['link'], headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    soup = BeautifulSoup(webpage, 'html.parser')

    item = {}
    item['name'] = entry['name']
    item['price'] = soup.find('meta', {'itemprop': 'price'})['content']
    item['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return item


# EMAG
def update_entry_mag(entry):
    session = dryscrape.Session()
    session.visit(entry['link'])
    response = session.body()
    soup = BeautifulSoup(response, 'html.parser')

    item = {}
    item['name'] = entry['name']
    price = soup.find('p', {'class': 'product-new-price'}).text.strip().split()[0].replace('.', '')
    item['price'] = price[:-2] + '.' + price[-2:]
    item['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return item


if __name__ == '__main__':
    sec = 1200
    count = entries.count()
    update_entries(sec//count)
