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

class ComprehensiveGoogleScraper:
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
        self.global_seen_hashes = set()

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
        """Normalize URL to catch duplicates"""
        if not url:
            return None
        
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 
                          'fbclid', 'gclid', 'ref', 'source']
        
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
        """Generate hash from content"""
        content = f"{title.lower().strip()}|{description.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def extract_url_from_href(self, href):
        """Extract actual URL from Google's various formats"""
        if not href:
            return None
            
        if href.startswith('/url?q='):
            try:
                url = href.split('/url?q=')[1].split('&')[0]
                return urllib.parse.unquote(url)
            except:
                return None
        elif href.startswith('http'):
            return href
        elif href.startswith('/search'):  # Internal Google search link
            return None
        else:
            return None

    def scrape_everything_from_page(self, html_content, local_seen_urls=None, local_seen_hashes=None):
        """
        COMPREHENSIVE SCRAPER - Collects EVERYTHING from the page:
        - Organic results
        - Featured snippets
        - Knowledge panels
        - People also ask
        - Related searches
        - News results
        - Video results
        - Image results
        - Shopping results
        - Local results
        - Ads (if present)
        """
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

        # ========== 1. ORGANIC SEARCH RESULTS ==========
        organic_containers = (
            soup.select('div.MjjYud') or
            soup.select('div.Gx5Zad.fP1Qef.xpd.EtOod.pkphOe') or
            soup.select('div.tF2Cxc') or
            soup.select('div.g:not(.g-blk)') or
            soup.select('div.rc')
        )
        
        for container in organic_containers:
            result = self._extract_organic_result(container, local_seen_urls, local_seen_hashes)
            if result:
                page_data['organic_results'].append(result)

        # ========== 2. FEATURED SNIPPET ==========
        featured_snippet = soup.select_one('.xpdopen, .kp-blk, .IZ6rdc')
        if featured_snippet:
            page_data['featured_snippet'] = self._extract_featured_snippet(featured_snippet)

        # ========== 3. KNOWLEDGE PANEL ==========
        knowledge_panel = soup.select_one('.kp-wholepage, .knowledge-panel, .osrp-blk')
        if knowledge_panel:
            page_data['knowledge_panel'] = self._extract_knowledge_panel(knowledge_panel)

        # ========== 4. PEOPLE ALSO ASK ==========
        paa_section = soup.select('.related-question-pair, .kno-ftr, div[jsname="yEVEwb"]')
        for question in paa_section:
            paa_item = self._extract_people_also_ask(question)
            if paa_item:
                page_data['people_also_ask'].append(paa_item)

        # ========== 5. RELATED SEARCHES ==========
        related_searches = soup.select('.k8XOCe, .s75CSd, .AJLUJb')
        for related in related_searches:
            search_text = related.get_text(strip=True)
            search_link = related.find('a')
            if search_text and search_link:
                page_data['related_searches'].append({
                    'text': search_text,
                    'url': 'https://www.google.com' + search_link.get('href', '')
                })

        # ========== 6. NEWS RESULTS ==========
        news_blocks = soup.select('.WlydOe, .SoaBEf, .nChh6e')
        for news in news_blocks:
            news_item = self._extract_news_result(news)
            if news_item:
                page_data['news_results'].append(news_item)

        # ========== 7. VIDEO RESULTS ==========
        video_blocks = soup.select('.RzdJxc, .VibNM, .dFd0Ac')
        for video in video_blocks:
            video_item = self._extract_video_result(video)
            if video_item:
                page_data['video_results'].append(video_item)

        # ========== 8. IMAGE RESULTS (if embedded) ==========
        image_blocks = soup.select('.ivg-i, .isv-r')
        for img in image_blocks[:10]:  # Limit to first 10
            image_item = self._extract_image_result(img)
            if image_item:
                page_data['image_results'].append(image_item)

        # ========== 9. SHOPPING RESULTS ==========
        shopping_blocks = soup.select('.sh-dgr__content, .pla-unit')
        for shop in shopping_blocks:
            shop_item = self._extract_shopping_result(shop)
            if shop_item:
                page_data['shopping_results'].append(shop_item)

        # ========== 10. LOCAL RESULTS (Maps) ==========
        local_blocks = soup.select('.rllt__details, .VkpGBb')
        for local in local_blocks:
            local_item = self._extract_local_result(local)
            if local_item:
                page_data['local_results'].append(local_item)

        # ========== 11. ADS (Top & Bottom) ==========
        ad_blocks = soup.select('.uEierd, .v5yQqb, div[data-text-ad]')
        for ad in ad_blocks:
            ad_item = self._extract_ad_result(ad)
            if ad_item:
                page_data['ads'].append(ad_item)

        # ========== 12. PAGINATION INFO ==========
        page_data['pagination'] = self._extract_pagination(soup)

        # ========== 13. METADATA ==========
        page_data['metadata'] = {
            'result_stats': self._extract_result_stats(soup),
            'search_time': self._extract_search_time(soup),
            'timestamp': datetime.now().isoformat()
        }

        # ========== SUMMARY ==========
        page_data['summary'] = {
            'total_organic': len(page_data['organic_results']),
            'total_paa': len(page_data['people_also_ask']),
            'total_related': len(page_data['related_searches']),
            'total_news': len(page_data['news_results']),
            'total_videos': len(page_data['video_results']),
            'total_images': len(page_data['image_results']),
            'total_shopping': len(page_data['shopping_results']),
            'total_local': len(page_data['local_results']),
            'total_ads': len(page_data['ads']),
            'has_featured_snippet': page_data['featured_snippet'] is not None,
            'has_knowledge_panel': page_data['knowledge_panel'] is not None,
            'total_items': (
                len(page_data['organic_results']) +
                len(page_data['people_also_ask']) +
                len(page_data['news_results']) +
                len(page_data['video_results']) +
                len(page_data['ads'])
            )
        }

        return page_data

    # ========== EXTRACTION METHODS ==========
    
    def _extract_organic_result(self, container, seen_urls, seen_hashes):
        """Extract organic search result"""
        result = {
            'type': 'organic',
            'title': '',
            'url': '',
            'normalized_url': '',
            'description': '',
            'source': '',
            'date': '',
            'rich_snippet': {}
        }
        
        # Title
        title_elem = (
            container.select_one('h3') or
            container.select_one('h3.LC20lb') or
            container.select_one('.DKV0Md')
        )
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        # URL
        link = container.find('a', href=True)
        if link:
            url = self.extract_url_from_href(link['href'])
            if url:
                result['url'] = url
                result['normalized_url'] = self.normalize_url(url)
        
        # Description
        desc_elem = (
            container.select_one('.VwiC3b') or
            container.select_one('.s3v9rd') or
            container.select_one('.aCOpRe') or
            container.select_one('.yDYNvb') or
            container.select_one('.IsZvec') or
            container.select_one('span')
        )
        if desc_elem:
            result['description'] = desc_elem.get_text(strip=True)
        
        # Source/Domain
        cite_elem = (
            container.select_one('cite') or
            container.select_one('.iUh30') or
            container.select_one('.tjvcx') or
            container.select_one('.qLRx3b')
        )
        if cite_elem:
            result['source'] = cite_elem.get_text(strip=True)
        
        # Date
        date_elem = container.select_one('.LEwnzc.Sqrs4e, .MUxGbd')
        if date_elem:
            result['date'] = date_elem.get_text(strip=True)
        
        # Rich Snippet (ratings, price, etc.)
        rating = container.select_one('.fG8Fp, .z3HNkc')
        if rating:
            result['rich_snippet']['rating'] = rating.get_text(strip=True)
        
        # Check for duplicates
        if not result['url'] or not result['title']:
            return None
            
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

    def _extract_featured_snippet(self, container):
        """Extract featured snippet"""
        return {
            'type': 'featured_snippet',
            'title': container.select_one('h3, .LrzXr').get_text(strip=True) if container.select_one('h3, .LrzXr') else '',
            'content': container.get_text(strip=True)[:500],
            'url': self.extract_url_from_href(container.find('a')['href']) if container.find('a') else ''
        }

    def _extract_knowledge_panel(self, container):
        """Extract knowledge panel"""
        return {
            'type': 'knowledge_panel',
            'title': container.select_one('h2, .qrShPb').get_text(strip=True) if container.select_one('h2, .qrShPb') else '',
            'description': container.select_one('.kno-rdesc, .LWkfKe').get_text(strip=True) if container.select_one('.kno-rdesc, .LWkfKe') else '',
            'image_url': container.find('img')['src'] if container.find('img') else None,
            'facts': [elem.get_text(strip=True) for elem in container.select('.w8qArf, .kno-fv')][:10]
        }

    def _extract_people_also_ask(self, container):
        """Extract people also ask question"""
        question = container.select_one('.LC20lb, .JlqpRe')
        if question:
            return {
                'type': 'people_also_ask',
                'question': question.get_text(strip=True),
                'answer': container.get_text(strip=True)[:300]
            }
        return None

    def _extract_news_result(self, container):
        """Extract news result"""
        title = container.select_one('.mCBkyc, .n0jPhd')
        link = container.find('a')
        if title and link:
            return {
                'type': 'news',
                'title': title.get_text(strip=True),
                'url': self.extract_url_from_href(link['href']),
                'source': container.select_one('.CEMjEf, .WF4CUc').get_text(strip=True) if container.select_one('.CEMjEf, .WF4CUc') else '',
                'date': container.select_one('.ZE0LJd, .OSrXXb').get_text(strip=True) if container.select_one('.ZE0LJd, .OSrXXb') else ''
            }
        return None

    def _extract_video_result(self, container):
        """Extract video result"""
        title = container.select_one('h3, .DhN8Cf')
        link = container.find('a')
        if title and link:
            return {
                'type': 'video',
                'title': title.get_text(strip=True),
                'url': self.extract_url_from_href(link['href']),
                'thumbnail': container.find('img')['src'] if container.find('img') else None,
                'duration': container.select_one('.J1mWY, .P7xzyf').get_text(strip=True) if container.select_one('.J1mWY, .P7xzyf') else '',
                'source': container.select_one('.Zg1NU, .fYyStc').get_text(strip=True) if container.select_one('.Zg1NU, .fYyStc') else ''
            }
        return None

    def _extract_image_result(self, container):
        """Extract image result"""
        img = container.find('img')
        link = container.find('a')
        if img and link:
            return {
                'type': 'image',
                'thumbnail_url': img.get('src', img.get('data-src', '')),
                'link_url': self.extract_url_from_href(link['href']),
                'title': img.get('alt', '')
            }
        return None

    def _extract_shopping_result(self, container):
        """Extract shopping result"""
        title = container.select_one('.Xjkr3b, .tAxDx')
        price = container.select_one('.a8Pemb, .e10twf')
        if title:
            return {
                'type': 'shopping',
                'title': title.get_text(strip=True),
                'price': price.get_text(strip=True) if price else '',
                'merchant': container.select_one('.IuHnof, .aULzUe').get_text(strip=True) if container.select_one('.IuHnof, .aULzUe') else '',
                'image': container.find('img')['src'] if container.find('img') else None
            }
        return None

    def _extract_local_result(self, container):
        """Extract local/map result"""
        name = container.select_one('.OSrXXb, .dbg0pd')
        if name:
            return {
                'type': 'local',
                'name': name.get_text(strip=True),
                'address': container.select_one('.rllt__details div').get_text(strip=True) if container.select_one('.rllt__details div') else '',
                'rating': container.select_one('.BTtC6e, .yi40Hd').get_text(strip=True) if container.select_one('.BTtC6e, .yi40Hd') else '',
                'hours': container.select_one('.aiRlze, .MGDDX').get_text(strip=True) if container.select_one('.aiRlze, .MGDDX') else ''
            }
        return None

    def _extract_ad_result(self, container):
        """Extract ad"""
        title = container.select_one('div[role="heading"], .v5yQqb')
        link = container.find('a')
        if title and link:
            return {
                'type': 'ad',
                'title': title.get_text(strip=True),
                'url': self.extract_url_from_href(link['href']),
                'description': container.get_text(strip=True)[:200],
                'position': 'top' if container.find_parent('.commercial-unit-desktop-top') else 'bottom'
            }
        return None

    def _extract_pagination(self, soup):
        """Extract pagination information"""
        pagination = {
            'current_page': 1,
            'has_next': False,
            'has_previous': False,
            'next_url': None,
            'previous_url': None,
            'pages': []
        }
        
        # Current page
        current = soup.select_one('.YyVfkd')
        if current:
            try:
                pagination['current_page'] = int(current.get_text(strip=True))
            except:
                pass
        
        # Next page
        next_link = soup.select_one('a#pnnext')
        if next_link and next_link.get('href'):
            pagination['has_next'] = True
            pagination['next_url'] = 'https://www.google.com' + next_link['href']
        
        # Previous page
        prev_link = soup.select_one('a#pnprev')
        if prev_link and prev_link.get('href'):
            pagination['has_previous'] = True
            pagination['previous_url'] = 'https://www.google.com' + prev_link['href']
        
        # All page numbers
        page_links = soup.select('.AaVjTc td a, .fl')
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                pagination['pages'].append({
                    'page': page_num,
                    'url': 'https://www.google.com' + link['href']
                })
            except:
                pass
        
        return pagination

    def _extract_result_stats(self, soup):
        """Extract result statistics"""
        stats = soup.select_one('#result-stats')
        if stats:
            return stats.get_text(strip=True)
        return ''

    def _extract_search_time(self, soup):
        """Extract search time"""
        stats = soup.select_one('#result-stats')
        if stats:
            text = stats.get_text()
            match = re.search(r'\(([\d.]+) seconds\)', text)
            if match:
                return float(match.group(1))
        return None

    def clear_global_cache(self):
        """Clear the global duplicate tracking cache"""
        with self.lock:
            self.global_seen_urls.clear()
            self.global_seen_hashes.clear()

    # ========== API METHODS ==========
    
    def fetch_complete_page(self, query, start=0):
        """Fetch and parse everything from a single page"""
        base_url = "https://www.google.com/search"
        params = {'q': query, 'hl': 'en', 'start': start}
        
        try:
            response = self.session.get(base_url, params=params, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            local_seen_urls = set()
            local_seen_hashes = set()
            
            page_data = self.scrape_everything_from_page(
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
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'page': (start // 10) + 1
            }

    def fetch_custom_range(self, query, start_page=1, end_page=3):
        """Fetch multiple pages with full control"""
        all_data = {
            'organic_results': [],
            'featured_snippets': [],
            'knowledge_panels': [],
            'people_also_ask': [],
            'related_searches': [],
            'news_results': [],
            'video_results': [],
            'image_results': [],
            'shopping_results': [],
            'local_results': [],
            'ads': []
        }
        
        seen_urls = set()
        seen_hashes = set()
        
        pages_collected = []
        
        for page in range(start_page, end_page + 1):
            start = (page - 1) * 10
            result = self.fetch_complete_page(query, start)
            
            if result['success']:
                pages_collected.append(page)
                data = result['data']
                
                # Aggregate all results
                for item in data['organic_results']:
                    if item['normalized_url'] not in seen_urls:
                        seen_urls.add(item['normalized_url'])
                        all_data['organic_results'].append(item)
                
                if data['featured_snippet'] and data['featured_snippet'] not in all_data['featured_snippets']:
                    all_data['featured_snippets'].append(data['featured_snippet'])
                
                if data['knowledge_panel'] and data['knowledge_panel'] not in all_data['knowledge_panels']:
                    all_data['knowledge_panels'].append(data['knowledge_panel'])
                
                all_data['people_also_ask'].extend(data['people_also_ask'])
                all_data['related_searches'].extend(data['related_searches'])
                all_data['news_results'].extend(data['news_results'])
                all_data['video_results'].extend(data['video_results'])
                all_data['image_results'].extend(data['image_results'])
                all_data['shopping_results'].extend(data['shopping_results'])
                all_data['local_results'].extend(data['local_results'])
                all_data['ads'].extend(data['ads'])
        
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
                'total_news': len(all_data['news_results']),
                'total_videos': len(all_data['video_results']),
                'total_images': len(all_data['image_results']),
                'total_shopping': len(all_data['shopping_results']),
                'total_local': len(all_data['local_results']),
                'total_ads': len(all_data['ads']),
                'total_items': (
                    len(all_data['organic_results']) +
                    len(all_data['people_also_ask']) +
                    len(all_data['news_results']) +
                    len(all_data['video_results']) +
                    len(all_data['ads'])
                )
            },
            'timestamp': datetime.now().isoformat()
        }


