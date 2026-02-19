#!/usr/bin/env python3

from flask import Flask, request, jsonify, send_file, Response
from bs4 import BeautifulSoup
import urllib.parse
import re
from datetime import datetime
import requests
import os
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib

app = Flask(__name__)

# Helper function for pretty JSON responses
def json_response(data, status=200):
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

class GoogleSearchScraper:
    def __init__(self):
        # Optimized session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=2,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.lock = threading.Lock()
        self.initialize_headers_and_cookies()
        os.makedirs('downloaded_images', exist_ok=True)
        
        # Global deduplication tracking across all scraping sessions
        self.global_seen_urls = set()
        self.global_seen_hashes = set()  # Track content hashes

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
            'Connection': 'keep-alive',
        }
        
        self.current_cookies = self.get_cookies_from_api()
        self.update_cookie_header()

    def update_cookie_header(self):
        cookie_string = '; '.join([f"{name}={value}" for name, value in self.current_cookies.items()])
        self.headers['Cookie'] = cookie_string
        self.session.cookies.update(self.current_cookies)

    def normalize_url(self, url):
        """
        Normalize URL to catch duplicates with different query parameters or trailing slashes
        """
        if not url:
            return None
        
        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 
                          'fbclid', 'gclid', 'ref', 'source']
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Parse query parameters
            params = urllib.parse.parse_qs(parsed.query)
            
            # Remove tracking parameters
            filtered_params = {k: v for k, v in params.items() if k not in tracking_params}
            
            # Rebuild query string
            new_query = urllib.parse.urlencode(filtered_params, doseq=True)
            
            # Normalize the URL
            normalized = urllib.parse.urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),  # Remove trailing slash
                parsed.params,
                new_query,
                ''  # Remove fragment
            ))
            
            return normalized
        except:
            return url

    def get_content_hash(self, result):
        """
        Generate a hash from title and description to catch near-duplicates
        """
        content = f"{result.get('title', '').lower().strip()}|{result.get('description', '').lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_valid_result(self, result):
        """Enhanced validation with more filters"""
        if not result.get('url'):
            return False
        
        # Filter out Google's own services and ads
        blocked_domains = [
            'google.com/ackl',
            'googleadservices',
            'google.com/aclk',
            'google.com/url',
            'accounts.google.com',
            'support.google.com/websearch'
        ]
        
        for domain in blocked_domains:
            if domain in result['url']:
                return False
        
        # Title validation
        if not result.get('title') or len(result['title']) < 3:
            return False
        
        # Filter out results with generic/spam titles
        spam_indicators = ['...', '›', '»', '|' * 3]
        title = result['title']
        if any(indicator in title for indicator in spam_indicators):
            if len(title) < 20:  # Only filter short titles with these
                return False
        
        return True

    def parse_google_search_results(self, html_content, local_seen_urls=None, local_seen_hashes=None):
        """
        Enhanced parsing with better duplicate detection
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # Use provided sets or create new ones
        if local_seen_urls is None:
            local_seen_urls = set()
        if local_seen_hashes is None:
            local_seen_hashes = set()

        # Multiple selector strategies based on actual Google HTML structure
        # Priority order: newest to oldest class names
        containers = (
            soup.select('div.MjjYud') or  # Current structure
            soup.select('div.Gx5Zad.fP1Qef.xpd.EtOod.pkphOe') or  # Alternative
            soup.select('div.tF2Cxc') or  # Older structure
            soup.select('div.g') or  # Even older
            soup.select('div.rc')  # Fallback
        )
        
        for container in containers:
            result = {
                'date': '',
                'description': '',
                'snippet': '',
                'source': '',
                'title': '',
                'type': 'regular',
                'url': '',
                'normalized_url': ''
            }
            
            # Extract title - try multiple selectors
            title_elem = (
                container.select_one('h3') or
                container.select_one('h3.LC20lb') or
                container.select_one('.DKV0Md')
            )
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            
            # Extract link - handle multiple formats
            link = container.find('a', href=True)
            if link and link.get('href'):
                href = link['href']
                
                # Handle different URL formats from Google
                if href.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    try:
                        result['url'] = href.split('/url?q=')[1].split('&')[0]
                        result['url'] = urllib.parse.unquote(result['url'])
                    except:
                        continue
                elif href.startswith('http'):
                    result['url'] = href
                else:
                    # Skip relative URLs or invalid formats
                    continue
                
                # Normalize URL for duplicate detection
                result['normalized_url'] = self.normalize_url(result['url'])
            
            # Extract description/snippet - try multiple selectors
            desc_elem = (
                container.select_one('.VwiC3b') or  # Current
                container.select_one('.s3v9rd') or  # Alternative
                container.select_one('.aCOpRe') or
                container.select_one('.yDYNvb') or
                container.select_one('.IsZvec')  # Older
            )
            if desc_elem:
                result['description'] = desc_elem.get_text(strip=True)
                result['snippet'] = result['description']  # Alias
            
            # Extract source/cite
            source_elem = (
                container.select_one('cite') or
                container.select_one('.iUh30') or
                container.select_one('.tjvcx') or
                container.select_one('.qLRx3b')
            )
            if source_elem:
                result['source'] = source_elem.get_text(strip=True)
            
            # Extract date if present
            date_elem = container.select_one('.LEwnzc.Sqrs4e')
            if date_elem:
                result['date'] = date_elem.get_text(strip=True)
            
            # Validate result
            if not self.is_valid_result(result):
                continue
            
            # Check for duplicates using normalized URL
            normalized_url = result['normalized_url']
            if normalized_url in local_seen_urls or normalized_url in self.global_seen_urls:
                continue
            
            # Check for near-duplicates using content hash
            content_hash = self.get_content_hash(result)
            if content_hash in local_seen_hashes or content_hash in self.global_seen_hashes:
                continue
            
            # Add to seen sets
            local_seen_urls.add(normalized_url)
            local_seen_hashes.add(content_hash)
            
            with self.lock:
                self.global_seen_urls.add(normalized_url)
                self.global_seen_hashes.add(content_hash)
            
            results.append(result)

        return results

    def get_next_page_url(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        next_link = soup.select_one('a#pnnext')
        if next_link and next_link.get('href'):
            return "https://www.google.com" + next_link.get('href')
        return None

    def clear_global_cache(self):
        """Clear the global duplicate tracking cache"""
        with self.lock:
            self.global_seen_urls.clear()
            self.global_seen_hashes.clear()

    # ========== WEB SEARCH METHODS ==========
    def fetch_page(self, query, start, local_seen_urls=None, local_seen_hashes=None):
        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'start': start}
        
        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            results = self.parse_google_search_results(
                response.text, 
                local_seen_urls, 
                local_seen_hashes
            )
            
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
        # Use local sets for this request
        local_seen_urls = set()
        local_seen_hashes = set()
        
        result = self.fetch_page(query, start, local_seen_urls, local_seen_hashes)
        
        return {
            'success': result['success'],
            'page': result['page'],
            'query': query,
            'results': result.get('results', []),
            'total_results': len(result.get('results', [])),
            'unique_results': len(result.get('results', [])),
            'next_page': True,
            'next_start': start + 10 if result['success'] else None,
            'timestamp': datetime.now().isoformat()
        }

    def search_pages_range_threaded(self, query, start_page=1, end_page=3):
        all_results = []
        seen_urls = set()
        seen_hashes = set()
        starts = [(page - 1) * 10 for page in range(start_page, end_page + 1)]
        
        # Increased max_workers for faster parallel execution
        with ThreadPoolExecutor(max_workers=min(10, len(starts))) as executor:
            futures = {
                executor.submit(self.fetch_page, query, start, seen_urls, seen_hashes): start 
                for start in starts
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    with self.lock:
                        for item in result['results']:
                            # Double-check in case of race conditions
                            norm_url = item.get('normalized_url', item.get('url'))
                            if norm_url not in seen_urls:
                                seen_urls.add(norm_url)
                                all_results.append(item)
        
        return {
            'success': True,
            'query': query,
            'pages_scraped': f"{start_page}-{end_page}",
            'total_results': len(all_results),
            'unique_results': len(all_results),
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }

    def search_all_pages_threaded(self, query, max_pages=10):
        all_results = []
        seen_urls = set()
        seen_hashes = set()
        starts = [(page - 1) * 10 for page in range(1, max_pages + 1)]
        
        # Increased max_workers for faster parallel execution
        with ThreadPoolExecutor(max_workers=min(10, len(starts))) as executor:
            futures = {
                executor.submit(self.fetch_page, query, start, seen_urls, seen_hashes): start 
                for start in starts
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    with self.lock:
                        for item in result['results']:
                            # Double-check in case of race conditions
                            norm_url = item.get('normalized_url', item.get('url'))
                            if norm_url not in seen_urls:
                                seen_urls.add(norm_url)
                                all_results.append(item)
        
        return {
            'success': True,
            'query': query,
            'total_pages': max_pages,
            'total_results': len(all_results),
            'unique_results': len(all_results),
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }


scraper = GoogleSearchScraper()


@app.route('/')
def home():
    return json_response({
        'status': 'Google Search Scraper API - ENHANCED DEDUPLICATION',
        'version': '2.0',
        'endpoints': {
            '/search': 'GET - Search single page (params: q, page)',
            '/search/range/threaded': 'GET - Search page range with threading (params: q, start_page, end_page)',
            '/search/all/threaded': 'GET - Search all pages with threading (params: q, max_pages)',
            '/clear_cache': 'POST - Clear global deduplication cache'
        },
        'examples': {
            'single_page': '/search?q=python&page=1',
            'range_fast': '/search/range/threaded?q=python&start_page=1&end_page=3',
            'all_fast': '/search/all/threaded?q=python&max_pages=5',
        },
        'features': [
            'URL normalization (removes tracking params)',
            'Content-based deduplication (title + description hashing)',
            'Global cross-request deduplication',
            'Thread-safe duplicate prevention',
            'Enhanced spam filtering'
        ]
    })


# ========== WEB SEARCH ROUTES ==========
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if page < 1:
        return json_response({'error': 'Page must be >= 1'}, 400)
    
    start = (page - 1) * 10
    result = scraper.search_single_page(query, start)
    
    return json_response(result)


@app.route('/search/range/threaded', methods=['GET'])
def search_range_threaded():
    query = request.args.get('q', '').strip()
    start_page = int(request.args.get('start_page', 1))
    end_page = int(request.args.get('end_page', 3))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if start_page < 1 or end_page < start_page or end_page > 50:
        return json_response({'error': 'Invalid page range'}, 400)
    
    result = scraper.search_pages_range_threaded(query, start_page, end_page)
    return json_response(result)


@app.route('/search/all/threaded', methods=['GET'])
def search_all_threaded():
    query = request.args.get('q', '').strip()
    max_pages = int(request.args.get('max_pages', 10))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if max_pages < 1 or max_pages > 50:
        return json_response({'error': 'max_pages must be between 1 and 50'}, 400)
    
    result = scraper.search_all_pages_threaded(query, max_pages)
    return json_response(result)


@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear the global deduplication cache"""
    scraper.clear_global_cache()
    return json_response({
        'success': True,
        'message': 'Global deduplication cache cleared'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', random.randint(5000, 6000)))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
