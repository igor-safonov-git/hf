### **API Summary**

**Common Rules:**
*   All endpoints are prefixed with `/accounts/{account_id}/`.
*   `account_id` (integer, Required) is an implicit path parameter for all endpoints.
*   `(R)` denotes a Required parameter.
*   Parameters listed are query parameters unless otherwise specified.

---

### **Vacancies**
Retrieve data about job openings, their structure, and history.

*   `GET /vacancies` - List all vacancies in the organization.
    *   `count`, `page`: integer - For pagination.
    *   `mine`: boolean - Show only vacancies for the current user.
    *   `state`: array - Filter by vacancy state.
*   `GET /vacancies/additional_fields` - Get the schema for custom vacancy fields.
*   **Path: `/vacancies/{vacancy_id}`**
    *   `GET /` - Retrieve a single vacancy by its ID.
    *   `GET /logs` - Get event logs for a specific vacancy.
        *   `date_begin`, `date_end`: string - Date range.
        *   `count`, `page`: integer - For pagination.
    *   `GET /periods` - Get the work, hold, and closed periods for a vacancy.
        *   `date_begin` (R), `date_end` (R): string - Date range.
    *   `GET /frame` - Get the most recent activity frame for a vacancy.
    *   `GET /frames` - List all historical activity frames for a vacancy.
        *   **Path: `/frames/{frame_id}/quotas`**
            *   `GET /` - Get hiring quotas within a specific historical frame.
    *   `GET /quotas` - List hiring quotas for a vacancy.
        *   `count`, `page`: integer - For pagination.

---

### **Applicants**
Retrieve data about candidates, their resumes, and activity.

*   `GET /applicants` - List all applicants with basic filtering.
    *   `count`, `page`: integer - For pagination.
    *   `status`: integer - Filter by recruitment status ID.
    *   `vacancy`: integer - Filter by Vacancy ID.
    *   `agreement_state`: string - Filter by personal data agreement state.
*   `GET /applicants/search` - Perform a detailed search for applicants with advanced filters.
    *   `q`: string - Search query.
    *   `field`: string - Field to search in.
    *   `tag`, `status`, `rejection_reason`, `vacancy`, `account_source`: array - Filter by various IDs.
    *   `only_current_status`: boolean - Filter by current vs. historical status.
    *   `count`, `page`: integer - For pagination.
*   `GET /applicants/search_by_cursor` - Search applicants using cursor-based pagination for large result sets.
    *   Same filters as `/search`, but uses `next_page_cursor` (string) instead of `page`.
*   `GET /applicants/sources` - Get the list of all possible applicant resume sources.
*   **Path: `/applicants/{applicant_id}`**
    *   `GET /` - Retrieve a single applicant by their ID.
    *   `GET /logs` - Get the activity log (worklog) for a specific applicant.
        *   `type`: array - Filter by log type.
        *   `personal`: boolean - Get only logs not tied to a vacancy.
        *   `vacancy`: integer - Get logs for a specific vacancy.
        *   `count`, `page`: integer - For pagination.
    *   `GET /responses` - List an applicant's responses from job sites.
        *   `count`: integer, `next_page_cursor`: string - For pagination.
    *   `GET /tags` - List all tags assigned to an applicant.
    *   **Path: `/externals/{external_id}`**
        *   `GET /` - Get a specific parsed resume for an applicant.
        *   `GET /pdf` - Download a specific resume as a PDF file.

---

### **Account & Organization**
Retrieve general configuration and dictionary resources for the account.

*   `GET /rejection_reasons` - Get all configured rejection reasons.
*   `GET /vacancies/statuses` - Get all recruitment statuses (hiring stages).
*   `GET /vacancies/status_groups` - Get all recruitment status groups.
*   `GET /divisions` - List all organizational divisions.
    *   `only_available`: boolean - Show only divisions available to the current user.
*   `GET /regions` - List all geographical regions.
*   `GET /tags` - List all tags available in the account.
*   `GET /tags/{tag_id}` - Get a single tag by its ID.
*   `GET /dictionaries` - List all custom dictionaries in the organization.
*   `GET /dictionaries/{dictionary_code}` - Get a specific dictionary by its code.
*   `GET /action_logs` - Get account security (audit) logs.
    *   `type`: array - Filter by log type.
    *   `count`, `next_id`, `previous_id`: integer - For pagination.

---

### **Coworkers**
Retrieve data about users within the account.

*   `GET /coworkers` - List all coworkers in the organization.
    *   `type`, `vacancy_id`: array - Filter by role or vacancy.
    *   `fetch_permissions`: boolean - Include permissions in the response.
    *   `count`, `page`: integer - For pagination.
*   **Path: `/coworkers/{coworker_id}`**
    *   `GET /` - Get a single coworker by their ID.
        *   `vacancy_id`: integer - Filter permissions by a specific vacancy.
    *   `GET /divisions` - Get the list of divisions a specific coworker has access to.