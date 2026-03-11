from crewai.tools import tool
import feedparser
from duckduckgo_search import DDGS
import trafilatura
from pytrends.request import TrendReq

def _feed_parser_logic(feed_url: str) -> str:
    try:
        agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        feed = feedparser.parse(feed_url, agent=agent)
        
        content = ""
        for i, entry in enumerate(feed.entries[:8]):
            content += f"{i+1}. Title: {entry.title}\nLink: {entry.link}\nSummary: {getattr(entry, 'summary', 'No summary')[:200]}\n\n"
        return content or "No entries found."
    except Exception as e:
        return f"Error parsing feed: {e}"

@tool("FeedParserTool")
def feed_parser_tool(feed_url: str) -> str:
    """Parses an RSS feed (Reddit, GitHub, etc.)"""
    return _feed_parser_logic(feed_url)

def _duckduckgo_logic(query: str) -> str:
    try:
        results = ""
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=3)):
                results += f"Source {i+1}: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}\n\n"
        return results or "No results found."
    except Exception as e:
        return f"Error searching: {e}"

@tool("DuckDuckGoSearchTool")
def duckduckgo_search_tool(query: str) -> str:
    """Searches the web using DuckDuckGo."""
    return _duckduckgo_logic(query)

@tool("TrafilaturaScraper")
def trafilatura_scraper(url: str) -> str:
    """
    Scrapes and extracts the main text content from a given web page URL.
    Useful for reading article content, pricing pages, or documentation.
    Args:
        url (str): The URL to scrape.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return "Error: Could not fetch URL."
        text = trafilatura.extract(downloaded)
        return text[:2000] + "... (truncated)" if text and len(text) > 2000 else text or "No content extracted."
    except Exception as e:
        return f"Scraping error: {e}"

@tool("PyTrendsTool")
def pytrends_tool(keyword: str) -> str:
    """
    Fetches interest over time for a specific keyword using Google Trends.
    Useful for determining if a topic is gaining or losing momentum.
    Args:
        keyword (str): The keyword to analyze.
    """
    try:
        pytrend = TrendReq()
        pytrend.build_payload(kw_list=[keyword], timeframe='now 7-d')
        df = pytrend.interest_over_time()
        if not df.empty and keyword in df.columns:
            recent_trend = df[keyword].tail(3).values
            return f"Recent 3-day trend interest scores for '{keyword}': {list(recent_trend)}"
        return "No trend data found."
    except Exception as e:
        if "429" in str(e):
            return "Google Trends Rate Limit (429). Please use Perplexity or RSS sources instead for now."
        return f"Error fetching trends: {e}"
import requests
import os

@tool("PerplexityTool")
def perplexity_tool(query: str) -> str:
    """
    Searches the real-time web using Perplexity Sonar models.
    Use this for finding the latest trends, news, or deep-diving into specific topics with citations.
    Args:
        query (str): The research question or trend search query.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        try:
            print("🔍 [Perplexity] Key not in env, checking DB...")
            from database import SessionLocal, SystemConfig
            db = SessionLocal()
            conf = db.query(SystemConfig).first()
            if conf and conf.perplexity_key:
                api_key = conf.perplexity_key
                print("✅ [Perplexity] Key found in DB.")
            else:
                print("❌ [Perplexity] No key found in DB.")
            db.close()
        except Exception as e:
            print(f"❌ [Perplexity] Error reading DB: {e}")
            pass
            
    if not api_key:
        return "Error: PERPLEXITY_API_KEY not found. Please check your settings."
        
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-reasoning", # Premium model with deep analysis
        "messages": [
            {
                "role": "user",
                "content": "Tu es un expert en viralité TikTok et en recherche technologique. Fournis des informations sourcées, précises et structurées.\n\n" + query
            }
        ],
        "return_citations": True
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # Check for credit/balance issues (HTTP 402 Payment Required or specific body)
        if response.status_code == 402 or "insufficient_balance" in response.text.lower():
            print("⚠️ [Perplexity] Pas de crédit !! Retour au format de base (DuckDuckGo/RSS)...")
            # --- INTERNAL FALLBACK ---
            ddg_results = _duckduckgo_logic("dernières tendances IA tech 24h")
            rss_results = _feed_parser_logic("https://www.reddit.com/r/artificial/new/.rss")
            return f"Note: Perplexity indisponible (Crédits épuisés). Résultats de secours :\n\n{ddg_results}\n\nFlux RSS :\n{rss_results}"
            
        response.raise_for_status()
        
        # Track cost (Approx 0.01$ per Sonar Reasoning call)
        try:
            from database import track_cost
            track_cost(0.01)
        except:
            pass
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])
        
        if citations:
            content += "\n\nSources / Citations :\n" + "\n".join([f"- {c}" for c in citations])
            
        return content
    except Exception as e:
        print(f"❌ Error calling Perplexity: {e}. Falling back...")
        ddg_results = _duckduckgo_logic("news IA tech actu")
        return f"Erreur Perplexity: {e}. Secours DuckDuckGo :\n\n{ddg_results}"
