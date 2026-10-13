import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def scrape_faculty_data():
    """
    Scrapes faculty name, designation, profile URL, and bio from multiple pages.
    Returns a list of dictionaries, where each dictionary represents a faculty member.
    """
    print("Scraping faculty data... this may take a moment.")
    faculty_data = []
    base_url = "https://www.amrita.edu/faculty/page/{}/?cmp=45"

    # Start with the first page
    urls = ["https://www.amrita.edu/faculty/?cmp=45"]
    # Add subsequent pages (2 to 8)
    for i in range(2, 9):
        urls.append(base_url.format(i))

    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            faculty_items = soup.find_all('div', class_='fc-item')

            for item in faculty_items:
                name_elem = item.find('h6')
                designation_elem = item.find('p')
                link_elem = item.find('a', href=True)

                name = name_elem.text.strip() if name_elem else 'N/A'
                designation = designation_elem.text.strip() if designation_elem else 'N/A'
                profile_url = link_elem['href'] if link_elem else 'N/A'

                bio = 'N/A'
                if profile_url and profile_url != 'N/A':
                    try:
                        profile_response = requests.get(profile_url)
                        profile_response.raise_for_status()
                        profile_soup = BeautifulSoup(profile_response.text, 'html.parser')

                        # More robust approach to find content
                        # Look for main content container
                        content_container = profile_soup.find('div', class_=re.compile(r'content-area|entry-content'))

                        if content_container:
                            # Extract all paragraph text and combine it
                            paragraphs = content_container.find_all('p')
                            bio_text = ' '.join([p.text.strip() for p in paragraphs if p.text.strip()])
                            bio = bio_text if bio_text else 'N/A'
                        else:
                            bio = 'N/A'

                    except requests.exceptions.RequestException as e:
                        print(f"Failed to scrape profile for {name} at {profile_url}. Error: {e}")

                faculty_data.append({
                    'name': name,
                    'designation': designation,
                    'profile_url': profile_url,
                    'bio': bio
                })

        except requests.exceptions.RequestException as e:
            print(f"Failed to scrape {url}. Error: {e}")
            continue

    print(f"Scraping complete. Found {len(faculty_data)} faculty members.")
    return faculty_data


def get_faculty_suggestions(user_input, faculty_data, top_n=5):
    """
    Suggests faculty based on the similarity of their work (bio/designation)
    to the user's input. Uses TF-IDF and Cosine Similarity for text matching.
    """
    if not faculty_data:
        print("No faculty data available to provide suggestions.")
        return []

    # Create a corpus of documents by combining designation and bio for better context
    corpus = [f['designation'] + ' ' + f['bio'] for f in faculty_data]

    # Initialize a TfidfVectorizer to convert text into a matrix of TF-IDF features
    vectorizer = TfidfVectorizer(stop_words='english')

    # Fit the vectorizer on the corpus and transform the corpus
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Transform the user's input using the same vectorizer
    user_vector = vectorizer.transform([user_input])

    # Calculate the cosine similarity between the user's input and all faculty documents
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

    # Get the indices of the most similar faculty, sorted in descending order
    most_similar_indices = cosine_similarities.argsort()[:-top_n - 1:-1]

    suggestions = []
    for i in most_similar_indices:
        suggestions.append({
            'name': faculty_data[i]['name'],
            'designation': faculty_data[i]['designation'],
            'profile_url': faculty_data[i]['profile_url'],
            'similarity_score': cosine_similarities[i]
        })

    return suggestions


if __name__ == "__main__":
    # Scrape the data first
    faculty_list = scrape_faculty_data()

    if not faculty_list:
        print("Exiting. Could not find any faculty data.")
    else:
        print("\nReady to find your faculty matches! Type your research interests, project ideas, or field of study.")
        print("Example: 'Machine learning and natural language processing in computer science'")

        while True:
            user_query = input("\nYour interest: ")
            if user_query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            suggestions = get_faculty_suggestions(user_query, faculty_list)

            print("\nTop 5 Faculty Suggestions:")
            if suggestions:
                for i, s in enumerate(suggestions):
                    print(f"\n{i + 1}. {s['name']}")
                    print(f"   Designation: {s['designation']}")
                    print(f"   Profile: {s['profile_url']}")
                    print(f"   Relevance: {s['similarity_score']:.2f}")
            else:
                print("No matches found. Try a different query.")
