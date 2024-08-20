from bs4 import BeautifulSoup
import requests
import pandas as pd

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
base_url = 'https://www.datart.cz/vyhledavani?q='
item_csv = open('data/item.csv', 'r').read()
# delineate according to double commas or newlines
item_csv = item_csv.replace('""', ',').replace('\n', ',').split(',')
# get rid of empty strings
item_csv = [item for item in item_csv if item and '.' not in item]
count = len(item_csv)

# create df to store data
dtypes = {
    'item': str,
    'lessOrEqual': str,
    'actualPrice': str,
    'url': str,
    'cashback': str,
    'available': bool,
    'promo': bool
}

# necessary to prevent type inference that bugs everything
df = pd.DataFrame(columns=['item', 'lessOrEqual', 'actualPrice', 'url', 'cashback', 'available', 'promo']).astype(dtypes)
counter = 1

def find_correct_data_from_soup(soup: BeautifulSoup, item: str) -> BeautifulSoup:
    '''
    Finds the correct data from the soup. If the item is not a TV, it will search for the next occurrence.
    '''
    # find the first item in response
    search_product = soup.find('div', class_='product-box')
    
    # check for None
    if not search_product:
        print('No product found')
        return None
    
    while search_product:
        item_title = search_product.find('h3', class_='item-title').text
        if 'Televize' in item_title and ('Samsung' in item_title or 'LG' in item_title) and item in item_title:
            break
        search_product = search_product.find_next('div', class_='product-box')
        if not search_product:
            print('No product found')
            return None
    
    return search_product
    
for item in item_csv:
    print(f'[DATART-CZ] running: {item} ({counter}/{count})')
    # set url
    url = base_url + item
    # acquire entire response page
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
    actualPrice = search_product.find('div', class_='actual').text
    try:
        # find any del tags and get the text
        lessOrEqual = search_product.find('del').text
    except:
        lessOrEqual = actualPrice
    # check for cashback
    try:
        cashback = search_product.find('span', class_='flag flag-color-orange').text
    except AttributeError:
        cashback = 'N/A'
    # check for availability
    is_available = search_product.find('span', class_='product-availability-state color-text-red')
    available = False if is_available else True
    # check for promo
    is_promo = search_product.find('div', class_='product-promo')
    promo = True if is_promo else False
    # remove whitespace from actualPrice and lessOrEqual and get rid of the 'Kč' sign
    actualPrice = actualPrice.strip()
    lessOrEqual = lessOrEqual.strip()
    cashback = cashback.strip().replace('CASHBACK', '')
    print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, cashback: {cashback}, available: {available}, promo: {promo}')
    # now put both into df
    df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'cashback': cashback, 'available': available, 'promo': promo}
    counter += 1

# finally, print df and also store as excel
# print(df)
df.to_excel('res/datart-cz.xlsx', index=False)
