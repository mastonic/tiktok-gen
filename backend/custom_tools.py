from crewai.tools import tool
import feedparser
from duckduckgo_search import DDGS
import trafilatura
from pytrends.request import TrendReq

@tool("FeedParserTool")
def feed_parser_tool(feed_url: str) -> str:
    """
    Parses an RSS feed (Reddit, GitHub, etc.) with a User-Agent to avoid blocks.
    Args:
        feed_url (str): The URL of the RSS feed to parse.
    """
    try:
        # Add User-Agent for feeds like Reddit that block bots
        agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        feed = feedparser.parse(feed_url, agent=agent)
        
        content = ""
        for i, entry in enumerate(feed.entries[:8]): # Take top 8
            content += f"{i+1}. Title: {entry.title}\nLink: {entry.link}\nSummary: {getattr(entry, 'summary', 'No summary')[:200]}\n\n"
        if not content:
            return "No entries found in this feed. Try another source."
        return content
    except Exception as e:
        return f"Error parsing feed: {e}"

@tool("DuckDuckGoSearchTool")
def duckduckgo_search_tool(query: str) -> str:
    """
    Searches the web using DuckDuckGo to find information.
    Useful for researching specific trends or tools.
    Args:
        query (str): The search query.
    """
    try:
        results = ""
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=3)):
                results += f"Source {i+1}: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}\n\n"
        
        if not results:
            return "No real-time results found for this specific query. Please try another search term or a different source."
            
        return results
    except Exception as e:
        return f"Error searching: {e}"

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
        return f"Error fetching trends: {e}"
