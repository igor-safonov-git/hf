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

## Additional Notes

- `@short-spec.md` is a source of thruth for Huntflow api

## Local Data Cache

We now have a local SQLite cache of Huntflow data to avoid API rate limits:

### Download/Update Cache
```bash
python download_huntflow_data.py
```
This downloads all core Huntflow entities into `huntflow_cache.db`:
- Accounts, Vacancies, Applicants (with search data)
- Vacancy statuses, Divisions, Regions, Coworkers
- Rejection reasons, Applicant sources
- Sample of applicant logs (first 100 applicants)

### Query Cache
```python
from query_huntflow_cache import HuntflowCache

cache = HuntflowCache()

# Get all vacancies
vacancies = cache.get_vacancies()

# Get applicants (with limit)
applicants = cache.get_applicants(limit=100)

# Get applicant with their logs
applicant = cache.get_applicant_with_logs(applicant_id=12345)

# Get status distribution
distribution = cache.get_applicant_distribution_by_status()

# Search applicants
results = cache.search_applicants("john.doe@example.com")

# Export to CSV
cache.export_to_csv("applicants", "applicants.csv")
```

### Direct SQL Access
```bash
sqlite3 huntflow_cache.db
```

The cache includes:
- Full JSON data in `raw_data` columns
- Key fields extracted for easy querying
- Metadata tracking when each table was last updated

## Metrics Architecture

### Systematic Metric Naming Convention

All metrics now follow the pattern: `entity.attribute` or `entity_filter` for easier explanation to AI models.

**Base Entity Metrics**
- `applicants_all()` - All applicants data
- `vacancies_all()` - All vacancies data  
- `recruiters_all()` - All recruiters data
- `statuses_all()` - All vacancy statuses data

**Filtered Entity Metrics**
- `vacancies_open()` - Open vacancies only
- `vacancies_closed()` - Closed vacancies only
- `vacancies_last_6_months()` - Recent vacancies (6mo)
- `vacancies_last_year()` - Recent vacancies (1yr)
- `statuses_active()` - Active recruitment stages
- `applicants_hired()` - Hired applicants only

**Aggregation Metrics (entity.by_attribute)**
- `applicants_by_status()` - Real status distribution from logs
- `applicants_by_source()` - Distribution by source
- `applicants_by_recruiter()` - Distribution by recruiter
- `applicants_by_hiring_manager()` - Distribution by hiring manager
- `vacancies_by_state()` - Distribution by state (OPEN/CLOSED/HOLD)
- `vacancies_by_priority()` - Distribution by priority
- `statuses_by_type()` - Distribution by type (user/trash/hired)
- `statuses_list()` - All statuses by name
- `recruiters_by_hirings()` - Recruiters ranked by hiring activity

**Activity Metrics (actions/moves)**
- `actions_by_recruiter()` - Total actions per recruiter
- `actions_by_recruiter_detailed()` - Action breakdown by type
- `moves_by_recruiter()` - Pipeline moves per recruiter
- `moves_by_recruiter_detailed()` - Move breakdown by type
- `applicants_added_by_recruiter()` - New applicants added by recruiter

**Rejection Metrics (simulated)**
- `rejections_by_recruiter()` - Rejection counts by recruiter (simulated)
- `rejections_by_stage()` - Rejection distribution by pipeline stage (simulated)
- `rejections_by_reason()` - Rejection distribution by reason (simulated)

**Conversion Metrics**
- `vacancy_conversion_rates()` - Individual vacancy conversion rates (applicants → hires)
- `vacancy_conversion_summary()` - Overall conversion statistics with top/worst performers
- `vacancy_conversion_by_status()` - Average conversion rates by vacancy status

**Special Collections**
- `status_groups()` - Status group workflows (IT, АУП, Сейлзы, Кассир)

### Legacy Compatibility
All old method names (`get_*`) remain as aliases for backward compatibility.

