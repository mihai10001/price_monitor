from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import quote
from urllib.request import Request, urlopen
from flask import Flask, render_template, g, Blueprint, jsonify, request as reqflask

# FLASK SETUP
app = Flask(__name__)

# MONGO SETUP
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


@app.route('/')
def home():
    products = []
    for document in entries.find():
        products.append(document['name'])

    return render_template('home.html', products=products)


@app.route('/graph/<string:name>')
def graph(name):
    date, price = [], []
    for document in metrics.find({'name': name}):
        date.append(document['date'])
        price.append(document['price'])

    return render_template('graph.html', name=name, date=date, price=price)


@app.route('/add', methods=['GET', 'POST'])
def add():
    stores = []
    for dist in entries.find().distinct('store'):
        stores.append(dist)

    if reqflask.form.get('submit') == 'Adauga':
        item_name = reqflask.form.get('produs')
        store = reqflask.form.get('magazin')
        if item_name and store:
            create_entry(item_name, store)

    return render_template('add.html', stores=stores)