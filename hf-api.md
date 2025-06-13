# Huntflow API Reference

<h1>Welcome!</h1>

<p>Easily build integrations with your corporate systems with Huntflow API:</p>

<ul>
<li><p>Pass vacancy requests from Intranet</p></li>
<li><p>Receive responses from vacancy landings</p></li>
<li><p>Synchronize company organization structure</p></li>
<li><p>Create individual reports</p></li>
<li><p>Connect with Power BI, Tableau, etc. </p></li>
</ul>

<h1>Full changelog</h1>

<p><details></p>

<p><summary>Show changelog</summary></p>

<h1>Changelog v2</h1>

<ul>
<li>No changelog available.</li>
</ul>

<p></details></p>

<h1>Sandbox</h1>

<p>Try out <a href="https://sandbox.huntflow.dev">Huntflow Sandbox</a> – a risk free environment for experimenting and testing developed integrations. </p>

<p>It's free for all Huntflow API customers. </p>

<h1>Getting started with API</h1>

<p>All requests to this API require Bearer token authentication. </p>

<p>Bearer authentication is an <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication">HTTP authentication scheme</a> that involves security tokens called bearer tokens. The name "Bearer authentication" can be understood as "give access to the bearer of this token". The client must send this token in the Authorization header when making requests to protected resources:</p>

<pre><code>Authorization: Bearer &lt;token&gt;</code></pre>

<p>The Bearer authentication scheme was originally created as part of OAuth 2.0 in <a href="https://tools.ietf.org/html/rfc6750">RFC 6750</a>, but is also used on its own.</p>

<p>You can get a token through the corresponding section in the Huntflow settings (Settings → API → Add Token).</p>

<p>Upon adding, you will be given a link for a pair of tokens: <code>access_token</code> and <code>refresh_token</code>.</p>

<p><code>access_token</code> is a Bearer token you should use for making requests to API:</p>

<pre><code>curl \

    -H 'Authorization: Bearer access_token' \

    https://&lt;api domain&gt;/v2/accounts

</code></pre>

<p>The lifetime of the <code>access_token</code> is 7 days. </p>

<p>Upon expiring you will start receiving a 401 HTTP response code for the requests to API with a body <code>{"errors":[{"type":"authorization_error","title":"Authorization Error","detail":"token_expired"}]}</code>. You should handle a pair of keys <code>type</code> and <code>detail</code> for checking token expiration. </p>

<p>In that case you should update and receive a new pair of tokens.</p>

<p>Here comes a <code>refresh_token</code>. The purpose of <code>refresh_token</code> is to update the pair of tokens for the new one after expiration of <code>access_token</code> by the calling a special <a href="/v2/docs#post-/token/refresh">refresh token method</a>:</p>

<pre><code>curl \

    -H 'Content-Type: application/json' \

    -d '{"refresh_token": "refresh_token"}' \

    https://&lt;api domain&gt;/v2/token/refresh

</code></pre>

<p>Keep in mind that <code>refresh_token</code> has its lifetime of 14 days. You will have to generate a new pair of tokens in Huntflow settings in case of the <code>refresh_token</code> won't be used in 14 days. </p>


# Base URL


| URL | Description |
|-----|-------------|
| /v2 |  |


# Authentication



## Security Schemes

| Name              | Type              | Description              | Scheme              | Bearer Format             |
|-------------------|-------------------|--------------------------|---------------------|---------------------------|
| HTTPBearerAuth | http |  | bearer |  |

# APIs

## GET /me

Get information about current user

Returns information about the user associated with the passed authentication




### Responses

#### 200


Successful Response