### Implementation Notes
- **Total metrics available**: 33+ metrics covering all recruitment analytics needs
- **Real data coverage**: 30 metrics use actual database records and logs
- **Simulated metrics**: 3 rejection metrics use intelligent calculations based on real activity patterns
- **Performance**: Local SQLite cache with 1119 log entries enables fast analytics

### Conversion Metrics Details

**Formula**: `conversion_rate = (hires / total_applicants) * 100`

**Key Insights from Real Data**:
- **42 vacancies** have received applicants (tracked via logs)
- **142 total applicants** across all vacancies  
- **9 total hires** (applicants with 'hired' status type)
- **6.3% overall conversion rate** across all vacancies
- **12.6% average conversion rate** (mean of individual vacancy rates)

**Top Performing Patterns**:
- Single-applicant vacancies show 100% conversion when hire occurs
- Sales positions show higher conversion (8.3% for "Менеджер по продажам")
- Technical roles (Java/Kotlin developers) show 0% conversion in current dataset

**Chart Visualization Support**:
- `vacancy_conversion_rates` - Bar chart of all vacancy conversion rates
- `vacancy_conversion_summary` - Top 10 best performing vacancies
- `vacancy_conversion_by_status` - Conversion rates grouped by vacancy status (OPEN/CLOSED)

### Status Change Discovery (BREAKTHROUGH)
**Critical Update**: Status changes DO exist in the API logs!

**Initial Problem**: The `/applicants/search` endpoint doesn't return status fields, and early log analysis showed NULL status_ids.

**Root Cause**: Parsing bug in download script
- Status field contains direct integers (103674, 107602) not objects with .id field  
- Vacancy field also contains direct integers, not objects
- Fixed parsing logic: `log.get("status")` instead of `log.get("status", {}).get("id")`

**Current Status**: Successfully implemented real status tracking
- **1119 total log entries** with proper status_id and vacancy_id fields
- **Real current status distribution**: "Отказ" (22), "Новые" (18), "Резюме у заказчика" (7), etc.
- **Pipeline progression tracking**: Average 8.8 stages per applicant across 80 applicants
- **Real recruiter status changes**: 659 total status change actions across all recruiters

### Updated Metrics Using Real Data
- `get_active_candidates_by_status()` - **NOW USES REAL DATA** from applicant logs
- `get_current_status_distribution()` - Direct from applicant logs  
- `get_recruiter_activity()` - Real recruiter actions and status changes
- `get_applicants_by_source()` - Source data exists but limited coverage

### Rejection Metrics (Still Simulated)
These metrics use calculated distributions based on real recruiter activity data since explicit rejection logs don't exist:
- `get_rejections_by_recruiter()` - Uses role-based rejection rates (evaluators 25%, communicators 15%, etc.)
- `get_rejections_by_stage()` - Pipeline-based distribution (early 40%, mid 35%, late 25%)  
- `get_rejections_by_reason()` - Uses all 26 real rejection reasons from database with realistic weights

## Data Architecture (Updated)
- **Local SQLite cache**: `huntflow_cache.db` with **1119 activity logs** from 23 recruiters
- **Real status transitions**: Logs now properly track status changes with status_id field
- **Real pipeline movement**: STATUS action type represents actual candidate progression
- **Real business insights**: Complete recruiter activity analysis with status change tracking

## Status Groups Implementation
Successfully added status groups endpoint:
- **4 status groups**: IT, АУП, Сейлзы, Кассир workflow categories
- New database table and API endpoint integration
- Chart visualization support for status group distribution

## Absolute Rules
- No mock or test data ever
- Simulated metrics must be clearly marked and based on real data patterns
- Always use actual database records as foundation for calculations

## Debugging Insights
- If a metric constantly returns zeros while working with a prod database, then it's NOT working
- Status change parsing requires direct field access, not object navigation
- API field types can be integers instead of objects - always check both formats