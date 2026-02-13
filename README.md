# Dental OPG Analysis

A full-stack application that analyzes dental OPG (Orthopantomogram) X-ray images to identify missing teeth using multiple AI models.

## Features

- **Multi-Model Analysis**: Uses three AI models (GPT-4o, Gemini, Anthropic Claude) to analyze dental images
- **Consensus Decision**: A deciding model (GPT-5.2) evaluates all three results and determines the most accurate analysis
- **Quadrant-Based Results**: Identifies missing teeth in all four dental quadrants
- **Modern React UI**: Beautiful, responsive interface with real-time analysis
- **Async Processing**: All three initial models run in parallel for faster results

## Project Structure

```
Dental/
├── backend/                 # FastAPI backend
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic data models
│   ├── ai_clients.py        # AI model client implementations
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx          # Main application component
│   │   └── components/      # UI components
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## Dental Quadrant System

```
        Upper
    ┌─────┬─────┐
    │ Q1  │ Q2  │
    │11-18│21-28│
    ├─────┼─────┤
    │ Q4  │ Q3  │
    │41-48│31-38│
    └─────┴─────┘
        Lower
```

## Quick Start

### Backend Setup

```bash
cd backend
source venv/bin/activate
# Add your API keys to config.py or create .env file
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API requests to the backend.

## API Keys Required

Add these to `backend/config.py` or create a `.env` file:
- `OPENAI_API_KEY` - For GPT-4o and GPT-5.2
- `GOOGLE_API_KEY` - For Gemini
- `ANTHROPIC_API_KEY` - For Claude

## API Endpoints

- `POST /analyze` - Full analysis with all model results
- `POST /analyze/simple` - Simplified response with just missing teeth
- `GET /health` - Health check

## License

MIT
