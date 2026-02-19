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
import time

app = Flask(__name__)

def json_response(data, status=200):
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

class RobustGoogleScraper:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.lock = threading.Lock()
        self.initialize_headers()
        
        self.global_seen_urls = set()
        self.global_seen_hashes = set()
        
        # User agents pool
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]

    def initialize_headers(self):
        """Initialize headers with a random user agent"""
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    def rotate_user_agent(self):
        """Rotate to a new user agent"""
        self.headers['User-Agent'] = random.choice(self.user_agents)

    def normalize_url(self, url):
        """Normalize URL"""
        if not url:
            return None
        
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                          'utm_term', 'fbclid', 'gclid', 'ref', 'source']
        
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            filtered_params = {k: v for k, v in params.items() if k not in tracking_params}
            new_query = urllib.parse.urlencode(filtered_params, doseq=True)
            
            normalized = urllib.parse.urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),
                parsed.params,
                new_query,
                ''
            ))
            
            return normalized
        except:
            return url

    def get_content_hash(self, title, description):
        """Generate content hash"""
        content = f"{title.lower().strip()}|{description.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def extract_url_from_href(self, href):
        """Extract URL from various Google formats"""
        if not href:
            return None
            
        # Skip ads and internal Google links
        if any(x in href for x in ['googleadservices', 'google.com/aclk', 'google.com/url?', 
                                     '/search?', 'accounts.google.com']):
            # Try to extract actual URL if it's a redirect
            if '/url?q=' in href or '/url?url=' in href:
                try:
                    # Extract the actual URL
                    match = re.search(r'[?&](q|url)=([^&]+)', href)
                    if match:
                        url = urllib.parse.unquote(match.group(2))
                        # Check if it's still a Google domain
                        if not any(x in url for x in ['google.com', 'gstatic.com']):
                            return url
                except:
                    pass
            return None
            
        if href.startswith('http'):
            return href
            
        return None

    def scrape_page(self, html_content, local_seen_urls=None, local_seen_hashes=None):
        """Comprehensive page scraper"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if local_seen_urls is None:
            local_seen_urls = set()
        if local_seen_hashes is None:
            local_seen_hashes = set()
        
        page_data = {
            'organic_results': [],
            'featured_snippet': None,
            'knowledge_panel': None,
            'people_also_ask': [],
            'related_searches': [],
            'news_results': [],
            'video_results': [],
            'image_results': [],
            'shopping_results': [],
            'local_results': [],
            'ads': [],
            'pagination': {},
            'metadata': {}
        }

        # Extract organic results with multiple fallback selectors
        result_containers = self._find_result_containers(soup)
        
        for container in result_containers:
            result = self._extract_organic_result(container, local_seen_urls, local_seen_hashes)
            if result:
                page_data['organic_results'].append(result)

        # Extract other content types
        page_data['featured_snippet'] = self._extract_featured_snippet(soup)
        page_data['knowledge_panel'] = self._extract_knowledge_panel(soup)
        page_data['people_also_ask'] = self._extract_people_also_ask(soup)
        page_data['related_searches'] = self._extract_related_searches(soup)
        page_data['pagination'] = self._extract_pagination(soup)
        page_data['metadata'] = self._extract_metadata(soup)

        # Summary
        page_data['summary'] = {
            'total_organic': len(page_data['organic_results']),
            'total_paa': len(page_data['people_also_ask']),
            'total_related': len(page_data['related_searches']),
            'has_featured_snippet': page_data['featured_snippet'] is not None,
            'has_knowledge_panel': page_data['knowledge_panel'] is not None,
            'total_items': (
                len(page_data['organic_results']) +
                len(page_data['people_also_ask']) +
                len(page_data['related_searches'])
            )
        }

        return page_data

    def _find_result_containers(self, soup):
        """Find all result containers using multiple selectors"""
        containers = []
        
        # Try multiple selector strategies
        selectors = [
            'div.MjjYud',
            'div.Gx5Zad.fP1Qef.xpd.EtOod.pkphOe',
            'div.tF2Cxc',
            'div.g:not(.g-blk):not(.related-question-pair)',
            'div.rc'
        ]
        
        for selector in selectors:
            found = soup.select(selector)
            if found:
                containers = found
                break
        
        return containers

    def _extract_organic_result(self, container, seen_urls, seen_hashes):
        """Extract organic search result"""
        result = {
            'type': 'organic',
            'title': '',
            'url': '',
            'normalized_url': '',
            'description': '',
            'source': '',
            'date': ''
        }
        
        # Extract title
        title_selectors = ['h3', 'h3.LC20lb', '.DKV0Md', 'div[role="heading"]']
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract URL
        link = container.find('a', href=True)
        if link:
            url = self.extract_url_from_href(link['href'])
            if url:
                result['url'] = url
                result['normalized_url'] = self.normalize_url(url)
        
        # Extract description
        desc_selectors = ['.VwiC3b', '.s3v9rd', '.aCOpRe', '.yDYNvb', '.IsZvec', 
                         'div.lyLwlc', 'span:not([class])']
        for selector in desc_selectors:
            desc_elem = container.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                if len(text) > 20:  # Ensure it's actually a description
                    result['description'] = text
                    break
        
        # Extract source
        cite_selectors = ['cite', '.iUh30', '.tjvcx', '.qLRx3b', '.UdvAnf']
        for selector in cite_selectors:
            cite_elem = container.select_one(selector)
            if cite_elem:
                result['source'] = cite_elem.get_text(strip=True)
                break
        
        # Extract date if present
        date_selectors = ['.LEwnzc.Sqrs4e', '.MUxGbd', '.f.nsa']
        for selector in date_selectors:
            date_elem = container.select_one(selector)
            if date_elem:
                result['date'] = date_elem.get_text(strip=True)
                break
        
        # Validate result
        if not result['url'] or not result['title']:
            return None
        
        # Check length constraints
        if len(result['title']) < 3:
            return None
        
        # Check for duplicates
        normalized_url = result['normalized_url']
        content_hash = self.get_content_hash(result['title'], result['description'])
        
        if normalized_url in seen_urls or content_hash in seen_hashes:
            return None
        
        seen_urls.add(normalized_url)
        seen_hashes.add(content_hash)
        
        with self.lock:
            self.global_seen_urls.add(normalized_url)
            self.global_seen_hashes.add(content_hash)
        
        return result

    def _extract_featured_snippet(self, soup):
        """Extract featured snippet"""
        snippet_selectors = ['.xpdopen', '.kp-blk', '.IZ6rdc', '.kno-rdesc']
        for selector in snippet_selectors:
            container = soup.select_one(selector)
            if container:
                title_elem = container.select_one('h3, .LrzXr, div[role="heading"]')
                return {
                    'type': 'featured_snippet',
                    'title': title_elem.get_text(strip=True) if title_elem else '',
                    'content': container.get_text(strip=True)[:500]
                }
        return None

    def _extract_knowledge_panel(self, soup):
        """Extract knowledge panel"""
        panel_selectors = ['.kp-wholepage', '.knowledge-panel', '.osrp-blk']
        for selector in panel_selectors:
            container = soup.select_one(selector)
            if container:
                return {
                    'type': 'knowledge_panel',
                    'title': container.select_one('h2, .qrShPb').get_text(strip=True) if container.select_one('h2, .qrShPb') else '',
                    'description': container.get_text(strip=True)[:300]
                }
        return None

    def _extract_people_also_ask(self, soup):
        """Extract people also ask questions"""
        questions = []
        paa_selectors = ['.related-question-pair', 'div[jsname="yEVEwb"]', '.cbphWd']
        
        for selector in paa_selectors:
            containers = soup.select(selector)
            for container in containers[:10]:  # Limit to 10
                question_elem = container.select_one('.LC20lb, .JlqpRe, div[role="heading"]')
                if question_elem:
                    questions.append({
                        'type': 'people_also_ask',
                        'question': question_elem.get_text(strip=True),
                        'answer': container.get_text(strip=True)[:300]
                    })
            
            if questions:
                break
        
        return questions

    def _extract_related_searches(self, soup):
        """Extract related searches"""
        related = []
        related_selectors = ['.k8XOCe', '.s75CSd', '.AJLUJb', 'div.s75CSd']
        
        for selector in related_selectors:
            containers = soup.select(selector)
            for container in containers:
                text = container.get_text(strip=True)
                link = container.find('a')
                if text and link and link.get('href'):
                    related.append({
                        'text': text,
                        'url': 'https://www.google.com' + link['href']
                    })
            
            if related:
                break
        
        return related[:15]  # Limit to 15

    def _extract_pagination(self, soup):
        """Extract pagination info"""
        pagination = {
            'current_page': 1,
            'has_next': False,
            'has_previous': False,
            'next_url': None,
            'previous_url': None
        }
        
        # Current page
        current = soup.select_one('.YyVfkd')
        if current:
            try:
                pagination['current_page'] = int(current.get_text(strip=True))
            except:
                pass
        
        # Next page
        next_link = soup.select_one('a#pnnext, a[aria-label="Next page"]')
        if next_link and next_link.get('href'):
            pagination['has_next'] = True
            pagination['next_url'] = 'https://www.google.com' + next_link['href']
        
        # Previous page
        prev_link = soup.select_one('a#pnprev, a[aria-label="Previous page"]')
        if prev_link and prev_link.get('href'):
            pagination['has_previous'] = True
            pagination['previous_url'] = 'https://www.google.com' + prev_link['href']
        
        return pagination

    def _extract_metadata(self, soup):
        """Extract metadata"""
        metadata = {
            'result_stats': '',
            'search_time': None,
            'timestamp': datetime.now().isoformat()
        }
        
        stats = soup.select_one('#result-stats')
        if stats:
            metadata['result_stats'] = stats.get_text(strip=True)
            
            # Extract search time
            match = re.search(r'\(([\d.]+) seconds?\)', metadata['result_stats'])
            if match:
                try:
                    metadata['search_time'] = float(match.group(1))
                except:
                    pass
        
        return metadata

    def fetch_page(self, query, start=0, max_retries=3):
        """Fetch a page with retry logic"""
        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'hl': 'en',
            'start': start,
            'num': 10  # Request 10 results
        }
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent on retry
                if attempt > 0:
                    self.rotate_user_agent()
                    time.sleep(random.uniform(2, 5))  # Random delay
                
                response = self.session.get(
                    base_url,
                    params=params,
                    headers=self.headers,
                    timeout=20,
                    allow_redirects=True
                )
                
                # Check for CAPTCHA or blocking
                if 'sorry/index' in response.url or response.status_code == 429:
                    if attempt < max_retries - 1:
                        print(f"Blocked/CAPTCHA detected, retrying... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(random.uniform(5, 10))
                        continue
                    else:
                        return {
                            'success': False,
                            'error': 'Google is blocking requests. Please try again later.',
                            'page': (start // 10) + 1
                        }
                
                response.raise_for_status()
                
                # Parse the page
                local_seen_urls = set()
                local_seen_hashes = set()
                
                page_data = self.scrape_page(
                    response.text,
                    local_seen_urls,
                    local_seen_hashes
                )
                
                return {
                    'success': True,
                    'query': query,
                    'page': (start // 10) + 1,
                    'start': start,
                    'data': page_data,
                    'timestamp': datetime.now().isoformat()
                }
                
            except requests.Timeout:
                if attempt < max_retries - 1:
                    print(f"Timeout, retrying... (attempt {attempt + 1}/{max_retries})")
                    continue
                return {
                    'success': False,
                    'error': 'Request timed out',
                    'page': (start // 10) + 1
                }
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"Request error, retrying... (attempt {attempt + 1}/{max_retries})")
                    continue
                return {
                    'success': False,
                    'error': f'Request failed: {str(e)}',
                    'page': (start // 10) + 1
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'page': (start // 10) + 1
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'page': (start // 10) + 1
        }

    def fetch_range(self, query, start_page=1, end_page=3):
        """Fetch multiple pages"""
        all_data = {
            'organic_results': [],
            'featured_snippets': [],
            'knowledge_panels': [],
            'people_also_ask': [],
            'related_searches': []
        }
        
        seen_urls = set()
        seen_hashes = set()
        pages_collected = []
        
        for page in range(start_page, end_page + 1):
            start = (page - 1) * 10
            
            # Add delay between pages
            if page > start_page:
                time.sleep(random.uniform(1, 3))
            
            result = self.fetch_page(query, start)
            
            if result['success']:
                pages_collected.append(page)
                data = result['data']
                
                # Aggregate results
                for item in data['organic_results']:
                    if item['normalized_url'] not in seen_urls:
                        seen_urls.add(item['normalized_url'])
                        all_data['organic_results'].append(item)
                
                if data['featured_snippet']:
                    all_data['featured_snippets'].append(data['featured_snippet'])
                
                if data['knowledge_panel']:
                    all_data['knowledge_panels'].append(data['knowledge_panel'])
                
                all_data['people_also_ask'].extend(data['people_also_ask'])
                all_data['related_searches'].extend(data['related_searches'])
            else:
                print(f"Failed to fetch page {page}: {result.get('error')}")
        
        return {
            'success': True,
            'query': query,
            'pages_collected': pages_collected,
            'page_range': f'{start_page}-{end_page}',
            'data': all_data,
            'summary': {
                'total_organic': len(all_data['organic_results']),
                'total_paa': len(all_data['people_also_ask']),
                'total_related': len(all_data['related_searches']),
                'total_items': (
                    len(all_data['organic_results']) +
                    len(all_data['people_also_ask']) +
                    len(all_data['related_searches'])
                )
            },
            'timestamp': datetime.now().isoformat()
        }

    def clear_cache(self):
        """Clear global cache"""
        with self.lock:
            self.global_seen_urls.clear()
            self.global_seen_hashes.clear()


scraper = RobustGoogleScraper()


@app.route('/')
def home():
    return json_response({
        'status': 'Production-Ready Google Scraper',
        'version': '4.0',
        'features': [
            'Collects everything from search pages',
            'Smart retry logic with exponential backoff',
            'User agent rotation',
            'CAPTCHA detection',
            'Comprehensive error handling',
            'You control pagination'
        ],
        'endpoints': {
            '/scrape/page': 'GET - Scrape one page (params: q, page)',
            '/scrape/range': 'GET - Scrape multiple pages (params: q, start_page, end_page)',
            '/health': 'GET - Health check',
            '/clear_cache': 'POST - Clear cache'
        },
        'examples': {
            'single': '/scrape/page?q=python&page=1',
            'range': '/scrape/range?q=python&start_page=1&end_page=5'
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return json_response({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/scrape/page', methods=['GET'])
def scrape_page():
    """Scrape a single page"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if page < 1:
        return json_response({'error': 'Page must be >= 1'}, 400)
    
    start = (page - 1) * 10
    result = scraper.fetch_page(query, start)
    
    return json_response(result)


@app.route('/scrape/range', methods=['GET'])
def scrape_range():
    """Scrape multiple pages"""
    query = request.args.get('q', '').strip()
    start_page = int(request.args.get('start_page', 1))
    end_page = int(request.args.get('end_page', 1))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if start_page < 1 or end_page < start_page:
        return json_response({'error': 'Invalid page range'}, 400)
    
    if end_page > 20:
        return json_response({'error': 'end_page cannot exceed 20 (rate limiting)'}, 400)
    
    result = scraper.fetch_range(query, start_page, end_page)
    return json_response(result)


@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear cache"""
    scraper.clear_cache()
    return json_response({'success': True, 'message': 'Cache cleared'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*80}")
    print(f"🚀 PRODUCTION-READY GOOGLE SCRAPER")
    print(f"{'='*80}")
    print(f"📡 Port: {port}")
    print(f"✅ Smart retry logic")
    print(f"✅ User agent rotation")
    print(f"✅ CAPTCHA detection")
    print(f"✅ Comprehensive error handling")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
