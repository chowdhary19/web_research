"""
Query Analyzer - Component for analyzing user queries and determining search strategies.
"""
import logging
import os
from typing import Dict, List, Any

# LLM providers
import openai
from anthropic import Anthropic
import google.generativeai as genai

class QueryAnalyzer:
    """
    Analyzes user queries to determine research strategies and search terms.
    """
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the Query Analyzer.
        
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
    
    def analyze(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyze the user query to determine search strategy.
        
        Args:
            query: The user's research query
            conversation_history: List of previous conversation messages
            
        Returns:
            Dictionary containing query analysis and search strategy
        """
        try:
            # Determine query characteristics using LLM
            analysis = self._get_llm_analysis(query, conversation_history)
            
            # Extract and structure the analysis
            structured_analysis = {
                "query_type": analysis.get("query_type", "factual"),
                "topics": analysis.get("topics", []),
                "search_terms": analysis.get("search_terms", []),
                "time_sensitivity": analysis.get("time_sensitivity", "any"),
                "required_depth": analysis.get("required_depth", "standard"),
                "result_limit": analysis.get("result_limit", 5),
                "additional_context": analysis.get("additional_context", {})
            }
            
            # If search terms aren't provided, use query as fallback
            if not structured_analysis["search_terms"]:
                structured_analysis["search_terms"] = [query]
                
            return structured_analysis
        
        except Exception as e:
            self.logger.error(f"Error analyzing query: {str(e)}")
            # Fallback analysis
            return {
                "query_type": "factual",
                "topics": [],
                "search_terms": [query],
                "time_sensitivity": "any",
                "required_depth": "standard",
                "result_limit": 5
            }
    
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
        
    def _get_llm_analysis(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Use LLM to analyze the query.
        
        Args:
            query: The user's research query
            conversation_history: List of previous conversation messages
            
        Returns:
            Dictionary containing LLM's analysis of the query
        """
        prompt = self._create_analysis_prompt(query, conversation_history)
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4"),
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a query analysis expert. Analyze research queries and output JSON."},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = response.choices[0].message.content
                
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    system="You are a query analysis expert. Analyze research queries and output JSON.",
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
                return data
                
            # If parsing fails, log error
            self.logger.error(f"Failed to parse LLM response as JSON: {result}")
            
            # Fallback to default analysis
            return {
                "query_type": "factual",
                "topics": [],
                "search_terms": [query],
                "time_sensitivity": "any",
                "required_depth": "standard"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting LLM analysis: {str(e)}")
            # Fallback analysis in case of error
            return {
                "query_type": "factual",
                "topics": [],
                "search_terms": [query],
                "time_sensitivity": "any",
                "required_depth": "standard"
            }
            
    def _create_analysis_prompt(self, query: str, conversation_history: List[Dict] = None) -> str:
        """
        Create the prompt for the LLM to analyze the query.
        
        Args:
            query: The user's research query
            conversation_history: List of previous conversation messages
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""
Analyze the following research query and provide a structured analysis:

QUERY: "{query}"

Return your analysis as a JSON object with the following structure:
{{
    "query_type": "factual | exploratory | comparative | news | opinion",
    "topics": ["list", "of", "main", "topics"],
    "search_terms": ["optimized", "search", "terms"],
    "time_sensitivity": "recent | past_year | any",
    "required_depth": "basic | standard | deep",
    "result_limit": 5,
    "additional_context": {{
        "specific_sources": ["any", "specific", "sources", "to", "prioritize"],
        "specific_exclusions": ["any", "sources", "to", "avoid"],
        "geographic_focus": "any geographic focus",
        "temporal_focus": "any time period focus"
    }}
}}

For search_terms, provide 1-3 distinct search queries that would yield the most relevant information.
"""

        # Add conversation context if available
        if conversation_history and len(conversation_history) > 1:
            context_prompt = "\nPrevious conversation context:\n"
            # Extract the last few exchanges (max 3)
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_prompt += f"{role}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"
            prompt += context_prompt
            prompt += "\nConsider this context when analyzing the query."

        return prompt