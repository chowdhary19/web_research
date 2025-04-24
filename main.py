""" Web Research Agent - Main application entry point. """
import os
import json
import argparse
from dotenv import load_dotenv
from src.agent.research_agent import ResearchAgent
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Configure logger
logger = setup_logger("web_research_agent")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("--provider", "-p", default="openai", choices=["openai", "anthropic", "google"], 
                        help="LLM provider to use (openai, anthropic, or google for Gemini)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Output file path for research results")
    return parser.parse_args()

def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Create research agent
    agent = ResearchAgent(llm_provider=args.provider, verbose=args.verbose)
    logger.info(f"Initialized Research Agent with {args.provider} provider")
    
    # If no query provided, run interactive mode
    if not args.query:
        print("Web Research Agent - Interactive Mode")
        print("Enter 'exit' or 'quit' to end the session\n")
        print("Available providers: openai, anthropic, google (Gemini)")
        
        while True:
            query = input("\nResearch Query: ")
            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            print("\nResearching... This may take a minute.\n")
            result = agent.research(query)
            
            if result["success"]:
                print("\n" + "=" * 80)
                print(f"RESEARCH SUMMARY: {query}")
                print("=" * 80 + "\n")
                print(result["summary"])
                print("\nSOURCES:")
                for i, source in enumerate(result["sources"]):
                    print(f"{i+1}. {source['title']} - {source['url']}")
            else:
                print(f"\nERROR: {result.get('message', 'Unknown error occurred')}")
    else:
        # Process single query from command line
        print(f"Researching: {args.query}")
        result = agent.research(args.query)
        
        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            if result["success"]:
                print("\n" + "=" * 80)
                print(f"RESEARCH SUMMARY: {args.query}")
                print("=" * 80 + "\n")
                print(result["summary"])
                print("\nSOURCES:")
                for i, source in enumerate(result["sources"]):
                    print(f"{i+1}. {source['title']} - {source['url']}")
            else:
                print(f"\nERROR: {result.get('message', 'Unknown error occurred')}")

if __name__ == "__main__":
    main()