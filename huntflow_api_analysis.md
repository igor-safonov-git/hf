# Huntflow API Analysis for HR Analytics

## Authentication
- **Method**: Bearer Token (HTTP Bearer Auth)
- **Header**: `Authorization: Bearer <token>`
- **Token Refresh**: `/token/refresh` endpoint available

## Key Endpoints for HR Analytics

### 1. Applicants/Candidates Endpoints

#### Search and List Applicants
- `GET /accounts/{account_id}/applicants/search`
  - Search applicants with filters
  - Parameters: `q` (query), `field`, `tag`, `status`, `rejection_reason`, `only_current_status`, `vacancy`, `account_source`, `count`, `page`
  - Useful for: Finding candidates by various criteria

- `GET /accounts/{account_id}/applicants/search_by_cursor`
  - Cursor-based pagination for large datasets
  
- `GET /accounts/{account_id}/applicants`
  - List all applicants

#### Individual Applicant Operations
- `GET /accounts/{account_id}/applicants/{applicant_id}`
  - Get detailed applicant information
  
- `GET /accounts/{account_id}/applicants/{applicant_id}/logs`
  - Get activity logs for specific applicant
  - Useful for: Time-to-hire tracking, process analysis

- `GET /accounts/{account_id}/applicants/{applicant_id}/vacancy`
  - Get applicant's vacancy assignment details

### 2. Vacancies Endpoints

#### List and Search Vacancies
- `GET /accounts/{account_id}/vacancies`
  - Parameters: `count`, `page`, `mine`, `opened`, `state`
  - Filter by state (open/closed) and ownership

#### Individual Vacancy Operations
- `GET /accounts/{account_id}/vacancies/{vacancy_id}`
  - Get detailed vacancy information

- `GET /accounts/{account_id}/vacancies/{vacancy_id}/periods`
  - Get vacancy time periods
  - Parameters: `date_begin`, `date_end`
  - **Key for time-to-hire metrics**

- `GET /accounts/{account_id}/vacancies/{vacancy_id}/logs`
  - Get activity logs for specific vacancy
  - Track changes and timeline

#### Vacancy Status Management
- `GET /accounts/{account_id}/vacancies/statuses`
  - Get all recruitment statuses (hiring stages)
  - **Critical for funnel analytics**

- `GET /accounts/{account_id}/vacancies/status_groups`
  - Get status groupings for reporting

### 3. Analytics/Statistics Endpoints

#### Time and Period Analytics
- `GET /accounts/{account_id}/vacancies/{vacancy_id}/periods`
  - Time periods for vacancy lifecycle
  - Filter by date range
  - Essential for time-to-hire calculations

#### Activity Tracking
- `GET /accounts/{account_id}/action_logs`
  - System-wide activity logs
  - Parameters: `type`, `count`, `next_id`, `previous_id`
  - Track user actions and system events

#### Quota and Planning
- `GET /accounts/{account_id}/vacancies/{vacancy_id}/quotas`
  - Hiring quotas and targets
  - Useful for: Plan vs actual analysis

### 4. Additional Useful Endpoints

#### Sources and Attribution
- `GET /accounts/{account_id}/applicants/sources`
  - Candidate source tracking
  - Essential for: Source effectiveness analysis

#### Offers and Conversions
- `GET /accounts/{account_id}/offers`
- `GET /accounts/{account_id}/offers/{offer_id}`
  - Track job offers made
  - Calculate offer-to-acceptance ratios

#### Rejection Tracking
- `GET /accounts/{account_id}/rejection_reasons`
  - Standardized rejection reasons
  - Analyze rejection patterns

## Key Metrics That Can Be Calculated

1. **Time-to-Hire**: Using vacancy periods and applicant logs
2. **Funnel Conversion Rates**: Using vacancy statuses and applicant status transitions
3. **Source Effectiveness**: Using applicant sources endpoint
4. **Offer Acceptance Rate**: Using offers endpoints
5. **Rejection Analysis**: Using rejection reasons and applicant status
6. **Activity Metrics**: Using various log endpoints

## Notable Limitations

- No dedicated analytics/reporting endpoints
- No pre-calculated metrics or dashboards
- Analytics must be computed client-side by aggregating data from various endpoints
- No specific time-to-hire endpoint - must be calculated from periods and logs

## Recommendations for HR Analytics Implementation

1. **Primary Data Sources**:
   - Use applicant search with vacancy filter for funnel data
   - Use vacancy periods for time tracking
   - Use logs endpoints for detailed timeline reconstruction

2. **Caching Strategy**:
   - Cache vacancy statuses (relatively static)
   - Cache rejection reasons and sources
   - Refresh applicant data as needed

3. **Metrics Calculation**:
   - Build client-side aggregation for all metrics
   - Use cursor-based pagination for large datasets
   - Combine multiple endpoints for comprehensive analytics