import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_sitemap(domain_url):
    """
    Attempts to find the sitemap URL for a given domain.
    1. Checks robots.txt
    2. Checks standard paths like /sitemap.xml, /sitemap_index.xml
    """
    domain_url = domain_url.rstrip('/')
    parsed_url = urlparse(domain_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # 1. Check robots.txt
    robots_url = urljoin(base_url, '/robots.txt')
    headers = {'User-Agent': 'Mozilla/5.0 (Compatible; SEO-Crawler/1.0)'}
    try:
        logger.info(f"Checking robots.txt at {robots_url}...")
        response = requests.get(robots_url, headers=headers, timeout=5)
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    logger.info(f"✅ Found sitemap in robots.txt: {sitemap_url}")
                    return sitemap_url
        else:
            logger.info("robots.txt not found or unavailable, proceeding to fallbacks.")
    except Exception as e:
        logger.warning(f"⚠️ Error/Timeout checking robots.txt: {e}. Proceeding to fallbacks.")

    # 2. Check standard fallbacks
    fallbacks = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemap.php',
        '/sitemap/sitemap.xml'
    ]
    
    logger.info("Checking standard sitemap locations...")
    for path in fallbacks:
        sitemap_url = urljoin(base_url, path)
        try:
            response = requests.head(sitemap_url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                logger.info(f"✅ Found sitemap at standard path: {sitemap_url}")
                return sitemap_url
        except Exception:
            continue
            
    logger.error("❌ No sitemap found.")
    return None

def get_all_urls(sitemap_url, recursive=True):
    """
    Parses a sitemap or sitemap index and returns a list of all page URLs.
    Handles recursive sitemap indices.
    """
    urls = set()
    try:
        logger.info(f"Fetching sitemap: {sitemap_url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Compatible; SEO-Crawler/1.0)'}
        response = requests.get(sitemap_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch sitemap: {sitemap_url} (Status: {response.status_code})")
            return []

        # Parse XML
        soup = BeautifulSoup(response.content, 'xml')
        
        # Check if it's a Sitemap Index
        sitemaps = soup.find_all('sitemap')
        if sitemaps and recursive:
            logger.info(f"Found sitemap index with {len(sitemaps)} sub-sitemaps.")
            for sm in sitemaps:
                loc = sm.find('loc')
                if loc:
                    sub_sitemap_url = loc.get_text().strip()
                    urls.update(get_all_urls(sub_sitemap_url, recursive=True))
        
        # Check if it's a URL Set
        url_tags = soup.find_all('url')
        if url_tags:
            logger.info(f"Found {len(url_tags)} URLs in {sitemap_url}")
            for url_tag in url_tags:
                loc = url_tag.find('loc')
                if loc:
                    urls.add(loc.get_text().strip())
                    
    except Exception as e:
        logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
        
    return list(urls)
