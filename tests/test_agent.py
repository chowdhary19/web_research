"""
Tests for the Research Agent.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.research_agent import ResearchAgent

class TestResearchAgent(unittest.TestCase):
    """Test cases for ResearchAgent class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock for environment variables
        self.env_patcher = patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test_key',
            'SERPAPI_API_KEY': 'test_key',
            'LOG_LEVEL': 'ERROR'  # Reduce logging noise during tests
        })
        self.env_patcher.start()
        
        # Create agent with mock provider
        self.agent = ResearchAgent(llm_provider="openai", verbose=False)
        
        # Create mocks for component methods
        self.agent.query_analyzer.analyze = MagicMock()
        self.agent.search_tool.search = MagicMock()
        self.agent.scraper.scrape = MagicMock()
        self.agent.content_analyzer.analyze = MagicMock()
        self.agent.response_generator.generate = MagicMock()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    def test_research_successful_flow(self):
        """Test successful research flow."""
        # Set up mock return values
        self.agent.query_analyzer.analyze.return_value = {
            'query_type': 'factual',
            'topics': ['test topic'],
            'search_terms': ['test query'],
            'time_sensitivity': 'any',
            'required_depth': 'standard'
        }
        
        self.agent.search_tool.search.return_value = [
            {'url': 'https://example.com', 'title': 'Test Result', 'snippet': 'Test snippet'}
        ]
        
        self.agent.scraper.scrape.return_value = "Test content extracted from the webpage."
        
        self.agent.content_analyzer.analyze.return_value = [
            {
                'url': 'https://example.com',
                'title': 'Test Result',
                'content': 'Test content extracted from the webpage.',
                'relevance_score': 95
            }
        ]
        
        self.agent.response_generator.generate.return_value = {
            'summary': 'Test summary of the research.',
            'detailed_response': 'Detailed research response.',
            'highlights': ['Key point 1', 'Key point 2']
        }
        
        # Execute research
        result = self.agent.research("test query")
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['query'], "test query")
        self.assertEqual(result['summary'], "Test summary of the research.")
        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(result['sources'][0]['url'], "https://example.com")
        
        # Verify method calls
        self.agent.query_analyzer.analyze.assert_called_once()
        self.agent.search_tool.search.assert_called_once()
        self.agent.scraper.scrape.assert_called_once_with('https://example.com')
        self.agent.content_analyzer.analyze.assert_called_once()
        self.agent.response_generator.generate.assert_called_once()
    
    def test_research_no_search_results(self):
        """Test handling of no search results."""
        # Set up mock return values
        self.agent.query_analyzer.analyze.return_value = {
            'query_type': 'factual',
            'topics': ['test topic'],
            'search_terms': ['test query'],
            'time_sensitivity': 'any',
            'required_depth': 'standard'
        }
        
        self.agent.search_tool.search.return_value = []  # No search results
        
        # Execute research
        result = self.agent.research("test query")
        
        # Verify results
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], "no_results")
        self.assertTrue("I couldn't find any information" in result['summary'])
        
        # Verify method calls
        self.agent.query_analyzer.analyze.assert_called_once()
        self.agent.search_tool.search.assert_called_once()
        self.agent.scraper.scrape.assert_not_called()
    
    def test_research_scraping_failure(self):
        """Test handling of scraping failures."""
        # Set up mock return values
        self.agent.query_analyzer.analyze.return_value = {
            'query_type': 'factual',
            'topics': ['test topic'],
            'search_terms': ['test query'],
            'time_sensitivity': 'any',
            'required_depth': 'standard'
        }
        
        self.agent.search_tool.search.return_value = [
            {'url': 'https://example.com', 'title': 'Test Result', 'snippet': 'Test snippet'}
        ]
        
        self.agent.scraper.scrape.return_value = None  # Scraping failed
        
        # Execute research
        result = self.agent.research("test query")
        
        # Verify results
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], "extraction_failed")
        self.assertTrue("couldn't extract" in result['summary'])
        
        # Verify method calls
        self.agent.query_analyzer.analyze.assert_called_once()
        self.agent.search_tool.search.assert_called_once()
        self.agent.scraper.scrape.assert_called_once()
        self.agent.content_analyzer.analyze.assert_not_called()
    
    def test_reset_conversation(self):
        """Test conversation history reset."""
        # Add some items to conversation history
        self.agent.conversation_history = [
            {"role": "user", "content": "test query"},
            {"role": "assistant", "content": "test response"}
        ]
        
        # Reset conversation
        result = self.agent.reset_conversation()
        
        # Verify results
        self.assertEqual(len(self.agent.conversation_history), 0)
        self.assertIn("reset", result["status"].lower())

if __name__ == '__main__':
    unittest.main()