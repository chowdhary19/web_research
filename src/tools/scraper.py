"""
Web Scraper - Component for extracting content from web pages.
"""
import logging
import os
import time
import re
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Import web scraping libraries
from bs4 import BeautifulSoup
from newspaper import Article
import urllib.robotparser

class WebScraper:
    """
    Tool for scraping content from web pages.
    """
    
    def __init__(self):
        """Initialize the Web Scraper."""
        self.logger = logging.getLogger(__name__)
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))
        self.user_agent = os.getenv("USER_AGENT", "WebResearchAgent/1.0")
        self.respect_robots = os.getenv("RESPECT_ROBOTS_TXT", "True").lower() == "true"
        
        # Cache for robots.txt permissions
        self.robots_cache = {}
        
        # Initialize headers for requests
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrape content from a webpage.
        
        Args:
            url: URL of the webpage to scrape
            
        Returns:
            Extracted text content or None if scraping fails
        """
        if not url or not url.startswith(("http://", "https://")):
            self.logger.warning(f"Invalid URL: {url}")
            return None
            
        try:
            # Check robots.txt if enabled
            if self.respect_robots and not self._can_fetch(url):
                self.logger.warning(f"Robots.txt disallows scraping: {url}")
                return f"[Access to this content is restricted by the website's robots.txt policy]"
            
            # Try different scraping methods
            content = None
            
            # First try with newspaper3k for article content
            content = self._scrape_with_newspaper(url)
            
            # If that fails, try with BeautifulSoup
            if not content or len(content.strip()) < 100:
                content = self._scrape_with_beautifulsoup(url)
                
            # Clean and normalize the content
            if content:
                content = self._clean_content(content)
                
            return content
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def _can_fetch(self, url: str) -> bool:
        """
        Check if scraping is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if scraping is allowed, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check cache first
            if base_url in self.robots_cache:
                return self.robots_cache[base_url]
            
            # Initialize robots parser
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            
            try:
                rp.read()
                allowed = rp.can_fetch(self.user_agent, url)
                
                # Cache the result
                self.robots_cache[base_url] = allowed
                return allowed
                
            except Exception as e:
                self.logger.warning(f"Error reading robots.txt for {base_url}: {e}")
                # If we can't read robots.txt, assume scraping is allowed
                self.robots_cache[base_url] = True
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking robots.txt: {e}")
            return True  # If we can't check, assume scraping is allowed
    
    def _scrape_with_newspaper(self, url: str) -> Optional[str]:
        """
        Scrape content using newspaper3k library.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text or None
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            content_parts = []
            
            # Add title
            if article.title:
                content_parts.append(f"# {article.title}\n")
                
            # Add publish date if available
            if article.publish_date:
                content_parts.append(f"Published: {article.publish_date.strftime('%Y-%m-%d')}\n")
                
            # Add authors if available
            if article.authors:
                content_parts.append(f"Authors: {', '.join(article.authors)}\n")
                
            # Add main text
            if article.text:
                content_parts.append(article.text)
                
            content = "\n".join(content_parts)
            
            if len(content.strip()) > 50:  # Check if we got meaningful content
                return content
                
            return None
            
        except Exception as e:
            self.logger.warning(f"Newspaper3k scraping failed for {url}: {e}")
            return None
    
    def _scrape_with_beautifulsoup(self, url: str) -> Optional[str]:
        """
        Scrape content using BeautifulSoup.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text or None
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
                
            # Create BeautifulSoup object
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
                
            # Get the page title
            title = soup.title.string if soup.title else "No Title"
            
            # Try to extract main content
            main_content = None
            
            # Try common content containers
            content_tags = [
                soup.find("main"),
                soup.find("article"),
                soup.find(id=re.compile("^(content|main|article)")),
                soup.find(class_=re.compile("^(content|main|article|post)"))
            ]
            
            # Use the first valid content container found
            for tag in content_tags:
                if tag and len(tag.get_text(strip=True)) > 100:
                    main_content = tag
                    break
                    
            # If no main content container found, use body
            if not main_content:
                main_content = soup.body
                
            if not main_content:
                return None
                
            # Extract text from paragraphs and headings
            text_elements = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"])
            
            content_parts = [f"# {title}\n"]
            
            for element in text_elements:
                text = element.get_text(strip=True)
                if text:
                    if element.name.startswith("h"):
                        # Add appropriate markdown heading level
                        level = int(element.name[1])
                        content_parts.append(f"{'#' * level} {text}\n")
                    else:
                        content_parts.append(text + "\n")
                        
            content = "\n".join(content_parts)
            
            if len(content.strip()) > 100:  # Check if we got meaningful content
                return content
                
            # If structured extraction didn't work, fall back to all text
            all_text = soup.get_text(separator="\n", strip=True)
            return f"# {title}\n\n{all_text}"
            
        except Exception as e:
            self.logger.warning(f"BeautifulSoup scraping failed for {url}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and normalize the extracted content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
            
        # Replace multiple newlines with double newline
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove very short lines (likely navigation/menu items)
        lines = content.split('\n')
        lines = [line for line in lines if len(line.strip()) > 2 or not line.strip()]
        content = '\n'.join(lines)
        
        # Remove duplicate paragraphs (common in scraped content)
        paragraphs = content.split('\n\n')
        unique_paragraphs = []
        for p in paragraphs:
            if p not in unique_paragraphs:
                unique_paragraphs.append(p)
        content = '\n\n'.join(unique_paragraphs)
        
        return content