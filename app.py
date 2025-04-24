"""
Web Research Agent - Flask web application interface.
"""
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

from src.agent.research_agent import ResearchAgent
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Configure logger
logger = setup_logger("web_app")

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for all routes

# Create research agent
agent = ResearchAgent(
    llm_provider=os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
    verbose=os.getenv("DEBUG", "False").lower() == "true"
)

@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route("/static/<path:path>")
def serve_static(path):
    """Serve static files."""
    return send_from_directory("static", path)

@app.route("/api/research", methods=["POST"])
def research():
    """API endpoint for research queries."""
    global agent
    try:
        data = request.get_json()
        
        if not data or "query" not in data:
            return jsonify({
                "success": False,
                "message": "No query provided"
            }), 400
            
        query = data["query"]
        logger.info(f"Received research query: {query}")
        
        # Optional parameters
        provider = data.get("provider")
        if provider and provider != agent.llm_provider:
            agent = ResearchAgent(
                llm_provider=provider,
                verbose=os.getenv("DEBUG", "False").lower() == "true"
            )
        
        # Perform research
        result = agent.research(query)
        logger.info(f"Completed research for query: {query}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing research request: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error processing request: {str(e)}"
        }), 500

@app.route("/api/reset", methods=["POST"])
def reset_conversation():
    """Reset the agent's conversation history."""
    result = agent.reset_conversation()
    return jsonify(result)

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

# Create simple HTML template if it doesn't exist
def create_template_if_not_exists():
    """Create templates directory and basic index.html if they don't exist."""
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    index_path = os.path.join("templates", "index.html")
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Research Agent</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .query-form {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        textarea {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            min-height: 100px;
            font-family: inherit;
        }
        .controls {
            display: flex;
            gap: 10px;
            justify-content: space-between;
            align-items: center;
        }
        .controls select {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        button:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        .reset {
            background-color: #e74c3c;
        }
        .reset:hover {
            background-color: #c0392b;
        }
        .results {
            display: none;
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .sources {
            margin-top: 20px;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }
        .source-item {
            margin-bottom: 8px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 2s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h1>Web Research Agent</h1>
    
    <div class="container">
        <div class="query-form">
            <textarea id="queryInput" placeholder="Enter your research query here..."></textarea>
            <div class="controls">
                <select id="providerSelect">
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google (Gemini)</option>
                </select>
                <div>
                    <button id="resetBtn" class="reset">Reset Conversation</button>
                    <button id="submitBtn">Research</button>
                </div>
            </div>
        </div>
        
        <div id="loading" class="loading">
            <p>Researching... This may take a minute.</p>
            <div class="spinner"></div>
        </div>
        
        <div id="results" class="results">
            <h2>Research Results</h2>
            <div id="summary"></div>
            
            <div class="sources">
                <h3>Sources</h3>
                <ul id="sourcesList"></ul>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const queryInput = document.getElementById('queryInput');
            const providerSelect = document.getElementById('providerSelect');
            const submitBtn = document.getElementById('submitBtn');
            const resetBtn = document.getElementById('resetBtn');
            const resultsDiv = document.getElementById('results');
            const summaryDiv = document.getElementById('summary');
            const sourcesList = document.getElementById('sourcesList');
            const loadingDiv = document.getElementById('loading');
            
            submitBtn.addEventListener('click', async function() {
                const query = queryInput.value.trim();
                if (!query) {
                    alert('Please enter a research query');
                    return;
                }
                
                // Show loading spinner
                loadingDiv.style.display = 'block';
                resultsDiv.style.display = 'none';
                submitBtn.disabled = true;
                
                try {
                    const response = await fetch('/api/research', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            query: query,
                            provider: providerSelect.value
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Hide loading spinner
                    loadingDiv.style.display = 'none';
                    
                    if (result.success) {
                        // Display results
                        summaryDiv.innerHTML = result.summary.replace(/\\n/g, '<br>');
                        
                        // Display sources
                        sourcesList.innerHTML = '';
                        if (result.sources && result.sources.length > 0) {
                            result.sources.forEach((source, index) => {
                                const li = document.createElement('li');
                                li.className = 'source-item';
                                li.innerHTML = `<strong>${source.title || 'Untitled'}</strong> - <a href="${source.url}" target="_blank">${source.url}</a>`;
                                sourcesList.appendChild(li);
                            });
                        } else {
                            sourcesList.innerHTML = '<li>No sources available</li>';
                        }
                        
                        resultsDiv.style.display = 'block';
                    } else {
                        // Display error
                        alert(`Error: ${result.message}`);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while processing your request.');
                    loadingDiv.style.display = 'none';
                }
                
                submitBtn.disabled = false;
            });
            
            resetBtn.addEventListener('click', async function() {
                try {
                    const response = await fetch('/api/reset', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    alert(result.status);
                    
                    // Clear form and results
                    queryInput.value = '';
                    resultsDiv.style.display = 'none';
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while resetting the conversation.');
                }
            });
        });
    </script>
</body>
</html>
""")
        
        # Create a simple CSS file
        css_path = os.path.join("static", "style.css")
        if not os.path.exists(css_path):
            with open(css_path, "w") as f:
                f.write("""/* Additional styles can be added here */
""")

if __name__ == "__main__":
    create_template_if_not_exists()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting web application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)