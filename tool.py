import os
import requests
import streamlit as st
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain_mistralai import ChatMistralAI
from langchain.schema import HumanMessage

# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Initialize LangChain's Mistral Chat model
llm = ChatMistralAI(
    model="mistral-small",
    temperature=0.7,
    max_tokens=1024,
    api_key=MISTRAL_API_KEY
)

# Streamlit UI
st.title("RockyBot: News Research Tool 📈")
st.sidebar.title("News Article URLs")

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i + 1}")
    urls.append(url)

process_url_clicked = st.sidebar.button("Process URLs")

# Extract plain text from URL
def extract_text_from_url(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        return text.strip()
    except Exception as e:
        return f"Error loading {url}: {e}"

# Split long text into chunks
def split_into_chunks(text, chunk_size=1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Store processed chunks with their source URLs
all_chunks = []  # List of tuples: (chunk_text, source_url)

if process_url_clicked:
    with st.spinner("Processing URLs..."):

        for url in urls:
            if url:
                text = extract_text_from_url(url)
                chunks = split_into_chunks(text)
                for chunk in chunks:
                    all_chunks.append((chunk, url))


# User query input
query = st.text_input("Ask your question:")

if query and all_chunks:
    # Extract just the text part for similarity matching
    chunk_texts = [chunk for chunk, _ in all_chunks]

    # Find the most relevant chunk using TF-IDF
    vectorizer = TfidfVectorizer().fit_transform([query] + chunk_texts)
    similarities = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()
    top_chunk_index = similarities.argmax()

    # Retrieve best-matched context and its source URL
    context, source_url = all_chunks[top_chunk_index]

    # Compose prompt
    final_prompt = f"Use the following news excerpt to answer the question:\n\n{context}\n\nQuestion: {query}\nAnswer:"

    # Query Mistral via LangChain
    response = llm([HumanMessage(content=final_prompt)])

    # Display results
    st.header("Answer")
    st.write(response.content)

    st.subheader("Context Used:")
    st.write(context)

    st.markdown(f"**Source URL:** [{source_url}]({source_url})")
