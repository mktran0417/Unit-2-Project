import time
import pandas as pd
from bs4 import BeautifulSoup as bs
import json
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

class Scrape():
    def __init__(self, driver):
        self.driver = driver
        self.urls = []
        self.phones_dict = []
        self.failed = []
        return

    def scrape_phone_urls(self):
        results = bs(self.driver.page_source, 'html.parser')
        finder_results = results.find(
            'div', class_='container-fluid phones-listing')
        phones = finder_results.findAll('a', class_='thumbnail')
        phones_list = []

        widget_pagination = results.find('ul', class_='widgetPagination__list')
        values = widget_pagination.findAll('li')
        NUMBER_OF_PAGES = int(values.pop(-2).text.strip('\n'))

        for i in range(1, NUMBER_OF_PAGES):
            if i != 1:
                clicker = self.driver.find_element_by_class_name(
                    'widgetPagination')
                next_page = clicker.find_elements_by_class_name(
                    'widgetPagination__list_item')
                next_page = next_page.pop()
                next_page.click()

            time.sleep(2)
            results = bs(self.driver.page_source, 'html.parser')
            finder_results = results.find(
                'div', class_='container-fluid phones-listing')
            phones = finder_results.findAll('a', class_='thumbnail')
            phones_list = phones_list + \
                [phone.attrs['href'] for phone in phones]
            self.urls = phones_list
        return

    def urls_to_csv(self):
        self.to_csv(pd.DataFrame(data=self.urls, columns=['url'], index=False))

    def load_phone_urls(self, url):
        with open(url) as fp:
            self.urls = fp.read().split()
        try:
            self.urls.remove('url')
        except:
            pass

    def scrape_specs(self):
        phones_dict = []
        for index, phone in enumerate(tqdm(self.urls)):
            self.driver.get(phone)
            time.sleep(2)
            results = bs(self.driver.page_source, 'html.parser')
            time.sleep(2)
            widget = results.find('div', class_='widgetSpecs')
            name = results.find(
                'section', class_='page__section page__section_quickSpecs').h1.text
            tables = widget.findAll('tbody')
            phone_dict = {'Name': name}
            for table in tables:
                for span in table.findAll('span'):
                    span.unwrap()
            for table in tables:
                for tr in table.findAll('tr'):
                    if(not tr.get('class') == ['has-alternative-variants']):
                        try:
                            key = tr.text.strip().split(':', 1)[0]
                            value = tr.text.strip().replace(
                                '\n', '').split(':', 1)[1]
                            phone_dict.update({key: value})
                        except:
                            self.failed.append(tr.text)

            phones_dict.append(phone_dict)
            self.phones_dict = phones_dict
        return

    def dump_json(self, filename):
        with open(filename, 'w') as fp:
            json.dump(self.phones_dict, fp)

