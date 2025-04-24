"""
Search Tool - Component for performing web searches and retrieving relevant results.
"""
import logging
import os
import time
import json
import random
from typing import List, Dict, Any, Optional

import requests
from urllib.parse import quote_plus

class SearchTool:
    """
    Tool for performing web searches using various search APIs.
    """
    
    def __init__(self):
        """Initialize the Search Tool."""
        self.logger = logging.getLogger(__name__)
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.result_limit = int(os.getenv("SEARCH_RESULT_LIMIT", "5"))
        
        # Determine which search provider to use based on available API keys
        if self.serpapi_key:
            self.search_provider = "serpapi"
        elif self.google_api_key and self.search_engine_id:
            self.search_provider = "google_cse"
        else:
            self.search_provider = "mock"  # Fallback to mock data
            self.logger.warning("No search API keys found. Using mock search results.")
    
    def search(self, search_terms: List[str], query_type: str = "factual", 
              limit: int = None) -> List[Dict[str, Any]]:
        """
        Perform a web search using the specified search terms.
        
        Args:
            search_terms: List of search queries to use
            query_type: Type of query (factual, exploratory, news, opinion)
            limit: Maximum number of results to return
            
        Returns:
            List of search results with URLs and metadata
        """
        if not limit:
            limit = self.result_limit
            
        results = []
        
        # For news queries, prioritize news sources
        is_news_query = query_type == "news"
        
        # Try each search term until we have enough results
        for term in search_terms:
            if len(results) >= limit:
                break
                
            try:
                # Perform the search using the selected provider
                if self.search_provider == "serpapi":
                    term_results = self._search_serpapi(term, is_news_query)
                elif self.search_provider == "google_cse":
                    term_results = self._search_google_cse(term, is_news_query)
                else:
                    term_results = self._mock_search(term, is_news_query)
                
                # Add new results, avoiding duplicates
                for result in term_results:
                    if len(results) >= limit:
                        break
                        
                    # Check if this URL is already in results
                    if not any(r["url"] == result["url"] for r in results):
                        results.append(result)
                        
            except Exception as e:
                self.logger.error(f"Error searching for term '{term}': {str(e)}")
                continue
                
        return results[:limit]  # Ensure we don't exceed the limit
    
    def _search_serpapi(self, query: str, is_news: bool = False) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI.
        
        Args:
            query: Search query
            is_news: Whether to prioritize news results
            
        Returns:
            List of search results
        """
        endpoint = "https://serpapi.com/search"
        
        params = {
            "api_key": self.serpapi_key,
            "q": query,
            "gl": "us",  # Location: United States
            "hl": "en",  # Language: English
        }
        
        if is_news:
            params["tbm"] = "nws"  # News search
        
        response = requests.get(endpoint, params=params)
        if response.status_code != 200:
            self.logger.error(f"SerpAPI error: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        
        results = []
        if "organic_results" in data:
            for item in data["organic_results"]:
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "metadata": {
                        "position": item.get("position"),
                        "displayed_link": item.get("displayed_link", ""),
                        "source": "serpapi"
                    }
                })
        elif "news_results" in data:
            for item in data["news_results"]:
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "metadata": {
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                        "thumbnail": item.get("thumbnail", ""),
                        "source_api": "serpapi"
                    }
                })
                
        return results
    
    def _search_google_cse(self, query: str, is_news: bool = False) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search Engine API.
        
        Args:
            query: Search query
            is_news: Whether to prioritize news results
            
        Returns:
            List of search results
        """
        endpoint = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.google_api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": 10,  # Max results per request
        }
        
        if is_news:
            params["sort"] = "date"  # Sort by date for news
        
        response = requests.get(endpoint, params=params)
        if response.status_code != 200:
            self.logger.error(f"Google CSE error: {response.status_code} - {response.text}")
            return []
            
        data = response.json()
        
        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "metadata": {
                        "display_link": item.get("displayLink", ""),
                        "file_format": item.get("fileFormat", ""),
                        "source_api": "google_cse"
                    }
                })
                
        return results
    
    def _mock_search(self, query: str, is_news: bool = False) -> List[Dict[str, Any]]:
        """
        Generate mock search results when no API keys are available.
        
        Args:
            query: Search query
            is_news: Whether to prioritize news results
            
        Returns:
            List of mock search results
        """
        self.logger.info(f"Generating mock search results for: {query}")
        
        # Sanitize the query for use in generating mock results
        sanitized_query = query.lower().replace(" ", "-")
        
        # Generate deterministic but different URLs based on the query
        domains = ["wikipedia.org", "blog.example.com", "news.example.com", 
                  "research.example.org", "academic.example.edu"]
        
        results = []
        for i in range(5):
            domain = domains[i % len(domains)]
            if is_news:
                date = f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                results.append({
                    "url": f"https://news.example.com/{sanitized_query}-article-{i+1}",
                    "title": f"Latest News About {query.title()} - Article {i+1}",
                    "snippet": f"This news article discusses recent developments in {query}...",
                    "metadata": {
                        "source": "Example News",
                        "date": date,
                        "source_api": "mock"
                    }
                })
            else:
                results.append({
                    "url": f"https://{domain}/{sanitized_query}-{i+1}",
                    "title": f"Information About {query.title()} - Result {i+1}",
                    "snippet": f"This webpage contains information about {query} including definitions, examples, and applications...",
                    "metadata": {
                        "display_link": domain,
                        "source_api": "mock"
                    }
                })
                
        # Add Wikipedia as the first result for factual queries
        if not is_news:
            wiki_term = query.replace(" ", "_")
            results.insert(0, {
                "url": f"https://en.wikipedia.org/wiki/{wiki_term}",
                "title": f"{query.title()} - Wikipedia",
                "snippet": f"This Wikipedia article provides comprehensive information about {query}, including its history, significance, and key concepts...",
                "metadata": {
                    "display_link": "en.wikipedia.org",
                    "source_api": "mock"
                }
            })
            
        # Sleep briefly to simulate API latency
        time.sleep(0.5)
        
        return results[:10]  # Return up to 10 mock results