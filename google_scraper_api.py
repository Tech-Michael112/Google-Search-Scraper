#!/usr/bin/env python3

from flask import Flask, request, jsonify, send_file
from bs4 import BeautifulSoup
import time
import urllib.parse
import re
from datetime import datetime
import requests
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

app = Flask(__name__)

class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.initialize_headers_and_cookies()
        os.makedirs('downloaded_images', exist_ok=True)

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
            "SEARCH_SAMESITE": "CgQIk6AB",
            "AEC": "AaJma5uw_Jq_Wdmjj8Tf1v3T-kQTa4kR9RgQ4HC4BsDx8Lfy-ddj3VfcGg",
            "DV": "U0Q-xZsTbixsACJ-bZgLX55dmtPKxplw4P5MyRCtAwIAAGDFgJ1aPE2BvQAAALDxvkO948-MMAAAAHxNtg6drFzxEAAAgEd3PB5P1eMpBAAAAA",
            "NID": "529=wMqN81nyLfNq3uEIFJoCigdccvxIf9QmjHm4aZA5fzVd3-xgZiT0ZOoPlBufpQIgJm87oqxMODuW23M_T9PPVWJ098HMLI54I6SyMHkGThEnUXMK8LjZ-WNyYYf5ADFXxrMc3DcRreXDsnHSB8flbZF1pfFrA3KdQqe_JqFmSNFqPpmcsA_vObmUNVTWHitwXBvFeLrVLg24_B8EggiJA-jTwgVa1ofOqaXVhvA6kqpZhpviuDU-wmK2eDcxEwq3XUQDEgjicrnw1WSE9-G6k1FTqaeFrU7leHNgq8bBYm8yAhrXdA02D0jVx-_jZnw39nSpTppjbORsvTprmqdtQ2Ck_fVYWqK_OvAZ1nFBXzK5ikF2ATrAj26tlQWaakRxHzC7qeVjbMGoSzQpZszal9r6EbMBa1rhGU3_Rdy2dCcYvSL9",
            "SIDCC": "AKEyXzX5oIHkaDpJk_UISD9wYXbFz8qgnPtV7QT3_YTrm39nhOqjqb5okMcVY8c4bg2eb1i4Kw",
            "__Secure-1PSIDCC": "AKEyXzVVocXPBGfE-xwMEwmDaDIyC4Ek7BmBe3TZHSolblk5wWp4o_dSpy2qnjv7MZEwRqpvdA",
            "__Secure-3PSIDCC": "AKEyXzU_i0ZnVVFD44I5-rv74QaP5ZO8qwBAzRF403-fr79Y50IELwCz44AKSIwWYxtfJPvFlyo",
            "__Secure-STRP": "AD6DogvFh7iJgaiAZjraKtlwnR966gpAQLn-0CQ4sNNAU7R-K2x3F_8yvoSNXe2FMnqLG9aJmfe1WBJX0gbQlllB3FeRS_MtgBFI"
        }

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'downlink': "0.9",
            'sec-ch-ua-full-version-list': "\"Chromium\";v=\"140.0.7339.207\", \"Not=A?Brand\";v=\"24.0.0.0\", \"Google Chrome\";v=\"140.0.7339.207\"",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            'sec-ch-ua-bitness': "\"\"",
            'sec-ch-ua-model': "\"2510DRA23G\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-form-factors': "\"Mobile\"",
            'sec-ch-ua-wow64': "?0",
            'sec-ch-ua-arch': "\"\"",
            'sec-ch-ua-full-version': "\"140.0.7339.207\"",
            'sec-ch-prefers-color-scheme': "dark",
            'rtt': "100",
            'sec-ch-ua-platform-version': "\"15.0.0\"",
            'x-browser-channel': "stable",
            'x-browser-year': "2025",
            'x-browser-copyright': "Copyright 2025 Google LLC. All rights reserved.",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://www.google.com/",
            'accept-language': "en-US,en;q=0.9",
            'priority': "u=1, i",
        }
        
        self.current_cookies = self.get_cookies_from_api()
        self.update_cookie_header()

    def update_cookie_header(self):
        cookie_string = '; '.join([f"{name}={value}" for name, value in self.current_cookies.items()])
        self.headers['Cookie'] = cookie_string
        self.session.cookies.update(self.current_cookies)

    def is_valid_result(self, result):
        if not result.get('url'):
            return False
        if 'google.com/ackl' in result['url'] or 'googleadservices' in result['url']:
            return False
        if not result.get('title') or len(result['title']) < 3:
            return False
        return True

    def parse_google_search_results(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        seen_urls = set()

        # Main search result containers based on the actual HTML structure
        for container in soup.select('div.MjjYud, div.g, div[jscontroller="SC7lYd"]'):
            result = {
                'date': '',
                'description': '',
                'snippet': '',
                'source': '',
                'title': '',
                'type': 'regular',
                'url': '',
                'position': len(results) + 1
            }
            
            # Get title from h3 with class LC20lb
            title_elem = container.select_one('h3.LC20lb')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            
            # Get URL from the main link
            link = container.find('a', href=True)
            if link and link.get('href'):
                href = link['href']
                if href.startswith('/url?q='):
                    # Extract URL from Google redirect
                    url_part = href.split('/url?q=')[1].split('&')[0]
                    result['url'] = urllib.parse.unquote(url_part)
                elif href.startswith('http') and not href.startswith('https://www.google.com'):
                    result['url'] = href
            
            # Skip if no URL or duplicate
            if not result['url'] or result['url'] in seen_urls:
                continue
            
            # Get description/snippet
            desc_elem = container.select_one('div.VwiC3b, div.yXK7lf, span[role="text"]')
            if desc_elem:
                result['description'] = desc_elem.get_text(strip=True)
            
            # Get source/website name
            source_elem = container.select_one('cite, div.VuuXrf, span.VuuXrf')
            if source_elem:
                result['source'] = source_elem.get_text(strip=True)
            
            # Get date if available
            date_elem = container.select_one('span.f, span.r0bn4c.rQMQod')
            if date_elem:
                result['date'] = date_elem.get_text(strip=True)
            
            if self.is_valid_result(result):
                seen_urls.add(result['url'])
                results.append(result)

        return results

    def get_next_page_url(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        next_link = soup.select_one('a#pnnext')
        if next_link and next_link.get('href'):
            return "https://www.google.com" + next_link.get('href')
        return None

    def get_result_stats(self, html_content):
        """Extract result statistics from the page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        stats = soup.select_one('#result-stats')
        if stats:
            return stats.get_text(strip=True)
        return None

    # ========== WEB SEARCH METHODS ==========
    def fetch_page(self, query, start):
        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'start': start}
        
        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            results = self.parse_google_search_results(response.text)
            next_page_url = self.get_next_page_url(response.text)
            result_stats = self.get_result_stats(response.text)
            
            return {
                'success': True,
                'page': (start // 10) + 1,
                'results': results,
                'start': start,
                'next_page_url': next_page_url,
                'result_stats': result_stats
            }
        except Exception as e:
            return {
                'success': False,
                'page': (start // 10) + 1,
                'error': str(e),
                'start': start
            }

    def search_single_page(self, query, start=0):
        result = self.fetch_page(query, start)
        
        return {
            'success': result['success'],
            'page': result['page'],
            'query': query,
            'results': result.get('results', []),
            'total_results': len(result.get('results', [])),
            'next_page': result.get('next_page_url') is not None,
            'next_page_url': result.get('next_page_url'),
            'next_start': start + 10 if result['success'] and result.get('next_page_url') else None,
            'result_stats': result.get('result_stats'),
            'timestamp': datetime.now().isoformat()
        }

    def search_pages_range_threaded(self, query, start_page=1, end_page=3):
        all_results = []
        seen_urls = set()
        starts = [(page - 1) * 10 for page in range(start_page, end_page + 1)]
        page_data = {}
        
        with ThreadPoolExecutor(max_workers=min(5, len(starts))) as executor:
            futures = {executor.submit(self.fetch_page, query, start): start for start in starts}
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    page_data[result['page']] = {
                        'result_stats': result.get('result_stats'),
                        'next_page_url': result.get('next_page_url')
                    }
                    with self.lock:
                        for item in result['results']:
                            if item.get('url') and item['url'] not in seen_urls:
                                seen_urls.add(item['url'])
                                all_results.append(item)
        
        return {
            'success': True,
            'query': query,
            'pages_scraped': f"{start_page}-{end_page}",
            'total_results': len(all_results),
            'results': all_results,
            'page_details': page_data,
            'timestamp': datetime.now().isoformat()
        }

    def search_all_pages_threaded(self, query, max_pages=10):
        all_results = []
        seen_urls = set()
        starts = [(page - 1) * 10 for page in range(1, max_pages + 1)]
        page_data = {}
        
        with ThreadPoolExecutor(max_workers=min(5, max_pages)) as executor:
            futures = {executor.submit(self.fetch_page, query, start): start for start in starts}
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    page_data[result['page']] = {
                        'result_stats': result.get('result_stats'),
                        'next_page_url': result.get('next_page_url')
                    }
                    with self.lock:
                        for item in result['results']:
                            if item.get('url') and item['url'] not in seen_urls:
                                seen_urls.add(item['url'])
                                all_results.append(item)
        
        return {
            'success': True,
            'query': query,
            'total_pages_scraped': max_pages,
            'total_results': len(all_results),
            'results': all_results,
            'page_details': page_data,
            'timestamp': datetime.now().isoformat()
        }

    # ========== IMAGE SEARCH METHODS ==========
    def download_image(self, img_url, img_title, index):
        try:
            safe_title = re.sub(r'[^\w\s-]', '', img_title).strip()[:50]
            filename = f"downloaded_images/{index}_{safe_title}.jpg"
            
            img_response = requests.get(img_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if img_response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(img_response.content)
                return {
                    'success': True,
                    'filename': filename,
                    'title': img_title,
                    'url': img_url
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'title': img_title,
                'url': img_url
            }
        return None

    def search_google_images(self, query, num_images=20, download=False):
        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'tbm': 'isch',
            'hl': 'en',
            'num': num_images
        }

        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            
            img_tags = soup.find_all('img')
            
            for i, img in enumerate(img_tags):
                if i >= num_images:
                    break
                    
                img_url = img.get('src') or img.get('data-src')
                if not img_url or img_url.startswith('data:image'):
                    continue
                
                img_title = img.get('alt', f'Image_{i+1}')
                
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                
                images.append({
                    'index': i + 1,
                    'title': img_title,
                    'thumbnail_url': img_url,
                })
            
            downloaded = []
            if download and images:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for i, img in enumerate(images[:num_images]):
                        future = executor.submit(
                            self.download_image, 
                            img['thumbnail_url'], 
                            img['title'], 
                            i+1
                        )
                        futures.append(future)
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result and result['success']:
                            downloaded.append(result)
            
            return {
                'success': True,
                'query': query,
                'total_images': len(images),
                'images': images,
                'downloaded': downloaded if download else [],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }

    def search_images_threaded(self, query, num_images=50, download=False):
        images_per_page = 20
        num_pages = (num_images + images_per_page - 1) // images_per_page
        all_images = []
        downloaded = []
        
        with ThreadPoolExecutor(max_workers=min(3, num_pages)) as executor:
            futures = []
            for page in range(num_pages):
                future = executor.submit(
                    self.search_google_images,
                    query,
                    images_per_page,
                    False
                )
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    all_images.extend(result['images'])
        
        if download and all_images:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i, img in enumerate(all_images[:num_images]):
                    future = executor.submit(
                        self.download_image,
                        img['thumbnail_url'],
                        img['title'],
                        i+1
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    result = future.result()
                    if result and result['success']:
                        downloaded.append(result)
        
        return {
            'success': True,
            'query': query,
            'total_images': len(all_images[:num_images]),
            'images': all_images[:num_images],
            'downloaded': downloaded,
            'timestamp': datetime.now().isoformat()
        }


scraper = GoogleSearchScraper()


@app.route('/')
def home():
    return jsonify({
        'status': 'Google Search Scraper API',
        'version': '1.0',
        'endpoints': {
            # Web search
            '/search': 'GET - Search single page (params: q, page)',
            '/search/range/threaded': 'GET - Search page range with threading (params: q, start_page, end_page)',
            '/search/all/threaded': 'GET - Search all pages with threading (params: q, max_pages)',
            
            # Image search
            '/images': 'GET - Search images (params: q, num, download)',
            '/images/threaded': 'GET - Search images with threading (params: q, num, download)',
            '/download/<filename>': 'GET - Download a specific image'
        },
        'examples': {
            # Web search
            'single_page': '/search?q=python&page=1',
            'range_fast': '/search/range/threaded?q=python&start_page=1&end_page=3',
            'all_fast': '/search/all/threaded?q=python&max_pages=5',
            
            # Image search
            'images': '/images?q=cats&num=20',
            'images_download': '/images?q=cats&num=10&download=true',
            'images_fast': '/images/threaded?q=cats&num=50&download=true'
        }
    })


# ========== WEB SEARCH ROUTES ==========
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


@app.route('/search/range/threaded', methods=['GET'])
def search_range_threaded():
    query = request.args.get('q', '').strip()
    start_page = int(request.args.get('start_page', 1))
    end_page = int(request.args.get('end_page', 3))
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if start_page < 1 or end_page < start_page or end_page > 50:
        return jsonify({'error': 'Invalid page range'}), 400
    
    result = scraper.search_pages_range_threaded(query, start_page, end_page)
    return jsonify(result)


@app.route('/search/all/threaded', methods=['GET'])
def search_all_threaded():
    query = request.args.get('q', '').strip()
    max_pages = int(request.args.get('max_pages', 10))
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if max_pages < 1 or max_pages > 50:
        return jsonify({'error': 'max_pages must be between 1 and 50'}), 400
    
    result = scraper.search_all_pages_threaded(query, max_pages)
    return jsonify(result)


# ========== IMAGE SEARCH ROUTES ==========
@app.route('/images', methods=['GET'])
def search_images():
    query = request.args.get('q', '').strip()
    num = int(request.args.get('num', 20))
    download = request.args.get('download', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if num < 1 or num > 100:
        return jsonify({'error': 'num must be between 1 and 100'}), 400
    
    result = scraper.search_google_images(query, num, download)
    return jsonify(result)


@app.route('/images/threaded', methods=['GET'])
def search_images_threaded():
    query = request.args.get('q', '').strip()
    num = int(request.args.get('num', 50))
    download = request.args.get('download', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Missing query parameter (q)'}), 400
    
    if num < 1 or num > 200:
        return jsonify({'error': 'num must be between 1 and 200'}), 400
    
    result = scraper.search_images_threaded(query, num, download)
    return jsonify(result)


@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(f'downloaded_images/{filename}', as_attachment=True)
    except:
        return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', random.randint(5000, 6000)))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
