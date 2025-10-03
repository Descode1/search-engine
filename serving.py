import json
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import nltk

# Download stopwords once
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

# keeps the query the same way as we built the index
def preprocess_query(query):
    query = query.lower()
    query = re.sub(r'[^a-z\s]', ' ', query)
    words = query.split()
    words = [stemmer.stem(w) for w in words if w not in stop_words]
    return words

#reads the indexed json file
def load_inverted_index(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def search(query, inverted_index):
    words = preprocess_query(query)
    index = inverted_index["index"]
    metadata = inverted_index["metadata"]

    scores = {}

    for word in words:
        if word in index:
            for url, freq in index[word].items():
                scores[url] = scores.get(url, 0) + freq

    # Rank results by score (descending)
    ranked_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Build final result list with metadata
    results = []
    for url, score in ranked_results:
        results.append({
            "url": url,
            "title": metadata.get(url, {}).get("title", ""),
            "description": metadata.get(url, {}).get("description", ""),
            "score": score
        })

    return results

if __name__ == "__main__":
    inverted_index = load_inverted_index("inverted_index.json")

    while True:
        query = input("\n Enter search query (or 'exit' to quit): ")
        if query.lower() == "exit":
            break

        results = search(query, inverted_index)

        if not results:
            print("No results found.")
        else:
            for r in results[:5]:
                print(f"\nTitle: {r['title']}")
                print(f"URL: {r['url']}")
                print(f"Description: {r['description']}")
                print(f"Score: {r['score']}")
