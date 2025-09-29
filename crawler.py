import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Worker function for each thread
def worker(queue, visited, visited_lock, max_pages, max_depth, headers):
    while True:
        try:
            url, depth = queue.get(timeout=5) 
        except:
            break  

        try:
            with visited_lock:
                if url in visited or len(visited) >= max_pages or depth > max_depth:
                    continue
                visited.add(url)

            try:
                response = requests.get(url, headers=headers, timeout=5)
                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue
            except requests.RequestException:
                continue

            print(f"[Depth {depth}] Crawling: {url}")

            if depth < max_depth:
                soup = BeautifulSoup(response.text, "html.parser")
                content = soup.select_one("div#mw-content-text > div.mw-parser-output")

                if content:
                    for link in content.select("a[href]"):
                        href = link["href"]
                        if any(href.startswith(prefix) for prefix in ("#", "/wiki/Special:", "/wiki/File:", "/wiki/Help:")):
                            continue

                        new_url = urljoin(url, href)
                        new_url, _ = urldefrag(new_url)

                        if new_url.startswith("http"):
                            with visited_lock:
                                if new_url not in visited:
                                    queue.put((new_url, depth + 1))

            time.sleep(0.2)  

        finally:
            queue.task_done()  

# Main crawl function
def crawl(seed_url, max_pages, max_depth, num_threads):
    visited = set()
    visited_lock = threading.Lock()
    queue = Queue()
    queue.put((seed_url, 0))

    headers = {
        "User-Agent": "MyCrawler/1.0 (https://example.com/info; contact@example.com)"
    }

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            executor.submit(worker, queue, visited, visited_lock, max_pages, max_depth, headers)

        queue.join()  

    return visited


pages = crawl("https://en.wikipedia.org/wiki/Rwanda", 10000,2,25)
print("\nTotal pages crawled:", len(pages))
