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
        self.cookie_expiry_hours = 1  # Refresh cookies every hour
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
        """Open a small internal browser and collect Google cookies"""
        cookies_dict = {}
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            print("Opening internal browser to collect Google cookies...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to Google
            self.driver.get("https://www.google.com")
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Perform a dummy search to get proper search cookies
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.send_keys("test")
            search_box.submit()
            
            time.sleep(3)
            
            # Collect cookies
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            # Save cookies
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies_dict, f)
            
            print(f"Successfully collected {len(cookies_dict)} cookies")
                
        except Exception as e:
            print(f"Browser error: {e}")
            # Try to load saved cookies if browser fails
            if os.path.exists(self.cookie_file):
                try:
                    with open(self.cookie_file, 'rb') as f:
                        cookies_dict = pickle.load(f)
                    print(f"Loaded {len(cookies_dict)} cookies from file")
                except:
                    pass
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return cookies_dict

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        # Get fresh cookies from browser
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
        # Also update session cookies
        self.session.cookies.update(self.current_cookies)

    def should_refresh_cookies(self):
        if not self.cookie_last_updated:
            return True
        time_since_update = datetime.now() - self.cookie_last_updated
        return time_since_update.total_seconds() > (self.cookie_expiry_hours * 3600)

    def refresh_cookies(self):
        print("Refreshing cookies...")
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

        # Regular search results
        regular_results = self.extract_regular_results(soup)
        results.extend(regular_results)

        return {
            'results': results,
            'total_results': len(results)
        }

    def extract_regular_results(self, soup):
        results = []
        
        # Modern Google search result selectors
        result_selectors = [
            'div.g',
            'div.MjjYud',
            'div.tF2Cxc',
            'div.rc',
            'div[jscontroller]',
            'div.Gx5Zad'
        ]

        for selector in result_selectors:
            result_containers = soup.select(selector)
            for container in result_containers:
                result_data = self.extract_single_result(container)
                if result_data and result_data.get('title') and result_data.get('link'):
                    results.append(result_data)

        return results

    def extract_single_result(self, container):
        result = {
            'title': '',
            'link': '',
            'snippet': '',
            'displayed_link': ''
        }

        # Extract title
        title_selectors = ['h3', '.LC20lb', '.DKV0Md', '.vvjwJb']
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
                break

        # Extract link
        link_elem = container.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            if href.startswith('/url?q='):
                result['link'] = href.split('/url?q=')[1].split('&')[0]
                result['link'] = urllib.parse.unquote(result['link'])
            elif href.startswith('http'):
                result['link'] = href

        # Extract snippet/description
        snippet_selectors = [
            '.VwiC3b',
            '.s3v9rd',
            '.MUxGbd',
            '.aCOpRe',
            '.yXK7lf'
        ]
        for selector in snippet_selectors:
            snippet_elem = container.select_one(selector)
            if snippet_elem:
                result['snippet'] = snippet_elem.get_text(strip=True)
                break

        # Extract displayed link
        displayed_link_selectors = ['.tjvcx', '.iUh30', '.B6fmyf']
        for selector in displayed_link_selectors:
            displayed_elem = container.select_one(selector)
            if displayed_elem:
                result['displayed_link'] = displayed_elem.get_text(strip=True)
                break

        return result

    def get_next_page_url(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find next page button
        next_selectors = [
            'a#pnnext',
            'a[aria-label*="Next"]',
            'a[class*="next"]',
            'a.fl:last-child'
        ]

        for selector in next_selectors:
            next_page_link = soup.select_one(selector)
            if next_page_link and next_page_link.get('href'):
                next_url = next_page_link.get('href')
                if next_url.startswith('/'):
                    return "https://www.google.com" + next_url
                return next_url
        return None

    def search_single_page(self, query, start=0):
        if not self.ensure_fresh_cookies():
            print("Warning: Could not ensure fresh cookies")

        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'hl': 'en',
            'start': start,
            'num': 10
        }

        try:
            print(f"Searching page {start//10 + 1} for: {query}")
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
            print(f"Error searching page: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'page': (start // 10) + 1
            }

    def search_all_pages(self, query, max_pages=10):
        if not self.ensure_fresh_cookies():
            print("Warning: Could not ensure fresh cookies")

        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'hl': 'en',
            'num': 10
        }

        all_results = []
        current_page = 1
        next_url = None

        while current_page <= max_pages:
            try:
                if current_page == 1:
                    print(f"Searching page 1 for: {query}")
                    response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
                else:
                    if not next_url:
                        break
                    print(f"Searching page {current_page} for: {query}")
                    response = self.session.get(next_url, headers=self.headers, timeout=15)

                response.raise_for_status()
                page_data = self.parse_google_search_results(response.text)
                all_results.extend(page_data['results'])
                
                next_url = self.get_next_page_url(response.text)
                
                if next_url:
                    time.sleep(2)  # Be respectful to Google
                
                current_page += 1

            except Exception as e:
                print(f"Error on page {current_page}: {e}")
                break

        return {
            'success': True,
            'query': query,
            'total_pages_scraped': current_page - 1,
            'total_results': len(all_results),
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }


# Initialize scraper
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
            'all_pages': '/search/all?q=python&max_pages=2'
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
    app.run(host='0.0.0.0', port=port, debug=False)
