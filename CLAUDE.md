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
# Run all tests with coverage (configured in pytest.ini)
pytest

# Run specific test files from tmp/ directory
pytest tmp/test_comprehensive_e2e.py           # End-to-end tests
pytest tmp/test_reports_with_questions.py      # Report generation tests
pytest tmp/test_performance_restructured.py    # Performance tests

# Run integration and unit tests
pytest tests/integration/                      # Integration tests
pytest tests/unit/                             # Unit tests

# Run with verbose output and coverage
pytest -v --cov=. --cov-report=html
```

### Environment Requirements
```bash
# Required environment variable
export DEEPSEEK_API_KEY="your-api-key"

# Optional for debugging
export DEBUG_MODE=true

# Optional for voice transcription
export OPENAI_API_KEY="your-openai-key"
```

## High-Level Architecture

### Core Data Flow
1. **User Input** → Frontend sends Russian question to `/chat` endpoint
2. **AI Processing** → `prompt.py` (~600 lines) converts natural language to structured JSON via DeepSeek API
3. **Data Filtering** → `EnhancedMetricsCalculator` → `UniversalFilterEngine` applies complex filters
4. **Data Enrichment** → `chart_data_processor.py` adds real data from SQLite cache
5. **Response Generation** → AI creates Russian analytics response with visualizations

### Key Architectural Components

**AI Layer:**
- `prompt.py` - Comprehensive prompt engineering system with 8-step process for JSON generation
- `context_data_injector.py` - Injects dynamic context (recruiters, sources, etc.) into prompts
- Uses DeepSeek API for LLM processing with structured JSON schema validation

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

- **Entities**: applicants, vacancies, hires, recruiters, sources, divisions, hiring_managers, stages, rejections, actions
- **Logical Operators**: AND/OR with nesting, complex operators (in, gt, gte, lt, lte, contains)
- **Time Filtering**: period-based (today, this week, 2 weeks, 1 month, 3 month, 6 month, year)

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

## Critical Development Rules

- **DO NOT EVER DELETE INFORMATION FROM PROMPT UNLESS ASKED TO** - `prompt.py` contains carefully engineered examples and patterns
- **Real Data Only**: Never use mock data - all calculations must use actual Huntflow cached data
- **Russian UI**: All user-facing text (report titles, labels, axis captions) must be in Russian
- **JSON Schema Compliance**: All chart outputs must follow the mandatory schema with proper validation
- **Report Title Format**: Must always include key metrics and time period following Step 8 rules
- **Entity Grouping**: Never group an entity by itself (e.g., hires by "hires" is INVALID)
- **File Structure**: Tests are located in both `tmp/` directory and `tests/` directory - check both locations

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

## Prompt Engineering System

The `prompt.py` file implements an 8-step structured process for converting natural language to analytics JSON:

1. **Determine user intent** - Maps questions to analysis types (pipeline, recruiter effectiveness, etc.)
2. **Choose metric-level filtering** - Applies entity-specific filters consistently across all metrics
3. **Choose main metric** - Selects primary measurement that answers the user's question
4. **Choose secondary metrics** - Adds 2 contextual metrics for comprehensive analysis
5. **Choose chart type** - Selects bar/line/scatter based on analysis pattern
6. **Choose X-axis metric** - Defines horizontal dimension for visualization
7. **Choose Y-axis metric** - Defines vertical measurement for charts
8. **Write report title** - Generates descriptive titles with metrics and time periods

Key features:
- 10 entity types with cross-entity filtering capabilities
- JSON schema validation with mandatory response template
- 8 comprehensive examples covering all major analysis patterns
- Dynamic context injection with real entity names and IDs

## File Structure Notes

### Test Organization
- `tmp/test_*.py` - Legacy test files and experimental tests
- `tests/integration/` - Integration tests for complete workflows
- `tests/unit/` - Unit tests for individual components
- `tests/fixtures/` - Shared test data and fixtures
- `pytest.ini` - Test configuration with coverage settings

### Data Flow Components
- `huntflow_local_client.py` - SQLite database interface
- `huntflow_cache.db` - Local recruitment data cache
- `universal_filter_engine.py` + `universal_filter.py` - Core filtering logic
- `enhanced_metrics_calculator.py` - Metrics computation with filtering
- `chart_data_processor.py` - Data preparation for visualization
- `universal_chart_processor.py` - Chart generation utilities

### SSL Configuration
- `cert.pem` and `key.pem` - HTTPS certificates
- `update_ssl_certs.sh` - Certificate update script
- HTTPS available at https://localhost:8443 when certificates present