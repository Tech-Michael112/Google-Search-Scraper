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
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# OR set it when creating the Flask app:
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
#app = Flask(__name__)

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
            "AEC": "AaJma5uu9hqnZGzXmcpCPmwi3kzY6Le8YkW9yUTATzXVDFcC6iGw5WAn8A",
            "NID": "528=AfXqFmNc3S-X-wh274GiLVtpF4ps2mV_r5aqv8hBPSsfQNi_yvNtpLuSUixk1jYS_y5pBd_qmCMYvlGtrrUA0BrVtsgYEi2Ts3_iYvqAZ8CQuzVkabxMuwLFNzr_EQqNnb2O2ePH7y3jaMI3jkxCP9ntkLs4_W6EjgvA12KMsa7FcIQUjPazhREb-REGTzpO57pV5zEunYcW6plCYI3aBTUnC7HmuQ-iWsw89ONNG0VTOGvt1HN8BBPDmg3Dp2lhMeDf6RwxX7hMacwEIhZ_ib6jFkcdrkHa8xuvqZB5EPgk_zG_6CjlaMyc-_0tM5zaM5ylrZjimwSx4OPhDn2HCdQb9l_rf_AwcB-DAuDfQUh-mYKGbYuSaYNii7S-ZaLxxeOL0w8z8jru7Uo"
        }

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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

        for container in soup.select('div.g, div.MjjYud, div.tF2Cxc, div.rc'):
            result = {
                'date': '',
                'description': '',
                'snippet': '',
                'source': '',
                'title': '',
                'type': 'regular',
                'url': ''
            }
            
            title = container.select_one('h3')
            if title:
                result['title'] = title.get_text(strip=True)
            
            link = container.find('a')
            if link and link.get('href'):
                href = link['href']
                if href.startswith('/url?q='):
                    result['url'] = href.split('/url?q=')[1].split('&')[0]
                    result['url'] = urllib.parse.unquote(result['url'])
                elif href.startswith('http'):
                    result['url'] = href
            
            desc = container.select_one('.VwiC3b, .s3v9rd, .aCOpRe')
            if desc:
                result['description'] = desc.get_text(strip=True)
            
            source = container.select_one('cite, .iUh30')
            if source:
                result['source'] = source.get_text(strip=True)
            
            if self.is_valid_result(result):
                results.append(result)

        return results

    def get_next_page_url(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        next_link = soup.select_one('a#pnnext')
        if next_link and next_link.get('href'):
            return "https://www.google.com" + next_link.get('href')
        return None

    # ========== WEB SEARCH METHODS ==========
    def fetch_page(self, query, start):
        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'start': start}
        
        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            results = self.parse_google_search_results(response.text)
            
            return {
                'success': True,
                'page': (start // 10) + 1,
                'results': results,
                'start': start
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
            'next_page': True,
            'next_start': start + 10 if result['success'] else None,
            'timestamp': datetime.now().isoformat()
        }

    def search_pages_range_threaded(self, query, start_page=1, end_page=3):
        all_results = []
        seen_urls = set()
        starts = [(page - 1) * 10 for page in range(start_page, end_page + 1)]
        
        with ThreadPoolExecutor(max_workers=min(5, len(starts))) as executor:
            futures = {executor.submit(self.fetch_page, query, start): start for start in starts}
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
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
            'timestamp': datetime.now().isoformat()
        }

    def search_all_pages_threaded(self, query, max_pages=10):
        all_results = []
        seen_urls = set()
        starts = [(page - 1) * 10 for page in range(1, max_pages + 1)]
        
        with ThreadPoolExecutor(max_workers=min(5, max_pages)) as executor:
            futures = {executor.submit(self.fetch_page, query, start): start for start in starts}
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
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
