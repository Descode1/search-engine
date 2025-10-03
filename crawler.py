import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlparse
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import csv
import random
import re
import sys

# checking for a robots.txt 
def can_crawl(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    time.sleep(random.uniform(1, 2)) 

    try:
        response = requests.get(robots_url, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return True  

    disallowed_paths = []
    current_user_agent = None
    for line in response.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("user-agent"):
            current_user_agent = line.split(":")[1].strip()
        if line.lower().startswith("disallow"):
            path = line.split(":")[1].strip()
            if current_user_agent in ("*", "MyCrawler") and path:
                disallowed_paths.append(path)

    for path in disallowed_paths:
        if urlparse(url).path.startswith(path):
            return False
    return True


# worker function for threads
def worker(queue, visited, visited_lock, results, results_lock, max_pages, max_depth, headers, csv_file, csv_writer, progress, progress_lock):
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

            if not can_crawl(url):
                continue

            try:
                response = requests.get(url, headers=headers, timeout=5)
                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue
            except requests.RequestException:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            full_content = None
            main_content = soup.select_one("div#mw-content-text")
            if main_content:
                full_content = main_content.get_text(" ", strip=True)
                full_content = re.sub(r"\[\d+\]", "", full_content)
                full_content = re.sub(r"\s+", " ", full_content)
            else:
                full_content = soup.get_text(" ", strip=True)
                full_content = re.sub(r"\s+", " ", full_content)

            # gets the title
            title_tag = soup.select_one("title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # gets meta description
            description = None
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag and meta_tag.get("content"):
                description = meta_tag["content"].strip()
            else:
                main_content = soup.select_one("div#mw-content-text")
                text = main_content.get_text(" ", strip=True) if main_content else ""
                text = re.sub(r"\[\d+\]", "", text)
                text = re.sub(r"\s+", " ", text)
                sentences = text.split(".")
                description = ". ".join(sentences[:3]).strip()
                if description and not description.endswith("."):
                    description += "."

            # gets the favicon 
            favicon = None
            icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
            if icon_link and icon_link.get("href"):
                favicon = urljoin(url, icon_link["href"])

            # saves results 
            with results_lock:
                results[url] = {
                    "title": title,
                    "description": description,
                    "favicon": favicon,
                    "content": full_content
                }
                csv_writer.writerow([url, title, description, favicon, full_content])
                csv_file.flush()

            # update progress
            with progress_lock:
                progress["count"] += 1
                crawled = progress["count"]
                if crawled % 10 == 0 or crawled == max_pages:  # print every 10 pages
                    percent = (crawled / max_pages) * 100
                    sys.stdout.write(f"\rCrawled {crawled}/{max_pages} pages ({percent:.2f}%)")
                    sys.stdout.flush()

            # Crawl links 
            if depth < max_depth:
                for link in soup.select("a[href]"):
                    href = link["href"]
                    new_url = urljoin(url, href)
                    new_url, _ = urldefrag(new_url)

                    if not new_url.startswith("http"):
                        continue

                    # Wikipedia English only
                    if "wikipedia.org" in new_url:
                        if not new_url.startswith("https://en.wikipedia.org/wiki/"):
                            continue
                        if any(new_url.startswith(f"https://en.wikipedia.org{prefix}") for prefix in (
                            "/wiki/Special:", "/wiki/File:", "/wiki/Help:", "/wiki/Talk:",
                            "/wiki/Category:", "/wiki/Portal:", "/wiki/Wikipedia:",
                            "/wiki/Template:", "/wiki/Book:", "/wiki/Draft:",
                            "/wiki/Module:", "/wiki/User:", "/wiki/Project:"
                        )):
                            continue

                    with visited_lock:
                        if new_url not in visited:
                            queue.put((new_url, depth + 1))

            time.sleep(0.2)

        finally:
            queue.task_done()


# main crawl function
def crawl(seed_url, max_pages=20000, max_depth=5, num_threads=50, csv_filename="crawl.csv"):
    visited = set()
    visited_lock = threading.Lock()
    results = {}
    results_lock = threading.Lock()
    progress = {"count": 0}
    progress_lock = threading.Lock()
    queue = Queue()
    queue.put((seed_url, 0))
    headers = {"User-Agent": "MyCrawler/1.0"}

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["URL", "Title", "Description", "Favicon","content"])

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for _ in range(num_threads):
                executor.submit(worker, queue, visited, visited_lock,
                                results, results_lock, max_pages, max_depth,
                                headers, csv_file, csv_writer,
                                progress, progress_lock)
            queue.join()

    print()  # move to next line after progress bar
    return results


if __name__ == "__main__":
    pages = crawl("https://en.wikipedia.org/wiki/Rwanda")
    print("\n" + "="*50)
    print("Crawling completed!")
    print("="*50 + "\n")
