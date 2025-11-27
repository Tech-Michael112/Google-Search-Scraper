#!/usr/bin/env python3

from bs4 import BeautifulSoup
import time
import urllib.parse
import json
import re
from datetime import datetime
import requests
import sys,os
os.system('clear')
print('\033[1;91m NOTE: \033[0mIF too many requests are being sent,\r use flight mode For lasting scraping')
class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.cookie_last_updated = None
        self.cookie_expiry_hours = 2
        self.initialize_headers_and_cookies()

    def get_cookies_from_api(self):
        try:
            url = "https://cookieLogger.pythonanywhere.com/get/mykey"
            headers = {"Authorization": "169e1538-b8dd-4faa-a636-f8173230a4c1"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            cookie_string = data.get("cookie", "")
            cookies_dict = {}
            for cookie_part in cookie_string.split(';'):
                cookie_part = cookie_part.strip()
                if '=' in cookie_part:
                    name, value = cookie_part.split('=', 1)
                    cookies_dict[name.strip()] = value.strip()
            return cookies_dict
        except Exception:
            return None

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-platform': "\"Linux\"",
            'upgrade-insecure-requests': "1",
            'accept-language': "en-GB,en-US;q=0.9,en;q=0.8",
        }

        api_cookies = self.get_cookies_from_api()
        if api_cookies:
            self.current_cookies = api_cookies
        else: exit()
#            self.current_cookies = {
 #               "AEC": "AaJma5tJLuswqMVJKhXSEt7IaeHERe6rJZxMy59O6hQrMarb9EjBYECaSgk",
  #              "OGPC": "19046228-1:",
   #             "NID": "526=g24CxEpXXXyb1stjLphaQOg7RJfqDpX3vFDigGXUcszE39PrMb5MjZlEHdgawjG1swf8AkAphQRngdwpdkJGYIOiAlX5lmPlwCQ169BVCjovrF19t4YT2dTDn9t_wixJNWv3WqioR7gmIGY49tm4K2DtOIoql3S_Nd7cIDh0zIe0ipQKF1eHtlxCErIzhz-uqnNNuPmtSewO5XQk5blxy4uVazwIqmLUE9asX5oismVRyMueio4dhKRsQg11c29cl5kj3StQKgL08BgVzvoqsU538H7UU7FZT_qb01G3ayiyRnnHmwb_xZdctWAVaoRo0fCYeLxMiV4eG7XwIFhP4SSIe7us8K57zQ",
    #            "DV": "o53JdnAcJgw1EM4dSZxmxyz6cce5qRlonmSkrvHUV_qPAVCRxydMTdb_NJ-LAAA"
     #       }
        
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
        api_cookies = self.get_cookies_from_api()
        if api_cookies:
            self.current_cookies = api_cookies
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

    def search(self, query):
        if not self.ensure_fresh_cookies():
            print("Using existing cookies")

        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en'}

        all_results = []
        current_page = 1
        next_url = base_url

        print(f"Searching: '{query}'")

        while next_url:
            try:
                if current_page == 1:
                    response = self.session.get(base_url, params=params, headers=self.headers, timeout=15) #;print(response.text)
                else:
                    response = self.session.get(next_url, headers=self.headers, timeout=15)

                response.raise_for_status()
                page_data = self.parse_google_search_results(response.text)
                all_results.extend(page_data['results'])
                next_url = self.get_next_page_url(response.text)

                print(f"Page {current_page}: {len(page_data['results'])} results")
                
                if next_url:
                    time.sleep(1)
                
                current_page += 1

            except Exception as e:
                print(f"Page {current_page} error: {e}")
                break

        final_data = {
            'metadata': {
                'query': query,
                'total_pages': current_page - 1,
                'total_results': len(all_results),
                'timestamp': datetime.now().isoformat()
            },
            'results': all_results
        }

        return final_data

def display_results(results):
    print("\n" + "-"*80)
    print(f"RESULTS: {results['metadata']['query']}")
    print(f"Total: {results['metadata']['total_results']}")
    print(f"Pages: {results['metadata']['total_pages']}")
    print("-"*80)

    for i, result in enumerate(results['results'], 1):
        print(f"\n--- Result {i} ---")
        print(f"Type: {result.get('type', 'unknown')}")

        if result['type'] == 'dictionary':
            print(f"Word: {result.get('word', 'N/A')}")
            if result.get('pronunciation'):
                print(f"Pronunciation: {result['pronunciation']}")
            if result.get('definitions'):
                print("Definitions:")
                for defn in result['definitions']:
                    print(f"  - {defn}")
            if result.get('examples'):
                print("Examples:")
                for ex in result['examples']:
                    print(f"  - {ex}")
            if result.get('similar_words'):
                print(f"Similar: {', '.join(result['similar_words'])}")
        else:
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"URL: {result.get('url', 'N/A')}")
            if result.get('description'):
                print(f"Desc: {result['description']}")
            if result.get('source'):
                print(f"Source: {result['source']}")
            if result.get('date'):
                print(f"Date: {result['date']}")

        print("-" * 40)

def main():
    print("-" * 50)
    print("Google Search Scraper")
    print("Auto-fetch cookies + All pages")
    print("-" * 50)

    scraper = GoogleSearchScraper()

    while True:
        try:
            search_query = input("\nSearch query (or 'quit'): ").strip()

            if search_query.lower() in ['quit', 'exit', 'q']:
                break

            if not search_query:
                continue

            results = scraper.search(search_query)
            display_results(results)

            save_choice = input("\nSave to JSON? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                filename = f"search_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"Saved: {filename}")

            continue_choice = input("\nAnother search? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
