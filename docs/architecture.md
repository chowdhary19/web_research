# Research Agent Architecture Documentation

## Overview

The Research Agent is an advanced web-based research system that leverages large language models (LLMs) to automate the process of finding, analyzing, and synthesizing information from the internet. It follows a modular design with specialized components that work together to deliver comprehensive research responses based on user queries.

## System Architecture

The system follows a pipeline architecture with the following core components:

```
+------------------+      +---------------+      +----------------+      +------------------+      +--------------------+
| QueryAnalyzer    | ---> | SearchTool    | ---> | WebScraper     | ---> | ContentAnalyzer  | ---> | ResponseGenerator  |
+------------------+      +---------------+      +----------------+      +------------------+      +--------------------+
        ^                                                                                                  |
        |                                                                                                  |
        +-------------------------------------------------------------------------------------------+------+
                                                                                                    |
                                                                                             +-------------+
                                                                                             | ResearchAgent |
                                                                                             +-------------+
```

### Component Interactions

1. **ResearchAgent**: Orchestrates the entire research process through its components
2. **QueryAnalyzer**: Analyzes user queries to determine search strategies and terms
3. **SearchTool**: Performs web searches using external search APIs
4. **WebScraper**: Extracts content from web pages 
5. **ContentAnalyzer**: Analyzes and filters content for relevance
6. **ResponseGenerator**: Synthesizes content into coherent research responses

## Component Breakdown

### ResearchAgent (`src/agent/research_agent.py`)

The central coordinator that manages the entire research process from query input to response generation.

#### Responsibilities:
- Initializes and orchestrates all subcomponents
- Handles the research pipeline flow
- Manages conversation history
- Provides error handling mechanisms

#### Key Methods:
- `research(query)`: Conducts the full research process
- `reset_conversation()`: Clears conversation history
- `_handle_no_results()`: Handles cases where no search results are found
- `_handle_no_content()`: Handles cases where content extraction fails

### QueryAnalyzer (`src/agent/query_analyzer.py`)

Analyzes user queries to determine optimal search strategies and understand user intent.

#### Responsibilities:
- Determines query type (factual, exploratory, etc.)
- Identifies important topics and concepts
- Generates optimized search terms
- Assesses time sensitivity and required depth

#### Key Methods:
- `analyze(query, conversation_history)`: Analyzes the query
- `_get_llm_analysis(query, conversation_history)`: Uses LLM to analyze the query
- `_create_analysis_prompt(query, conversation_history)`: Creates the prompt for LLM analysis

#### Prompt Design Highlights:
- Structures the analysis as a JSON object
- Requests specific fields: query_type, topics, search_terms, time_sensitivity, required_depth
- Includes conversation context to improve analysis accuracy

### SearchTool (`src/tools/search_tool.py`)

Performs web searches using different search APIs to retrieve relevant results.

#### Responsibilities:
- Connects to search APIs (SerpAPI, Google CSE)
- Formats and sends search requests
- Processes and standardizes search results
- Provides a mock search option for development

#### Key Methods:
- `search(search_terms, query_type, limit)`: Performs web searches
- `_search_serpapi(query, is_news)`: Searches using SerpAPI
- `_search_google_cse(query, is_news)`: Searches using Google Custom Search
- `_mock_search(query, is_news)`: Generates mock search results

#### API Integrations:
- SerpAPI: Primary search provider
- Google Custom Search Engine: Alternative search provider
- Mock search: Fallback when no API keys are available

### WebScraper (`src/tools/web_scraper.py`)

Extracts content from web pages using various web scraping techniques.

#### Responsibilities:
- Extracts text content from web pages
- Respects robots.txt policies
- Uses multiple extraction strategies
- Cleans and formats content

#### Key Methods:
- `scrape(url)`: Scrapes content from a webpage
- `_can_fetch(url)`: Checks robots.txt permissions
- `_scrape_with_newspaper(url)`: Extracts using newspaper3k
- `_scrape_with_beautifulsoup(url)`: Extracts using BeautifulSoup
- `_clean_content(content)`: Cleans and normalizes content

#### Technology Integrations:
- newspaper3k: Article extraction library
- BeautifulSoup: DOM parsing and traversal
- urllib.robotparser: Robots.txt parsing

### ContentAnalyzer (`src/tools/content_analyzer.py`)

Evaluates the relevance and quality of scraped content in relation to the user query.

#### Responsibilities:
- Filters content based on relevance
- Ranks content by importance
- Organizes content for processing
- Identifies key information

#### Key Methods:
- `analyze(query_analysis, content_items)`: Analyzes content relevance
- `_basic_text_filter(query_analysis, content_items)`: Performs text-based filtering
- `_llm_relevance_ranking(query_analysis, filtered_items)`: Uses LLM to rank content
- `_get_llm_ranking(query_analysis, analysis_data)`: Gets content rankings from LLM

