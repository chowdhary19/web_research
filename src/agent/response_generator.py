"""
Response Generator - Component for synthesizing content into coherent responses.
"""
import logging
import os
import json
from typing import Dict, List, Any

# LLM providers
import openai
from anthropic import Anthropic
import google.generativeai as genai

class ResponseGenerator:
    """
    Generates coherent research responses from filtered content.
    """
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the Response Generator.
        
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
    
    def generate(self, query: str, query_analysis: Dict, filtered_content: List[Dict], 
                conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive research response.
        
        Args:
            query: The original user query
            query_analysis: Analysis of the query
            filtered_content: List of relevant content items
            conversation_history: List of previous conversation messages
            
        Returns:
            Dictionary containing the generated response
        """
        try:
            # Prepare content for synthesis
            content_for_synthesis = self._prepare_content(filtered_content)
            
            # Generate the response using LLM
            synthesis_result = self._get_llm_synthesis(
                query, 
                query_analysis, 
                content_for_synthesis,
                conversation_history
            )
            
            # Format the final response
            response = {
                "summary": synthesis_result.get("summary", ""),
                "detailed_response": synthesis_result.get("detailed_response", ""),
                "highlights": synthesis_result.get("highlights", []),
                "source_evaluation": synthesis_result.get("source_evaluation", {})
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            # Fallback response
            return {
                "summary": f"I found information about '{query}', but encountered an error while synthesizing a response. "
                           f"Please try rephrasing your question or being more specific.",
                "detailed_response": "",
                "highlights": []
            }
    
    def _prepare_content(self, filtered_content: List[Dict]) -> List[Dict]:
        """
        Prepare content for synthesis by organizing and filtering.
        
        Args:
            filtered_content: List of content items
            
        Returns:
            Prepared content for synthesis
        """
        prepared_content = []
        
        for item in filtered_content:
            # Extract key information and truncate content if needed
            content = item.get("content", "")
            if len(content) > 8000:  # Truncate very long content
                content = content[:8000] + "... [content truncated]"
                
            prepared_content.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "content": content,
                "metadata": item.get("metadata", {})
            })
        
        return prepared_content
    
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
    
    def _get_llm_synthesis(self, query: str, query_analysis: Dict, 
                  content: List[Dict], conversation_history: List[Dict] = None) -> Dict:
        """
        Use LLM to synthesize content into a response.
        
        Args:
            query: The original user query
            query_analysis: Analysis of the query
            content: List of content items
            conversation_history: List of previous conversation messages
            
        Returns:
            Dictionary containing the synthesized response
        """
        prompt = self._create_synthesis_prompt(query, query_analysis, content, conversation_history)
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4"),
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a research specialist that synthesizes information into clear, comprehensive responses."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4000"))
                )
                result = response.choices[0].message.content
                
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4000")),
                    system="You are a research specialist that synthesizes information into clear, comprehensive responses.",
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
            
            # Fallback to basic response if all parsing attempts fail
            return {
                "summary": f"Based on my research about '{query}', I found relevant information but encountered an error formatting it. The information appears to support answering your question, but I need to present it differently.",
                "detailed_response": result,
                "highlights": []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting LLM synthesis: {str(e)}")
            # Fallback response in case of error
            return {
                "summary": f"I encountered an error while researching '{query}'. Please try rephrasing your question or try again later.",
                "detailed_response": f"Error processing your request: {str(e)}",
                "highlights": []
            }
    
    def _create_synthesis_prompt(self, query: str, query_analysis: Dict, 
                               content: List[Dict], conversation_history: List[Dict] = None) -> str:
        """
        Create the prompt for the LLM to synthesize content.
        
        Args:
            query: The original user query
            query_analysis: Analysis of the query
            content: List of content items
            conversation_history: List of previous conversation messages
            
        Returns:
            Formatted prompt for LLM
        """
        # Create a summary of conversation history if available
        context_summary = ""
        if conversation_history and len(conversation_history) > 1:
            context_summary = "Previous conversation context:\n"
            # Extract the last few exchanges (max 3)
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_summary += f"{role}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}\n"
        
        # Determine response depth based on query analysis
        depth = query_analysis.get("required_depth", "standard")
        
        prompt = f"""
Research Query: "{query}"

Query Analysis:
- Type: {query_analysis.get('query_type', 'factual')}
- Required Depth: {depth}
- Topics: {', '.join(query_analysis.get('topics', []))}

{context_summary}

Below are relevant content excerpts from {len(content)} sources:

"""
        
        # Add content from sources
        for i, item in enumerate(content):
            prompt += f"\nSOURCE {i+1}: {item.get('title', 'Untitled')}\n"
            prompt += f"URL: {item.get('url', 'No URL')}\n"
            prompt += f"EXCERPT: {item.get('content', '')[:1500]}{'...' if len(item.get('content', '')) > 1500 else ''}\n"
            prompt += "--------------------------------------------\n\n"
        
        prompt += f"""
Based on these sources, synthesize a comprehensive response to the query.

Return your response as a JSON object with the following structure:
{{
    "summary": "A concise summary answering the query (400-600 words)",
    "detailed_response": "A detailed response with in-depth information (800-1200 words)",
    "highlights": ["key", "points", "or", "findings"],
    "source_evaluation": {{
        "reliability": "assessment of source reliability",
        "contradictions": "note any contradictions between sources",
        "information_gaps": "identify any information gaps"
    }}
}}

For the {depth} depth requested, focus on providing {'basic facts and a clear answer' if depth == 'basic' else 'comprehensive information with nuanced analysis' if depth == 'deep' else 'balanced information with key details and context'}.

Important:
1. Synthesize information from all sources - don't just summarize each individually
2. Resolve contradictions between sources when possible
3. Cite specific sources where appropriate using [Source X] notation
4. Maintain factual accuracy - don't add information not found in the sources
5. Format the detailed_response using markdown for readability
"""

        return prompt