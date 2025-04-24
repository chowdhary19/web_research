"""
Content Analyzer - Component for analyzing and filtering extracted content.
"""
import logging
import os
from typing import Dict, List, Any
import json
import re

# LLM providers
import openai
from anthropic import Anthropic
import google.generativeai as genai

class ContentAnalyzer:
    """
    Tool for analyzing and filtering content for relevance and reliability.
    """
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the Content Analyzer.
        
        Args:
            llm_provider: The LLM provider to use (openai, anthropic, or google)
        """
        self.logger = logging.getLogger(__name__)
        self.llm_provider = llm_provider
        
        # Initialize LLM client based on provider
        if llm_provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.client = openai.Client()
        elif llm_provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif llm_provider == "google":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.client = genai
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    def analyze(self, query_analysis: Dict, content_items: List[Dict]) -> List[Dict]:
        """
        Analyze content items for relevance and reliability.
        
        Args:
            query_analysis: Query analysis data
            content_items: List of content items to analyze
            
        Returns:
            Filtered and ranked list of relevant content items
        """
        try:
            # For efficiency, do a basic text-based filtering first
            filtered_items = self._basic_text_filter(query_analysis, content_items)
            
            if not filtered_items:
                self.logger.warning("No content items passed basic filtering")
                return content_items[:3] if len(content_items) > 3 else content_items
                
            # For remaining items, use LLM to assess relevance
            if len(filtered_items) > 3:
                ranked_items = self._llm_relevance_ranking(query_analysis, filtered_items)
            else:
                ranked_items = filtered_items
                
            return ranked_items
            
        except Exception as e:
            self.logger.error(f"Error in content analysis: {str(e)}")
            # Return original items in case of error, limited to first 3
            return content_items[:3] if len(content_items) > 3 else content_items
    
    def _basic_text_filter(self, query_analysis: Dict, content_items: List[Dict]) -> List[Dict]:
        """
        Perform basic text-based filtering of content items.
        
        Args:
            query_analysis: Query analysis data
            content_items: List of content items
        
        Returns:
            Filtered list of content items with relevance scores
        """
        filtered_items = []
        
        # Extract key terms from topics and search terms
        topics = query_analysis.get("topics", [])
        search_terms = query_analysis.get("search_terms", [])
        
        all_key_terms = []
        for term in search_terms:
            all_key_terms.extend(term.lower().split())
        for topic in topics:
            all_key_terms.extend(topic.lower().split())
            
        # Remove duplicates and common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "of"}
        key_terms = [term for term in all_key_terms if term not in common_words and len(term) > 2]
        
        # Create a set for faster lookups
        key_terms_set = set(key_terms)
        
        for item in content_items:
            content = item.get("content", "").lower()
            title = item.get("title", "").lower()
            url = item.get("url", "").lower()
            
            # Calculate a simple relevance score based on term frequency
            score = 0
            
            # Check title (highest weight)
            title_score = 0
            for term in key_terms:
                if term in title:
                    title_score += 10  # Higher weight for title matches
            
            # Apply diminishing returns for title matches
            score += min(50, title_score)
            
            # Check URL components for relevance
            url_score = 0
            for term in key_terms:
                if term in url:
                    url_score += 3  # Medium weight for URL matches
            
            score += min(15, url_score)
            
            # Check content (full text)
            content_score = 0
            for term in key_terms:
                term_count = content.count(term)
                # Apply diminishing returns for multiple occurrences
                if term_count > 0:
                    content_score += min(5, term_count) * 2
            
            score += content_score
            
            # Exact phrase matching (for multi-word search terms)
            for term in search_terms:
                if len(term.split()) > 1:  # Only check multi-word terms
                    if term.lower() in content:
                        score += 15  # Bonus for exact phrase match
                    if term.lower() in title:
                        score += 25  # Higher bonus for phrase in title
            
            # Content freshness and length factors
            if item.get("published_date"):
                try:
                    # Assuming published_date is in ISO format or similar
                    from datetime import datetime
                    published_date = datetime.fromisoformat(item["published_date"].replace('Z', '+00:00'))
                    now = datetime.now()
                    days_old = (now - published_date).days
                    
                    if days_old < 30:  # Published in last month
                        score += 10
                    elif days_old < 90:  # Published in last quarter
                        score += 5
                    elif days_old < 365:  # Published in last year
                        score += 2
                except (ValueError, TypeError):
                    # If date parsing fails, don't adjust score
                    pass
            
            # Content length factor (longer content often has more information)
            content_length = len(content.split())
            if content_length > 1000:
                score += 5
            elif content_length > 500:
                score += 3
            elif content_length > 200:
                score += 1
            
            # Add item if score is above threshold
            threshold = 5  # Minimum relevance score to include
            if score > threshold:
                # Convert to percentile score (0-100)
                percentile_score = min(98, score)  # Cap at 98% to avoid absolute certainty
                item["relevance_score"] = percentile_score
                filtered_items.append(item)
        
        # Sort by relevance score
        filtered_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Limit results to avoid overwhelming
        max_results = 20
        return filtered_items[:max_results]
    
    def _llm_relevance_ranking(self, query_analysis: Dict, filtered_items: List[Dict]) -> List[Dict]:
        """
        Use LLM to rank content items by relevance.
        
        Args:
            query_analysis: Query analysis data
            filtered_items: Pre-filtered list of content items
            
        Returns:
            Ranked list of content items
        """
        # Prepare items for analysis
        items_for_analysis = filtered_items[:10]  # Limit to top 10 for efficiency
        
        # Prepare analysis data
        analysis_data = []
        for i, item in enumerate(items_for_analysis):
            # Extract a sample of the content
            content = item.get("content", "")
            content_sample = content[:3000] + "..." if len(content) > 3000 else content
            
            analysis_data.append({
                "id": i,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content_sample": content_sample
            })
            
        # Get LLM analysis
        rankings = self._get_llm_ranking(query_analysis, analysis_data)
        
        # Reorder items based on rankings
        ranked_items = []
        for rank in rankings:
            item_id = rank.get("id")
            if item_id is not None and 0 <= item_id < len(items_for_analysis):
                item = items_for_analysis[item_id]
                item["relevance_score"] = rank.get("relevance_score", 0)
                item["relevance_reason"] = rank.get("reason", "")
                ranked_items.append(item)
                
        # Add any remaining items not ranked by LLM
        ranked_ids = [r.get("id") for r in rankings if r.get("id") is not None]
        for i, item in enumerate(items_for_analysis):
            if i not in ranked_ids:
                ranked_items.append(item)
                
        return ranked_items
    
    def _extract_and_clean_json(self, raw_text):
        """
        Extract JSON from text (including from code blocks) and clean it
        by removing comments before parsing.
        
        Args:
            raw_text: Text potentially containing JSON, possibly in code blocks
            
        Returns:
            Parsed JSON object or None if parsing fails
        """
        import json
        import re
        
        # Function to remove comments from JSON string
        def remove_json_comments(json_str):
            # Remove single-line comments (// comment)
            json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
            # Remove trailing commas (common error in hand-written JSON)
            json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
            return json_str
        
        # First try to extract JSON from code blocks if present
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                cleaned_json = remove_json_comments(json_str)
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse extracted JSON from code block: {e}")
                
        # If no code block or parsing failed, try direct JSON parsing after cleaning
        try:
            cleaned_text = remove_json_comments(raw_text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {raw_text}")
            return None  # Return None if all parsing attempts fail
    
    def _get_llm_ranking(self, query_analysis: Dict, analysis_data: List[Dict]) -> List[Dict]:
        """
        Get content relevance rankings from LLM.
        
        Args:
            query_analysis: Query analysis data
            analysis_data: Data for LLM analysis
            
        Returns:
            Ranked list of content items with relevance scores
        """
        prompt = self._create_ranking_prompt(query_analysis, analysis_data)
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4"),
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a content relevance expert. Analyze content and rank by relevance."},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = response.choices[0].message.content
                
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    system="You are a content relevance expert. Analyze content and rank by relevance.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
                
            elif self.llm_provider == "google":
                model = self.client.GenerativeModel('gemini-1.5-pro-latest')
                response = model.generate_content(prompt)
                result = response.text
            
            # Parse the result using the helper function
            data = self._extract_and_clean_json(result)
            
            if data is not None:
                if isinstance(data, dict) and "rankings" in data:
                    return data.get("rankings", [])
                elif isinstance(data, list):
                    return data  # It might be a direct list of rankings
            
            # If parsing fails or data doesn't match expected format, log error
            self.logger.error(f"Failed to parse or extract valid ranking data from LLM response")
                    
            # Default to basic ranking if parsing fails
            return [{"id": i, "relevance_score": 10 - i} for i in range(min(10, len(analysis_data)))]
                
        except Exception as e:
            self.logger.error(f"Error getting LLM ranking: {str(e)}")
            # Default ranking in case of error
            return [{"id": i, "relevance_score": 10 - i} for i in range(min(10, len(analysis_data)))]
    
    def _create_ranking_prompt(self, query_analysis: Dict, analysis_data: List[Dict]) -> str:
        """
        Create prompt for LLM to rank content relevance.
        
        Args:
            query_analysis: Query analysis data
            analysis_data: Content data for analysis
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""
Analyze these content items and rank them by relevance to the research query.

Research Query Analysis:
- Type: {query_analysis.get('query_type', 'factual')}
- Topics: {', '.join(query_analysis.get('topics', []))}
- Search Terms: {', '.join(query_analysis.get('search_terms', []))}
- Time Sensitivity: {query_analysis.get('time_sensitivity', 'any')}

Content Items to Rank:
"""
        
        # Add content items
        for item in analysis_data:
            prompt += f"""
ITEM {item['id']}:
Title: {item['title']}
URL: {item['url']}
Content Sample: {item['content_sample'][:500]}...
"""
        
        prompt += """
Rank these items by relevance to the research query. For each item, provide:
1. Relevance score (0-100)
2. Brief reason for the ranking

Return your analysis as a JSON object with this structure:
{
    "rankings": [
        {
            "id": 0,
            "relevance_score": 95,
            "reason": "Directly addresses the main topics with recent information"
        },
        ...
    ]
}

Sort the rankings from most relevant to least relevant.
"""
        
        return prompt