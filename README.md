# Web Research Agent

A sophisticated web-based research system that leverages large language models (LLMs) to automate the process of finding, analyzing, and synthesizing information from the internet.

## Features

- **Intelligent Query Analysis**: Automatically determines search strategies based on user questions
- **Multi-Provider Support**: Works with OpenAI (GPT), Anthropic (Claude), or Google (Gemini) models
- **Advanced Web Scraping**: Extracts content from search results with respect to robots.txt
- **Smart Content Filtering**: Ranks and filters content based on relevance to your query
- **Comprehensive Responses**: Synthesizes information from multiple sources into coherent research answers

## Architecture

The system follows a pipeline architecture with specialized components:

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

## Requirements

- Python 3.8+
- LLM API access (OpenAI, Anthropic, or Google)
- Search API access (SerpAPI or Google CSE)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-research-agent.git
   cd web-research-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided template:
   ```
   # API Keys (replace with your actual keys)
   OPENAI_API_KEY=
   ANTHROPIC_API_KEY=
   GOOGLE_API_KEY=
   SERPAPI_API_KEY=
   
   # LLM Settings
   DEFAULT_LLM_MODEL=gpt-3.5-turbo
   DEFAULT_MAX_TOKENS=4000
   
   # Search Settings
   SEARCH_RESULT_LIMIT=5
   MAX_PAGES_PER_SEARCH=3
   
   # Web Scraper Settings
   REQUEST_TIMEOUT=10
   USER_AGENT="WebResearchAgent/1.0"
   RESPECT_ROBOTS_TXT=True
   
   # Application Settings
   DEBUG=True
   PORT=5001
   ```

5. Add at least one LLM API key (OpenAI, Anthropic, or Google) to the `.env` file

## Usage

### Running the Web Interface

1. Start the web server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5001`

3. Enter your research query in the input field and click "Research"

### Command Line Interface

The agent can be used directly from the command line:

```bash
# Research with a specific query
python main.py "What are the latest advances in quantum computing?"

# Specify the LLM provider
python main.py "Explain machine learning" --provider anthropic

# Save results to a file
python main.py "History of space exploration" --output research_results.json

# Run in interactive mode
python main.py
```

Command line options:
- `--provider`, `-p`: LLM provider to use (openai, anthropic, or google)
- `--verbose`, `-v`: Enable verbose output
- `--output`, `-o`: Output file path for research results

### Using as a Library

```python
from src.agent.research_agent import ResearchAgent

# Initialize the agent
agent = ResearchAgent()

# Conduct research
result = agent.research("What are the latest advances in quantum computing?")

# Print the response
print(result["summary"])
```

## Configuration

### LLM Providers

The agent supports multiple LLM providers:

- **OpenAI (GPT-4/3.5)**: Set `OPENAI_API_KEY` in the `.env` file
- **Anthropic (Claude)**: Set `ANTHROPIC_API_KEY` in the `.env` file
- **Google (Gemini)**: Set `GOOGLE_API_KEY` in the `.env` file

The agent automatically selects the first available provider in the order listed above, or you can specify the provider using the `--provider` argument.

### Search Providers

The agent supports the following search providers:

- **SerpAPI**: Set `SERPAPI_API_KEY` in the `.env` file
- **Google Custom Search Engine**: Set `GOOGLE_SEARCH_ENGINE_ID` and `GOOGLE_API_KEY` in the `.env` file

## Advanced Configuration

Additional settings can be adjusted in the `.env` file:

- `DEFAULT_LLM_MODEL`: The default model to use (e.g., "gpt-3.5-turbo", "claude-3-opus-20240229")
- `DEFAULT_MAX_TOKENS`: Maximum tokens for LLM responses
- `SEARCH_RESULT_LIMIT`: Maximum number of search results to process
- `MAX_PAGES_PER_SEARCH`: Maximum number of pages to scrape per search
- `REQUEST_TIMEOUT`: Timeout for web requests in seconds
- `USER_AGENT`: User agent string for web requests
- `RESPECT_ROBOTS_TXT`: Whether to respect robots.txt files (True/False)
- `DEBUG`: Enable debug logging (True/False)

## Development

### Project Structure

```
web-research-agent/
├── src/
│   ├── agent/
│   │   ├── research_agent.py     # Main agent orchestration
│   │   ├── query_analyzer.py     # Query analysis component
│   │   └── response_generator.py # Response generation component
│   ├── tools/
│   │   ├── search_tool.py        # Web search functionality
│   │   ├── web_scraper.py        # Web content extraction
│   │   └── content_analyzer.py   # Content relevance analysis
│   └── utils/
│       ├── llm_utils.py          # LLM provider interface
│       ├── logger.py             # Logging configuration
│       └── error_handling.py     # Error handling utilities
├── app.py                        # Web application & CLI entry point
├── requirements.txt              # Project dependencies
├── .env                          # Environment configuration
└── README.md                     # This file
```

### Running Tests

```bash
pytest tests/
```

## Example

```bash
$ python main.py "What are the environmental impacts of electric vehicles?"

Researching: What are the environmental impacts of electric vehicles?

================================================================================
RESEARCH SUMMARY: What are the environmental impacts of electric vehicles?
================================================================================

Electric vehicles (EVs) have mixed environmental impacts. While they produce zero 
tailpipe emissions and significantly reduce greenhouse gas emissions during operation 
compared to conventional vehicles, their overall environmental footprint depends on 
several factors:

Positive impacts:
- Lower lifetime greenhouse gas emissions (30-70% less than conventional vehicles)
- Zero direct air pollution during operation
- Reduced dependence on fossil fuels
- Lower noise pollution
- Potential for integration with renewable energy systems

Negative impacts:
- Carbon-intensive manufacturing process, especially for batteries
- Environmental concerns with battery material mining (lithium, cobalt, nickel)
- Electricity generation source affects overall emissions (coal vs renewable)
- Battery disposal and recycling challenges
- Increased water usage in manufacturing

The environmental benefits of EVs increase when powered by renewable energy sources 
and as battery production becomes more efficient and sustainable. The consensus among 
researchers is that despite manufacturing impacts, EVs are environmentally superior to 
conventional vehicles over their lifetime, especially as electricity grids become 
greener.

SOURCES:
1. Environmental Impacts of Electric Vehicles - EPA - https://www.epa.gov/greenvehicles/electric-vehicle-myths
2. Life Cycle Analysis of Electric Vehicles - Nature Climate Change - https://www.nature.com/articles/s41558-020-0898-6
3. Electric Vehicle Battery Materials: Environmental Concerns - Environmental Science & Technology - https://pubs.acs.org/doi/10.1021/acs.est.0c02194
```

## Limitations

- The agent's capabilities are limited by the underlying LLM and search provider APIs
- Some websites may block web scraping attempts
- Results depend on the quality and availability of online information
- Response synthesis may occasionally contain inaccuracies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses various open-source libraries and APIs
- Special thanks to the developers of the LLM models that power this agent