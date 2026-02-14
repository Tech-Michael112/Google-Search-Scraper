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
            "AEC": "AaJma5uu9hqnZGzXmcpCPmwi3kzY6Le8YkW9yUTATzXVDFcC6iGw5WAn8A",
            "DV": "U0Q-xZsTbix8ANnp3MkihgvKHfq8xZlw4P5MyRCtw4dcAGByNTkKG2nvGyIXACDieIlUoJVphMgFACDi14a58OXZI3IBgFHE6s4B_coMilwAEAC_7T8lkz1UIxcAAA",
            "__Secure-STRP": "AD6DogslGWMoDErEJDGFyAbD5IYXvQ9QrU_1W6SlgjxkZvIInSQ7SGhtqK0PQaEPhfZpN2_mr-tgAMCDvLpZmWTaW7p18M6YUnFO",
            "NID": "529=ZrNRQlwwKM4zXeTtoj1XoCVUgb7ZDJrbZ5E1z77NedH-NWx0Wu3u9Ex2YD4YhdOlLGLiladLJqHmbS5Ns_UKwISl8Mx9T2di0BqvhDPBLeLq2lxeJ0_eX-J0hu2nM-uoQfoum6oQSIO2XFKyCgKFkA5O_1dTe7flwLRT5EMXAp3uYn6FdP7alc4P-mCwnzQTUUD5XS4oh2OIbYhjOTdyA1NpnXr0Nicw07Fv2Bx2Gn9jAvIIzzNkgyqsTZPvMoUpljns29_PD5eOKaXoq0z1Z9MeRoCcvVNnPqG0EW568WIz4MNvrkjeRtvaILRUEF04XRnOmPnHTLHDkqYz-U5j-w8hcPoYLLKR3NJQOwPz6ULMFkU60_PSS9ClFWZy9UxfQGp_4mx_GnN0Qow",
            "SIDCC": "AKEyXzUOk6L7gxF_dJGz5uRCBb8G_YjYeCeTe4db8F2DAtSY-gBQvx5yZBueUo8AAV2Q6DX-Qg",
            "__Secure-1PSIDCC": "AKEyXzWTKIg-PavJJEUSazeiz7q5r-GdhaxQe22UqFb89ZqKL7jCeBGVsQr1uXgQBQ66Kb6JgA",
            "__Secure-3PSIDCC": "AKEyXzUVDxbvG3Z0d4QSF9DjewE592J9sfG8x4o2JzEzS0_WpHhJGPxCdt-5mQ0hKUo3oE8E1SU"
        }

    def initialize_headers_and_cookies(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'Accept-Language': "en-US,en;q=0.9",
            'rtt': "250",
            'downlink': "3.65",
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-full-version': '"140.0.7339.207"',
            'sec-ch-ua-arch': '""',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-ch-ua-model': '"2510DRA23G"',
            'sec-ch-ua-bitness': '""',
            'sec-ch-ua-wow64': "?0",
            'sec-ch-ua-full-version-list': '"Chromium";v="140.0.7339.207", "Not=A?Brand";v="24.0.0.0", "Google Chrome";v="140.0.7339.207"',
            'sec-ch-ua-form-factors': '"Mobile"',
            'sec-ch-prefers-color-scheme': "dark",
            'upgrade-insecure-requests': "1",
            'x-chrome-connected': "source=Chrome,mode=0,enable_account_consistency=true,supervised=false,consistency_enabled_by_default=false",
            'x-browser-channel': "stable",
            'x-browser-year': "2025",
            'x-browser-validation': "sa/BMelw7zzqFIJ9TfB82t336ew=",
            'x-browser-copyright': "Copyright 2025 Google LLC. All rights reserved.",
            'x-client-data': "CI+2yQEIpLbJAQipncoBCPTfygEIlqHLAQiKoM0BCLHDzQEI08/NAQjVz80BCNnXzQEI29fNAQiVjM8BCNKtzwE=",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'referer': "https://www.google.com/",
            'priority': "u=0, i",
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
        params = {
            'q': query, 
            'hl': 'en', 
            'start': start,
            'client': "ms-android-xiaomi-terr1-rso2",
        }
        
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
    def extract_image_urls(self, html_content):
        """Extract image URLs from Google Image Search response"""
        image_urls = []
        
        # Method 1: Look for image URLs in script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string:
                # Look for image URLs in various formats
                # Pattern for http/https image URLs
                patterns = [
                    r'https?://[^\s"\'\\]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)[^\s"\'\\]*',
                    r'\["([^"]+\.(?:jpg|jpeg|png|gif|webp))"',
                    r'"(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp))"',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.I)
                    for match in matches:
                        # Clean up the URL
                        url = match if isinstance(match, str) else match[0]
                        if url.startswith('http') and not any(x in url for x in ['google.com', 'gstatic.com', 'logo']):
                            if url not in image_urls:
                                image_urls.append(url)
        
        # Method 2: Look in img tags as fallback
        img_tags = soup.find_all('img')
        for img in img_tags:
            for attr in ['src', 'data-src']:
                url = img.get(attr)
                if url and url.startswith('http') and 'gstatic.com' not in url:
                    if re.search(r'\.(jpg|jpeg|png|gif|webp)', url, re.I):
                        if url not in image_urls:
                            image_urls.append(url)
        
        return image_urls

    def download_image(self, img_url, img_title, index):
        try:
            safe_title = re.sub(r'[^\w\s-]', '', img_title).strip()[:50]
            if not safe_title:
                safe_title = f"image_{index}"
            
            # Get file extension from URL
            ext_match = re.search(r'\.(jpg|jpeg|png|gif|webp)', img_url, re.I)
            ext = ext_match.group(1) if ext_match else 'jpg'
            
            filename = f"downloaded_images/{index}_{safe_title}.{ext}"
            
            img_response = requests.get(img_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if img_response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(img_response.content)
                return {
                    'success': True,
                    'filename': filename,
                    'title': safe_title,
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
        url = "https://www.google.com/search"
        
        params = {
            'client': "ms-android-xiaomi-terr1-rso2",
            'hs': "tkLp",
            'sca_esv': "c792f36581e0cd30",
            'sxsrf': f"ANbL-n4ZJxtNraX9CQi3qqWLUH92svjwag:{int(time.time())}",
            'udm': "2",
            'fbs': "ADc_l-aN0CWEZBOHjofHoaMMDiKpaEWjvZ2Py1XXV8d8KvlI3vWUtYx0DZdicpfE1faGYenqWn-q4MFiFFtvJjTKeAVxBf9XF8ByrMpEedseJb6C24e7QdJQdIE3TPpl5mEwf0HZUp1chSl04q3NzUG-sivE9fh2upv_LUl1i41J2OLX0ntDV3FbKmN59pJf5BBarEFT9msi8Zx3tjpgPrbRkWHc8AvYww",
            'q': query,
            'sa': "X",
            'ved': "2ahUKEwjG1JDr6diSAxWfdUEAHcMPCEkQtKgLegQIEhAB",
            'biw': "384",
            'bih': "707",
            'dpr': "2.81"
        }

        try:
            response = self.session.get(url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Extract image URLs
            all_image_urls = self.extract_image_urls(response.text)
            
            # Remove duplicates and limit to requested number
            unique_urls = []
            seen = set()
            for url in all_image_urls:
                if url not in seen and len(unique_urls) < num_images:
                    seen.add(url)
                    unique_urls.append(url)
            
            images = []
            for i, img_url in enumerate(unique_urls):
                images.append({
                    'index': i + 1,
                    'title': f"{query} image {i+1}",
                    'thumbnail_url': img_url,
                })
            
            downloaded = []
            if download and images:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for i, img in enumerate(images):
                        future = executor.submit(
                            self.download_image, 
                            img['thumbnail_url'], 
                            f"{query}_{i+1}", 
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
        # For now, just use the regular method since it's working well
        return self.search_google_images(query, num_images, download)


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
