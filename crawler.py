import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from collections import deque
import time

def crawl(seed_url, max_pages, max_depth):
    visited = set()
    queue = deque([(seed_url, 0)])  
    
    headers = {
        "User-Agent": "MyCrawler/1.0 (https://example.com/info; contact@example.com)"
    }

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue

        try:
            response = requests.get(url, headers=headers, timeout=5)
            if "text/html" not in response.headers.get("Content-Type", ""):
                continue
        except requests.RequestException:
            continue

        print(f"[Depth {depth}] Crawling: {url}")
        visited.add(url)

        if depth < max_depth:
            
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.select_one("div#mw-content-text > div.mw-parser-output")

            if content:
                for link in content.select("a[href]"):
                    href = link["href"]

                    # Skip unwanted namespaces early
                    if any(href.startswith(prefix) for prefix in ("#", "/wiki/Special:", "/wiki/File:", "/wiki/Help:")):
                        continue

                    new_url = urljoin(url, href)
                    new_url, _ = urldefrag(new_url)

                    if new_url.startswith("http") and new_url not in visited:
                        queue.append((new_url, depth + 1))

       
        time.sleep(0.2)  

    return visited


pages = crawl("https://en.wikipedia.org/wiki/Wikipedia", max_pages=1000, max_depth=2)
print("\nTotal pages crawled:", len(pages))
