"""
Tests for the tools components (search, scraper, content analyzer).
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import requests
from bs4 import BeautifulSoup

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.search_tool import SearchTool
from src.tools.web_scraper import WebScraper
from src.tools.content_analyzer import ContentAnalyzer

class TestSearchTool(unittest.TestCase):
    """Test cases for SearchTool class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock for environment variables
        self.env_patcher = patch.dict('os.environ', {
            'SERPAPI_API_KEY': 'test_key',
            'GOOGLE_API_KEY': 'test_key',
            'GOOGLE_SEARCH_ENGINE_ID': 'test_cx',
            'SEARCH_RESULT_LIMIT': '5'
        })
        self.env_patcher.start()
        
        # Create search tool
        self.search_tool = SearchTool()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    @patch('requests.get')
    def test_serpapi_search(self, mock_get):
        """Test search using SerpAPI."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'organic_results': [
                {
                    'position': 1,
                    'title': 'Test Result 1',
                    'link': 'https://example.com/1',
                    'snippet': 'This is test result 1',
                    'displayed_link': 'example.com/1'
                },
                {
                    'position': 2,
                    'title': 'Test Result 2',
                    'link': 'https://example.com/2',
                    'snippet': 'This is test result 2',
                    'displayed_link': 'example.com/2'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Force using serpapi
        self.search_tool.search_provider = 'serpapi'
        
        # Execute search
        results = self.search_tool.search(['test query'])
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/1')
        self.assertEqual(results[0]['title'], 'Test Result 1')
        self.assertEqual(results[0]['metadata']['source'], 'serpapi')
        
        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], 'https://serpapi.com/search')
        self.assertEqual(kwargs['params']['q'], 'test query')
    
    @patch('requests.get')
    def test_google_cse_search(self, mock_get):
        """Test search using Google Custom Search Engine."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'title': 'Test Result 1',
                    'link': 'https://example.com/1',
                    'snippet': 'This is test result 1',
                    'displayLink': 'example.com/1'
                },
                {
                    'title': 'Test Result 2',
                    'link': 'https://example.com/2',
                    'snippet': 'This is test result 2',
                    'displayLink': 'example.com/2'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Force using google_cse
        self.search_tool.search_provider = 'google_cse'
        
        # Execute search
        results = self.search_tool.search(['test query'])
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/1')
        self.assertEqual(results[0]['title'], 'Test Result 1')
        self.assertEqual(results[0]['metadata']['source_api'], 'google_cse')
        
        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], 'https://www.googleapis.com/customsearch/v1')
        self.assertEqual(kwargs['params']['q'], 'test query')
    
    def test_mock_search(self):
        """Test mock search when no API keys are available."""
        # Force using mock provider
        self.search_tool.search_provider = 'mock'
        
        # Execute search
        results = self.search_tool.search(['test query'])
        
        # Verify results
        self.assertGreater(len(results), 0)
        self.assertTrue(any('wikipedia.org' in r['url'] for r in results))
        self.assertEqual(results[0]['metadata']['source_api'], 'mock')
    
    def test_search_multiple_terms(self):
        """Test searching with multiple search terms."""
        # Force using mock provider
        self.search_tool.search_provider = 'mock'
        
        # Execute search with multiple terms
        results = self.search_tool.search(['term1', 'term2', 'term3'], limit=10)
        
        # Verify results
        self.assertLessEqual(len(results), 10)
        # Verify URLs are unique
        urls = [r['url'] for r in results]
        self.assertEqual(len(urls), len(set(urls)))

