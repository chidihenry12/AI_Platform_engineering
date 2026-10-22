import os
import pandas as pd
from dotenv import load_dotenv
from euriai.langgraph import EuriaiLangGraph

load_dotenv()

# EURI API Key (set in .env, see .env.example)
EURI_API_KEY = os.getenv("EURI_API_KEY")

graph = EuriaiLangGraph(
    api_key=EURI_API_KEY,
    default_model="gpt-4.1-nano"
)

def ingest_csv(file_path):
    df = pd.read_csv(file_path)
    # You can customize how you chunk/index here
    return df

def crawl_website(url):
    # Minimalistic placeholder for crawling
    import requests
    from bs4 import BeautifulSoup
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = ' '.join([p.get_text() for p in soup.find_all('p')])
    return text

def index_data(data):
    # Only add the node if it doesn't already exist
    if "processor" not in graph.graph.nodes:
        graph.add_ai_node(
            "processor",
            "Process and enhance this text: {input}"
        )
        graph.set_entry_point("processor")
        graph.set_finish_point("processor")
    result = graph.run({"input": data})
    return result 