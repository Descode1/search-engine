import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import csv
import re


def worker(queue, visited, visited_lock, results, results_lock, max_pages, max_depth, headers, csv_file, csv_writer):
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

            soup = BeautifulSoup(response.text, "html.parser")

            # --- Title ---
            title_tag = soup.select_one("title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # --- Content ---
            content = soup

            description = None

            # Try meta description first
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag and meta_tag.get("content"):
                description = meta_tag["content"].strip()
            else:
                # Fallback: main content text
                main_content = soup.select_one("div#mw-content-text")
                text = main_content.get_text(" ", strip=True) if main_content else ""
                text = re.sub(r"\[\d+\]", "", text)
                text = re.sub(r"\s+", " ", text)
                sentences = text.split(".")
                description = ". ".join(sentences[:3]).strip()
                if description and not description.endswith("."):
                    description += "."

            # --- Favicon ---
            favicon = None
            icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
            if icon_link and icon_link.get("href"):
                favicon = urljoin(url, icon_link["href"])

            # --- Save results ---
            with results_lock:
                results[url] = {
                    "title": title,
                    "description": description,
                    "favicon": favicon,
                }
                csv_writer.writerow([url, title, description, favicon])
                csv_file.flush()  

            # --- Crawl links ---
            if depth < max_depth and content:
                for link in content.select("a[href]"):
                    href = link["href"]
                    new_url = urljoin(url, href)
                    new_url, _ = urldefrag(new_url)

                    # If link is not HTTP, skip
                    if not new_url.startswith("http"):
                        continue

                    # If the page is from Wikipedia, restrict to English only
                    if "wikipedia.org" in new_url:
                        if not new_url.startswith("https://en.wikipedia.org/wiki/"):
                            continue
                        # skip non-article namespaces
                        if any(new_url.startswith(f"https://en.wikipedia.org{prefix}") for prefix in (
                            "/wiki/Special:", "/wiki/File:", "/wiki/Help:", "/wiki/Talk:",
                            "/wiki/Category:", "/wiki/Portal:", "/wiki/Wikipedia:",
                            "/wiki/Template:", "/wiki/Book:", "/wiki/Draft:",
                            "/wiki/Module:", "/wiki/User:", "/wiki/Project:"
                        )):
                            continue

                    # Add to queue if not visited
                    with visited_lock:
                        if new_url not in visited:
                            queue.put((new_url, depth + 1))

            time.sleep(0.2)  

        finally:
            queue.task_done()  


def crawl(seed_url, max_pages, max_depth, num_threads, csv_filename):
    visited = set()
    visited_lock = threading.Lock()
    results = {}         
    results_lock = threading.Lock()

    queue = Queue()
    queue.put((seed_url, 0))

    headers = {"User-Agent": "MyCrawler/1.0"}

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["URL", "Title", "Description", "Favicon"])
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for _ in range(num_threads):
                executor.submit(worker, queue, visited, visited_lock,
                                results, results_lock, max_pages, max_depth, 
                                headers, csv_file, csv_writer)
            queue.join()

    return results


# Run the crawler
pages = crawl("https://en.wikipedia.org/wiki/Rwanda", 100, 2, 50, "crawl.csv")

print("\n" + "="*50)
print("Crawling completed!")
print(f"Total pages crawled: {len(pages)}")
print("Results saved to: crawl.csv")
print("="*50 + "\n")

