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
import base64
import hashlib

app = Flask(__name__)

class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.initialize_headers_and_cookies()
        # Create images directory if it doesn't exist
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

    def download_image(self, img_url, img_title, index):
        """Download a single image"""
        try:
            # Create a safe filename
            safe_title = re.sub(r'[^\w\s-]', '', img_title).strip()[:50]
            filename = f"downloaded_images/{index}_{safe_title}.jpg"
            
            # Download image
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
        """Search Google Images"""
        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'tbm': 'isch',  # Image search
            'hl': 'en',
            'num': num_images
        }

        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Parse image results
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            
            # Find image elements
            img_tags = soup.find_all('img')
            
            for i, img in enumerate(img_tags):
                if i >= num_images:
                    break
                    
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # Handle base64 images
                if img_url.startswith('data:image'):
                    continue
                
                # Get alt text for title
                img_title = img.get('alt', f'Image_{i+1}')
                
                # Clean URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.google.com' + img_url
                
                image_data = {
                    'index': i + 1,
                    'title': img_title,
                    'thumbnail_url': img_url,
                    'full_url': None,  # Would need to click through to get full size
                }
                
                images.append(image_data)
            
            # Download images if requested
            downloaded = []
            if download and images:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for i, img in enumerate(images):
                        if img['thumbnail_url'] and not img['thumbnail_url'].startswith('data:'):
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
        """Search images using multiple threads for faster results"""
        # Split into multiple requests to get more images
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
                    False  # Don't download in sub-threads
                )
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    all_images.extend(result['images'])
        
        # Download if requested
        if download and all_images:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i, img in enumerate(all_images[:num_images]):
                    if img['thumbnail_url'] and not img['thumbnail_url'].startswith('data:'):
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
            '/search': 'GET - Search web pages (params: q, page)',
            '/search/all': 'GET - Search all web pages (params: q, max_pages)',
            '/images': 'GET - Search images (params: q, num, download)',
            '/images/threaded': 'GET - Search images with threading (params: q, num, download)',
            '/download/<filename>': 'GET - Download a specific image'
        },
        'examples': {
            'web_search': '/search?q=python&page=1',
            'image_search': '/images?q=cats&num=20',
            'image_search_download': '/images?q=cats&num=10&download=true',
            'threaded_images': '/images/threaded?q=cats&num=50&download=true'
        }
    })


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
    """Download a specific image file"""
    try:
        return send_file(f'downloaded_images/{filename}', as_attachment=True)
    except:
        return jsonify({'error': 'File not found'}), 404


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
    
    result = scraper.search_all_pages_threaded(query, max_pages)
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', random.randint(5000, 6000)))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
