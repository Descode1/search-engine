##  Search Engine

### Description

This project is a minimal end‑to‑end search engine pipeline that:

- Crawls web pages (focused on Wikipedia by default) and stores page text plus metadata into a CSV.
- Builds a tokenized, stemmed inverted index from the crawl output.
- Provides a simple keyword search CLI that ranks results by term frequency.

It is intended as a concise, beginner‑friendly reference implementation of the classic crawl → index → search workflow.

### Features

- **Polite crawler with robots.txt check**: Respects disallow rules where possible and throttles requests.
- **Focused link expansion**: Follows only English Wikipedia article pages by default to stay on‑topic.
- **Metadata extraction**: Title, description (heuristic), favicon, and full page text.
- **Text preprocessing**: Lowercasing, non‑letter filtering, English stopword removal, Porter stemming.
- **Inverted index**: Maps each stemmed term to URLs and term frequencies.
- **Search & ranking**: Simple term‑frequency scoring aggregated across query terms; returns top matches with titles and snippets.

### Installation

The project is pure Python. You’ll need Python 3.8+.

1. Clone or download this repository to your machine.

2. (Recommended) Create and activate a virtual environment.

```powershell
# From the project root
python -m venv .venv
./.venv/Scripts/Activate.ps1
```

3. Install dependencies.

```powershell
pip install requests beautifulsoup4 nltk
```

Note: The first run of `indexer.py` or `serving.py` downloads the NLTK English stopwords corpus automatically.

### Usage

There are three main steps: crawl, index, and search. All commands below assume you run them from the project root and that your virtual environment is active.

#### 1) Crawl web pages → produce crawl.csv

`crawler.py` starts from a seed URL, expands links (Wikipedia‑focused), and writes rows into `crawl.csv`.

```powershell
python crawler.py
```

Default behavior crawls starting from `https://en.wikipedia.org/wiki/Rwanda` with multiple threads and prints progress, producing a `crawl.csv` like:

```text
URL,Title,Description,Favicon,content
https://en.wikipedia.org/wiki/Rwanda, Rwanda - Wikipedia, Rwanda is a country..., https://.../favicon.ico, Full page text...
...
```

Want to use a different seed URL or limits? Two easy options:

- Edit the call at the bottom of `crawler.py` to your preferred seed URL and rerun.
- Or open a Python REPL and run the function directly:

```powershell
python -c "import crawler; crawler.crawl('https://en.wikipedia.org/wiki/Natural_language_processing', max_pages=500, max_depth=3, num_threads=20, csv_filename='crawl.csv')"
```

#### 2) Build the inverted index → produce inverted_index.json

`indexer.py` reads `crawl.csv`, preprocesses text, and writes `inverted_index.json` (index + page metadata).

```powershell
python indexer.py
```

Expected output:

```text
saved to inverted_index.json
```

#### 3) Search via CLI over the built index

`serving.py` loads `inverted_index.json` and provides an interactive prompt:

```powershell
python serving.py
```

Example session:

```text
 Enter search query (or 'exit' to quit): rwanda geography

Title: Rwanda - Wikipedia
URL: https://en.wikipedia.org/wiki/Rwanda
Description: Rwanda, officially the Republic of Rwanda, is a landlocked country...
Score: 27
```

Type `exit` to quit.

### File Structure

- `crawler.py`: Multithreaded crawler that starts from a seed URL, respects robots.txt where possible, extracts metadata and main text, and writes to `crawl.csv`.
- `indexer.py`: Reads `crawl.csv`, preprocesses text (stopwords + stemming), and builds `inverted_index.json` with an inverted index and page metadata.
- `serving.py`: Interactive keyword search over `inverted_index.json`, returning ranked results with titles/descriptions.
- `crawl.csv`: Output of the crawler (generated).
- `inverted_index.json`: Output of the indexer (generated).

### How It Works

#### CSV crawler/indexer

- The crawler visits pages breadth‑first using a work queue and a visited set, with concurrency via `ThreadPoolExecutor`.
- It extracts title, a heuristic description (meta description if present, else first sentences), favicon URL, and cleaned full text. Every crawled page is appended to `crawl.csv`.
- The indexer reads `crawl.csv` and constructs two artifacts:
  - `index`: term → { url → frequency }
  - `metadata`: url → { title, description }

#### Text preprocessing (stopwords removal, stemming)

Preprocessing normalizes text as follows:

1. Lowercase text.
2. Remove non‑alphabetic characters.
3. Tokenize on whitespace.
4. Remove English stopwords using NLTK’s stopword list.
5. Stem remaining tokens with the Porter stemmer.

This is applied consistently when building the index and when preprocessing queries so terms match.

#### Inverted index

The inverted index is a dictionary keyed by stemmed term. For each term, it stores a mapping of URL → frequency (number of occurrences in that page’s combined title + description + content). It is serialized to `inverted_index.json` alongside page metadata for display.

Data shape in `inverted_index.json`:

```json
{
  "index": {
    "rwanda": {"https://en.wikipedia.org/wiki/Rwanda": 42, ...},
    "geograph": {"https://en.wikipedia.org/wiki/Rwanda": 8, ...}
  },
  "metadata": {
    "https://en.wikipedia.org/wiki/Rwanda": {
      "title": "Rwanda - Wikipedia",
      "description": "Rwanda, officially the Republic of Rwanda, ..."
    }
  }
}
```

#### Search and ranking mechanism

User queries are preprocessed the same way as documents. For each query term, the engine looks up matching URLs in the inverted index and accumulates scores equal to term frequencies (which is not that good). Final ranking sorts URLs by total score descending. Returned results include URL, title, description, and score.

### Troubleshooting & Tips

- If you want a smaller/larger crawl, tune `max_pages`, `max_depth`, and `num_threads` in the call to `crawl(...)`.
- The crawler checks `robots.txt` with a simple parser. When in doubt, it errs on continuing only if not explicitly disallowed.
- The crawler focuses link expansion to English Wikipedia article pages. Remove those checks in `crawler.py` if you want a broader crawl (use cautiously).
