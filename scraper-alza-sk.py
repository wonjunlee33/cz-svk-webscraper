from bs4 import BeautifulSoup
import pandas as pd
import re
import requests

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
base_url = 'https://www.alza.sk/search.htm?exps='
item_csv = open('alza-item.csv', 'r').read()
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
    # 'promo': bool
}

# necessary to prevent type inference that bugs everything
df = pd.DataFrame(columns=['item', 'lessOrEqual', 'actualPrice', 'url', 'available']).astype(dtypes)
counter = 1

rerun = []

def find_correct_data_from_soup(soup: BeautifulSoup, item: str) -> BeautifulSoup:
    '''
    Finds the correct data from the soup. If the item is not a TV, it will search for the next occurrence.
    '''
    # find the first item in response
    # search_product = soup.find('div', class_='box browsingitem js-box canBuy inStockAvailability')
    # find any divs with class name that starts with 'box browsingitem js-box canBuy inStockAvailability' but can end with anything
    search_product = soup.find(
            'div', 
            # class_=re.compile(r'(?=.*\bbox\b)(?=.*\bbrowsingitem\b)(?=.*\bjs-box\b)(?=.*\bcanBuy\b)(?=.*\binStockAvailability\b)')
            class_=re.compile(r'(?=.*\bbox\b)(?=.*\bbrowsingitem\b)(?=.*\bjs-box\b)')
    )
    # check for None
    if not search_product:
        print('No product found (no search results)')
        rerun.append(item)
        # raise ValueError('Dying')
        return None
    
    while search_product:
        item_title = search_product.find('a', class_='name browsinglink js-box-link').text
        if ('Samsung' in item_title or 'LG' in item_title) and item in item_title:
            break
        # match anything that has 'box browsingitem js-box canBuy inStockAvailability' in it 
        search_product = search_product.find_next(
            'div', 
            class_=re.compile(r'(?=.*\bbox\b)(?=.*\bbrowsingitem\b)(?=.*\bjs-box\b)')
        )
        if not search_product:
            print('No product found (searched entire page)')
            return None
    
    return search_product

# first pass
for item in item_csv:
    print(f'[ALZA-SK] running: {item} ({counter}/{count})')
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
    # print(soup.prettify())
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
    # check for cashback
    # try:
    #     cashback = search_product.find('span', class_='flag flag-color-orange').text
    # except AttributeError:
    #     cashback = 'N/A'
    # check for availability
    is_available = search_product.find('span', class_='avlVal avl3 none') or search_product.find('span', class_='avlVal avl2 none')
    if not is_available:
        is_available = 'Očakávame' in search_product.find('span', class_='avlVal avl1 none').text if search_product.find('span', class_='avlVal avl1 none') else False
    available = False if is_available else True
    # check for promo
    # is_promo = search_product.find('div', class_='product-promo')
    # promo = True if is_promo else False
    # remove whitespace from actualPrice and lessOrEqual
    actualPrice = actualPrice.strip()
    lessOrEqual = lessOrEqual.strip()
    # cashback = cashback.strip().replace('CASHBACK', '')
    # print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, cashback: {cashback}, available: {available}, promo: {promo}')
    print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, available: {available}')
    # now put both into df
    # df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'cashback': cashback, 'available': available, 'promo': promo}
    df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'available': available}
    counter += 1

# count = len(rerun)
# counter = 1
# # rerun all broken instances until none are left
# while len(rerun) > 0:
#     item = rerun.pop(0)
#     print(f'[ALZA] re-running: {item} ({counter}/{count})')
#     url = base_url + item
#     try: 
#         response = requests.get(url, headers=hdr)
#     except:
#         print('Response Error: ', item)
#         continue
#     soup = BeautifulSoup(response.content, 'html.parser')
#     search_product = find_correct_data_from_soup(soup, item)
#     if not search_product:
#         counter += 1
#         continue
#     actualPrice = search_product.find('span', class_='price-box__price').text
#     try:
#         lessOrEqual = search_product.find('span', class_="price-box__compare-price").text
#     except:
#         lessOrEqual = actualPrice
#     is_available = search_product.find('span', class_='avlVal avl3 none') or search_product.find('span', class_='avlVal avl2 none')
#     available = False if is_available else True
#     actualPrice = actualPrice.strip()
#     lessOrEqual = lessOrEqual.strip()
#     print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, available: {available}')
#     df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'available': available}
#     counter += 1
#     count = len(rerun)
    
# finally, print df and also store as excel
# print(df)
df.to_excel('alza-sk.xlsx', index=False)