[MeResponse](#meresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts

Get all available organizations

Returns a list of available organizations for the user associated with the passed authentication




### Responses

#### 200


Successful Response


[OrganizationsListResponse](#organizationslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}

Get information about organization

Returns information about specified organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[OrganizationInfoResponse](#organizationinforesponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /token/refresh

Refresh existing token





### Request Body

[RefreshTokenRequest](#refreshtokenrequest)







### Responses

#### 200


Successful Response


[RefreshTokenResponse](#refreshtokenresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /email_accounts

Get user email accounts

Returns a list of user email accounts.




### Responses

#### 200


Successful Response


[EmailAccountsListResponse](#emailaccountslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /calendar_accounts

Get user calendar accounts

Returns a list of user calendar accounts with associated calendars.




### Responses

#### 200


Successful Response


[CalendarAccountsListResponse](#calendaraccountslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/account_vacancy_requests

Get all vacancy request schemas

Returns a list of vacancy requests schemas available in the organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| only_active | boolean | False | Shows only active schemas |


### Responses

#### 200


Successful Response


[AccountVacancyRequestsListResponse](#accountvacancyrequestslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/account_vacancy_requests/{account_vacancy_request_id}

Get vacancy request schema

Returns the specified vacancy request schema.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| account_vacancy_request_id | integer | True | [Vacancy request schema ID](/v2/docs#get-/accounts/-account_id-/account_vacancy_requests) |


### Responses

#### 200


Successful Response


[AccountVacancyRequestResponse](#accountvacancyrequestresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancy_requests

Get all vacancy requests

Returns a list of vacancy requests.
__________
By default, only vacancy requests that have not been accepted for work will be returned.<br>
Also, you can pass the `vacancy_id` query-parameter with the vacancy ID
to get a list of vacancy requests that were taken to work on the vacancy


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |
| vacancy_id | integer | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies). If supplied, only vacancy requests related to the specified vacancy will be returned |
| values | boolean | False | Show values flag (if supplied, vacancy requests fields will be included) |


### Responses

#### 200


Successful Response


[VacancyRequestListResponse](#vacancyrequestlistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/vacancy_requests

Create a vacancy request

The request body structure depends on
[Vacancy request schemas](/v2/docs#get-/accounts/-account_id-/account_vacancy_requests).

Two options for transferring custom or system dictionary fields are allowed:
 - You can get the custom dictionary
 [here](/v2/docs#get-/accounts/-account_id-/dictionaries/-dictionary_code-),
 and use the dictionary ID in request body. For example:
```
{
    ...,
    "dictionary_field": 42,
    ...
}
```
 - You can use the foreign value specified when creating the dictionary. For example:
```
{
    ...,
    "dictionary_field": {"foreign": "field_foreign_value"},
    ...
}
```


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[VacancyRequestResponse](#vacancyrequestresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancy_requests/{vacancy_request_id}

Get a vacancy request



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_request_id | integer | True | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |


### Responses

#### 200


Successful Response


[VacancyRequestResponse](#vacancyrequestresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/additional_fields

Get organization vacancy's additional fields schema

Returns a schema of additional fields for vacancies set in organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[AdditionalFieldsSchemaResponse](#additionalfieldsschemaresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies

Get all vacancies

Returns a list of vacancies.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |
| mine | boolean | False | Shows only vacancies that the current user is working on |
| opened | boolean | False | Show only open vacancies. This parameter is deprecated, use the state parameter instead |
| state | array | False | The state of a vacancy |


### Responses

#### 200


Successful Response


[VacancyListResponse](#vacancylistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/vacancies

Create a vacancy

Create a vacancy and returns it.
______________________

Restrictions:
- When creating a new vacancy, you cannot specify more than one quota in the fill_quotas list.
- The same [vacancy request](/v2/docs#get-/accounts/-account_id-/vacancy_requests)
cannot be linked more than once (to the same vacancy or to different ones)

______________________
Quotas [(Hiring quotas)](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas)

A vacancy can have one or more hiring quotas.<br>
Hiring quotas link the vacancy, the vacancy request (optional),
the number of people to hire and the deadline for closing the quota.<br>
An arbitrary number of quotas for one vacancy makes it possible to accurately
track the deadlines for closing vacancy requests.<br>
There can be several vacancy requests for the same vacancy,
they can also be added to a vacancy at any time.
One vacancy quota is allowed without specifying an vacancy request.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[VacancyCreateResponse](#vacancycreateresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}

Get a vacancy

Returns a vacancy.
______________________
The response body depends on the vacancy fields schema. You can see this schema
[here](/v2/docs#get-/accounts/-account_id-/vacancies/additional_fields)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Responses

#### 200


Successful Response


[VacancyResponse](#vacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/vacancies/{vacancy_id}

Update a vacancy

Updates a vacancy and returns it.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Request Body









### Responses

#### 200


Successful Response


[VacancyResponse](#vacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PATCH /accounts/{account_id}/vacancies/{vacancy_id}

Partially update a vacancy

Partially updates a vacancy and returns it (only passed request body parameters would be updated).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Request Body









### Responses

#### 200


Successful Response


[VacancyResponse](#vacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/vacancies/{vacancy_id}

Delete a vacancy



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/logs

Get a vacancy's logs

Returns a list of vacancy logs with pagination.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| date_begin | string | False |  |
| date_end | string | False |  |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |


### Responses

#### 200


Successful Response


[VacancyLogsResponse](#vacancylogsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/periods

Get a vacancy periods

Returns the periods of the vacancy.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| date_begin | string | True |  |
| date_end | string | True |  |


### Responses

#### 200


Successful Response


[VacancyPeriodsResponse](#vacancyperiodsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/frame

Get a last vacancy frame

Returns the last frame of a vacancy.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Responses

#### 200


Successful Response


[LastVacancyFrameResponse](#lastvacancyframeresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/frames

Get a list of vacancy frames

Returns the list of vacancy frames.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Responses

#### 200


Successful Response


[VacancyFramesListResponse](#vacancyframeslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/quotas

Get a vacancy quotas

Returns quotas for vacancy.

A vacancy can have one or more fill quotas.
Fill quotas bind vacancies, vacancy requests (optional),
a number of applicants to hire and deadlines to close vacancies.
Selectable number of fill quotas for one vacancy allows to precise
control times of vacancy requests closing.
And at the same time there may be several vacancy requests on one vacancy,
also requests may be attached to the vacancy at any moment.
For a vacancy it's allowed to have one fill quota without a vacancy request.
______________________
Cases:
1. Vacancy is not multivacancy - just select all vacancy's quotas
2. Vacancy is multivacancy - select all children quotas not further than first page,
 otherwise error returned.

______________________
Response format is:
```json
{
    "vacancy_id": {
        "page": 1,
        "count": 5,
        "total": 10,
        "items": [{quota_1}, {quota_2}, ...]
    },
    "another_vacancy_id": {
        ...
    }
}
```


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |


### Responses

#### 200


Successful Response


[VacancyQuotasResponse](#vacancyquotasresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/{vacancy_id}/frames/{frame_id}/quotas

Get a vacancy quotas in frame

Returns quotas for vacancy frame.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| frame_id | integer | True | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |


### Responses

#### 200


Successful Response


[VacancyFrameQuotasResponse](#vacancyframequotasresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/vacancies/{vacancy_id}/members/{account_member_id}

Assign a coworker to a vacancy

Assigns a coworker to a vacancy.
__________
Restrictions:
- To assign a `watcher` to a vacancy, you must specify a permission list with vacancy statuses,
 otherwise a 400 error will be returned.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| account_member_id | integer | True | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |


### Request Body









### Responses

#### 200


Successful Response


[StatusResponse](#statusresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/vacancies/{vacancy_id}/members/{account_member_id}

Remove a coworker from a vacancy



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| account_member_id | integer | True | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/vacancies/{vacancy_id}/state/close

Close vacancy

Changes the vacancy's state to 'CLOSED'.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Request Body









### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/vacancies/{vacancy_id}/state/hold

Hold vacancy

Changes the vacancy's status to 'HOLD'.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Request Body









### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/vacancies/{vacancy_id}/state/resume

Resume vacancy

Changes the vacancy's state to 'OPEN' (for vacancies with 'HOLD' state).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants

Get all applicants

Returns a list of applicants with pagination. This is a simple method that has limited filtering options.
Use [search](/v2/docs#get-/accounts/-account_id-/applicants/search) method for more precise filtering.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |
| status | integer | False | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses)<br>If supplied, then only applicants who are currently in vacancies at the specified status will be returned.<br>Cannot be supplied if the `agreement_state` parameter is passed. |
| vacancy | integer | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies)<br>Used to filter applicants by vacancy. |
| agreement_state |  | False | Agreement's state of applicant to personal data processing.<br>Available if the Personal Data module is enabled for organization.<br>Cannot be supplied if the `status` parameter is passed. |


### Responses

#### 200


Successful Response


[ApplicantListResponse](#applicantlistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/applicants

Create an applicant

Returns the created applicant.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantCreateResponse](#applicantcreateresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







#### 402


Payment Required








## GET /accounts/{account_id}/applicants/{applicant_id}

Get an applicant

Returns the specified applicant.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Responses

#### 200


Successful Response


[ApplicantItem](#applicantitem)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PATCH /accounts/{account_id}/applicants/{applicant_id}

Update an applicant

Partially updates an applicant and returns it.

For example, to update the applicant's firstname only, you can send a request like this:
```json
{"first_name": "John"}
```


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantItem](#applicantitem)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/applicants/{applicant_id}

Delete an applicant



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/search

Search applicants

Returns a list of found applicants. Limited by 20k items.
If you want to get more, use [applicants search by cursor](/v2/docs#get-/accounts/-account_id-/applicants/search_by_cursor)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| q | string | False | Search query |
| field |  | False | Search field |
| tag | array | False | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |
| status | array | False | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| rejection_reason | array | False | 
[Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons). This parameter is applicable only in conjunction with 
`status` parameter, which is set to the rejection status identifier (one with type='trash').
Otherwise it will be ignored.
 |
| only_current_status | boolean | False | If the value is set to `true`, then applicants who are currently at this status will be displayed. Otherwise applicants who have ever been at this status will be displayed |
| vacancy | array | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies)<br>If you pass a `null` value, then applicants who have not been added to any vacancy will be displayed |
| account_source | array | False | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |


### Responses

#### 200


Successful Response


[ApplicantSearchResponse](#applicantsearchresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/search_by_cursor

Search applicants by cursor

Returns a list of found applicants and a cursor to the next page.
To get the next page, you have to copy `next_page_cursor` from the answer and pass it in the request params.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| q | string | False | Search query |
| next_page_cursor | string | False | Next page cursor |
| field |  | False | Search field |
| count | integer | False | Number of items per page |
| tag | array | False | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |
| status | array | False | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| rejection_reason | array | False | 
[Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons). This parameter is applicable only in conjunction with 
`status` parameter, which is set to the rejection status identifier (one with type='trash').
Otherwise it will be ignored.
 |
| only_current_status | boolean | False | If the value is set to `true`, then applicants who are currently at this status will be displayed. Otherwise applicants who have ever been at this status will be displayed |
| vacancy | array | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies)<br>If you pass a `null` value, then applicants who have not been added to any vacancy will be displayed |
| account_source | array | False | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |


### Responses

#### 200


Successful Response


[ApplicantSearchByCursorResponse](#applicantsearchbycursorresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/logs

Get an applicant's worklog

Returns a list of applicant's worklog.

Available log types:
- `COMMENT`: Regular comment
- `ADD`: Applicant created
- `RESPONSE`: Response letter
- `STATUS`: Applicant moved to the [vacancy status](/v2/docs#get-/accounts/-account_id-/vacancies/statuses)
- `VACANCY-ADD`: Applicant applied on the vacancy
- `UPDATE`: Resume updated from another source
- `DOUBLE`: Applicant was merged with another applicant (duplicate)
- `MAIL`: Email
- `AGREEMENT`: Applicant agreement

__________
Restrictions:
- Arguments `vacancy` and `personal` are mutually exclusive.
You must provide only one of them, not both.
Otherwise, a 400 error will be returned.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| type | array | False | Log type |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |
| personal | boolean | False | If supplied, only logs not related to any vacancy will be returned |
| vacancy | integer | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies)<br>If supplied, only logs related to the specified vacancy will be returned |


### Responses

#### 200


Successful Response


[ApplicantLogResponse](#applicantlogresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/applicants/{applicant_id}/logs

Create a worklog note

Adds a log of type `COMMENT` to the applicant's worklog.

Possible log types available [here](/v2/docs#get-/accounts/-account_id-/applicants/-applicant_id-/logs)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[CreateApplicantLogResponse](#createapplicantlogresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/responses

Get an applicant's responses

Returns a list of applicant's responses from job sites.

To get the next page, you have to copy `next_page_cursor`
from the answer and pass it in the request params.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| count | integer | False | Number of items per page |
| next_page_cursor | string | False | Next page cursor |


### Responses

#### 200


Successful Response


[ApplicantResponsesListResponse](#applicantresponseslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/externals/{external_id}

Get an applicant's resume

Returns an applicant resume.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| external_id | integer | True | Resume ID |


### Responses

#### 200


Successful Response


[ApplicantResumeResponse](#applicantresumeresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/applicants/{applicant_id}/externals/{external_id}

Update an applicant's resume

Edits the specified applicant's resume and returns it.
_____________
Restrictions:
- Note that you cannot edit the body of a resume from job boards
- Only one file can be attached to a resume


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| external_id | integer | True | Resume ID |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantResumeResponse](#applicantresumeresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/applicants/{applicant_id}/externals/{external_id}

Delete an applicant's resume

________
Restrictions:
  - Note that you cannot delete the only remaining resume.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| external_id | integer | True | Resume ID |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/externals/{external_id}/pdf

Download an applicant's resume in PDF

Returns a pdf file of the applicant's resume.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| external_id | integer | True | Resume ID |


### Responses

#### 200


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/sources

Get all applicants' resume sources

Returns a list of applicant's resume sources.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[ApplicantSourcesResponse](#applicantsourcesresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/upload

Upload file

To upload a file send a request `multipart/form-data` with a file in parameter `file`.

To make sure that the file will be processed by the system of field recognition, one has to pass a header `X-File-Parse: true`. <br>
In this case the response will contain the fields `text`, `photo`, `fields`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | Organization ID |
| x-file-parse | boolean | False |  |
| x-ignore-lastname | string | False |  |
| x-ignore-email | string | False |  |
| x-ignore-phone | string | False |  |


### Request Body

[Body_upload_file_accounts__account_id__upload_post](#body_upload_file_accounts__account_id__upload_post)







### Responses

#### 200


Successful Response


[UploadResponse](#uploadresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/applicants/{applicant_id}/vacancy

Add an applicant or applicant's response to the vacancy

Attaches an applicant to the vacancy

`Note`: Optionally you can add email message, calendar event, offer, sms or telegram-message


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | string | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) / Response ID |


### Request Body









### Responses

#### 200


Successful Response


[AddApplicantToVacancyResponse](#addapplicanttovacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







#### 402


Payment Required








## PUT /accounts/{account_id}/applicants/{applicant_id}/vacancy

Change a recruitment status for an applicant

Changes a vacancy status for an applicant

`Note`: Optionally you can add email message, calendar event, offer, sms or telegram-message


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[AddApplicantToVacancyResponse](#addapplicanttovacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/applicants/vacancy/{vacancy_id}/split

Move an applicant to a child vacancy

In case the applicant is on the [multivacancy](/v2/docs#tag--Multivacancies),
he can be moved to a child vacancy using this endpoint.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | Organization ID |
| vacancy_id | integer | True | Child vacancy ID |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantVacancySplitResponse](#applicantvacancysplitresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/statuses

Get all recruitment statuses

Returns a list of recruitment statuses (hiring stages).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[VacancyStatusesResponse](#vacancystatusesresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancies/status_groups

Get a list of recruitment status groups

Returns a list of recruitment status groups.
______________________
Recruitment status groups are groups of hiring stages


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[VacancyStatusGroupsResponse](#vacancystatusgroupsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/rejection_reasons

Get all rejection reasons

Returns a list of applicant on vacancy rejection reasons


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[RejectionReasonsListResponse](#rejectionreasonslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/tags

Get all tags

Returns a list of tags in the organization.
____________
Restrictions:
- Users of type `watcher` do not have access to get the list of tags


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[AccountTagsListResponse](#accounttagslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/tags

Create a tag

Creates a new tag in the organization and returns it.
_____________
Restrictions:
- Users of type `watcher` do not have access to create a tag
- Users of type `manager` have access to create a tag only if they have the
`manage-tags` permission.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[AccountTagResponse](#accounttagresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/tags/{tag_id}

Get a tag

Returns the specified tag.
____________
Restrictions:
- Users of type `watcher` do not have access to get the tag


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| tag_id | integer | True | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |


### Responses

#### 200


Successful Response


[AccountTagResponse](#accounttagresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/tags/{tag_id}

Update a tag

Edits the specified tag in the organization and returns it.
_____________
Restrictions:
- Users of type `watcher` do not have access to edit a tag
- Users of type `manager` have access to edit a tag only if they have the
`manage-tags` permission.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| tag_id | integer | True | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |


### Request Body









### Responses

#### 200


Successful Response


[AccountTagResponse](#accounttagresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/tags/{tag_id}

Delete a tag

Deletes the specified tag in the organization.
_____________
Restrictions:
- Users of type `watcher` do not have access to delete a tag
- Users of type `manager` have access to delete a tag only if they have the
`manage-tags` permission.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| tag_id | integer | True | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/tags

Get all applicant's tags

Returns a list of applicant's tags IDs.
_____________
Restrictions:
- Users of type `watcher` do not have access to get applicant's tags


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Responses

#### 200


Successful Response


[ApplicantTagsListResponse](#applicanttagslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/applicants/{applicant_id}/tags

Update applicant's tags

Edits a list of applicant's tags.

This operation overwrites all applicant's tags.
For example: current list of applicant's tags is `{"tags": [1, 2]}`.
- To add a new tag with `ID=3` to the applicant, you should send `{"tags": [1, 2, 3]}`
- To remove an existing applicant's tag with `ID=2`, you should send `{"tags": [1, 3]}`
- To remove all applicant's tags, you should send `{"tags": []}`

_____________
Restrictions:
- Users of type `watcher` cannot edit a list of applicant's tags


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantTagsListResponse](#applicanttagslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/questionary

Get organization applicant's questionary schema

Returns a schema of applicant's questionary for organization.
_________
The successful response may be very different from the example given here
and depends on the settings of the organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[QuestionarySchemaResponse](#questionaryschemaresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/questionary

Get an applicant's questionary

Returns a questionary for the specified applicant.
_________
The successful response depends on the
[questionary schema](/v2/docs#get-/accounts/-account_id-/applicants/questionary).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Responses

#### 200


Successful Response


[QuestionaryResponse](#questionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/applicants/{applicant_id}/questionary

Create an applicant's questionary

Creates the questionary for the specified applicant and returns it.
_________
The successful response depends on the
[questionary schema](/v2/docs#get-/accounts/-account_id-/applicants/questionary).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[QuestionaryResponse](#questionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PATCH /accounts/{account_id}/applicants/{applicant_id}/questionary

Partially update an applicant's questionary

Partially updates (changes only fields that passed with a request) a questionary for the
 specified applicant and returns it.
_________
The successful response depends on the
[questionary schema](/v2/docs#get-/accounts/-account_id-/applicants/questionary).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


### Request Body









### Responses

#### 200


Successful Response


[QuestionaryResponse](#questionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/offers

Get all organization offers

Returns a list of organization's offers.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[AccountOffersListResponse](#accountofferslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/offers/{offer_id}

Get an organization offer with it's schema

Returns an organization's offer with a schema of values.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| offer_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[AccountOfferResponse](#accountofferresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/offers/{offer_id}/pdf

Get an applicant's PDF offer

Returns an applicant offer in PDF format.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| offer_id | integer | True | Offer ID |


### Responses

#### 200


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/applicants/{applicant_id}/offers/{offer_id}

Update an applicant's offer

Updates an applicant's offer.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| offer_id | integer | True | Offer ID |


### Request Body









### Responses

#### 200


Successful Response


[ApplicantVacancyOfferResponse](#applicantvacancyofferresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/applicants/{applicant_id}/vacancy_frames/{vacancy_frame_id}/offer

Get an applicant's vacancy offer

Returns an applicant's offer for vacancy with its values.<br>
The composition of the values depends on the organization's offer settings.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| applicant_id | integer | True | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| vacancy_frame_id | integer | True | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |
| normalize | boolean | False | Expand dictionary values to objects |


### Responses

#### 200


Successful Response


[ApplicantVacancyOfferResponse](#applicantvacancyofferresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/multi-vacancies

Create a multivacancy

Creates a background task to create multivacancy and returns the [Task ID](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[MultiVacancyResponse](#multivacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/multi-vacancies/{vacancy_id}

Update a multivacancy

Creates a background task to edit a multivacancy and returns the [Task ID](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | Multivacancy ID |


### Request Body









### Responses

#### 200


Successful Response


[MultiVacancyResponse](#multivacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PATCH /accounts/{account_id}/multi-vacancies/{vacancy_id}

Partially update a multivacancy

Creates a background task to partially update a multivacancy and returns the [Task ID](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | Multivacancy ID |


### Request Body









### Responses

#### 200


Successful Response


[MultiVacancyResponse](#multivacancyresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/divisions

Get all company divisions

Returns a list of company divisions.
___________
Restrictions:
- Users of type `watcher` can only see their own available divisions


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| only_available | boolean | False | If supplied, then only divisions available to the current user will be returned |


### Responses

#### 200


Successful Response


[DivisionsListResponse](#divisionslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/coworkers/{coworker_id}/divisions

Get company divisions available to the specified user

Returns a list of company divisions available to the specified user.

**Note**: Coworker's company divisions are cached for 10 minutes.
 If a coworker's company divisions list has been changed,
 these changes will be displayed after a maximum of 10 minutes
___________
Restrictions:
- Users of type `watcher` can not see coworker's company divisions


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| coworker_id | integer | True | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |


### Responses

#### 200


Successful Response


[DivisionsListResponse](#divisionslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/divisions/batch

Create or update company divisions

Creates or updates the structure of company divisions.<br>
<span style="color:red">Important</span>: Method requires the full structure of the actual divisions to be passed
_____________
You can add some additional information for each division in the `meta` field.<br>
This endpoint creates a background task for updating the division structure and returns
its identifier.
_____________
Restrictions:
- `name` and `foreign` fields must be with non-zero length
- `foreign` must be unique in the entire structure of the request body
- Maximum nesting of subdivisions - 10
- You cannot create tasks to update the hierarchy of division more than
once every 20 minutes (for the same organization). If an attempt is made
to update divisions before 20 minutes have elapsed since the last
successful request, the server will return an error with HTTP status 429 (Too Many Requests).

If the task to update the divisions is accepted, the response will contains
`payload.task_id` - the unique identifier of the task.
You can track this task [here](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-)


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[BatchDivisionsResponse](#batchdivisionsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







#### 429


Too Many Requests








## GET /accounts/{account_id}/regions

Get all organization regions

Returns a list of organization regions.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[RegionsListResponse](#regionslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/dictionaries

Get all custom dictionaries

Returns a list of organization's custom dictionaries.
_____________
Restrictions:
- This endpoint is only available to users of type `owner`,
otherwise a 403 error will be returned


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[DictionariesListResponse](#dictionarieslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/dictionaries

Create a custom dictionary



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[DictionaryCreateResponse](#dictionarycreateresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/dictionaries/{dictionary_code}

Get a custom dictionary



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| dictionary_code | string | True | Dictionary code |


### Responses

#### 200


Successful Response


[DictionaryResponse](#dictionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/dictionaries/{dictionary_code}

Update a custom dictionary



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| dictionary_code | string | True | Dictionary code |


### Request Body









### Responses

#### 200


Successful Response


[DictionaryUpdateResponse](#dictionaryupdateresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/action_logs

Get all security logs

Returns a list of security logs sorted in descending order (from newest to older).

Possible types:
- `SUCCESS_LOGIN`: Successful login
- `FAILED_LOGIN`: User failed to login
- `LOGOUT`: Sign Out
- `INVITE_ACCEPTED`: Accepting an invitation to the system
- `NEW_AUTH_IN_ACCOUNT`: Adding an additional login to the account (for example,
 linking the HeadHunter account via OAuth2)
- `VACANCY_EXTERNAL`: Actions for posting vacancies on external resources
- `ACCOUNT_MEMBER`: Actions related to changing user permissions
- `DOWNLOAD_APPLICANTS`: Actions related to the bulk download of candidates (from the search, stop list and etc.)
- `PASSWORD_CHANGE`: Actions related to password changing

Pagination is implemented using the `next_id` and `previous_id` parameters.<br>
If the response body contains the `next_id` field, and you need to get older logs,
supply its value as query-parameter.

To get logs that are newer than a particular log,
you need to supply this particular log ID as `previous_id` query-parameter
__________
Restrictions:
- Users of types `manager` and `watcher` do not have access to get security logs


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| type | array | False | Security log type |
| count | integer | False | Number of items per page |
| next_id | integer | False | Security logs with IDs less than or equal to the specified one will be received |
| previous_id | integer | False | Security logs with IDs strictly greater than the specified one will be received |


### Responses

#### 200


Successful Response


[ActionLogsResponse](#actionlogsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/delayed_tasks/{task_id}

Get status of a system delayed task



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| task_id | string | True | Task ID |


### Responses

#### 200


Successful Response


[DelayedTask](#delayedtask)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/hooks

Get all webhooks



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| webhook_type |  | False | Webhook type<br>If no value provided, webhooks of all types will be returned |


### Responses

#### 200


Successful Response


[WebhooksListResponse](#webhookslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/hooks

Create a webhook



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[WebhookResponse](#webhookresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/hooks/{webhook_id}

Delete a webhook



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| webhook_id | integer | True | [Webhook ID](/v2/docs#get-/accounts/-account_id-/hooks) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /production_calendars

Get all production calendars

Returns a list of production calendars




### Responses

#### 200


Successful Response


[CalendarListResponse](#calendarlistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /production_calendars/{calendar_id}

Get a production calendar

Returns a production calendar


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |


### Responses

#### 200


Successful Response


[CalendarResponse](#calendarresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /production_calendars/{calendar_id}/days/{deadline}

Get non-working days in a given period

Returns the total number of non-working\working days and a list of weekends and holidays within a range


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |
| deadline | string | True | Deadline date |
| start | string | False | A date to start counting of non-working days. Default is today |
| verbose | boolean | False | Extends the response with the items field — list of dates, weekends and holidays within given range; in YYYY-MM-DD format |


### Responses

#### 200


Successful Response


[NonWorkingDaysResponse](#nonworkingdaysresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /production_calendars/{calendar_id}/days

Get non-working days for multiple periods

Returns a list of objects with the total number of non-working / working days for the specified periods.
Objects do not contain verbose information, as if you were making a single request


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |


### Request Body









### Responses

#### 200


Successful Response


[NonWorkingDaysBulkResponse](#nonworkingdaysbulkresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /production_calendars/{calendar_id}/deadline/{days}

Get a deadline date evaluation taking into account the non-working days

Returns a deadline after {days} working days


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |
| days | integer | True | Working days amount |
| start | string | False | A date to start counting. Default is today |


### Responses

#### 200


Successful Response


string







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /production_calendars/{calendar_id}/deadline

Get multiple deadline dates evaluation taking into account the non-working days

Returns a list of deadlines


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |


### Request Body









### Responses

#### 200


Successful Response


[DeadLineDatesBulkResponse](#deadlinedatesbulkresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /production_calendars/{calendar_id}/start/{days}

Get a start date evaluation taking into account the non-working days

Returns a date in {days} working days ahead, according to {calendar_id} production calendar.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |
| days | integer | True | Working days amount |
| deadline | string | False | A date to start reverse counting. Default is today |


### Responses

#### 200


Successful Response


string







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /production_calendars/{calendar_id}/start

Get a list of start dates evaluation taking into account the non-working days

Returns a list of start dates


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| calendar_id | integer | True | Calendar ID |


### Request Body









### Responses

#### 200


Successful Response


[DeadLineDatesBulkResponse](#deadlinedatesbulkresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/calendar

Get organization's production calendar



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[AccountCalendar](#accountcalendar)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/coworkers

Get all coworkers

Returns a list of coworkers with pagination.
______________

Restrictions:
- Users of type `watcher` can only see coworkers who are on the same vacancies with them.
Coworker permissions are not available for users of this type.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| type | array | False | Coworker type. Used to filter coworkers by their type (role). If not supplied, then coworkers of all types will be returned. |
| fetch_permissions | boolean | False | Flag for returning coworker's permissions. If supplied, then all coworkers will contain a list of their permissions. |
| vacancy_id | array | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies). Used to filter coworkers by vacancies. If supplied, a list of coworkers working on the specified vacancies will be returned. |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |


### Responses

#### 200


Successful Response


[CoworkersListResponse](#coworkerslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/coworkers/{coworker_id}

Get a coworker

Returns the specified coworker with a list of their permissions.
______________
Restrictions:
- Users of type `watcher` cannot see coworker detail information.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| coworker_id | integer | True | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |
| vacancy_id | integer | False | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies). Used to filter permissions by vacancy. If supplied, then the list of permissions will only contain permissions for the specified vacancy. |


### Responses

#### 200


Successful Response


[CoworkerResponse](#coworkerresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/mail/templates

Get all email templates

Returns a list of email templates.
______________
Restrictions:
- Users of type `watcher` do not have access to the list of email templates


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| editable | boolean | False | Pass `true` if the method should return only templates that the current user can edit |


### Responses

#### 200


Successful Response


[MailTemplatesResponse](#mailtemplatesresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancy_close_reasons

Get all vacancy close reasons

Returns a list of vacancy close reasons


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[CloseHoldReasonsListResponse](#closeholdreasonslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/vacancy_hold_reasons

Get all vacancy hold reasons

Returns a list of vacancy hold reasons


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[CloseHoldReasonsListResponse](#closeholdreasonslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/interview_types

Get all interview types

Returns a list of interview types


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Responses

#### 200


Successful Response


[InterviewTypesListResponse](#interviewtypeslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/users/{user_id}

Get a user

Returns the specified user with a list of his permissions.
______________
Restrictions:
- Users of type `watcher` cannot see other users detail information.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| user_id | integer | True | User id |


### Responses

#### 200


Successful Response


[UserResponse](#userresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/users/foreign/task/{task_id}

Get foreign user control task result

Returns users management task handling result.
All user identifiers in response are foreign.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| task_id | string | True | Task ID |


### Responses

#### 200


Successful Response


[UserControlTaskResponse](#usercontroltaskresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/users/foreign

Get a list of all users with their foreign identifiers

Returns all users in organization with
their permissions (vacancies permissions are not included),
 available divisions and their manager's identifiers.
All identifiers in response are foreign.
______________
Restrictions:
- Divisions and managers fields available when this service kinds are active.
- `null` in permissions or/and divisions fields means "all".


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| member_types | array | False | Member types |
| count | integer | False | Number of items per page |
| page | integer | False | Page number |


### Responses

#### 200


Successful Response


[ForeignUsersListResponse](#foreignuserslistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/users/foreign

Create new user

Schedules a task to create a new user and returns the task's data.
You can track this task [here](/v2/docs#get-/accounts/-account_id-/users/foreign/task/-task_id-).
You can get created user [here](/v2/docs#get-/accounts/-account_id-/users/foreign/-foreign_user_id-).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 202


Successful Response


[CreatedUserControlTaskResponse](#createdusercontroltaskresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/users/foreign/{foreign_user_id}/id

Get internal ID of an existing user by his foreign identifier

Returns internal ID of the specified user.
Request user's identifier is foreign, response user's identifier is internal.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| foreign_user_id | string | True | Foreign ID of User |


### Responses

#### 200


Successful Response


[UserId](#userid)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/users/foreign/{foreign_user_id}

Get an existing user by his foreign identifier

Returns the specified user with his permissions,
available divisions and his manager's identificators.
All identifiers in request and response are foreign.
______________
Restrictions:
- Divisions and managers fields available when these service kinds are active.
- `null` in permissions or/and divisions fields means "all".


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| foreign_user_id | string | True | Foreign ID of User |


### Responses

#### 200


Successful Response


[ForeignUserResponse](#foreignuserresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## PUT /accounts/{account_id}/users/foreign/{foreign_user_id}

Update existing user

Schedules a task to update existing user and returns the task's data.
You can track this task [here](/v2/docs#get-/accounts/-account_id-/users/foreign/task/-task_id-).
You can get updated user [here](/v2/docs#get-/accounts/-account_id-/users/foreign/-foreign_user_id-).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| foreign_user_id | string | True | Foreign ID of User |


### Request Body









### Responses

#### 202


Successful Response


[CreatedUserControlTaskResponse](#createdusercontroltaskresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/users/foreign/{foreign_user_id}

Delete existing user by his foreign identifier

Schedules task to delete user and returns the task's data.
You can track this task [here](/v2/docs#get-/accounts/-account_id-/users/foreign/task/-task_id-).


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| foreign_user_id | string | True | Foreign ID of User |


### Responses

#### 202


Successful Response


[CreatedUserControlTaskResponse](#createdusercontroltaskresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_a

Get all applicant feedback form schemas

Returns all applicant feedback form schemas in organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| active | boolean | True | Shows either active or archived forms |


### Responses

#### 200


Successful Response


[SurveySchemasTypeAListResponse](#surveyschemastypealistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_a/{survey_id}

Get an applicant feedback form schema

Returns an applicant feedback form schema.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| survey_id | integer | True | Survey ID |


### Responses

#### 200


Successful Response


[SurveySchemaTypeAResponse](#surveyschematypearesponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_a/{survey_id}/answers/{answer_id}

Get an answer of applicant feedback form by ID

Returns answer of applicant feedback form.
Each key in `data` represents a question in the survey form.
Schema properties can be used to find information about the question by key.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| survey_id | integer | True | [Survey of type A ID](/v2/docs#get-/accounts/-account_id-/surveys/type_a/-survey_id-) |
| answer_id | integer | True | [Survey answer of type A ID](/v2/docs#get-/accounts/-account_id-/surveys/type_a/-survey_id-/answers/-answer_id-) |


### Responses

#### 200


Successful Response


[SurveyAnswerTypeAResponse](#surveyanswertypearesponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_q

Get all survey questionary schemas for applicants

Returns all survey questionary schemas for applicants for organization.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| active | boolean | False | Shows only active schemas |


### Responses

#### 200


Successful Response


[SurveySchemasTypeQListResponse](#surveyschemastypeqlistresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_q/{survey_id}

Get survey questionary schema for applicants

Returns survey questionary schema for applicants.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| survey_id | integer | True | Survey ID |


### Responses

#### 200


Successful Response


[SurveySchemaTypeQResponse](#surveyschematypeqresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## POST /accounts/{account_id}/surveys/type_q/questionaries

Create survey questionary for applicant

Creates survey questionary.

For proper questionary creation a log must be created with survey questionary attached by
[create a worklog note](/v2/docs#post-/accounts/-account_id-/applicants/-applicant_id-/logs)
method.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |


### Request Body









### Responses

#### 200


Successful Response


[SurveyQuestionaryResponse](#surveyquestionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_q/questionaries/{questionary_id}

Get survey questionary for applicant by ID

Returns survey questionary.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| questionary_id | integer | True | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |


### Responses

#### 200


Successful Response


[SurveyQuestionaryResponse](#surveyquestionaryresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## DELETE /accounts/{account_id}/surveys/type_q/questionaries/{questionary_id}

Delete survey questionary for applicant by ID

Deletes survey questionary.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| questionary_id | integer | True | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |


### Responses

#### 204


Successful Response




#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/surveys/type_q/answers/{answer_id}

Get survey questionary answer by ID

Returns survey questionary answer.
Each key in `data` represents a question in the survey form.
Schema properties can be used to find information about the question by key.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| answer_id | integer | True | [Survey questionary answer ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/answers/-answer_id-) |


### Responses

#### 200


Successful Response


[SurveyQuestionaryAnswerResponse](#surveyquestionaryanswerresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







## GET /accounts/{account_id}/recommendations/{vacancy_id}

Get a list of applicants recommended for a vacancy



### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_id | integer | True | [Organization ID](/v2/docs#get-/accounts) |
| vacancy_id | integer | True | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| count | integer | False | Number of items per page |
| next_page_cursor | string | False | Next page cursor |
| processing_status |  | False | Get all recommendations or processed\unprocessed only |


### Responses

#### 200


Successful Response


[VacancyRecommendationsResponse](#vacancyrecommendationsresponse)







#### 400


Bad Request


[ErrorResponse](#errorresponse)







# Components



## AcceptorInfo



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) who accepted the vacancy request |
| name | string | Name of coworker who accepted the vacancy request |
| email | string | Email of coworker who accepted the vacancy request |


## Account



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Account ID |
| name | string | Account name |
| email | string | Account email |
| account_type | string | Account type |
| last_action | string | When was last action in account |
| created | string | When account created |
| locale | string | Account locale |
| photo | string | Photo file |
| source | string | Source |
| phone | string | Phone number |
| nick | string | Account nick |
| meta |  | Additional info |
| production_calendar | integer | Production calendar ID |
| active | boolean | Is active |
| position | string | Position |
| crm | integer | CRM |


## AccountCalendar



| Field | Type | Description |
|-------|------|-------------|
| account | integer | Organization ID |
| production_calendar | integer | Calendar ID |


## AccountInfo



| Field | Type | Description |
|-------|------|-------------|
| id | integer | ID of the user who opened the quota |
| name | string | Name of the user who opened the quota |
| email | string | Email of the user who opened the quota |


## AccountOffer



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Offer ID |
| name | string | Offer name |
| active | boolean | Offer activity flag |
| template | string | HTML template |


## AccountOfferResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Offer ID |
| name | string | Offer name |
| active | boolean | Offer activity flag |
| template | string | HTML template |
| schema | object | Values schema |


## AccountOffersListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of organization offers |


## AccountTagResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Tag ID |
| name | string | Tag name |
| color | string | Tag color (HEX format) |


## AccountTagsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## AccountVacancyRequestResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Schema ID |
| account | integer | Organization ID |
| name | string | Schema name |
| attendee_required | boolean | The flag of the presence of the 'Send for approval' field when creating an application (null - no field, false — optional field, true — required field) |
| attendee_hint | string | Hint under the field 'Send for approval' |
| active | boolean | Schema activity flag |
| schema |  | Description of schema fields |


## AccountVacancyRequestSchema





## AccountVacancyRequestSchemaField



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Field ID |
| type |  | Field type |
| title | string | Field title |
| required | boolean | Field required flag |
| order | integer | The order of the field on the form |
| values | array | List of possible values (for fields with `select` type) |
| value | string | Default value |
| fields | object | Nested fields |


## AccountVacancyRequestsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## ActionLog



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Action log ID |
| user |  | User who performed the action |
| log_type |  | Action log type |
| created | string | Date and time of creating an action log |
| action | string | Action |
| ipv4 | string | IP address |
| data | object | Action data |


## ActionLogType


An enumeration.




## ActionLogsResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |
| next_id | integer | The next action log ID |


## AddApplicantToVacancyRequest



| Field | Type | Description |
|-------|------|-------------|
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| comment | string | Comment text |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons)<br>The reason of the rejection (if the status is 'rejected') |
| fill_quota | integer | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) (if the status is 'hired') |
| employment_date | string | Employment date (if the status is 'hired') |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>The list of file's ID attached to the log |
| calendar_event |  | Calendar event object |
| email |  | Email object |
| im | array | Telegram message |
| sms |  | SMS message |
| applicant_offer |  | Applicant's offer |
| survey_questionary_id | integer | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |


## AddApplicantToVacancyResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Binding ID |
| changed | string | The date of recruitment stage change |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons) |


## Additional



| Field | Type | Description |
|-------|------|-------------|
| name | string | Name of additional info |
| description | string | Description of additional info |


## AdditionalFieldsSchemaResponse





## AgreementState


An enumeration.




## ApplicantAgreement



| Field | Type | Description |
|-------|------|-------------|
| state |  | Agreement's state of applicant to personal data processing |
| decision_date | string | Date of applicant's decision to personal data processing |


## ApplicantCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| money | string | Salary expectation |
| phone | string | Phone number |
| email | string | Email address |
| skype | string | Skype login |
| position | string | Applicant’s occupation |
| company | string | Applicant’s place of work |
| photo | integer | Applicant’s photo ID |
| birthday | string | Date of birth |
| externals | array | List of applicant's resumes |
| social | array | List of applicant's social accounts |


## ApplicantCreateResponse



| Field | Type | Description |
|-------|------|-------------|
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| money | string | Salary expectation |
| phone | string | Phone number |
| email | string | Email address |
| skype | string | Skype login |
| position | string | Applicant’s occupation |
| company | string | Applicant’s place of work |
| photo | integer | Applicant’s photo ID |
| id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| created | string | Date and time of adding an applicant |
| birthday | string | Date of birth |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>The list of file's ID attached to the applicant |
| doubles | array | List of duplicates |
| agreement |  | Agreement's state of applicant to personal data processing |
| external | array | Applicant's resume |
| social | array | List of applicant's social accounts |
| reindex_job_id | string |  |


## ApplicantDouble



| Field | Type | Description |
|-------|------|-------------|
| double | integer | The ID of a duplicated applicant |


## ApplicantEvent



| Field | Type | Description |
|-------|------|-------------|
| private | boolean | Event private flag |
| name | string | Event name |
| reminders | array | List of reminders <a href=https://tools.ietf.org/html/rfc5545>RFC 5545</a> |
| location | string | Event location |
| interview_type | integer | Interview type ID |
| event_type |  | Calendar event type |
| description | string | Event description (comment) |
| calendar | integer | [Calendar ID](/v2/docs#get-/calendar_accounts) |
| attendees | array | Event attendees (participants) |
| start | string | Event start date |
| end | string | Event end date |
| timezone | string | Time zone |
| transparency |  | Event transparency (availability) |


## ApplicantItem



| Field | Type | Description |
|-------|------|-------------|
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| money | string | Salary expectation |
| phone | string | Phone number |
| email |  | Email address |
| skype | string | Skype login |
| position | string | Applicant’s occupation |
| company | string | Applicant’s place of work |
| photo | integer | Applicant’s photo ID |
| id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| account | integer | [Organization ID](/v2/docs#get-/accounts) |
| photo_url | string | A link to an applicant’s photo |
| birthday | string | Date of birth |
| created | string | Date and time of adding an applicant |
| tags | array | List of tags |
| links | array | Applicant's vacancies |
| external | array | Applicant's resume |
| agreement |  | Agreement's state of applicant to personal data processing |
| doubles | array | List of duplicates |
| social | array | List of applicant's social accounts |


## ApplicantLink



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Link ID |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| updated | string | The date of the applicant's update at a vacancy |
| changed | string | The date of the latest changes at the current recruitment stage |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


## ApplicantListResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array | List of applicants |


## ApplicantLogAccountInfo



| Field | Type | Description |
|-------|------|-------------|
| id | integer | ID of the user who created the log |
| name | string | Name of the user who created the log |


## ApplicantLogEmail



| Field | Type | Description |
|-------|------|-------------|
| account_email | integer | [Email account ID](/v2/docs#get-/email_accounts) |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>List of uploaded files ID |
| followups | array | Followups list. You can get all available followups here - [List of email templates](/v2/docs#get-/accounts/-account_id-/mail/templates) |
| html | string | Email content (HTML) |
| email | string | Recipient email address |
| subject | string | Email subject |
| send_at | string | Date and time to send email. If not supplied, email will be sent immediately |
| timezone | string | Time zone |
| to | array | List of additional recipients (cc/bcc) |
| reply | integer | Reply email ID |


## ApplicantLogEmailResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Email ID |
| created | string | Date and time of creating email |
| subject | string | Email subject |
| email_thread | integer | Email thread ID |
| account_email | integer | [Email account ID](/v2/docs#get-/email_accounts) |
| files | array | List of uploaded files ID |
| foreign | string | Foreign email ID |
| timezone | string | Time zone |
| html | string | Email content (HTML) |
| from_email | string | Sender email address |
| from_name | string | Sender name |
| replyto | array | List of email foreign IDs, to which a reply is send |
| send_at | string | Date and time to send email |
| to | array | Recipients list |
| state | string | Email state |


## ApplicantLogIm



| Field | Type | Description |
|-------|------|-------------|
| account_im | integer | Account IM ID |
| receiver | string | Username or phone of recipient |
| body | string | Message text |


## ApplicantLogItem



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Log ID |
| type |  | Log type |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| source | string | Source ID |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons) |
| created | string | Date and time of creation of the log |
| employment_date | string | Employment date |
| account_info |  | The user who created the log |
| comment | string | Comment text |
| files | array | List of files attached to the log |
| calendar_event |  | Calendar event |
| hired_in_fill_quota |  | Quota data by which applicant was hired |
| applicant_offer |  | Applicant's offer |
| email |  | Email object |
| survey_questionary |  | [Survey Questionary](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries) |
| survey_answer_of_type_a |  | [Survey answer of type A ID](/v2/docs#get-/accounts/-account_id-/surveys/type_a/-survey_id-/answers/-answer_id-) |


## ApplicantLogResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array | List of applicant's logs |


## ApplicantLogSms



| Field | Type | Description |
|-------|------|-------------|
| phone | string | Phone number of recipient |
| body | string | Message text |


## ApplicantLogSurveyAnswerTypeA



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Survey answer of type A ID](/v2/docs#get-/accounts/-account_id-/surveys/type_a/-survey_id-/answers/-answer_id-) |
| created | string | Date and time of creating an survey answer of type A |
| respondent |  | Who created the survey answer |
| survey |  | Survey schema |


## ApplicantLogSurveyQuestionary



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |
| survey |  | Survey schema |
| survey_answer_id | integer | [Survey questionary answer ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/answers/-answer_id-) |
| created | string | Date and time of creating an survey questionary |


## ApplicantLogType


An enumeration.




## ApplicantResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Response ID |
| foreign | string | Foreign response ID (from job site) |
| created | string | Date and time of response creation |
| applicant_external | integer | [Applicant resume ID](/v2/docs#get-/accounts/-account_id-/applicants/-applicant_id-/externals/-external_id-) |
| vacancy |  | Vacancy |
| vacancy_external |  | Publication of a vacancy for which an applicant responded |


## ApplicantResponseVacancy



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| position | string | The name of the vacancy (occupation) |


## ApplicantResponseVacancyExternal



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Publication ID |
| foreign | string | Foreign publication ID (from job site) |


## ApplicantResponsesListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of applicant's responses |
| next_page_cursor | string |  |


## ApplicantResume



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Resume ID |
| auth_type | string | The format of resume |
| account_source | integer | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |
| updated | string | The date and time of resume update |


## ApplicantResumeCreate



| Field | Type | Description |
|-------|------|-------------|
| auth_type | string | Auth type |
| account_source | integer | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |
| data |  | Resume data |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>List of file's ID attached to the applicant resume |


## ApplicantResumeData



| Field | Type | Description |
|-------|------|-------------|
| body | string | Resume text |


## ApplicantResumeResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Resume ID |
| auth_type | string | The format of resume |
| account_source | integer | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |
| updated | string | The date and time of resume update |
| created | string | The date and time of resume create |
| files | array | List of files |
| source_url | string | Link to resume source |
| foreign | string | Foreign resume ID |
| key | string | Resume key |
| portfolio | array | Portfolio images |
| data |  | Raw resume data (format depends on auth_type) |
| resume |  | Resume data in unified format |


## ApplicantResumeUpdateData



| Field | Type | Description |
|-------|------|-------------|
| body | string | Resume text |


## ApplicantResumeUpdateRequest



| Field | Type | Description |
|-------|------|-------------|
| account_source | integer | [Resume source ID](/v2/docs#get-/accounts/-account_id-/applicants/sources) |
| data |  | Resume data |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>List of file's ID attached to the applicant resume |


## ApplicantSearchByCursorResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of applicants |
| next_page_cursor | string | Next page cursor |


## ApplicantSearchField


An enumeration.




## ApplicantSearchItem



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| birthday | string | Date of birth |
| phone | string | Phone number |
| skype | string | Skype login |
| email |  | Email address |
| money | string | Salary expectation |
| position | string | Candidate’s occupation |
| company | string | Candidate’s place of work |
| photo | integer | Candidate’s photo ID |
| photo_url | string | A link to a candidate’s photo |
| created | string | Date and time of adding a candidate |


## ApplicantSearchItemWithOrder



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| birthday | string | Date of birth |
| phone | string | Phone number |
| skype | string | Skype login |
| email |  | Email address |
| money | string | Salary expectation |
| position | string | Candidate’s occupation |
| company | string | Candidate’s place of work |
| photo | integer | Candidate’s photo ID |
| photo_url | string | A link to a candidate’s photo |
| created | string | Date and time of adding a candidate |
| order | integer | Order number |


## ApplicantSearchResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array | List of applicants |


## ApplicantSource



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Applicant source ID |
| foreign | string | Applicant source foreign |
| name | string | Applicant source name |
| type | string | Applicant source type |


## ApplicantSourcesResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of applicant's sources |


## ApplicantTag



| Field | Type | Description |
|-------|------|-------------|
| tag | integer | [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |
| id | integer | [Applicant's tag ID](/v2/docs#get-/accounts/-account_id-/applicants/-applicant_id-/tags) |


## ApplicantTagsListResponse



| Field | Type | Description |
|-------|------|-------------|
| tags | array | List of [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |


## ApplicantUpdateRequest



| Field | Type | Description |
|-------|------|-------------|
| first_name | string | First name |
| last_name | string | Last name |
| middle_name | string | Middle name |
| money | string | Salary expectation |
| phone | string | Phone number |
| email | string | Email address |
| skype | string | Skype login |
| position | string | Applicant’s occupation |
| company | string | Applicant’s place of work |
| photo | integer | Applicant’s photo ID |
| birthday | string | Date of birth |
| social | array | List of applicant's social accounts |


## ApplicantVacancyOffer



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Offer ID |
| account_applicant_offer | integer | Organization's offer ID |
| created | string | Date and time of creating an offer |


## ApplicantVacancyOfferResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Offer ID |
| account_applicant_offer | integer | Organization's offer ID |
| created | string | Date and time of creating an offer |
| values | object | Offer values (fields). The composition of the values depends on the organization's offer settings. |


## ApplicantVacancySplitRequest



| Field | Type | Description |
|-------|------|-------------|
| applicant | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| fill_quota | integer | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| employment_date | string | Employment date |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons) for trash status |


## ApplicantVacancySplitResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Applicant log ID |
| applicant | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| vacancy | integer | Child vacancy ID |
| vacancy_parent | integer | Parent vacancy ID |


## Area



| Field | Type | Description |
|-------|------|-------------|
| country |  | Country |
| city |  | City |
| metro |  | Metro station |
| address | string | Full address |
| lat | number | Latitude |
| lng | number | Longitude |


## Attestation



| Field | Type | Description |
|-------|------|-------------|
| date |  |  |
| name | string |  |
| organization | string |  |
| description | string |  |
| result | string |  |


## BaseEducationInfo



| Field | Type | Description |
|-------|------|-------------|
| name | string | Education name |
| description | string | Education description |
| date_from |  | Education start date |
| date_to |  | Education end date |
| area |  | Education area |


## BaseSurveySchemaType



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey ID |
| name | string | Survey name |
| type |  | Type of survey |
| active | boolean | Is survey active? |
| created | string | Date and time of creating a survey |
| updated | string | Date and time of the last update of the survey |


## BatchDivisionsMeta



| Field | Type | Description |
|-------|------|-------------|
| data | object | Request body content |
| account_id | integer | [Organization ID](/v2/docs#get-/accounts) |


## BatchDivisionsPayload



| Field | Type | Description |
|-------|------|-------------|
| task_id | string | [Task ID](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-) |


## BatchDivisionsRequest



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## BatchDivisionsResponse



| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| payload |  |  |
| meta |  |  |


## Birthdate



| Field | Type | Description |
|-------|------|-------------|
| year | integer | Year |
| month | integer | Month |
| day | integer | Day |
| precision | string | Precision of the date. Can be represented by values: year (2000) | month (2000-07) | day (2000-10-07) |


## Body_upload_file_accounts__account_id__upload_post



| Field | Type | Description |
|-------|------|-------------|
| file | string |  |
| preset | string |  |


## Calendar



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Calendar ID |
| foreign | string | Foreign value |
| name | string | Calendar name |
| access_role | string | Role |


## CalendarAccount



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Calendar account ID |
| name | string | Calendar account name |
| auth_type | string | Authentication type |
| freebusy | boolean |  |
| calendars | array | List of calendars associated with the account |


## CalendarAccountsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of connected calendar accounts |


## CalendarEventCreator



| Field | Type | Description |
|-------|------|-------------|
| displayName | string | Event creator name |
| email | string | Event creator email |
| self | boolean | Flag indicating that you are the creator of the event |


## CalendarEventReminderMethod


An enumeration.




## CalendarEventStatus


An enumeration.




## CalendarEventType


An enumeration.




## CalendarListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of available production calendars |


## CalendarResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Calendar ID |
| name | string | Calendar name |


## Certificate



| Field | Type | Description |
|-------|------|-------------|
| name | string | Name of certificate |
| organization | string | The organization that issued the certificate |
| description | string | Certificate description |
| url | string | Certificate url |
| area |  | Area of issue of the certificate |
| date |  | Date of issue of the certificate |


## ChangeVacancyApplicantStatusRequest



| Field | Type | Description |
|-------|------|-------------|
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| comment | string | Comment text |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons)<br>The reason of the rejection (if the status is 'rejected') |
| fill_quota | integer | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) (if the status is 'hired') |
| employment_date | string | Employment date (if the status is 'hired') |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>The list of file's ID attached to the log |
| applicant_offer |  | Applicant's offer |
| calendar_event |  | Calendar event object |
| email |  | Email object |
| im | array | Telegram message |
| sms |  | SMS message |
| survey_questionary_id | integer | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |


## CloseHoldReason



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Reason ID |
| name | string | Reason name |


## CloseHoldReasonsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## Contact



| Field | Type | Description |
|-------|------|-------------|
| type |  | Contact type |
| value | string | Contact value |
| preferred | boolean | This is the preferred method of communication |
| full_value |  | If contact is a phone number - additional data about it |


## ContactFullValue



| Field | Type | Description |
|-------|------|-------------|
| country | string |  |
| city | string |  |
| number | string |  |
| formatted | string |  |


## CoworkerResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Coworker ID |
| member | integer | User ID |
| name | string | Coworker name |
| type | string | Coworker type (role) |
| head | integer | Head user ID |
| email | string | Email |
| meta | object | Additional meta information |
| permissions | array | Coworker permissions |


## CoworkersListResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array | List of coworkers |


## CreateAccountTagRequest



| Field | Type | Description |
|-------|------|-------------|
| name | string | Tag name |
| color | string | Tag color (HEX format) |


## CreateApplicantLogRequest



| Field | Type | Description |
|-------|------|-------------|
| comment | string | Comment text |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies)<br>If this field is not set then the log will be added to `personal notes` block |
| files | array | [Upload files](/v2/docs#post-/accounts/-account_id-/upload)<br>List of uploaded files ID |
| applicant_offer |  | Applicant's offer |
| email |  | Email object |
| calendar_event |  | Calendar event object |
| im | array | Telegram message |
| sms |  | SMS message |
| survey_questionary_id | integer | [Survey questionary ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries/-questionary_id-) |


## CreateApplicantLogResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Log ID |
| applicant | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| type |  | Log type |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| rejection_reason | integer | [Rejection reason ID](/v2/docs#get-/accounts/-account_id-/rejection_reasons) |
| created | string | Date and time of creation of the log |
| employment_date | string | Employment date |
| applicant_offer |  | Offer object |
| comment | string | Comment text |
| files | array | List of files attached to the log |
| calendar_event |  | Calendar event object |
| email |  | Email object |
| survey_questionary |  | [Survey Questionary](/v2/docs#get-/accounts/-account_id-/surveys/type_q/questionaries) |


## CreateApplicantTagRequest



| Field | Type | Description |
|-------|------|-------------|
| tags | array | List of [Tag ID](/v2/docs#get-/accounts/-account_id-/tags) |


## CreateVacancyRequestRequest



| Field | Type | Description |
|-------|------|-------------|
| account_vacancy_request | integer | [Vacancy request schema ID](/v2/docs#get-/accounts/-account_id-/account_vacancy_requests) |
| position | string | The name of the vacancy (occupation) |
| attendees | array | List of people to send a request for approval |
| files | array | List of file IDs to attach to the vacancy request. [Upload files](/v2/docs#post-/accounts/-account_id-/upload) |


## CreatedUserControlTaskResponse



| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Task ID |
| action |  | Task action |
| created | string | Task creation time |


## Creator



| Field | Type | Description |
|-------|------|-------------|
| account_id | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |
| name | string | Coworker name |


## CreatorInfo



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) who created the vacancy request |
| name | string | Name of coworker who created the vacancy request |
| email | string | Email of coworker who created the vacancy request |


## DateWithPrecision



| Field | Type | Description |
|-------|------|-------------|
| year | integer | Year |
| month | integer | Month |
| day | integer | Day |
| precision |  | Precision type |


## DeadLineDate



| Field | Type | Description |
|-------|------|-------------|
| days | integer | Amount of working days |
| start | string | A date to start counting. Default is today |


## DeadLineDatesBulkRequest





## DeadLineDatesBulkResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of deadlines |


## DelayedTask



| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Task ID |
| state |  | Current task status |
| created | number | Unix timestamp of task creation |
| updated | number | Unix timestamp of the last task update |
| created_datetime | string | Date and time of task creation (ISO 8601) |
| updated_datetime | string | Date and time of the last task update (ISO 8601) |
| states_log | array | Task change log |
| result |  | Task execution result |


## DictionariesListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## DictionaryCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| code | string | Dictionary code |
| name | string | Dictionary name |
| foreign | string | Foreign |
| items | array | Dictionary items |


## DictionaryCreateResponse



| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| payload |  |  |
| meta |  |  |


## DictionaryField



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Dictionary field ID |
| name | string | Dictionary field name |
| order | integer | Order |
| active | boolean | Activity flag |
| parent | integer | Parent dictionary field ID |
| deep | integer | Depth level |
| foreign | string | Foreign |
| meta | object | Meta information |


## DictionaryResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Dictionary ID |
| code | string | Dictionary code |
| name | string | Dictionary name |
| foreign | string | Foreign |
| created | string | Date and time of creating a dictionary |
| fields | array | Dictionary fields |


## DictionaryTaskResponseMeta



| Field | Type | Description |
|-------|------|-------------|
| data | object | Request body |
| account_id | integer | Organization ID |


## DictionaryTaskResponsePayload



| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Job ID |


## DictionaryUpdateRequest



| Field | Type | Description |
|-------|------|-------------|
| name | string | Dictionary name |
| foreign | string | Foreign |
| items | array | Dictionary items |


## DictionaryUpdateResponse



| Field | Type | Description |
|-------|------|-------------|
| status | string | Operation status |
| payload |  |  |
| meta |  |  |


## DivisionsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |
| meta |  |  |


## EditedFillQuota



| Field | Type | Description |
|-------|------|-------------|
| deadline | string | Date when the quota should be filled |
| applicants_to_hire | integer | Number of applicants should be hired on the fill quota |
| vacancy_request | integer | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |
| id | integer | Quota ID |


## Education



| Field | Type | Description |
|-------|------|-------------|
| level |  | Education level |
| higher | array | List of higher education institutions |
| vocational | array | List of vocational education institutions |
| elementary | array | List of elementary education institutions |
| additional | array | List of additional education institutions |
| attestation | array | List of attestations |


## EducationInfoWithResult



| Field | Type | Description |
|-------|------|-------------|
| name | string | Education name |
| description | string | Education description |
| date_from |  | Education start date |
| date_to |  | Education end date |
| area |  | Education area |
| result | string | Education result |


## EmailAccount



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Email account ID |
| name | string | Email name |
| email | string | Email address |
| receive | boolean | Is it possible to receive letters |
| send | boolean | Is it possible to send letters |
| last_sync | string | Date and time of last sync |


## EmailAccountsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of connected email accounts |


## EmailContactType


An enumeration.




## EmailFollowup



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Followup ID |
| account_member_template | integer | Email template ID |
| html | string | Email content (HTML) |
| days | integer | The number of days after which to send a followup if there is no response |


## ErrorBase



| Field | Type | Description |
|-------|------|-------------|
| type | string | Error type |
| title | string | Title |
| detail | string | Error detail |
| location |  | Error location |


## ErrorResponse



| Field | Type | Description |
|-------|------|-------------|
| errors | array | Errors list |


## EventReminderMultiplier


An enumeration.




## ExtendedEducationInfo



| Field | Type | Description |
|-------|------|-------------|
| name | string | Education name |
| description | string | Education description |
| date_from |  | Education start date |
| date_to |  | Education end date |
| area |  | Education area |
| faculty | string | Faculty name |
| form |  |  |


## ExternalEntity



| Field | Type | Description |
|-------|------|-------------|
| id |  | Entity ID in Huntflow system |
| external_id | string | Entity external ID |
| name | string | Entity name |


## FieldType


An enumeration.




## FillQuota



| Field | Type | Description |
|-------|------|-------------|
| deadline | string | Date when the quota should be filled |
| applicants_to_hire | integer | Number of applicants should be hired on the fill quota |
| vacancy_request | integer | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |


## ForeignUserRequest



| Field | Type | Description |
|-------|------|-------------|
| id | string | Foreign User ID |
| name | string | User name |
| email | string | Email |
| type |  | User type (role) |
| head_id | string | Foreign user ID of head |
| division_ids | array | Foreign IDs of available divisions. If field is not provided, contains null or empty list, it means access to all divisions |
| permissions | array | User permissions |
| meta | object | Additional meta information |


## ForeignUserResponse



| Field | Type | Description |
|-------|------|-------------|
| id | string | Foreign User ID |
| name | string | User name |
| email | string | Email |
| type |  | User type (role) |
| head_id | string | Foreign user ID of head |
| division_ids | array | Foreign IDs of available divisions. If field is not provided, contains null or empty list, it means access to all divisions |
| permissions | array | User permissions |
| meta | object | Additional meta information |


## ForeignUsersListResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array | Users with foreign identifiers |


## HTTPValidationError



| Field | Type | Description |
|-------|------|-------------|
| detail | array |  |


## InterviewType



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Interview type ID |
| name | string | Interview type name |
| account | integer | [Organization ID](/v2/docs#get-/accounts) |
| order | integer | Order number |
| type |  | Type of the interview |


## InterviewTypeEnum


An enumeration.




## InterviewTypesListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## Language



| Field | Type | Description |
|-------|------|-------------|
| id |  | Entity ID in Huntflow system |
| external_id | string | Entity external ID |
| name | string | Entity name |
| level |  | Language proficiency level |


## LastVacancyFrameResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |
| frame_begin | string | Date and time of creating a frame |
| frame_end | string | Date and time of closing a frame |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| hired_applicants | array | Hired [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants)s |
| workdays_in_work | integer | How many working days the vacancy is in work |
| workdays_before_deadline | integer | How many working days before deadline |


## Location



| Field | Type | Description |
|-------|------|-------------|
| entity | string | Entity where error was raised |
| variable | string | Json-pointer path to error |


## MailTemplate



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Template ID |
| subject | string | Subject text |
| name | string | Template name |
| member | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) who created the template |
| html | string | HTML content |
| type | string | Template type |
| followups | array | Follow-up list |
| attendees | array | Attendees list |
| divisions | array | Divisions list |
| files | array | Files list |


## MailTemplateAttendee



| Field | Type | Description |
|-------|------|-------------|
| type | string | Attendee type |
| email | string | Attendee email |


## MailTemplateDivision



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Division ID |


## MailTemplatesResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## MeResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | User ID |
| name | string | User name |
| position | string | User occupation |
| email | string | Email address |
| phone | string | Phone number |
| locale | string | User locale |


## MemberType


An enumeration.




## Military



| Field | Type | Description |
|-------|------|-------------|
| date_from |  | Military service start date |
| date_to |  | Military service end date |
| area |  | Military service area |
| unit | object | Military service unit |


## MultiVacancyCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| account_applicant_offer | integer | Organization offer ID |
| position | string | The name of the vacancy (occupation) |
| company | string | Department name (ignored if the [Divisions](/v2/docs#tag--Divisions) are enabled) |
| hidden | boolean | Is the vacancy hidden from [Coworkers](/v2/docs#tag--Coworkers)? |
| state |  | The state of a vacancy |
| coworkers | array | The list of [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) working with a vacancy |
| body | string | The responsibilities for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| requirements | string | The requirements for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| conditions | string | The conditions for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| files | array | The list of file IDs to be attached to a vacancy ([Upload files](/v2/docs#post-/accounts/-account_id-/upload)) |
| blocks | array | List of sub-vacancies for a multivacancy |


## MultiVacancyResponse



| Field | Type | Description |
|-------|------|-------------|
| task_id | string | [Task ID](/v2/docs#get-/accounts/-account_id-/delayed_tasks/-task_id-) |


## MultiVacancyUpdatePartialRequest



| Field | Type | Description |
|-------|------|-------------|
| account_applicant_offer | integer | Organization offer ID |
| position | string | The name of the vacancy (occupation) |
| company | string | Department name (ignored if the [Divisions](/v2/docs#tag--Divisions) are enabled) |
| hidden | boolean | Is the vacancy hidden from [Coworkers](/v2/docs#tag--Coworkers)? |
| state |  | The state of a vacancy |
| body | string | The responsibilities for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| requirements | string | The requirements for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| conditions | string | The conditions for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| files | array | The list of file IDs to be attached to a vacancy ([Upload files](/v2/docs#post-/accounts/-account_id-/upload)) |
| blocks | array | List of sub-vacancies for a multivacancy |


## MultiVacancyUpdateRequest



| Field | Type | Description |
|-------|------|-------------|
| account_applicant_offer | integer | Organization offer ID |
| position | string | The name of the vacancy (occupation) |
| company | string | Department name (ignored if the [Divisions](/v2/docs#tag--Divisions) are enabled) |
| hidden | boolean | Is the vacancy hidden from [Coworkers](/v2/docs#tag--Coworkers)? |
| state |  | The state of a vacancy |
| body | string | The responsibilities for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| requirements | string | The requirements for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| conditions | string | The conditions for a vacancy in HTML format. Available tags: ul, ol, li, p, br, a, strong, em, u, b, i |
| files | array | The list of file IDs to be attached to a vacancy ([Upload files](/v2/docs#post-/accounts/-account_id-/upload)) |
| blocks | array | List of sub-vacancies for a multivacancy |


## MultivacancyAddChildTaskResult



| Field | Type | Description |
|-------|------|-------------|
| child_vacancy_id | integer |  |


## MultivacancyUpsertTaskResult



| Field | Type | Description |
|-------|------|-------------|
| parent_vacancy_id | integer |  |
| children_vacancies_ids | array |  |


## Name



| Field | Type | Description |
|-------|------|-------------|
| first | string | Firstname |
| last | string | Lastname |
| middle | string | Middlename |


## NonWorkingDaysBulkRequest





## NonWorkingDaysBulkResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | Info about non-working days for several periods |


## NonWorkingDaysResponse



| Field | Type | Description |
|-------|------|-------------|
| start | string | Start date |
| deadline | string | Deadline date |
| total_days | integer | Total amount of days within the range |
| not_working_days | integer | Amount of non-working days within the range |
| production_calendar | integer | Calendar ID |
| items | array | List of dates, weekends and holidays within the range |


## NullStr


An enumeration.




## Organization



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Organization ID |
| name | string | Organization name |
| nick | string | Short organization name |
| member_type |  | Role of the current user in the organization |
| production_calendar | integer | [Production calendar ID](/v2/docs#get-/production_calendars) |


## OrganizationInfoResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Organization ID](/v2/docs#get-/accounts) |
| name | string | Organization name |
| nick | string | Short organization name |
| locale | string | Organization locale |
| photo | string | Organization logo url |


## OrganizationsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of available organizations |


## ParsedFields



| Field | Type | Description |
|-------|------|-------------|
| name |  |  |
| birthdate |  |  |
| phones | array | Phones |
| email | string | Email |
| salary | integer | Salary |
| position | string | Position |
| skype | string | Skype |
| telegram | string | Telegram |
| experience | array | Experience |


## ParsingMetaResponse



| Field | Type | Description |
|-------|------|-------------|
| last_names_ignored | boolean | If last names ignored |
| emails_ignored | boolean | If emails ignored |
| phones_ignored | boolean | If phones ignored |


## Permission



| Field | Type | Description |
|-------|------|-------------|
| permission | string | Permission name |
| value | string | Permission value |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |


## PersonalInfo



| Field | Type | Description |
|-------|------|-------------|
| photo |  | Urls for resume photo |
| first_name | string | First name |
| middle_name | string | Middle name |
| last_name | string | Last name |
| birth_date |  | Date of birth |
| text_block |  | Additional "About" info |


## PhotoData



| Field | Type | Description |
|-------|------|-------------|
| small | string | Small image url |
| medium | string | Medium image url |
| large | string | Large image url |
| external_id | string | Photo external ID |
| description | string | Photo description |
| source | string | Photo's source url |
| id | integer | Huntflow photo ID |


## Portfolio



| Field | Type | Description |
|-------|------|-------------|
| small | string | Small image url |
| large | string | Large image url |
| description | string | Image description |


## PrecisionTypes


An enumeration.




## QuestionaryField



| Field | Type | Description |
|-------|------|-------------|
| type |  | Field type |
| id | integer | Field ID |
| title | string | Field title |
| required | boolean | Field required flag |
| order | integer | The order of the field on the form |
| values | array | List of possible values (for fields with select type) |
| value | string | Set value |
| fields | object | Child fields |
| show_in_profile | boolean | Display field value in applicant's profile |
| dictionary | string | Organization dictionary name (for type=dictionary) |


## QuestionaryRequest





## QuestionaryResponse





## QuestionarySchemaResponse


Mapping of fields in the questionary and objects with their values




## RawData



| Field | Type | Description |
|-------|------|-------------|
| body | string | Resume text (for resumes with auth_type = NATIVE) |


## RecommendationProcessingFilter


An enumeration.




## RecommendationStatus


- TAKEN: recommended applicant was taken from recommendations tab
- TAKEN_OTHER: recommended applicant was taken from any other place
- DECLINED: recommended applicant was declined




## RefreshTokenRequest



| Field | Type | Description |
|-------|------|-------------|
| refresh_token | string | Refresh token |


## RefreshTokenResponse



| Field | Type | Description |
|-------|------|-------------|
| access_token | string | New access token |
| token_type | string | Token type |
| expires_in | integer | Token lifetime in seconds |
| refresh_token_expires_in | integer | Refresh token lifetime in seconds |
| refresh_token | string | New refresh token |


## Region



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Region ID |
| name | string | Region name |
| order | integer | Order number |
| parent | integer | Parent Region ID |
| deep | integer | Depth level |


## RegionsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |
| meta |  |  |


## RejectionReason


The ID can be None because the backend adds the rejection reason "Other" where ID is None


| Field | Type | Description |
|-------|------|-------------|
| id | integer | Rejection reason ID |
| name | string | Rejection reason name |
| order | integer | Order |


## RejectionReasonsListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## Relocation



| Field | Type | Description |
|-------|------|-------------|
| type |  | Type of relocation |
| area | array | List of areas for relocation |


## Resume



| Field | Type | Description |
|-------|------|-------------|
| personal_info |  | Personal info |
| source_url | string | Resume url to external job site |
| position | string | Resume header |
| specialization | array | Specializations |
| skill_set | array | List of skills |
| gender |  | Gender |
| experience | array | Work experiences |
| education |  | Education |
| certificate | array | Certificates |
| portfolio | array | Portfolio |
| contact | array | List of contacts |
| area |  | Living area |
| relocation |  | Relocation info |
| citizenship | array | Citizenship |
| work_permit | array | List of countries with work permission |
| language | array | Language proficiency |
| wanted_salary |  | Desired salary |
| work_schedule | array | Work schedules |
| business_trip_readiness |  | Readiness for business trips |
| recommendations | array | List of recommendations |
| has_vehicle | boolean | Ownership of vehicle |
| driver_license_types | array | List of available driver's licenses |
| military | array | Military service |
| social_ratings | array | Social ratings |
| photos | array | Photos |
| additionals | array | Some additional info related to resume |
| wanted_place_of_work | string | Desired place of work |
| updated_on_source |  | Date of resume update in the source |
| travel_time |  | Preferred travel time |


## Salary



| Field | Type | Description |
|-------|------|-------------|
| amount | number | Salary amount |
| currency | string | Salary currency |


## SimplePhoto



| Field | Type | Description |
|-------|------|-------------|
| url | string | Photo url |
| original | string | Photo original |


## SimpleVacancyRequest



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| position | string |  |
| created | string |  |
| updated | string |  |
| changed | string | Changes on attach to vacancy |


## Skill



| Field | Type | Description |
|-------|------|-------------|
| title | string | Skill name |


## SocialRating



| Field | Type | Description |
|-------|------|-------------|
| kind | string |  |
| stats |  |  |
| tags | array |  |
| url | string |  |
| login | string |  |
| registered_at | string | ISO datetime |


## Specialization



| Field | Type | Description |
|-------|------|-------------|
| id |  | Entity ID in Huntflow system |
| external_id | string | Entity external ID |
| name | string | Entity name |
| profarea_id | string | Specialization ID in Huntflow system |
| external_profarea_id | string | Specialization external ID |
| prefarea_name | string | Specialization name |


## StartDate



| Field | Type | Description |
|-------|------|-------------|
| days | integer | Amount of working days |
| deadline | string | A date to finish the reverse counting. Default is today. |


## StartDatesBulkRequest





## StatusResponse



| Field | Type | Description |
|-------|------|-------------|
| status | boolean |  |


## SurveyAnswerTypeAResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Survey answer of type A ID](/v2/docs#get-/accounts/-account_id-/surveys/type_a/-survey_id-/answers/-answer_id-) |
| created | string | Date and time of creating an answer |
| survey |  | Survey schema |
| respondent |  | Who created the survey answer |
| data | object | Answer data |


## SurveyQuestionaryAnswerResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Survey questionary answer ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/answers/-answer_id-) |
| created | string | Date and time of creating an answer |
| survey |  | Survey questionary schema |
| respondent |  |  |
| survey_questionary |  |  |
| data | object | Answer data |


## SurveyQuestionaryCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| survey_id | integer |  |
| respondent |  |  |


## SurveyQuestionaryCreatedInfo



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey questionary ID |
| created | string | Date and time of creating a survey |
| created_by |  |  |


## SurveyQuestionaryRespondent



| Field | Type | Description |
|-------|------|-------------|
| applicant_id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |


## SurveyQuestionaryRespondentWithName



| Field | Type | Description |
|-------|------|-------------|
| applicant_id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| name | string |  |


## SurveyQuestionaryResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey questionary ID |
| created | string | Date and time of creating a survey |
| created_by |  |  |
| survey |  | Survey questionary schema |
| respondent |  |  |
| survey_answer_id | integer | [Survey questionary answer ID](/v2/docs#get-/accounts/-account_id-/surveys/type_q/answers/-answer_id-) |
| link | string | Survey questionary link for applicant |


## SurveySchemaTypeALogResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey ID |
| name | string | Survey name |
| type |  | Type of survey |
| active | boolean | Is survey active? |
| created | string | Date and time of creating a survey |
| updated | string | Date and time of the last update of the survey |


## SurveySchemaTypeAResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey ID |
| name | string | Survey name |
| type |  | Type of survey |
| active | boolean | Is survey active? |
| created | string | Date and time of creating a survey |
| updated | string | Date and time of the last update of the survey |
| schema | object | JSON schema for the survey fields |
| ui_schema | object | UI schema for the survey fields |


## SurveySchemaTypeQLogResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey ID |
| name | string | Survey name |
| type |  | Type of survey |
| active | boolean | Is survey active? |
| created | string | Date and time of creating a survey |
| updated | string | Date and time of the last update of the survey |
| title | string | Survey title |


## SurveySchemaTypeQResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Survey ID |
| name | string | Survey name |
| type |  | Type of survey |
| active | boolean | Is survey active? |
| created | string | Date and time of creating a survey |
| updated | string | Date and time of the last update of the survey |
| schema | object | JSON schema for the survey fields |
| ui_schema | object | UI schema for the survey fields |
| title | string | Survey title |


## SurveySchemasTypeAListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of type a survey schemas |


## SurveySchemasTypeQListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | List of type q survey schemas |


## SurveyTypeARespondent



| Field | Type | Description |
|-------|------|-------------|
| account_id | integer | [User ID](/v2/docs#get-/accounts/-account_id-/users/-user_id-) |
| name | string | Name of the user who created the survey answer |


## SurveyTypesEnum


An enumeration.




## TaskLog



| Field | Type | Description |
|-------|------|-------------|
| state |  | Task status |
| timestamp | number | Unix timestamp of the task state change |
| datetime | string | Date and time of the task state change (ISO 8601) |
| comment | string | Comment text |


## TaskState


An enumeration.




## TextBlock



| Field | Type | Description |
|-------|------|-------------|
| header | string | Text block header |
| body | string | Text block body |


## Transparency


An enumeration.




## UploadResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | File ID |
| url | string | File URL |
| content_type | string | File content type |
| name | string | File name |
| photo |  | Photo file |
| text | string | Parsed text |
| fields |  | Parsed fields |
| parsing_meta |  | Info on ignored arguments |


## User



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |
| name | string | Coworker name |
| email | string | Email |
| phone | string | Phone number |
| meta | object | Additional information |


## UserControlTaskAction


An enumeration.




## UserControlTaskResponse



| Field | Type | Description |
|-------|------|-------------|
| id | string | Task ID |
| account_id | integer | Organization account ID |
| action |  | Task action |
| status |  | Task status |
| data | object | Task result |
| comment | string | Comment (in case of error) |
| created | string | Task creation time |
| completed | string | Task completion time |


## UserControlTaskStatus


An enumeration.




## UserId



| Field | Type | Description |
|-------|------|-------------|
| id | integer | User ID |


## UserResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | User ID |
| name | string | User name |
| type | string | User type (role) |
| head | integer | Head user ID |
| email | string | Email |
| meta | object | Additional meta information |
| permissions | array | User permissions |


## VacancyBlock


Child vacancy for multivacancy


| Field | Type | Description |
|-------|------|-------------|
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |


## VacancyBlockUpdate


Child vacancy for multivacancy


| Field | Type | Description |
|-------|------|-------------|
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| id | integer | Sub-vacancy ID |


## VacancyBlockUpdatePartial


Child vacancy for multivacancy


| Field | Type | Description |
|-------|------|-------------|
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| id | integer | Sub-vacancy ID |
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |


## VacancyChild


Child vacancy for multivacancy


| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| created | string | Date and time of creating a vacancy |
| additional_fields_list | array | List of additional field names. [Getting a schema of additional fields](/v2/docs#/Vacancies/get_additional_fields_schema_accounts__account_id__vacancies_additional_fields_get) |
| multiple | boolean | Flag indicating if this vacancy is a multiple |
| parent | integer | Vacancy parent ID |
| account_vacancy_status_group | integer | [Recruitment status group ID](/v2/docs#get-/accounts/-account_id-/vacancies/status_groups) |
| updated | string | Date and time of updating a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array |  |
| source | string | Vacancy source ID if it was imported |


## VacancyCloseRequest



| Field | Type | Description |
|-------|------|-------------|
| date | string | Action date |
| comment | string | Comment |
| account_vacancy_close_reason | integer | [Vacancy close reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_close_reasons) |
| unpublish_all | boolean | Remove a vacancy from all publications |


## VacancyCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| account_applicant_offer | integer | Organization offer ID |
| coworkers | array | List of [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) working with a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array | List of file IDs attached to a vacancy. [Upload files](/v2/docs#post-/accounts/-account_id-/upload) |
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |


## VacancyCreateResponse



| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| created | string | Date and time of creating a vacancy |
| coworkers | array | List of [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) working with a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array | The list of file IDs attached to a vacancy |
| account_vacancy_status_group | integer | [Recruitment status group ID](/v2/docs#get-/accounts/-account_id-/vacancies/status_groups) |
| parent | integer | Parent vacancy ID |
| source | string | Vacancy source ID if it was imported |
| multiple | boolean | Flag indicating if this vacancy is a multiple |
| vacancy_request | integer | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |


## VacancyCreateState


An enumeration.




## VacancyFrame



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |
| frame_begin | string | Date and time of creating a frame |
| frame_end | string | Date and time of closing a frame |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| hired_applicants | array | Hired [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants)s |
| workdays_in_work | integer | How many working days the vacancy is in work |
| workdays_before_deadline | integer | How many working days before deadline |
| next_id | integer | The next frame ID |


## VacancyFrameQuotasResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## VacancyFramesListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## VacancyHoldRequest



| Field | Type | Description |
|-------|------|-------------|
| date | string | Action date |
| comment | string | Comment |
| account_vacancy_hold_reason | integer | [Vacancy hold reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_hold_reasons) |
| unpublish_all | boolean | Remove a vacancy from all publications |


## VacancyItem



| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| created | string | Date and time of creating a vacancy |
| additional_fields_list | array | List of additional field names. [Getting a schema of additional fields](/v2/docs#/Vacancies/get_additional_fields_schema_accounts__account_id__vacancies_additional_fields_get) |
| multiple | boolean | Flag indicating if this vacancy is a multiple |
| parent | integer | Vacancy parent ID |
| account_vacancy_status_group | integer | [Recruitment status group ID](/v2/docs#get-/accounts/-account_id-/vacancies/status_groups) |


## VacancyListResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array |  |


## VacancyListState


An enumeration.




## VacancyLog



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Vacancy log ID |
| state |  | Vacancy state ID |
| created | string | Vacancy log creation date |
| account_vacancy_hold_reason | integer | [Vacancy hold reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_hold_reasons) |
| account_vacancy_close_reason | integer | [Vacancy close reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_close_reasons) |
| data |  |  |
| account_data |  |  |
| vacancy_request |  |  |
| vacancy_frame_fill_quota |  |  |


## VacancyLogsResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array | Vacancy logs, from newer to older |
| page | integer | Has value when page param passed, current page |
| count | integer | Has value when page param passed, count per page |
| total | integer | Has value when page param passed, total pages number |


## VacancyMemberCreateRequest



| Field | Type | Description |
|-------|------|-------------|
| permissions | array | List of permissions (if member type is `watcher`) |


## VacancyMemberPermission



| Field | Type | Description |
|-------|------|-------------|
| permission | string | Permission ID |
| value |  | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |


## VacancyPeriodsResponse



| Field | Type | Description |
|-------|------|-------------|
| days_in_work | integer | How many days the vacancy is in work |
| work_days_in_work | integer | How many working days the vacancy is in work |
| hold_periods | array | List of periods when the vacancy was in HOLD state |
| closed_periods | array | List of periods when the vacancy was in CLOSED state |


## VacancyQuotaExtendedItem



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| vacancy_frame | integer | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |
| vacancy_request | integer | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |
| created | string | Date and time of creating a vacancy quota |
| changed | string | Date and time of updating a vacancy quota |
| applicants_to_hire | integer | Number of applicants should be hired on the quota |
| already_hired | integer | Number of applicants already hired on the quota |
| deadline | string | Date when the quota should be filled |
| closed | string | Date and time when the quota was closed |
| work_days_in_work | integer | How many working days the vacancy is in work |
| work_days_after_deadline | integer | How many working days the vacancy is in work after deadline |
| account_info |  |  |


## VacancyQuotaItem



| Field | Type | Description |
|-------|------|-------------|
| id | integer | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| vacancy_frame | integer | [Vacancy frame ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/frames) |
| vacancy_request | integer | [Vacancy request ID](/v2/docs#get-/accounts/-account_id-/vacancy_requests) |
| created | string | Date and time of creating a vacancy quota |
| changed | string | Date and time of updating a vacancy quota |
| applicants_to_hire | integer | Number of applicants should be hired on the quota |
| already_hired | integer | Number of applicants already hired on the quota |
| deadline | string | Date when the quota should be filled |
| closed | string | Date and time when the quota was closed |
| work_days_in_work | integer | How many working days the vacancy is in work |
| work_days_after_deadline | integer | How many working days the vacancy is in work after deadline |
| account_info |  |  |


## VacancyQuotaList



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array |  |


## VacancyQuotasResponse





## VacancyRecommendationsResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |
| next_page_cursor | string |  |


## VacancyRequest



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Vacancy request ID |
| position | string | The name of the vacancy (occupation) |
| status |  | Vacancy request status |
| account_vacancy_request | integer | [Vacancy request schema ID](/v2/docs#get-/accounts/-account_id-/account_vacancy_requests) |
| created | string | Date and time of creation of the request |
| updated | string | Date and time of editing of the request |
| changed | string | Date and time of attaching to vacancy |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| creator |  | User who created the request |
| files | array | List of files attached to the request |
| states | array | List of approval states |
| values | object | Vacancy request values |


## VacancyRequestApprovalState



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Approval ID |
| status |  | Approval status |
| email | string | Email, which was used to send the request for approval |
| reason | string | Rejection reason |
| order | integer | Approval order number |
| changed | string | Date and time of the last approval change |


## VacancyRequestAttendee



| Field | Type | Description |
|-------|------|-------------|
| email | string | Attendee email |
| name | string | Attendee name |


## VacancyRequestListResponse



| Field | Type | Description |
|-------|------|-------------|
| page | integer | Page number |
| count | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| total_items | integer | Total number of items |
| items | array |  |


## VacancyRequestResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Vacancy request ID |
| position | string | The name of the vacancy (occupation) |
| status |  | Vacancy request status |
| account_vacancy_request | integer | [Vacancy request schema ID](/v2/docs#get-/accounts/-account_id-/account_vacancy_requests) |
| created | string | Date and time of creation of the request |
| updated | string | Date and time of editing of the request |
| changed | string | Date and time of attaching to vacancy |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| creator |  | User who created the request |
| files | array | List of files attached to the request |
| states | array | List of approval states |
| values | object | Vacancy request values |
| taken_by |  | User who accepted the vacancy request for work |


## VacancyRequestStatus


An enumeration.




## VacancyResponse


Child vacancy for multivacancy


| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| created | string | Date and time of creating a vacancy |
| additional_fields_list | array | List of additional field names. [Getting a schema of additional fields](/v2/docs#/Vacancies/get_additional_fields_schema_accounts__account_id__vacancies_additional_fields_get) |
| multiple | boolean | Flag indicating if this vacancy is a multiple |
| parent | integer | Vacancy parent ID |
| account_vacancy_status_group | integer | [Recruitment status group ID](/v2/docs#get-/accounts/-account_id-/vacancies/status_groups) |
| updated | string | Date and time of updating a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array |  |
| source | string | Vacancy source ID if it was imported |
| blocks | array | Affiliate vacancies if vacancy is a multiple |


## VacancyState


An enumeration.




## VacancyStatus



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Status ID |
| type | string | Status type |
| name | string | Status name |
| removed | string | Date and time of removing |
| order | integer | Order number |
| stay_duration | integer | The allowed number of days of a applicant's stay at this status.`null` means unlimited |


## VacancyStatusGroup



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Group ID |
| name | string | Group name |
| statuses | array | List of recruitment statuses in the group |


## VacancyStatusGroupsResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## VacancyStatusInGroup



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Item ID |
| account_vacancy_status | integer | [Recruitment status ID](/v2/docs#get-/accounts/-account_id-/vacancies/statuses) |
| stay_duration | integer | The allowed number of days of a candidate's stay at this status.`null` means unlimited |


## VacancyStatusesResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## VacancyUpdatePartialRequest



| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array | The list of files attached to a vacancy |
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| account_vacancy_hold_reason | integer | [Vacancy hold reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_hold_reasons) |
| account_vacancy_close_reason | integer | [Vacancy close reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_close_reasons) |


## VacancyUpdateRequest



| Field | Type | Description |
|-------|------|-------------|
| account_division | integer | [Division ID](/v2/docs#get-/accounts/-account_id-/divisions) |
| account_region | integer | [Region ID](/v2/docs#get-/accounts/-account_id-/regions) |
| position | string | The name of the vacancy (occupation) |
| company | string | Department (ignored if the DEPARTMENTS are enabled) |
| money | string | Salary |
| priority | integer | The priority of a vacancy (0 for usual or 1 for high) |
| hidden | boolean | Is the vacancy hidden from the colleagues? |
| state |  | The state of a vacancy |
| body | string | The responsibilities for a vacancy in HTML format |
| requirements | string | The requirements for a vacancy in HTML format |
| conditions | string | The conditions for a vacancy in HTML format |
| files | array | The list of files attached to a vacancy |
| fill_quotas | array | [Fill quota ID](/v2/docs#get-/accounts/-account_id-/vacancies/-vacancy_id-/quotas) |
| account_vacancy_hold_reason | integer | [Vacancy hold reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_hold_reasons) |
| account_vacancy_close_reason | integer | [Vacancy close reason ID](/v2/docs#get-/accounts/-account_id-/vacancy_close_reasons) |


## VacancyUpdateState


An enumeration.




## ValidationError



| Field | Type | Description |
|-------|------|-------------|
| loc | array |  |
| msg | string |  |
| type | string |  |


## WebhookEvent


An enumeration.




## WebhookRequest



| Field | Type | Description |
|-------|------|-------------|
| secret | string | Secret key |
| url | string | Webhook URL |
| active | boolean | Webhook activity flag |
| webhook_events | array | Events types |
| type |  | Webhook type |


## WebhookResponse



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Webhook ID |
| account | integer | Organization ID |
| url | string | Webhook URL |
| created | string | Date and time of creating a webhook |
| active | boolean | Webhook activity flag |
| webhook_events | array | Event types |
| type |  | Webhook type |


## WebhookType


An enumeration.




## WebhooksListResponse



| Field | Type | Description |
|-------|------|-------------|
| items | array |  |


## api__v2__serializers__common__File



| Field | Type | Description |
|-------|------|-------------|
| id | integer | File ID |
| url | string | File URL |
| content_type | string | MIME type of file |
| name | string | File name |


## api__v2__serializers__request__applicants__ApplicantLogCalendarEvent



| Field | Type | Description |
|-------|------|-------------|
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| private | boolean | Event private flag |
| name | string | Event name |
| reminders | array | List of reminders <a href=https://tools.ietf.org/html/rfc5545>RFC 5545</a> |
| location | string | Event location |
| interview_type | integer | Interview type ID |
| event_type |  | Calendar event type |
| description | string | Event description (comment) |
| calendar | integer | [Calendar ID](/v2/docs#get-/calendar_accounts) |
| attendees | array | Event attendees (participants) |
| start | string | Event start date |
| end | string | Event end date |
| timezone | string | Time zone |
| transparency |  | Event transparency (availability) |


## api__v2__serializers__request__applicants__ApplicantOffer



| Field | Type | Description |
|-------|------|-------------|
| account_applicant_offer | integer | [Organization offer ID](/v2/docs#get-/accounts/-account_id-/offers) |
| values | object | Offer values. You can see required values here - [Organization offer schema](/v2/docs#get-/accounts/-account_id-/offers/-offer_id-) |


## api__v2__serializers__request__applicants__ApplicantSocial



| Field | Type | Description |
|-------|------|-------------|
| social_type | string | Type |
| value | string | Value |


## api__v2__serializers__request__applicants__CalendarEventAttendee



| Field | Type | Description |
|-------|------|-------------|
| member | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |
| displayName | string | Attendee name |
| email | string | Attendee email |


## api__v2__serializers__request__applicants__CalendarEventReminder



| Field | Type | Description |
|-------|------|-------------|
| multiplier |  | Reminder period |
| value | integer | Reminder value |
| method |  | Reminder method |


## api__v2__serializers__request__applicants__EmailRecipient



| Field | Type | Description |
|-------|------|-------------|
| email | string | Email address |
| type |  | Recipient type |
| displayName | string | Recipient name |


## api__v2__serializers__request__calendar__NonWorkingDays



| Field | Type | Description |
|-------|------|-------------|
| deadline | string | Deadline date |
| start | string | Start date |


## api__v2__serializers__request__dictionaries__DictionaryItem



| Field | Type | Description |
|-------|------|-------------|
| name | string | Dictionary item name |
| foreign | string | Foreign |
| meta | object | Meta information |
| items | array | Dictionary items |


## api__v2__serializers__request__divisions__Division



| Field | Type | Description |
|-------|------|-------------|
| name | string | Division name |
| foreign | string | The unique identifier in the customer's internal system |
| meta | object | Arbitrary structure with additional information |
| items | array | List with subdivisions |


## api__v2__serializers__response__applicants__ApplicantLogCalendarEvent



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Calendar event ID |
| name | string | Event name |
| all_day | boolean | Flag indicating that the event is scheduled for the whole day |
| created | string | Date and time of event creation |
| creator |  | Event creator |
| description | string | Event description |
| timezone | string | Event time zone |
| start | string | Event start date and time |
| end | string | Event end date and time |
| etag | string | Event Etag |
| event_type |  | Event type |
| interview_type | integer | Interview type ID |
| calendar | integer | [Calendar ID](/v2/docs#get-/calendar_accounts) |
| vacancy | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| foreign | string | Foreign ID of event |
| location | string | Event location |
| attendees | array | Event attendees (participants) |
| reminders | array | List of reminders <a href=https://tools.ietf.org/html/rfc5545>RFC 5545</a> |
| status |  | Event status |
| transparency |  | Event transparency (availability) |
| recurrence | array |  |


## api__v2__serializers__response__applicants__ApplicantOffer



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Applicant's offer ID |
| account_applicant_offer | integer | Organization's offer ID |
| created | string | Date and time of creating an offer |


## api__v2__serializers__response__applicants__ApplicantSocial



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Social ID |
| social_type | string | Type |
| value | string | Value |
| verified | boolean | Verification flag |
| verification_date | string | Verification date |


## api__v2__serializers__response__applicants__CalendarEventAttendee



| Field | Type | Description |
|-------|------|-------------|
| member | integer | [Coworker ID](/v2/docs#get-/accounts/-account_id-/coworkers) |
| displayName | string | Attendee name |
| email | string | Attendee email |
| responseStatus |  | Attendee response status |


## api__v2__serializers__response__applicants__CalendarEventReminder



| Field | Type | Description |
|-------|------|-------------|
| method |  | Reminder method |
| minutes | integer | How many minutes in advance to remind about the event |


## api__v2__serializers__response__applicants__EmailRecipient



| Field | Type | Description |
|-------|------|-------------|
| type |  | Type of the email contact |
| displayName | string | Name of email recipient |
| email | string | Email address |


## api__v2__serializers__response__calendar__NonWorkingDays



| Field | Type | Description |
|-------|------|-------------|
| start | string | Start date |
| deadline | string | Deadline date |
| total_days | integer | Total amount of days within the range |
| not_working_days | integer | Amount of non-working days within the range |
| production_calendar | integer | Calendar ID |


## api__v2__serializers__response__dictionaries__DictionaryItem



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Dictionary ID |
| code | string | Dictionary code |
| name | string | Dictionary name |
| foreign | string | The unique identifier in the customer's internal system |
| created | string | Date and time of creating a dictionary |


## api__v2__serializers__response__divisions__Division



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Division ID |
| name | string | Division name |
| order | integer | Order number |
| active | boolean | Activity flag |
| parent | integer | Parent division ID |
| deep | integer | Depth level |
| foreign | string | The unique identifier in the customer's internal system |
| meta | object | Additional meta information |


## api__v2__serializers__response__divisions__Meta



| Field | Type | Description |
|-------|------|-------------|
| levels | integer | The number of levels of nesting in the structure |
| has_inactive | boolean | A flag indicating whether the structure has inactive divisions |


## api__v2__serializers__response__recommendations__Recommendation



| Field | Type | Description |
|-------|------|-------------|
| id | integer | Recommendation ID |
| vacancy_id | integer | [Vacancy ID](/v2/docs#get-/accounts/-account_id-/vacancies) |
| applicant_id | integer | [Applicant ID](/v2/docs#get-/accounts/-account_id-/applicants) |
| rank | integer | Position of the recommendation in the ranking list. |
| created_at | string | Date and time when the recommendation was created. |
| updated_at | string | Date and time when the recommendation was last updated. |
| resolved_by_user | integer | ID of the recruiter who resolved recommendation. null if not processed yet. |
| status |  | Current status of the recommendation. null if not processed yet. |


## api__v2__serializers__response__regions__Meta



| Field | Type | Description |
|-------|------|-------------|
| levels | integer | The number of levels of nesting in the structure |
| has_inactive | boolean | A flag indicating whether the structure has inactive regions |


## api__v2__serializers__response__resume__Experience



| Field | Type | Description |
|-------|------|-------------|
| position | string | Position |
| date_from |  | Experience start date |
| date_to |  | Experience end date |
| company | string | Company name |
| url | string | Company's url |
| area |  | Experience area |
| industries | array | List of experience industries |
| description | string | Experience description |
| skills | array | List of skills |


## api__v2__serializers__response__resume__Recommendation



| Field | Type | Description |
|-------|------|-------------|
| value | string | Recommendation |
| date |  | Date of recommendation |
| name | string | Name to whom recommendation |
| position | string | Position |
| organization | string | Organization name |
| contact | string | Contact |


## api__v2__serializers__response__upload__Experience



| Field | Type | Description |
|-------|------|-------------|
| position | string | Position |
| company | string | Company name |


## api__v2__serializers__response__vacancies__File



| Field | Type | Description |
|-------|------|-------------|
| id | integer | File ID |
| name | string | File name |
| content_type | string | MIME type of file |
| url | string | File URL |
