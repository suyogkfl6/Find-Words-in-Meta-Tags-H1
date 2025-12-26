import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_metadata(url):
    """
    Fetches the URL and extracts:
    - URL
    - Meta Title
    - Meta Description
    - H1 Tag
    
    Returns a dictionary.
    """
    result = {
        'URL': url,
        'Title': 'N/A',
        'Description': 'N/A',
        'H1': 'N/A',
        'Status': 'Failed'
    }
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Compatible; SEO-Crawler/1.0)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result['Status'] = 'Success'
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Title
            if soup.title and soup.title.string:
                result['Title'] = soup.title.string.strip()
            
            # Meta Description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if not meta_desc:
                # Try case-insensitive variation just in case
                meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
                
            if meta_desc and meta_desc.get('content'):
                result['Description'] = meta_desc.get('content').strip()
            
            # H1
            h1 = soup.find('h1')
            if h1:
                result['H1'] = h1.get_text().strip()
                
        else:
            result['Status'] = f"Error: {response.status_code}"
            
    except Exception as e:
        result['Status'] = f"scraper_error: {str(e)}"
        
    return result

def contains_term(text, term):
    """Helper to check if a term is in the text (case-insensitive)."""
    if not text or text == 'N/A' or not term:
        return False
    return str(term).lower() in str(text).lower()
