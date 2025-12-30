# LinkedIn Post Generator

AI-powered LinkedIn post generator using LangChain and Google Gemini 2.5 Flash with web search capabilities.

![LinkedIn Post Generator](https://img.shields.io/badge/AI-Powered-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)

## Features

- 🔍 **Trending Topic Discovery**: Identifies trending topics in your professional field using Google Search
- 📚 **Deep Research**: Compiles comprehensive research reports with statistics and expert perspectives
- ✍️ **Multiple Post Variations**: Generates 3 unique LinkedIn post styles (Storytelling, Data-Driven, Thought Leadership)
- 🔄 **Post Refinement**: Iteratively refine posts based on your feedback
- 📊 **Real-time Processing**: Watch the AI agent work through each stage with live updates
- 🎨 **Professional UI**: Clean, modern interface with blue/white/gray color scheme

## Tech Stack

- **Backend**: FastAPI + LangChain + Google Generative AI
- **Frontend**: Vanilla HTML/CSS/JS with Server-Sent Events (SSE)
- **AI Model**: Gemini 2.5 Flash with Google Search grounding
- **Deployment**: Render.com ready

## Local Development

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Google AI API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd linkedin-post-generator
```

2. Create virtual environment with uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

5. Run the development server:
```bash
python -m app.main
```

6. Open http://localhost:8000 in your browser

## Deployment on Render.com

### Option 1: Using Render Blueprint (Recommended)

1. Fork this repository to your GitHub account

2. Go to [Render Dashboard](https://dashboard.render.com/)

3. Click "New" → "Blueprint"

4. Connect your GitHub repository

5. Render will automatically detect the `render.yaml` configuration

6. Add your environment variables:
   - `GOOGLE_API_KEY`: Your Google AI API key

7. Click "Apply" to deploy

### Option 2: Manual Deployment

1. Go to [Render Dashboard](https://dashboard.render.com/)

2. Click "New" → "Web Service"

3. Connect your repository

4. Configure the service:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. Add environment variables:
   - `GOOGLE_API_KEY`: Your Google AI API key
   - `ENVIRONMENT`: `production`

6. Deploy!

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini | Yes |
| `ENVIRONMENT` | `development` or `production` | No |
| `PORT` | Server port (default: 8000) | No |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the main web interface |
| `/health` | GET | Health check endpoint |
| `/api/generate` | POST | Generate LinkedIn posts (SSE stream) |
| `/api/refine` | POST | Refine a post based on feedback |
| `/api/trending/{field}` | GET | Get trending topics for a field |

## How It Works

1. **Enter Your Field**: Specify your professional field (e.g., "Artificial Intelligence", "Digital Marketing")

2. **AI Research Phase**:
   - The agent searches for trending topics using Google Search
   - Compiles research from multiple queries
   - Creates a comprehensive research report

3. **Post Generation**:
   - Generates 3 unique LinkedIn post variations
   - Each post follows best practices for LinkedIn engagement

4. **Review & Refine**:
   - Copy any post to your clipboard
   - Refine posts with specific feedback
   - Download or share directly

## Project Structure

```
linkedin-post-generator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── agent/
│       ├── __init__.py
│       └── linkedin_agent.py # LangChain agent
├── static/
│   ├── index.html           # Frontend HTML
│   ├── styles.css           # CSS styles
│   └── app.js               # Frontend JavaScript
├── pyproject.toml           # Python project config
├── requirements.txt         # Dependencies
├── render.yaml              # Render deployment config
├── Procfile                 # Process file
└── README.md
```

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

