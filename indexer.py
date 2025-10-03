import re
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk
import csv
import sys
import json

# Download stopwords once
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

csv.field_size_limit(sys.maxsize)

def load_crawl_csv(csv_filename):
    results = {}
    with open(csv_filename, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            full_content = row.get('Content', '')
            results[row['URL']] = {
                "title": row.get('Title', ''),
                "description": row.get('Description', ''),
                "favicon": row.get('Favicon', ''),
                "content": full_content
            }
    return results

# --- Preprocess text ---
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)  
    words = text.split()
    words = [stemmer.stem(w) for w in words if w not in stop_words]
    return words

# --- Build inverted index ---
def build_inverted_index(results):
    inverted_index = defaultdict(lambda: defaultdict(int))
    for url, data in results.items():
        text = " ".join(filter(None, [data.get("title"), data.get("description"), data.get("content", "")]))
        words = preprocess_text(text)
        for word in words:
            inverted_index[word][url] += 1
    return inverted_index

# --- Save inverted index to JSON ---
def save_inverted_index_json(inverted_index, filename="inverted_index.json"):
    # Convert defaultdicts into normal dicts for JSON serialization
    normal_index = {word: dict(urls) for word, urls in inverted_index.items()}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(normal_index, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    results = load_crawl_csv("crawl.csv")
    inverted_index = build_inverted_index(results)
    save_inverted_index_json(inverted_index, "inverted_index.json")
    print("saved to inverted_index.json")