#### Filtering Techniques:
- Term frequency scoring
- Title and URL relevance weighting
- Content freshness assessment
- LLM-based deep analysis

### ResponseGenerator (`src/agent/response_generator.py`)

Synthesizes filtered content into coherent research responses.

#### Responsibilities:
- Integrates content from multiple sources
- Structures responses based on query requirements
- Resolves contradictions in information
- Formats responses for readability

#### Key Methods:
- `generate(query, query_analysis, filtered_content, conversation_history)`: Generates responses
- `_prepare_content(filtered_content)`: Prepares content for synthesis
- `_get_llm_synthesis(query, query_analysis, content, conversation_history)`: Uses LLM for synthesis
- `_create_synthesis_prompt(query, query_analysis, content, conversation_history)`: Creates prompt for LLM

#### Response Structure:
- Summary: Concise answer to the query
- Detailed response: In-depth exploration of the topic
- Highlights: Key points and findings
- Source evaluation: Assessment of reliability and gaps

## LLM Integration

The system supports multiple LLM providers for AI capabilities, including:

1. **OpenAI (GPT-4)**
   - Used for query analysis, content ranking, and response synthesis
   - Configured through environment variables (`OPENAI_API_KEY`)
   - Default model: "gpt-4"

2. **Anthropic (Claude)**
   - Alternative LLM provider
   - Model: "claude-3-opus-20240229"
   - Configured through environment variables (`ANTHROPIC_API_KEY`)

3. **Google (Gemini)**
   - Alternative LLM provider
   - Model: "gemini-1.5-pro-latest"
   - Configured through environment variables (`GOOGLE_API_KEY`)

### LLM Prompt Design

The system employs carefully designed prompts for different tasks:

1. **Query Analysis Prompts**
   - Structured to extract specific information categories
   - JSON output format for easy parsing
   - Includes conversation context when available

2. **Content Ranking Prompts**
   - Provides content samples with context
   - Requests numerical relevance scores with reasoning
   - Tailored to the query type and topics

3. **Response Synthesis Prompts**
   - Includes relevant content excerpts
   - Specifies the desired response structure
   - Adjusts depth based on query requirements
   - Emphasizes factual accuracy and source synthesis

### JSON Response Handling

The system includes robust JSON parsing capabilities to handle LLM responses:

- Extracts JSON from code blocks or direct responses
- Removes comments and trailing commas
- Implements fallback mechanisms when parsing fails
- Logs parsing errors for debugging

## Error Handling

The system implements comprehensive error handling throughout:

### Graceful Degradation

Components are designed to handle failures gracefully:

- If query analysis fails, basic search terms are used
- If search fails, informative error messages are returned
- If content extraction fails, available search results are still provided
- If LLM synthesis fails, raw content is formatted as a basic response

### Error Responses

The `handle_error` utility provides standardized error handling:

- Categorizes errors by type
- Provides user-friendly error messages
- Logs details for debugging
- Returns partial results when possible

### Fallback Mechanisms

Each component includes fallback options:

- `QueryAnalyzer`: Falls back to using the raw query as search term
- `SearchTool`: Provides mock results when APIs are unavailable
- `WebScraper`: Tries multiple extraction methods when one fails
- `ContentAnalyzer`: Uses basic filtering when LLM ranking fails
- `ResponseGenerator`: Returns simplified responses when synthesis fails

## Configuration and Environment

The system uses environment variables for configuration:

- API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- Search API keys: `SERPAPI_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID`
- Default settings: `DEFAULT_LLM_MODEL`, `DEFAULT_MAX_TOKENS`, `REQUEST_TIMEOUT`
- Behavioral flags: `RESPECT_ROBOTS_TXT`, `USER_AGENT`

## Data Flow

The complete research process follows this data flow:

1. User provides a research query
2. Query is analyzed to determine search strategy
3. Web searches are performed using optimized search terms
4. Content is extracted from search results
5. Content is analyzed and filtered for relevance
6. Relevant content is synthesized into a comprehensive response
7. Response is returned to the user
8. Conversation history is updated

## System Performance Considerations

The system includes several optimizations for performance:

- Caching of robots.txt permissions
- Basic text filtering before LLM analysis
- Content truncation for very large pages
- Result limiting for efficiency
- Parallel processing of independent tasks

## Extensibility and Future Improvements

The modular design allows for easy extension:

- Additional LLM providers can be added
- New search APIs can be integrated
- Advanced scraping techniques can be implemented
- Custom response formats can be developed
- Domain-specific analyzers can be created

## Conclusion

The Research Agent provides a comprehensive solution for automated web research, combining traditional web search and scraping techniques with advanced LLM-based analysis and synthesis. Its modular design allows for flexibility, scalability, and continuous improvement.