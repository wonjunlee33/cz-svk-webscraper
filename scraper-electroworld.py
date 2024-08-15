from bs4 import BeautifulSoup
import pandas as pd
from playwright.sync_api import sync_playwright

# define base url(s) 
base_url = 'https://www.electroworld.cz/vysledky-vyhledavani?q='
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
    'promo': bool
}

# necessary to prevent type inference that bugs everything
df = pd.DataFrame(columns=['item', 'lessOrEqual', 'actualPrice', 'url', 'available', 'promo']).astype(dtypes)
counter = 1

def find_correct_data_from_soup(soup: BeautifulSoup, item: str) -> BeautifulSoup:
    '''
    Finds the correct data from the soup. If the item is not a TV, it will search for the next occurrence.
    '''
    # find the first item in response
    # search product must be a section that contains class name 'product-box'
    search_product = soup.find('section', class_='product-box product-box--main position-relative bg-white bs-p-3 bs-p-sm-4 typo-complex-12 flex-grow-0 flex-shrink-0')
    # print(search_product)
    
    # check for None
    if not search_product:
        print('something is extremely broken')
        return None
    
    while search_product:
        item_title = search_product.find('h3', class_='product-box__name bs-m-0 font-weight-bold typo-complex-14 typo-complex-sm-16').text
        # print(item_title)
        if ('Samsung' in item_title or 'LG' in item_title) and item in item_title:
            break
        search_product = search_product.find_next('div', class_='product-box product-box--main position-relative bg-white bs-p-3 bs-p-sm-4 typo-complex-12 flex-grow-0 flex-shrink-0')
        if not search_product:
            print('No product found (searched entire page)')
            return None
    
    return search_product

for item in item_csv:
    print(f'running: {item} ({counter}/{count})')
    # set url
    url = base_url + item
    # here, we use playwright to get the content
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Wait for the element to appear
        # wait for this class. if does not appear for 5 seconds, it will raise an error
        try:
            # page.wait_for_selector('.product-box.product-box--main.position-relative.bg-white.bs-p-3.bs-p-sm-4.typo-complex-12.flex-grow-0.flex-shrink-0', timeout=5000)
            page.wait_for_selector('.product-box__availability.bs-mb-sm-n2.bs-mx-sm-n2.d-flex', timeout=5000)
        except:
            print('TimeoutError: Either the page took too long to load or the element was not found.')
            browser.close()
            counter += 1
            continue
        # Get the content and process with BeautifulSoup
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        browser.close()
    # print(soup)
    # find the correct data from the soup
    search_product = find_correct_data_from_soup(soup, item)
    if not search_product:
        counter += 1
        continue
    # now scrape from class name 'lessOrEqual' and 'actual' from 'items' variable
    actualPrice = search_product.find('strong', class_='typo-complex-16').text
    try:
        # find any del tags and get the text
        lessOrEqual = search_product.find('del').text
    except:
        lessOrEqual = actualPrice
    # check for cashback
    # try:
    #     cashback = search_product.find('span', class_='flag flag-color-orange').text
    # except AttributeError:
    #     cashback = 'N/A'
    # check for availability
    is_available = search_product.find('i', class_='icon-check icon-fs-15 bs-mr-2')
    available = True if is_available else False
    # check for promo
    # is_promo = search_product.find('div', class_='product-promo')
    promo = False if lessOrEqual == actualPrice else True
    # remove whitespace from actualPrice and lessOrEqual and get rid of the 'Kč' sign
    actualPrice = actualPrice.strip()
    lessOrEqual = lessOrEqual.strip()
    # cashback = cashback.strip().replace('CASHBACK', '')
    print(f'actualPrice: {actualPrice}, lessOrEqual: {lessOrEqual}, available: {available}, promo: {promo}')
    # now put both into df
    df.loc[len(df)] = {'item': item, 'lessOrEqual': lessOrEqual, 'actualPrice': actualPrice, 'url': url, 'available': available, 'promo': promo}
    counter += 1

# finally, print df and also store as excel
print(df)
df.to_excel('electroworld.xlsx', index=False)
