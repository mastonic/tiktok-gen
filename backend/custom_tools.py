from crewai.tools import tool
import feedparser
from duckduckgo_search import DDGS
import trafilatura
from pytrends.request import TrendReq

def _feed_parser_logic(feed_url: str) -> str:
    try:
        # Robust user agent to avoid blocks (especially for Reddit)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 iM-System-Bot/1.0"
        }
        
        import requests
        resp = requests.get(feed_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return f"Error: RSS source returned status {resp.status_code}"
            
        feed = feedparser.parse(resp.content)
        
        content = ""
        for i, entry in enumerate(feed.entries[:10]):
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', 'No Link')
            summary = getattr(entry, 'summary', 'No summary')[:300]
            content += f"{i+1}. [{title}]({link})\n{summary}\n\n"
        return content or "No entries found in this feed."
    except Exception as e:
        return f"Error parsing feed: {e}"

@tool("FeedParserTool")
def feed_parser_tool(feed_url: str) -> str:
    """Parses an RSS feed (Reddit, GitHub, Tech Blogs). Highly robust fallback."""
    return _feed_parser_logic(feed_url)

@tool("HackerNewsTool")
def hacker_news_tool(query: str = "") -> str:
    """
    Fetches the top stories from HackerNews.
    If a query is provided, it use search; otherwise it returns current top tech trends.
    """
    try:
        if query:
            url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=5"
        else:
            url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10"
            
        resp = requests.get(url, timeout=10)
        data = resp.json()
        results = "Top HackerNews Stories:\n"
        for hit in data.get('hits', []):
            results += f"- {hit['title']} ({hit['url']}) | Points: {hit['points']}\n"
        return results
    except Exception as e:
        return f"HN Error: {e}"

@tool("GithubTrendingTool")
def github_trending_tool(language: str = "") -> str:
    """
    Fetches trending repositories on GitHub. 
    Can filter by language (e.g. 'python', 'javascript').
    """
    try:
        # Use a more reliable mirror or public scraper API
        url = "https://gtrend.yapie.me/repositories"
        params = {"language": language.lower()} if language else {}
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            results = f"Trending GitHub Repos ({language or 'all'}):\n"
            for repo in data[:8]:
                name = repo.get('name', 'Unknown')
                author = repo.get('author', 'Unknown')
                stars = repo.get('stars', '?')
                url_repo = repo.get('url', '')
                desc = repo.get('description', 'No description')
                results += f"- {name} by {author} | Stars: {stars} | {url_repo}\n"
                results += f"  Desc: {desc}\n\n"
            return results
        else:
            # Fallback to another mirror or secondary method
            raise ValueError(f"GitHub API Error {resp.status_code}")
            
    except Exception as e:
        print(f"⚠️ [GitHub] API Primary Failed ({e}), trying secondary mirror...")
        try:
             # Secondary fallback: Scraper Mirror
             url = f"https://github-trending-api.mirror.workers.dev/repositories"
             params = {"language": language.lower()} if language else {}
             resp = requests.get(url, params=params, timeout=15)
             if resp.status_code == 200:
                 data = resp.json()
                 results = f"Trending GitHub Repos (Mirror - {language or 'all'}):\n"
                 for repo in data[:8]:
                     results += f"- {repo.get('name')} | Stars: {repo.get('stars')} | {repo.get('url')}\n"
                 return results
        except Exception as e2:
            print(f"⚠️ [GitHub] Secondary Mirror Failed ({e2}), falling back to Official Search API...")
            
        try:
            # Tertiary fallback: Official GitHub Search API (Most stars in last 7 days)
            from datetime import datetime, timedelta
            last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = f"created:>{last_week}"
            if language:
                query += f" language:{language}"
            
            search_url = f"https://api.github.com/search/repositories"
            search_params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 8
            }
            
            resp = requests.get(search_url, params=search_params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = f"Trending GitHub Repos (Official Search - {language or 'all'}):\n"
                for repo in data.get('items', []):
                    results += f"- {repo['name']} by {repo['owner']['login']} | ⭐ {repo['stargazers_count']} | {repo['html_url']}\n"
                    results += f"  Desc: {repo.get('description', 'No description')}\n\n"
                return results
        except Exception as e3:
             print(f"⚠️ [GitHub] Official Search Failed ({e3})")

        return hacker_news_tool(f"github {language}")

@tool("ArxivTool")
def arxiv_tool(query: str = "Artificial Intelligence") -> str:
    """
    Searches Arxiv for the latest research papers.
    Useful for deep technical content or new AI breakthroughs.
    """
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending"
        import feedparser
        feed = feedparser.parse(url)
        results = f"Latest Arxiv Papers for '{query}':\n"
        for entry in feed.entries:
            results += f"- {entry.title}\n  Summary: {entry.summary[:200]}...\n  Link: {entry.link}\n\n"
        return results
    except Exception as e:
        return f"Arxiv Error: {e}"

def _duckduckgo_logic(query: str) -> str:
    try:
        results = ""
        with DDGS() as ddgs:
            # Try original query with regional focus and year limit if needed
            search_results = list(ddgs.text(query, region="wt-wt", safesearch="off", timelimit="y", max_results=5))
            
            # If no results, try a much broader fallback
            if not search_results:
                print(f"⚠️ [DDG] No results for '{query}', trying AI-wide news fallback...")
                search_results = list(ddgs.text("AI development open source trending 2026", max_results=5))
                
            for i, r in enumerate(search_results):
                results += f"Source {i+1}: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}\n\n"
        return results or "No results found even after fallback. Try using Perplexity."
    except Exception as e:
        return f"Error searching: {e}. Source possibly blocked."

@tool("DuckDuckGoSearchTool")
def duckduckgo_search_tool(query: str) -> str:
    """Searches the web using DuckDuckGo."""
    return _duckduckgo_logic(query)

@tool("DuckDuckGoImageTool")
def duckduckgo_image_tool(query: str) -> str:
    """
    Searches for an image URL on the web using DuckDuckGo.
    Useful for finding real product logos or tool screenshots.
    Args:
        query (str): The search query for the image.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=3))
            if results:
                return results[0]['image']
        return "No image found."
    except Exception as e:
        return f"Error searching images: {e}"

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
        print("⚠️ [Perplexity] Key not found, falling back to multi-source search.")
        ddg_results = _duckduckgo_logic(query)
        hn_results = hacker_news_tool(query)
        reddit_rss = _feed_parser_logic("https://www.reddit.com/r/artificial/top/.rss?t=day")
        return f"Note: Perplexity indisponible. Résultats combinés :\n\n-- DDG --\n{ddg_results}\n\n-- HackerNews --\n{hn_results}\n\n-- Reddit RSS --\n{reddit_rss}"
        
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar", # More conservative model choice
        "messages": [
            {
                "role": "user",
                "content": "Tu es un expert en viralité TikTok et en recherche technologique. Fournis des informations sourcées, précises et structurées.\n\n" + query
            }
        ],
        "return_citations": True
    }
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # Check for credit/balance issues
        if response.status_code == 402 or "insufficient_balance" in response.text.lower():
            print("⚠️ [Perplexity] Pas de crédit !! Pas de secours auto pour éviter les boucles.")
            ddg_results = _duckduckgo_logic(query)
            rss_results = _feed_parser_logic("https://www.reddit.com/r/artificial/new/.rss")
            return f"Note: Perplexity indisponible (Crédits épuisés). Secours :\n{ddg_results}\n\n{rss_results}"
            
        if response.status_code != 200:
             print(f"⚠️ [Perplexity] Status {response.status_code}: {response.text}")
             ddg_results = _duckduckgo_logic(query)
             return f"Perplexity Error ({response.status_code}). Secours DuckDuckGo :\n\n{ddg_results}"

        # Track cost
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
        ddg_results = _duckduckgo_logic(query)
        return f"Erreur Perplexity: {e}. Secours DuckDuckGo :\n\n{ddg_results}"
