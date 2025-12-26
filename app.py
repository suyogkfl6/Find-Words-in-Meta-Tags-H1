import streamlit as st
import pandas as pd
from utils import crawler, extractor
import time

st.set_page_config(page_title="SEO Metadata Crawler", layout="wide", page_icon="🔍")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 SEO Metadata Crawler")
st.markdown("Crawl sitemaps, extract metadata, and filter for **specific keywords** in real-time at Url, Meta Data & H1.")

# Input Section with Columns
col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input("Website URL", placeholder="https://example.com")
with col2:
    search_term = st.text_input("Search Term", value="2025, 26 (seperated by comma)", placeholder="e.g., 2025, AI, Pricing")

start_button = st.button("🚀 Start Crawl", type="primary")

if start_button:
    if not url_input:
        st.error("Please enter a URL.")
    else:
        # Normalize URL
        if not url_input.startswith(('http://', 'https://')):
            url_input = 'https://' + url_input

        # UI Containers
        status_container = st.empty()
        metrics_container = st.container()
        progress_bar = st.progress(0)
        table_placeholder = st.empty()
        
        # Metrics Placeholders
        with metrics_container:
            m1, m2, m3 = st.columns(3)
            metric_urls = m1.empty()
            metric_scanned = m2.empty()
            metric_matches = m3.empty()

        # Initialize Data
        results = []
        
        # 1. Find Sitemap
        status_container.info("Searching for sitemap... 🕵️‍♂️")
        sitemap_url = crawler.find_sitemap(url_input)
        
        if not sitemap_url:
            st.error(f"❌ Could not find a sitemap for {url_input}.")
        else:
            status_container.success(f"✅ Found sitemap: {sitemap_url}")
            time.sleep(1)
            
            # 2. Get All URLs
            status_container.info(f"Crawling sitemap... 🕸️")
            urls = crawler.get_all_urls(sitemap_url)
            
            if not urls:
                st.error("❌ No URLs found in the sitemap.")
            else:
                total_urls = len(urls)
                status_container.info(f"Processing {total_urls} URLs... ⏳")
                
                # Update Metrics Initial State
                metric_urls.metric("Total URLs", total_urls)
                metric_scanned.metric("Scanned", 0)
                metric_matches.metric("Matches Found", 0)

                # 3. Extract Metadata
                for i, url in enumerate(urls):
                    # Update Progress
                    progress = (i + 1) / total_urls
                    progress_bar.progress(progress)
                    
                    # Extract Data
                    data = extractor.extract_metadata(url)
                    
                    # Prepare Search Terms (Comma separated)
                    search_terms = [t.strip() for t in search_term.split(',') if t.strip()] if search_term else []
                    
                    # Check for Matches
                    match_found = False
                    if not search_terms:
                        # If no search term, show everything (or nothing? usually nothing if filter mode, but let's assume specific filter)
                        # User said "search multiple string", implying filtering. If empty, maybe show none or all? 
                        # Previous logic: if search_term was empty, it might have matched nothing.
                        # Let's assume if empty input, we don't match anything effectively unless we want to show all. 
                        # But typically 'search' implies filtering.
                        pass 
                    else:
                        # Check if ANY term matches ANY field (including URL)
                        for term in search_terms:
                            if (extractor.contains_term(data.get('URL'), term) or 
                                extractor.contains_term(data.get('Title'), term) or 
                                extractor.contains_term(data.get('Description'), term) or 
                                extractor.contains_term(data.get('H1'), term)):
                                match_found = True
                                break
                    
                    if match_found:
                        results.append(data)
                        
                        # Real-time Table Update
                        df = pd.DataFrame(results)
                        # Reorder/Ensure Columns
                        cols = ['URL', 'Title', 'Description', 'H1', 'Status']
                        for c in cols:
                            if c not in df.columns: df[c] = 'N/A'
                        df = df[cols]

                        def highlight_terms(val):
                            if isinstance(val, str) and search_terms:
                                for term in search_terms:
                                    if term.lower() in val.lower():
                                        return 'background-color: #fff9c4; color: black; font-weight: bold;' # Light yellow
                            return ''

                        styled_df = df.style.map(highlight_terms)
                        table_placeholder.dataframe(styled_df, use_container_width=True, height=400)
                        
                        # Update Matches Metric
                        metric_matches.metric("Matches Found", len(results))

                    # Update Scanned Metric
                    metric_scanned.metric("Scanned", i + 1)
                
                progress_bar.empty()
                status_container.success("🎉 Crawl Complete!")
                
                # Final Export (if results exist)
                if results:
                    csv = pd.DataFrame(results).to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f'seo_report.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning(f"No pages found matching: {search_term}")