class TestWebScraper(unittest.TestCase):
    """Test cases for WebScraper class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create web scraper
        self.scraper = WebScraper()
    
    @patch('newspaper.Article')
    def test_scrape_with_newspaper(self, mock_article):
        """Test content extraction using newspaper3k."""
        # Mock Article instance
        article_instance = MagicMock()
        article_instance.title = 'Test Article'
        article_instance.publish_date.strftime.return_value = '2023-01-01'
        article_instance.authors = ['Author 1', 'Author 2']
        article_instance.text = 'This is the article content for testing purposes.'
        mock_article.return_value = article_instance
        
        # Execute scrape
        content = self.scraper._scrape_with_newspaper('https://example.com')
        
        # Verify results
        self.assertIn('Test Article', content)
        self.assertIn('2023-01-01', content)
        self.assertIn('Author 1', content)
        self.assertIn('This is the article content', content)
        
        # Verify Article usage
        mock_article.assert_called_once_with('https://example.com')
        article_instance.download.assert_called_once()
        article_instance.parse.assert_called_once()
    
    @patch('requests.get')
    def test_scrape_with_beautifulsoup(self, mock_get):
        """Test content extraction using BeautifulSoup."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Page Title</title>
            </head>
            <body>
                <article>
                    <h1>Main Heading</h1>
                    <p>First paragraph content.</p>
                    <h2>Subheading</h2>
                    <p>Second paragraph content.</p>
                </article>
                <script>alert('test');</script>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Execute scrape
        content = self.scraper._scrape_with_beautifulsoup('https://example.com')
        
        # Verify results
        self.assertIn('Test Page Title', content)
        self.assertIn('Main Heading', content)
        self.assertIn('First paragraph content', content)
        self.assertIn('Subheading', content)
        self.assertNotIn('alert', content)  # Script should be removed
        
        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], 'https://example.com')
    
    @patch('urllib.robotparser.RobotFileParser')
    def test_robots_txt_check(self, mock_parser):
        """Test robots.txt checking functionality."""
        # Mock parser
        parser_instance = MagicMock()
        parser_instance.can_fetch.return_value = False  # Disallow scraping
        mock_parser.return_value = parser_instance
        
        # Set up scraper to respect robots.txt
        self.scraper.respect_robots = True
        
        # Execute check
        result = self.scraper._can_fetch('https://example.com/page')
        
        # Verify result
        self.assertFalse(result)
        
        # Verify parser usage
        parser_instance.set_url.assert_called_once_with('https://example.com/robots.txt')
        parser_instance.read.assert_called_once()
        parser_instance.can_fetch.assert_called_once()
    
    @patch.object(WebScraper, '_can_fetch')
    @patch.object(WebScraper, '_scrape_with_newspaper')
    @patch.object(WebScraper, '_scrape_with_beautifulsoup')
    def test_scrape_main_flow(self, mock_bs, mock_newspaper, mock_can_fetch):
        """Test the main scraping workflow."""
        # Configure mocks
        mock_can_fetch.return_value = True
        mock_newspaper.return_value = None  # Newspaper fails
        mock_bs.return_value = "Content from BeautifulSoup"
        
        # Execute scrape
        result = self.scraper.scrape('https://example.com')
        
        # Verify results
        self.assertEqual(result, "Content from BeautifulSoup")
        
        # Verify calls
        mock_can_fetch.assert_called_once()
        mock_newspaper.assert_called_once()
        mock_bs.assert_called_once()
    
    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        # Test with various invalid URLs
        result1 = self.scraper.scrape(None)
        result2 = self.scraper.scrape('not-a-url')
        result3 = self.scraper.scrape('ftp://example.com')
        
        # Verify results
        self.assertIsNone(result1)
        self.assertIsNone(result2)
        self.assertIsNone(result3)

