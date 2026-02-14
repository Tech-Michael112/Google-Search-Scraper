#!/usr/bin/env python3

from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import time
import urllib.parse
import re
from datetime import datetime
import requests
import os
import random

app = Flask(__name__)

class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.initialize_headers_and_cookies()

    def get_cookies_from_api(self):
        return {
            "SID": "g.a0006QgzClcDNP7pW-T_YmGqp6eM4RFSfEP7vhSD7Cb8YgBgfn_hA0qRDYqQt59KsT4rcfqqigACgYKAbgSARESFQHGX2MiO6wgsORLoTshqWiFxHvsSxoVAUF8yKoaOCKKD_VpNzx3xSFkHfGo0076",
            "__Secure-1PSID": "g.a0006QgzClcDNP7pW-T_YmGqp6eM4RFSfEP7vhSD7Cb8YgBgfn_hKh1pGleTRJUQpbS31E7MVQACgYKAdYSARESFQHGX2MimiZ9BB9h9e9JAFUVnTY13xoVAUF8yKrAROrx4q5SCMUmKa31TirQ0076",
            "__Secure-3PSID": "g.a0006QgzClcDNP7pW-T_YmGqp6eM4RFSfEP7vhSD7Cb8YgBgfn_hdfHctwd_WoR1vEuljnnFgwACgYKAWwSARESFQHGX2MirCMVebTbpJGSpt4oc1FHLRoVAUF8yKozH-Tque28j2CiCGgsWkjb0076",
            "HSID": "AFCrzVkaSTW0t8BDH",
            "SSID": "AY7bU1zbNnyOT6-XJ",
            "APISID": "Syfw_KQwYvSIZ7RT/AQSJ89iPhLG_drtjt",
            "SAPISID": "1yLWPeTBXAXw1b4c/ApzC4WZfpcRIIgkmc",
            "__Secure-1PAPISID": "1yLWPeTBXAXw1b4c/ApzC4WZfpcRIIgkmc",
            "__Secure-3PAPISID": "1yLWPeTBXAXw1b4c/ApzC4WZfpcRIIgkmc",
            "__Secure-BUCKET": "CJgB",
            "SEARCH_SAMESITE": "CgQIiKAB",
            "AEC": "AaJma5uu9hqnZGzXmcpCPmwi3kzY6Le8YkW9yUTATzXVDFcC6iGw5WAn8A",
            "NID": "528=AfXqFmNc3S-X-wh274GiLVtpF4ps2mV_r5aqv8hBPSsfQNi_yvNtpLuSUixk1jYS_y5pBd_qmCMYvlGtrrUA0BrVtsgYEi2Ts3_iYvqAZ8CQuzVkabxMuwLFNzr_EQqNnb2O2ePH7y3jaMI3jkxCP9ntkLs4_W6EjgvA12KMsa7FcIQUjPazhREb-REGTzpO57pV5zEunYcW6plCYI3aBTUnC7HmuQ-iWsw89ONNG0VTOGvt1HN8BBPDmg3Dp2lhMeDf6RwxX7hMacwEIhZ_ib6jFkcdrkHa8xuvqZB5EPgk_zG_6CjlaMyc-_0tM5zaM5ylrZjimwSx4OPhDn2HCdQb9l_rf_AwcB-DAuDfQUh-mYKGbYuSaYNii7S-ZaLxxeOL0w8z8jru7Uo",
            "__Secure-STRP": "AD6Dogs-v12aiTtlXbdRlneWMnAkA77cTPuDod7J6MAy-Qk9TJDRVQRrg3poLJbZSwQwRYdrYfl5H5v5W2mavTe0MfLQBdpEFg",
            "DV": "U0Q-xZsTbixsIBy4P1MyROtg6z6LxRmI-LVhLnx5NgEAAGAUsbpzQL8ycwAAAJhcTY7CRtr7IgAAAAHw2_5TMtlDCgAAACKOl0gFWpnGAgAAAA",
            "SIDCC": "AKEyXzXUGhYY3uQDEWo4eoe6LMCvO7scBDrYh9Pp-_L03vVfPmMJ-EMUQ1dOQ2rO9QyKFbprfQ",
            "__Secure-1PSIDCC": "AKEyXzWz-lk8U1eLUQsntYll6u-vU9Lz_mw6UtAhgmsAKH7x2zxRDIr2AucPNi0cL2m3LNkMgw",
            "__Secure-3PSIDCC": "AKEyXzVw-_S1H08RajM6CEmrcVDPBZtPvJMbKprmkJ9qRsw8h9wga5VFVkkggwedR9GyADlf7PA"
        }

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'upgrade-insecure-requests': '1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.google.com/',
        }
        
        self.current_cookies = self.get_cookies_from_api()
        self.update_cookie_header()

    def update_cookie_header(self):
        cookie_string = '; '.join([f"{name}={value}" for name, value in self.current_cookies.items()])
        self.headers['Cookie'] = cookie_string
        self.session.cookies.update(self.current_cookies)

    def parse_google_search_results(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        dictionary_result = self.extract_dictionary_result(soup)
        if dictionary_result:
            results.append(dictionary_result)

        regular_results = self.extract_regular_results(soup)
        results.extend(regular_results)

        return {
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

    def search_pages_range(self, query, start_page=1, end_page=3):
        """Search multiple pages and return combined results"""
        all_results = []
        seen_urls = set()
        current_page = start_page
        
        while current_page <= end_page:
            start = (current_page - 1) * 10
            result = self.search_single_page(query, start)
            
            if result['success']:
                for item in result['results']:
                    if item.get('url') and item['url'] not in seen_urls:
                        seen_urls.add(item['url'])
                        all_results.append(item)
            
            current_page += 1
            if current_page <= end_page:
                time.sleep(1)
        
        return {
            'success': True,
            'query': query,
            'pages_scraped': f"{start_page}-{end_page}",
            'total_results': len(all_results),
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }

    def search_all_pages(self, query, max_pages=10):
        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'num': 10}

        all_results = []
        seen_urls = set()
        current_page = 1
        next_url = None

        while current_page <= max_pages:
            try:
                if current_page == 1:
                    response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
                else:
                    if not next_url:
                        break
                    response = self.session.get(next_url, headers=self.headers, timeout=15)

                response.raise_for_status()
                page_data = self.parse_google_search_results(response.text)
                
                for result in page_data['results']:
                    if result.get('url') and result['url'] not in seen_urls:
                        seen_urls.add(result['url'])
                        all_results.append(result)
                
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
            '/search/range': 'GET - Search page range (params: q, start_page, end_page)',
        },
        'examples': {
            'single_page': '/search?q=python&page=1',
            'all_pages': '/search/all?q=python&max_pages=5',
            'page_range': '/search/range?q=python&start_page=1&end_page=3'
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


@app.route('/search/range', methods=['GET'])
def search_range():
    query = request.args.get('q', '').strip()
    start_page = int(request.args.get('start_page', 1))
    end_page = int(request.args.get('end_page', 3))
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if start_page < 1 or end_page < start_page or end_page > 50:
        return jsonify({'error': 'Invalid page range'}), 400
    
    result = scraper.search_pages_range(query, start_page, end_page)
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
    port = int(os.environ.get('PORT', random.randint(5000, 6000)))
    app.run(host='0.0.0.0', port=port, debug=True)
