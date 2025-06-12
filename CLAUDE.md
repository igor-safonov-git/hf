# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based chatbot that integrates with the Huntflow recruitment platform API and OpenAI's GPT-4 to provide AI-powered hiring analytics. The app provides real-time visualization of recruitment funnels and candidate statistics through a web interface.

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with actual credentials:
# - HF_TOKEN: Huntflow API token
# - ACC_ID: Huntflow account ID  
# - OPENAI_API_KEY: OpenAI API key
```

### Running the Application
```bash
# Run FastAPI server (development)
python app.py

# Or with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Access the chat interface
# Open http://localhost:8000 in browser
```

### Testing
```bash
# Test imports and environment
./test_app.sh

# Check health endpoint
curl http://localhost:8000/health
```

## Architecture

### Core Components

**HuntflowClient** (`app.py`)
- Manages authentication and API calls to Huntflow recruitment platform
- Auto-handles token refresh (401) and rate limiting (429) with retry logic
- Key endpoints:
  - `/v2/accounts/{acc_id}/vacancies` - Job postings
  - `/v2/accounts/{acc_id}/applicants/search` - Candidate search
  - `/v2/accounts/{acc_id}/vacancy_statuses` - Recruitment stages

**OpenAI Integration**
- Uses GPT-4 with function calling (`tool_choice="required"`)
- Two main tools exposed:
  - `hf_fetch` - Generic Huntflow API endpoint caller
  - `make_chart` - Matplotlib chart generator returning base64 PNG data URIs
- System prompts configure the AI to analyze recruitment data

**Chart Generation**
- `make_chart()` creates bar charts from stage distribution data
- Automatically groups stages into "Other" if more than 7
- Returns charts as base64-encoded data URIs for direct embedding

### Frontend (`index.html`)
- Single-page React app (no build process)
- Uses @assistant-ui/react for chat interface
- Automatic rendering of base64 chart images in responses
- Connects to backend on port 8000

## Key Implementation Details

- Account ID (`ACC_ID`) is automatically injected into API paths via string replacement
- All Huntflow API calls go through `_req()` method for consistent error handling
- Chart images are embedded in markdown as `![Chart](data:image/png;base64,...)`
- Frontend automatically detects and renders base64 images in AI responses
- CORS enabled for browser access from any origin

## Huntflow API Specification

The Huntflow API v2 is designed for integrating corporate systems with the Huntflow recruitment platform.

### Authentication
- **Bearer Token Authentication**: Include `Authorization: Bearer <token>` header
- **Token Lifecycle**: `access_token` (7 days), `refresh_token` (14 days)
- **Token Refresh**: Use `/token/refresh` endpoint when receiving 401 errors
- **Base URL**: `https://api.huntflow.ru/v2`

### Core Entities & Endpoints

#### Account Management
- `GET /accounts` - List available organizations
- `GET /accounts/{account_id}` - Get organization details
- `GET /me` - Current user information

#### Vacancies
- `GET /accounts/{account_id}/vacancies` - List job postings
- `POST /accounts/{account_id}/vacancies` - Create vacancy
- `GET /accounts/{account_id}/vacancies/{vacancy_id}` - Get specific vacancy
- `PUT/PATCH /accounts/{account_id}/vacancies/{vacancy_id}` - Update vacancy
- `GET /accounts/{account_id}/vacancies/statuses` - Get recruitment stages
- `GET /accounts/{account_id}/vacancy_statuses` - Get vacancy statuses (alternative endpoint)

#### Applicants
- `GET /accounts/{account_id}/applicants` - List applicants
- `POST /accounts/{account_id}/applicants` - Create applicant
- `GET /accounts/{account_id}/applicants/search` - Search with pagination (`count`, `page`)
- `GET /accounts/{account_id}/applicants/search_by_cursor` - Cursor-based search
- `GET /accounts/{account_id}/applicants/{applicant_id}` - Get applicant details
- `PATCH /accounts/{account_id}/applicants/{applicant_id}` - Update applicant
- `GET /accounts/{account_id}/applicants/{applicant_id}/logs` - Get activity logs (status changes)
- `POST /accounts/{account_id}/applicants/{applicant_id}/vacancy` - Add to vacancy
- `GET /accounts/{account_id}/applicants/sources` - Get applicant sources

#### Organization Structure
- `GET /accounts/{account_id}/divisions` - Company divisions
- `GET /accounts/{account_id}/regions` - Organization regions
- `GET /accounts/{account_id}/coworkers` - Team members
- `GET /accounts/{account_id}/rejection_reasons` - Rejection reasons

#### Files & CV Processing
- `POST /accounts/{account_id}/upload` - Upload files
- Add `X-File-Parse: true` header to parse CVs and extract structured data

### Key Implementation Notes

#### Status Information Strategy
**Critical**: The `/applicants/search` endpoint does NOT return status fields in applicant objects. To get current applicant status:

1. **Use Logs Approach** (Recommended):
   ```python
   # Get applicant activity logs
   logs = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/{applicant_id}/logs")
   
   # Find most recent status change
   for log_entry in logs.get("items", []):
       if log_entry.get("status"):
           current_status = log_entry.get("status")
           break
   ```

2. **Sample & Scale**: For performance, sample a subset of applicants and extrapolate to full population.

#### API Response Patterns
- **Pagination**: Most endpoints support `count` and `page` parameters
- **Error Handling**: 401 (token expired), 429 (rate limited), standard REST codes
- **Data Format**: JSON request/response, multipart for file uploads

#### Performance Optimization
- **Applicant Status Distribution**: Sample 30 applicants' logs, scale to total population
- **Caching**: Cache applicant lists to reduce API calls from 250+ to ~30
- **Rate Limiting**: Respect `Retry-After` headers on 429 responses

## Common Huntflow API Patterns

```python
# Get all vacancies
await hf_client._req("GET", f"/v2/accounts/{acc_id}/vacancies")

# Search applicants (NOTE: does not include status field)
await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/search", 
                     params={"count": 100, "page": 1})

# Get applicant status via logs
logs = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/{applicant_id}/logs")
current_status = next((log.get("status") for log in logs.get("items", []) if log.get("status")), None)

# Get recruitment stages
await hf_client._req("GET", f"/v2/accounts/{acc_id}/vacancies/statuses")

# Status distribution (sampling approach)
all_applicants = await get_all_applicants()  # Get IDs only
sample_size = min(30, len(all_applicants))
status_counts = {}

for applicant in all_applicants[:sample_size]:
    logs = await hf_client._req("GET", f"/v2/accounts/{acc_id}/applicants/{applicant['id']}/logs")
    status = extract_current_status_from_logs(logs)
    if status:
        status_counts[status] = status_counts.get(status, 0) + 1

# Scale to full population
scale_factor = len(all_applicants) / sample_size
scaled_counts = {k: int(v * scale_factor) for k, v in status_counts.items()}
```

## Error Handling

- HTTP 401: Triggers token refresh attempt
- HTTP 429: Respects Retry-After header with exponential backoff
- Missing env vars: Returns graceful error messages
- API errors: Detailed error info preserved in function call responses