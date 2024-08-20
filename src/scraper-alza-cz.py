from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from Exceptions import ProbablyDoesNotExistException

hdr = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers'
}

# define base url(s) 
base_url = 'https://www.alza.cz/search.htm?exps='
item_csv = open('data/alza-item.csv', 'r').read()
# delineate according to double commas or newlines
item_csv = item_csv.replace('""', ',').replace('\n', ',').split(',')
# get rid of empty strings
item_csv = [item for item in item_csv if item and '.' not in item]
# knock final 2 chars off each item
item_csv = [item[:-2] for item in item_csv]
# print(item_csv)
count = len(item_csv)

# create df to store data
dtypes = {
    'item': str,
    'lessOrEqual': str,
    'actualPrice': str,
    'url': str,
    # 'cashback': str,
    'available': bool,
    'promo': bool
}

# necessary to prevent type inference that bugs everything
df = pd.DataFrame(columns=['item', 'lessOrEqual', 'actualPrice', 'url', 'available', 'promo']).astype(dtypes)
counter = 1
rerun = []

def find_correct_data_from_soup(soup: BeautifulSoup, item: str) -> BeautifulSoup:
    '''
    Finds the correct data from the soup. If the item is not a TV, it will search for the next occurrence.
    '''
    # find the first item in response
    # find any divs with class name that starts with 'box browsingitem js-box canBuy inStockAvailability' but can end with anything
    search_product = soup.find(
            'div', 
            class_=re.compile(r'(?=.*\bbox\b)(?=.*\bbrowsingitem\b)(?=.*\bjs-box\b)')
    )
    # check for None
    if not search_product:
        print('No product found. Rerunning this product.')
        rerun.append(item)
        return None
    
    while search_product:
        item_title = search_product.find('a', class_='name browsinglink js-box-link').text
        if ('Samsung' in item_title or 'LG' in item_title) and item in item_title:
            break

        search_product = search_product.find_next(
            'div', 
            class_=re.compile(r'(?=.*\bbox\b)(?=.*\bbrowsingitem\b)(?=.*\bjs-box\b)')
        )
        if not search_product:
            print('No product found (searched entire page)')
            return None
    
    return search_product

# main loop
for item in item_csv:
    print(f'[ALZA-CZ] running: {item} ({counter}/{count})')
    # set url
    url = base_url + item

    try:
        response = requests.get(url, headers=hdr)
    except:
        # handle error
        print('Response Error: ', item)
        continue
    # parse response page
    soup = BeautifulSoup(response.content, 'html.parser')
    # find the correct data from the soup
    search_product = find_correct_data_from_soup(soup, item)
    if not search_product:
        counter += 1
        continue
    # now scrape from class name 'lessOrEqual' and 'actual' from 'items' variable
    actualPrice = search_product.find('span', class_='price-box__price').text
    try:
        # find any del tags and get the text
        lessOrEqual = search_product.find('span', class_="price-box__compare-price").text
    except:
        lessOrEqual = actualPrice
    # check for availability
    is_available = search_product.find('span', class_='avlVal avl3 none') or search_product.find('span', class_='avlVal avl2 none') or search_product.find('span', class_='avlVal avl0 variant')
    available = False if is_available else True
    # check for promo
    is_promo = search_product.find('span', class_='prcoupon-block__label')
    promo = True if is_promo else False
    actualPrice = actualPrice.strip()
    lessOrEqual = lessOrEqual.strip()
    print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, available: {available}')
    # now put both into df
    df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'available': available, 'promo': promo}
    counter += 1

bleft = len(rerun)
die_counter = 0
# rerun the failed items
while len(rerun) > 0:
    item = rerun.pop(0)
    aleft = len(rerun)
    if aleft == bleft:
        die_counter += 1
    else: 
        die_counter = 0
    bleft = aleft
    print(f'[ALZA-CZ] rerunning: {item} ({bleft} items left to re run)')
    # set url
    url = base_url + item

    if die_counter > 100:
        print('Too many failed attempts. The items probably do not exist.')
        break
    
    try:
        response = requests.get(url, headers=hdr)
    except:
        # handle error
        print('Response Error: ', item)
        continue
    # parse response page
    soup = BeautifulSoup(response.content, 'html.parser')
    # find the correct data from the soup
    search_product = find_correct_data_from_soup(soup, item)
    if not search_product:
        counter += 1
        continue
    # now scrape from class name 'lessOrEqual' and 'actual' from 'items' variable
    actualPrice = search_product.find('span', class_='price-box__price').text
    try:
        # find any del tags and get the text
        lessOrEqual = search_product.find('span', class_="price-box__compare-price").text
    except:
        lessOrEqual = actualPrice
    # check for availability
    is_available = search_product.find('span', class_='avlVal avl3 none') or search_product.find('span', class_='avlVal avl2 none') or search_product.find('span', class_='avlVal avl0 variant')
    available = False if is_available else True
    # check for promo
    is_promo = search_product.find('span', class_='prcoupon-block__label')
    promo = True if is_promo else False
    actualPrice = actualPrice.strip()
    lessOrEqual = lessOrEqual.strip()
    print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, available: {available}')
    # now put both into df
    df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'available': available, 'promo': promo}
    
# finally, print df and also store as excel
df.to_excel('res/alza-cz.xlsx', index=False)