class TestContentAnalyzer(unittest.TestCase):
    """Test cases for ContentAnalyzer class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock for environment variables
        self.env_patcher = patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test_key',
            'DEFAULT_LLM_MODEL': 'gpt-4'
        })
        self.env_patcher.start()
        
        # Create content analyzer
        self.analyzer = ContentAnalyzer(llm_provider="openai")
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    def test_basic_text_filter(self):
        """Test basic text filtering functionality."""
        # Create test data
        query_analysis = {
            'topics': ['artificial intelligence', 'machine learning'],
            'search_terms': ['AI applications', 'neural networks']
        }
        
        content_items = [
            {
                'title': 'Introduction to AI',
                'url': 'https://example.com/ai',
                'content': 'Artificial intelligence is a field focused on creating intelligent machines.'
            },
            {
                'title': 'Cooking Tips',
                'url': 'https://example.com/cooking',
                'content': 'How to make delicious pasta dishes with minimal effort.'
            },
            {
                'title': 'Neural Networks Explained',
                'url': 'https://example.com/neural',
                'content': 'Neural networks are computing systems inspired by biological neural networks.'
            }
        ]
        
        # Execute filtering
        filtered = self.analyzer._basic_text_filter(query_analysis, content_items)
        
        # Verify results
        self.assertEqual(len(filtered), 2)  # Should exclude cooking article
        self.assertEqual(filtered[0]['url'], 'https://example.com/neural')  # Higher relevance score
        self.assertEqual(filtered[1]['url'], 'https://example.com/ai')  # Lower relevance score
    
    @patch('openai.Client')
    def test_llm_ranking(self, mock_client):
        """Test LLM-based relevance ranking."""
        # Mock OpenAI client
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            'rankings': [
                {'id': 2, 'relevance_score': 95, 'reason': 'Highly relevant'},
                {'id': 0, 'relevance_score': 80, 'reason': 'Somewhat relevant'},
                {'id': 1, 'relevance_score': 30, 'reason': 'Not relevant'}
            ]
        })
        mock_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_instance
        
        # Create test data
        query_analysis = {
            'topics': ['climate change'],
            'search_terms': ['global warming effects']
        }
        
        analysis_data = [
            {'id': 0, 'title': 'Article 1', 'url': 'https://example.com/1', 'content_sample': 'Sample 1'},
            {'id': 1, 'title': 'Article 2', 'url': 'https://example.com/2', 'content_sample': 'Sample 2'},
            {'id': 2, 'title': 'Article 3', 'url': 'https://example.com/3', 'content_sample': 'Sample 3'}
        ]
        
        # Execute ranking
        rankings = self.analyzer._get_llm_ranking(query_analysis, analysis_data)
        
        # Verify results
        self.assertEqual(len(rankings), 3)
        self.assertEqual(rankings[0]['id'], 2)  # Highest relevance
        self.assertEqual(rankings[1]['id'], 0)  # Middle relevance
        self.assertEqual(rankings[2]['id'], 1)  # Lowest relevance
        
        # Verify LLM usage
        mock_instance.chat.completions.create.assert_called_once()
    
    def test_create_ranking_prompt(self):
        """Test creation of ranking prompt."""
        # Create test data
        query_analysis = {
            'query_type': 'factual',
            'topics': ['renewable energy'],
            'search_terms': ['solar power benefits'],
            'time_sensitivity': 'recent'
        }
        
        analysis_data = [
            {'id': 0, 'title': 'Solar Energy Guide', 'url': 'https://example.com/solar', 
             'content_sample': 'Overview of solar power technology and applications.'}
        ]
        
        # Generate prompt
        prompt = self.analyzer._create_ranking_prompt(query_analysis, analysis_data)
        
        # Verify content
        self.assertIn('Research Query Analysis:', prompt)
        self.assertIn('- Type: factual', prompt)
        self.assertIn('renewable energy', prompt)
        self.assertIn('solar power benefits', prompt)
        self.assertIn('- Time Sensitivity: recent', prompt)
        self.assertIn('ITEM 0:', prompt)
        self.assertIn('Solar Energy Guide', prompt)
        self.assertIn('https://example.com/solar', prompt)
    
    @patch.object(ContentAnalyzer, '_basic_text_filter')
    @patch.object(ContentAnalyzer, '_llm_relevance_ranking')
    def test_analyze_main_flow(self, mock_llm_ranking, mock_basic_filter):
        """Test the main analysis workflow."""
        # Configure mocks
        mock_basic_filter.return_value = [
            {'url': 'https://example.com/1', 'title': 'Article 1'},
            {'url': 'https://example.com/2', 'title': 'Article 2'},
            {'url': 'https://example.com/3', 'title': 'Article 3'},
            {'url': 'https://example.com/4', 'title': 'Article 4'}
        ]
        
        mock_llm_ranking.return_value = [
            {'url': 'https://example.com/3', 'title': 'Article 3', 'relevance_score': 95},
            {'url': 'https://example.com/1', 'title': 'Article 1', 'relevance_score': 80},
            {'url': 'https://example.com/4', 'title': 'Article 4', 'relevance_score': 65},
            {'url': 'https://example.com/2', 'title': 'Article 2', 'relevance_score': 40}
        ]
        
        # Execute analysis
        query_analysis = {'topics': ['test'], 'search_terms': ['test query']}
        content_items = [{'url': f'https://example.com/{i}', 'title': f'Article {i}'} for i in range(1, 6)]
        
        results = self.analyzer.analyze(query_analysis, content_items)
        
        # Verify results
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['url'], 'https://example.com/3')  # Highest relevance
        
        # Verify method calls
        mock_basic_filter.assert_called_once()
        mock_llm_ranking.assert_called_once()

if __name__ == '__main__':
    unittest.main()