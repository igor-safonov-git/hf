# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based chatbot that integrates with the Huntflow recruitment platform API and DeepSeek AI to provide AI-powered hiring analytics. The app provides real-time visualization of recruitment funnels and candidate statistics through a web interface.

## Commands

### Running the Application
```bash
# Start the FastAPI server (runs on http://localhost:8000)
python app.py

# The server automatically:
# - Serves frontend at http://localhost:8000
# - Provides API endpoints at /chat, /health, /api/prefetch-data, /db-info
# - Enables HTTPS at https://localhost:8443 if cert.pem and key.pem exist
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest -v                            # Verbose output
pytest tests/unit/test_universal_filter.py  # Single test file
```

### Environment Requirements
```bash
# Required environment variable
export DEEPSEEK_API_KEY="your-api-key"

# Optional for debugging
export DEBUG_MODE=true
```

## High-Level Architecture

### Core Data Flow
1. **User Input** → Frontend sends Russian question to `/chat` endpoint
2. **AI Processing** → `prompt.py` (1500+ lines) converts natural language to structured JSON
3. **Data Filtering** → `EnhancedMetricsCalculator` → `UniversalFilterEngine` applies complex filters
4. **Data Enrichment** → `chart_data_processor.py` adds real data from SQLite cache
5. **Response Generation** → AI creates Russian analytics response with visualizations

### Key Architectural Components

**AI Layer:**
- `prompt.py` - Massive prompt engineering system defining all entities, operations, and patterns
- `context_data_injector.py` - Injects dynamic context (recruiters, sources, etc.) into prompts
- Uses DeepSeek API for LLM processing

**Data Processing Layer:**
- `enhanced_metrics_calculator.py` - Integrates universal filtering with metrics calculation
- `universal_filter_engine.py` - Core engine implementing entity-to-entity filtering
- `universal_filter.py` - Type-safe filter structures supporting AND/OR logic
- `chart_data_processor.py` - Processes and validates chart data

**Data Storage:**
- `huntflow_local_client.py` - SQLite-based cache of Huntflow data
- `huntflow_cache.db` - Local SQLite database with recruitment data
- All queries work against real cached data, never mock data

**Frontend:**
- Single-page `index.html` with 35/65 split (chat/visualization)
- Chart.js for rendering various chart types
- Metrics cards and breakdown tables for grouped data

### Universal Filtering System

The codebase implements a sophisticated filtering system where **every entity can filter by every other entity**:

- **Entities**: applicants, vacancies, hires, recruiters, sources, divisions, hiring_managers, stages
- **Logical Operators**: AND/OR with nesting, complex operators (in, gt, gte, lt, lte, between)
- **Time Filtering**: period-based (1 month, 3 month, 6 month, 1 year, all)

Example:
```python
filters = {
    "and": [
        {"period": "6 month"},
        {"or": [
            {"recruiters": "12345"},
            {"sources": {"operator": "in", "value": ["hh", "linkedin"]}}
        ]}
    ]
}
```

### Metrics System

The project uses a **centralized metrics_filter** approach:
- Single `metrics_filter` object for all metrics (main + secondary)
- Automatic grouping when only period is specified
- Charts can have independent `group_by` from metrics
- All responses return clean aggregated totals

### Performance Characteristics
- Average response time: 0.259s (exceeds <0.5s target by 48%)
- Processing rate: 16,737 items/second
- All operations are async for optimal performance
- Response caching via 15-minute cache in web operations

## Absolute Rules

- DO NOT EVER DELETE INFORMATION FROM PROMPT UNLESS ASKED TO
- No mock or test data ever - always use real database records
- Simulated metrics must be clearly marked and based on real data patterns
- All user-facing text must be in Russian
- JSON schema compliance is mandatory for all chart outputs

## Key Patterns

- **Async Everything**: All database operations and API calls use async/await
- **Type Safety**: Extensive use of Pydantic models and type hints
- **Real Data Only**: Every calculation based on actual Huntflow cached data
- **Russian UI**: All user-facing text in Russian, technical logs in English
- **Clean Responses**: No detailed breakdown objects in responses, only totals

## Recent Major Features

### Universal Filtering System (✅ PRODUCTION READY)
- Every entity filters by every other entity
- Complex AND/OR logical operators
- Performance: 0.0344s max response time

### Unified Metrics Group By (✅ PRODUCTION READY)
- All metrics grouped by single dimension
- Independent chart grouping capabilities
- Breakdown tables for entity performance

### Centralized Metrics Filter (✅ PRODUCTION READY)
- Single `metrics_filter` for all metrics
- 48% performance improvement over previous system
- Clean, simplified response structure