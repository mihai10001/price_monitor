import time
import datetime
import dryscrape  # sudo apt-get install qt5-default
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import quote
from urllib.request import Request, urlopen


client = MongoClient('localhost', 27017)
db = client['prices']
entries = db['entries']
metrics = db['metrics']


def create_entry(item_name, store):
    if not entries.find_one({'name': item_name}):
        if store == 'PcGarage':
            entries.insert_one(create_entry_garage(item_name))
        elif store == 'Emag':
            entries.insert_one(create_entry_mag(item_name))
    else:
        print('Item already present.')


# PCGARAGE
def create_entry_garage(item_name):
    brand_page = 'https://www.pcgarage.ro/cauta/'
    query_style = '+'.join(item_name.split(' '))
    req = Request(brand_page + query_style, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    soup = BeautifulSoup(webpage, 'html.parser')
    first_res = soup.find('div', {'class': 'product-list-container'}).findChild()

    item = {}
    item['store'] = 'PcGarage'
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


# EMAG
def create_entry_mag(item_name):
    brand_page = 'https://www.emag.ro/search/'
    req = Request(brand_page + quote(item_name), headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    soup = BeautifulSoup(webpage, 'html.parser')
    first_res = soup.find('div', {'class': 'js-products-container'}).findChild()

    item = {}
    item['store'] = 'Emag'
    item['name'] = item_name
    item['link'] = first_res.find('div', {'class': 'card'}).findChild().findChild().findChild().findChild()['href']
    return item


def update_entry_mag(entry):
    session = dryscrape.Session()
    session.visit(entry['link'])
    response = session.body()
    soup = BeautifulSoup(response, 'html.parser')

    item = {}
    item['name'] = entry['name']
    price = soup.find('p', {'class': 'product-new-price'}).text.strip().split()[0].replace('.', '')
    item['price'] = price[:-2] + '.' + price[-2:]
    item['date'] = datetime.datetime.now()
    return item


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


if __name__ == '__main__':
    # sec = 7200
    sec = 30
    item_name = 'Lada frigorifica Zanussi ZFC26400WA, 260 l, Clasa A+, Alb'
    create_entry(item_name, store='Emag')
    count = entries.count()
    update_entries(sec//count)
