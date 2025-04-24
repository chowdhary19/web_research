"""
Research Agent - Main agent implementation that orchestrates the research process.
"""
import logging
from typing import Dict, List, Optional, Any

from src.agent.query_analyzer import QueryAnalyzer
from src.agent.response_generator import ResponseGenerator
from src.tools.search_tool import SearchTool
from src.tools.scraper import WebScraper
from src.tools.content_analyzer import ContentAnalyzer
from src.utils.error_handler import handle_error

class ResearchAgent:
    """
    Web Research Agent that orchestrates the research process from query to response.
    """
    
    def __init__(self, llm_provider: str = "openai", verbose: bool = False):
        """
        Initialize the Research Agent with its component tools.
        
        Args:
            llm_provider: The LLM provider to use (openai, anthropic, or google)
            verbose: Whether to enable verbose logging
        """
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose
        
        # Store the LLM provider (missing in original code)
        self.llm_provider = llm_provider
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer(llm_provider)
        self.search_tool = SearchTool()
        self.scraper = WebScraper()
        self.content_analyzer = ContentAnalyzer(llm_provider)
        self.response_generator = ResponseGenerator(llm_provider)
        
        self.conversation_history = []
        
    def research(self, query: str) -> Dict[str, Any]:
        """
        Perform research based on the user query.
        
        Args:
            query: The research query provided by the user
            
        Returns:
            Dictionary containing the research results and metadata
        """
        try:
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            
            # Step 1: Analyze the query
            self.logger.info(f"Analyzing query: {query}")
            query_analysis = self.query_analyzer.analyze(query, self.conversation_history)
            
            if self.verbose:
                self.logger.debug(f"Query analysis: {query_analysis}")
            
            # Step 2: Perform web search
            self.logger.info(f"Searching for information with terms: {query_analysis['search_terms']}")
            search_results = self.search_tool.search(
                query_analysis['search_terms'],
                query_type=query_analysis['query_type'],
                limit=query_analysis.get('result_limit', 5)
            )
            
            if not search_results:
                return self._handle_no_results(query, query_analysis)
            
            if self.verbose:
                self.logger.debug(f"Found {len(search_results)} search results")
                
            # Step 3: Scrape and extract content from search results
            all_content = []
            for result in search_results:
                try:
                    self.logger.info(f"Scraping content from: {result['url']}")
                    content = self.scraper.scrape(result['url'])
                    if content:
                        all_content.append({
                            "url": result['url'],
                            "title": result.get('title', ''),
                            "content": content,
                            "metadata": result.get('metadata', {})
                        })
                except Exception as e:
                    self.logger.warning(f"Error scraping {result['url']}: {str(e)}")
            
            if not all_content:
                return self._handle_no_content(query, query_analysis, search_results)
                
            # Step 4: Analyze and filter extracted content
            self.logger.info("Analyzing content relevance")
            filtered_content = self.content_analyzer.analyze(
                query_analysis, 
                all_content
            )
            
            if self.verbose:
                self.logger.debug(f"Filtered down to {len(filtered_content)} relevant sources")
                
            # Step 5: Generate response
            self.logger.info("Generating research response")
            response = self.response_generator.generate(
                query,
                query_analysis,
                filtered_content,
                self.conversation_history
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "assistant", "content": response['summary']})
            
            # Return comprehensive result
            return {
                "query": query,
                "analysis": query_analysis,
                "sources": [{"url": item["url"], "title": item["title"]} for item in filtered_content],
                "summary": response['summary'],
                "detailed_response": response.get('detailed_response', ''),
                "highlights": response.get('highlights', []),
                "success": True
            }
            
        except Exception as e:
            error_response = handle_error(e, query)
            self.logger.error(f"Research error: {str(e)}")
            self.conversation_history.append({"role": "assistant", "content": error_response["message"]})
            return error_response
    
    def _handle_no_results(self, query: str, query_analysis: Dict) -> Dict:
        """Handle case when no search results are found."""
        message = f"I couldn't find any information about '{query}'. Could you try rephrasing your question or providing more details?"
        self.logger.warning(f"No search results found for: {query}")
        self.conversation_history.append({"role": "assistant", "content": message})
        return {
            "query": query,
            "analysis": query_analysis,
            "sources": [],
            "summary": message,
            "success": False,
            "error_type": "no_results"
        }
    
    def _handle_no_content(self, query: str, query_analysis: Dict, search_results: List) -> Dict:
        """Handle case when content extraction failed for all results."""
        message = "I found some relevant sources, but couldn't extract their content. This might be due to access restrictions or complex page structures."
        self.logger.warning(f"Content extraction failed for all results: {query}")
        self.conversation_history.append({"role": "assistant", "content": message})
        return {
            "query": query,
            "analysis": query_analysis,
            "sources": [{"url": r["url"], "title": r.get("title", "")} for r in search_results],
            "summary": message,
            "success": False,
            "error_type": "extraction_failed"
        }
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        return {"status": "Conversation history has been reset."}