scraper = ComprehensiveGoogleScraper()


@app.route('/')
def home():
    return json_response({
        'status': 'Comprehensive Google Scraper - COLLECT EVERYTHING',
        'version': '3.0',
        'description': 'Scrapes ALL content types from Google search pages. You control pagination.',
        'endpoints': {
            '/scrape/page': 'GET - Scrape EVERYTHING from a single page (params: q, page)',
            '/scrape/range': 'GET - Scrape multiple pages (params: q, start_page, end_page)',
            '/clear_cache': 'POST - Clear global deduplication cache'
        },
        'collected_content': [
            'Organic search results',
            'Featured snippets',
            'Knowledge panels',
            'People also ask',
            'Related searches',
            'News results',
            'Video results',
            'Image results (embedded)',
            'Shopping results',
            'Local/Map results',
            'Ads (top & bottom)',
            'Pagination metadata',
            'Search statistics'
        ],
        'examples': {
            'single_page': '/scrape/page?q=python&page=1',
            'custom_range': '/scrape/range?q=python&start_page=1&end_page=5',
            'specific_page': '/scrape/page?q=hostinger&page=3'
        }
    })


@app.route('/scrape/page', methods=['GET'])
def scrape_single_page():
    """Scrape EVERYTHING from a single page"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if page < 1:
        return json_response({'error': 'Page must be >= 1'}, 400)
    
    start = (page - 1) * 10
    result = scraper.fetch_complete_page(query, start)
    
    return json_response(result)


@app.route('/scrape/range', methods=['GET'])
def scrape_page_range():
    """Scrape multiple pages - YOU control pagination"""
    query = request.args.get('q', '').strip()
    start_page = int(request.args.get('start_page', 1))
    end_page = int(request.args.get('end_page', 1))
    
    if not query:
        return json_response({'error': 'Missing query parameter (q)'}, 400)
    
    if start_page < 1 or end_page < start_page:
        return json_response({'error': 'Invalid page range'}, 400)
    
    if end_page > 50:
        return json_response({'error': 'end_page cannot exceed 50'}, 400)
    
    result = scraper.fetch_custom_range(query, start_page, end_page)
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
    print(f"\n{'='*80}")
    print(f"🚀 COMPREHENSIVE GOOGLE SCRAPER STARTED")
    print(f"{'='*80}")
    print(f"📡 Port: {port}")
    print(f"🎯 Collects: Organic results, Featured snippets, Knowledge panels,")
    print(f"            People also ask, Related searches, News, Videos, Images,")
    print(f"            Shopping, Local results, Ads, and more!")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
