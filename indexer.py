import re
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk
import csv
import sys
import json

# Download stopwords and initialises a stemmer to normalise words
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
# increases the maximum field size for CSV reader
csv.field_size_limit(sys.maxsize)

# reads the crawl csv file and stores each page's urls as key along with its metadata as a dictionary
def load_crawl_csv(csv_filename):
    results = {}
    with open(csv_filename, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
 
            results[row['URL']] = {
                "title": row.get('Title', ''),
                "description": row.get('Description', ''),
                "favicon": row.get('Favicon', ''),
                "content": row.get('content', '')
            }
    return results

# converts text to lowercase, removes non-letter chars and removes stopwords
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    words = text.split()
    words = [stemmer.stem(w) for w in words if w not in stop_words]
    return words

# keeps track of how many times each word occurs per page and returns inverted_index and page_metadata
def build_inverted_index(results):
    inverted_index = defaultdict(lambda: defaultdict(int))
    page_metadata = {}

    for url, data in results.items():
        page_metadata[url] = {
            "title": data.get("title", ""),
            "description": data.get("description", "")[:200]  
        }

        #combines title, description and content for indexing
        text = " ".join(filter(None, [data.get("title"), data.get("description"), data.get("content", "")]))
        words = preprocess_text(text)
        for word in words:
            inverted_index[word][url] += 1

    return inverted_index, page_metadata

# saves both the inverted index and page metadata to a json file
def save_inverted_index_json(inverted_index, page_metadata, filename="inverted_index.json"):
    # Convert defaultdicts into normal dicts
    normal_index = {word: dict(urls) for word, urls in inverted_index.items()}
    
    final_data = {
        "index": normal_index,
        "metadata": page_metadata
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    results = load_crawl_csv("crawl.csv")
    inverted_index, page_metadata = build_inverted_index(results)
    save_inverted_index_json(inverted_index, page_metadata, "inverted_index.json")
    print("saved to inverted_index.json")
