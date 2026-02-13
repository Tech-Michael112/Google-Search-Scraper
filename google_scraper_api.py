#!/usr/bin/env python3

from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import time
import urllib.parse
import re
from datetime import datetime
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import tempfile
import atexit
import signal
import sys

app = Flask(__name__)

class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.cookie_last_updated = None
        self.cookie_expiry_hours = 2
        self.driver = None
        self.temp_dir = tempfile.mkdtemp()
        self.cookie_file = os.path.join(self.temp_dir, 'google_cookies.pkl')
        self.initialize_headers_and_cookies()
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

    def get_cookies_from_browser(self):
        cookies_dict = {}
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.get("https://www.google.com")
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(3)
            
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies_dict, f)
                
        except Exception as e:
            print(f"Browser error: {e}")
            if os.path.exists(self.cookie_file):
                try:
                    with open(self.cookie_file, 'rb') as f:
                        cookies_dict = pickle.load(f)
                except:
                    pass
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return cookies_dict

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-platform': '"Linux"',
            'upgrade-insecure-requests': "1",
            'accept-language': "en-US,en;q=0.9",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'referer': "https://www.google.com/",
        }

        browser_cookies = self.get_cookies_from_browser()
        if browser_cookies:
            self.current_cookies = browser_cookies
        else:
            self.current_cookies = {}
        
        self.update_cookie_header()
        self.cookie_last_updated = datetime.now()

    def update_cookie_header(self):
        cookie_string = '; '.join([f"{name}={value}" for name, value in self.current_cookies.items()])
        self.headers['Cookie'] = cookie_string

    def should_refresh_cookies(self):
        if not self.cookie_last_updated:
            return True
        time_since_update = datetime.now() - self.cookie_last_updated
        return time_since_update.total_seconds() > (self.cookie_expiry_hours * 3600)

    def refresh_cookies(self):
        browser_cookies = self.get_cookies_from_browser()
        if browser_cookies:
            self.current_cookies = browser_cookies
            self.update_cookie_header()
            self.cookie_last_updated = datetime.now()
            return True
        return False

    def ensure_fresh_cookies(self):
        if self.should_refresh_cookies():
            return self.refresh_cookies()
        return True

    def parse_google_search_results(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        dictionary_result = self.extract_dictionary_result(soup)
        if dictionary_result:
            results.append(dictionary_result)

        regular_results = self.extract_regular_results(soup)
        results.extend(regular_results)

        metadata = self.extract_search_metadata(soup)

        return {
            'metadata': metadata,
            'results': results,
            'total_results': len(results)
        }

    def extract_dictionary_result(self, soup):
        dictionary_selectors = [
            {'data-dobid': 'hdw'},
            {'class': 'LTKOO'},
            {'class': 'sY7ric'},
            {'class': 'kno-ecr-pt'}
        ]

        dictionary_div = None
        for selector in dictionary_selectors:
            dictionary_div = soup.find('div', selector)
            if dictionary_div:
                break

        if not dictionary_div:
            return None

        result = {
            'type': 'dictionary',
            'word': dictionary_div.get_text(strip=True),
            'pronunciation': '',
            'definitions': [],
            'examples': [],
            'similar_words': []
        }

        pronunciation_selectors = ['span.ApHyTb', 'span.pronunciation', 'span.rtng']
        for selector in pronunciation_selectors:
            pronunciation = soup.select_one(selector)
            if pronunciation:
                result['pronunciation'] = pronunciation.get_text(strip=True)
                break

        definition_elements = soup.find_all('div', {'data-attrid': re.compile('.*definition.*|.*SenseDefinition.*')})
        for def_element in definition_elements:
            definition_text = def_element.find('span', {'data-dobid': 'dfn'}) or def_element.find('span')
            if definition_text:
                definition = definition_text.get_text(strip=True)
                if definition and len(definition) > 10:
                    result['definitions'].append(definition)
                    example = def_element.find('div', class_='ZYHQ7e') or def_element.find('div', class_=re.compile('.*example.*'))
                    if example:
                        result['examples'].append(example.get_text(strip=True))

        similar_words_containers = [
            'div.qFRZdb', 'div.related-words', 'div.kno-swp', 'div.similar-words'
        ]

        for container_selector in similar_words_containers:
            similar_words_container = soup.select_one(container_selector)
            if similar_words_container:
                similar_words = similar_words_container.find_all('span', class_=re.compile('.*word.*|.*clOx1e.*'))
                for word in similar_words:
                    word_text = word.get_text(strip=True)
                    if word_text and len(word_text) > 1:
                        result['similar_words'].append(word_text)
                break

        return result

    def extract_regular_results(self, soup):
        results = []
        result_selectors = [
            'div.g', 'div.MjjYud', 'div.tF2Cxc', 'div.rc',
            'div[data-hveid]', 'div[data-ved]', 'div.section'
        ]

        for selector in result_selectors:
            result_containers = soup.select(selector)
            for container in result_containers:
                result_data = self.extract_single_result(container)
                if result_data and result_data.get('title') and result_data.get('url'):
                    results.append(result_data)

        return results

    def extract_single_result(self, container):
        result = {
            'type': 'regular',
            'title': '',
            'url': '',
            'description': '',
            'snippet': '',
            'source': '',
            'date': ''
        }

        title_selectors = ['h3', 'a h3', '.DKV0Md', '.LC20lb', '.MBeuO']
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
                break

        link_elem = container.find('a')
        if link_elem and link_elem.get('href'):
            result['url'] = link_elem['href']
            if result['url'].startswith('/url?q='):
                result['url'] = result['url'].split('/url?q=')[1].split('&')[0]
                result['url'] = urllib.parse.unquote(result['url'])

        desc_selectors = [
            '.VwiC3b', '.MUxGbd', '.s3v9rd', '.aCOpRe',
            'span[class*="snippet"]', 'div[class*="snippet"]',
            'span[class*="description"]', 'div[class*="description"]'
        ]

        for selector in desc_selectors:
            desc_elem = container.select_one(selector)
            if desc_elem:
                result['description'] = desc_elem.get_text(strip=True)
                break

        source_selectors = ['cite', '.TbwUpd', '.iUh30', '.fjqwze']
        for selector in source_selectors:
            source_elem = container.select_one(selector)
            if source_elem:
                result['source'] = source_elem.get_text(strip=True)
                break

        date_selectors = ['span.f', '.MUxGbd.wuQ4Ob.WZ8Tjf', '.LEwnzc']
        for selector in date_selectors:
            date_elem = container.select_one(selector)
            if date_elem:
                result['date'] = date_elem.get_text(strip=True)
                break

        return result

    def extract_search_metadata(self, soup):
        metadata = {
            'query': '',
            'filters': [],
            'result_stats': ''
        }

        search_input = soup.find('textarea', {'name': 'q'})
        if search_input:
            metadata['query'] = search_input.get('value', '')

        filter_selectors = [
            'div[class*="filter"]', 'div[class*="tab"]', 'a[class*="filter"]',
            'a[class*="tab"]', '.hdtb-mitem', '.hdtbItm'
        ]

        for selector in filter_selectors:
            filter_elements = soup.select(selector)
            for filter_elem in filter_elements:
                filter_text = filter_elem.get_text(strip=True)
                if (filter_text and len(filter_text) > 2 and
                    len(filter_text) < 50 and
                    filter_text.lower() not in ['all', 'images', 'videos', 'news', 'maps']):
                    metadata['filters'].append(filter_text)

        stats_selectors = ['#result-stats', '.appbar', '.sd', '#search']
        for selector in stats_selectors:
            stats_elem = soup.select_one(selector)
            if stats_elem:
                metadata['result_stats'] = stats_elem.get_text(strip=True)
                break

        return metadata

    def get_next_page_url(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        next_page_selectors = [
            'a#pnnext',
            'a[aria-label*="Next"]',
            'a[class*="next"]',
            'a.fl'
        ]

        for selector in next_page_selectors:
            next_page_link = soup.select_one(selector)
            if next_page_link and next_page_link.get('href'):
                next_url = next_page_link.get('href')
                if next_url.startswith('/'):
                    return "https://www.google.com" + next_url
                return next_url
        return None

    def search_single_page(self, query, start=0):
        if not self.ensure_fresh_cookies():
            pass

        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'start': start}

        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            page_data = self.parse_google_search_results(response.text)
            next_url = self.get_next_page_url(response.text)
            
            return {
                'success': True,
                'page': (start // 10) + 1,
                'query': query,
                'results': page_data['results'],
                'total_results': len(page_data['results']),
                'next_page': next_url is not None,
                'next_start': start + 10 if next_url else None,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'page': (start // 10) + 1
            }

    def search_all_pages(self, query, max_pages=10):
        if not self.ensure_fresh_cookies():
            pass

        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en'}

        all_results = []
        current_page = 1
        next_url = base_url

        while next_url and current_page <= max_pages:
            try:
                if current_page == 1:
                    response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
                else:
                    response = self.session.get(next_url, headers=self.headers, timeout=15)

                response.raise_for_status()
                page_data = self.parse_google_search_results(response.text)
                all_results.extend(page_data['results'])
                next_url = self.get_next_page_url(response.text)

                if next_url:
                    time.sleep(1)
                
                current_page += 1

            except Exception as e:
                break

        return {
            'success': True,
            'query': query,
            'total_pages_scraped': current_page - 1,
            'total_results': len(all_results),
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }


scraper = GoogleSearchScraper()


@app.route('/')
def home():
    return jsonify({
        'status': 'Google Search Scraper API',
        'version': '1.0',
        'endpoints': {
            '/search': 'GET - Search single page (params: q, page)',
            '/search/all': 'GET - Search all pages (params: q, max_pages)',
        },
        'examples': {
            'single_page': '/search?q=python&page=1',
            'all_pages': '/search/all?q=python&max_pages=5'
        }
    })


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if page < 1:
        return jsonify({'error': 'Page must be >= 1'}), 400
    
    start = (page - 1) * 10
    result = scraper.search_single_page(query, start)
    
    return jsonify(result)


@app.route('/search/all', methods=['GET'])
def search_all():
    query = request.args.get('q', '').strip()
    max_pages = int(request.args.get('max_pages', 10))
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if max_pages < 1 or max_pages > 50:
        return jsonify({'error': 'max_pages must be between 1 and 50'}), 400
    
    result = scraper.search_all_pages(query, max_pages)
    
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
