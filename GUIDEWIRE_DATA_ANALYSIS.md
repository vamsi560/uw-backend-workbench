# Guidewire Data Integration Analysis for UI

## 📊 Overview
Based on the analysis of Guidewire PolicyCenter response data and our integration, here are all the APIs and data points available for the UI to display Guidewire information.

## 🏗️ Database Structure
We store comprehensive Guidewire response data in the `guidewire_responses` table with the following key fields:

### Account Information
- `guidewire_account_id` - Unique Guidewire account identifier
- `account_number` - Guidewire-generated account number (e.g., "4901420895")
- `account_status` - Status (Pending, Active, etc.)
- `organization_name` - Company/organization name
- `number_of_contacts` - Number of contacts associated

### Job/Submission Information
- `guidewire_job_id` - Unique Guidewire job identifier
- `job_number` - Guidewire-generated job number (e.g., "0001563719") 
- `job_status` - Current status (Draft, Quoted, Bound, etc.)
- `job_effective_date` - Policy effective date
- `base_state` - Primary jurisdiction (CA, NY, etc.)
- `policy_type` - Product type (USCyber, etc.)
- `producer_code` - Agent/broker code
- `underwriting_company` - UW company name

### Pricing Information
- `total_cost_amount` - Total policy cost
- `total_cost_currency` - Currency (USD)
- `total_premium_amount` - Premium amount
- `total_premium_currency` - Premium currency
- `rate_as_of_date` - Quote generation date

### Coverage Information (JSON fields)
- `coverage_terms` - All coverage terms and limits
- `coverage_display_values` - Human-readable coverage descriptions

### Business Data
- `business_started_date` - When business was started
- `total_employees` - Number of employees
- `total_revenues` - Annual revenue
- `total_assets` - Total company assets
- `total_liabilities` - Total liabilities
- `industry_type` - Industry classification

### Response Metadata
- `api_response_raw` - Complete Guidewire response (JSON)
- `api_links` - Available Guidewire API actions
- `submission_success` - Whether submission was successful
- `quote_generated` - Whether quote was generated
- `response_checksum` - For change detection

## 🌐 Available APIs for UI

### 1. Dashboard & Summary APIs

#### `GET /api/guidewire/dashboard/summary`
**Purpose**: High-level dashboard metrics for Guidewire integration
**Parameters**: 
- `days` (optional, default: 30) - Analysis period

**Returns**:
```json
{
  "summary": {
    "total_submissions": 156,
    "recent_submissions": 23,
    "success_rate": 94.23,
    "quote_rate": 87.18
  },
  "status_distribution": [
    {"status": "Quoted", "count": 45},
    {"status": "Draft", "count": 12},
    {"status": "Bound", "count": 8}
  ],
  "recent_activity": [
    {
      "id": 123,
      "account_number": "4901420895",
      "job_number": "0001563719",
      "job_status": "Quoted",
      "organization_name": "Ctrl-Alt-Del Solutions",
      "created_at": "2025-10-13T09:30:00Z",
      "success": true
    }
  ]
}
```

### 2. Account Management APIs

#### `GET /api/guidewire/accounts`
**Purpose**: List all Guidewire accounts with filtering and pagination
**Parameters**:
- `status` (optional) - Filter by account status
- `limit` (default: 50, max: 200) - Results per page
- `offset` (default: 0) - Pagination offset

**Returns**: Array of account summaries with navigation info

#### `GET /api/guidewire/accounts/{account_id}`
**Purpose**: Detailed account information including business data
**Returns**: Complete account profile with business metrics

### 3. Jobs & Submissions APIs

#### `GET /api/guidewire/jobs`
**Purpose**: List all Guidewire jobs/submissions with filtering
**Parameters**:
- `status` (optional) - Filter by job status (Draft, Quoted, etc.)
- `product` (optional) - Filter by product type
- `limit` & `offset` - Pagination

**Returns**: Array of job summaries with pricing information

#### `GET /api/guidewire/jobs/{job_id}`
**Purpose**: Complete job details including coverage and pricing
**Returns**: Full submission details with all associated data

### 4. Coverage & Pricing APIs

#### `GET /api/guidewire/coverage/summary`
**Purpose**: Coverage analysis across all submissions
**Returns**: Coverage terms distribution and popular selections

#### `GET /api/guidewire/pricing/analysis`
**Purpose**: Pricing trends and analysis
**Parameters**:
- `days` (default: 90) - Analysis period

**Returns**:
```json
{
  "analysis_period": 90,
  "total_quotes": 45,
  "average_premium": 1250.75,
  "premium_range": {"min": 500.00, "max": 5000.00},
  "quote_success_rate": 87.18,
  "distribution": [...]
}
```

### 5. Work Item Integration APIs

#### `GET /api/guidewire/workitem/{work_item_id}/guidewire-data`
**Purpose**: Complete Guidewire data for a specific work item
**Returns**: All Guidewire information linked to the work item including:
- Account and job details
- Coverage and pricing information
- Submission status and history
- Available Guidewire actions (view, update, bind)

### 6. Search & Discovery APIs

#### `GET /api/guidewire/search`
**Purpose**: Search across all Guidewire data
**Parameters**:
- `q` (required) - Search query
- `type` (default: "all") - Search scope (all, accounts, jobs, organizations)
- `limit` (default: 20, max: 100) - Results limit

**Returns**: Unified search results across accounts, jobs, and organizations

### 7. Export & Reporting APIs

#### `GET /api/guidewire/export/submissions`
**Purpose**: Export submission data for reporting
**Parameters**:
- `format` (default: "json") - Export format
- `start_date` & `end_date` (optional) - Date range
- `status` (optional) - Status filter

**Returns**: Structured export data with filtering metadata

## 📋 Specific Data Points Available from Guidewire

### From Account Creation Response (Step 1):
- Account ID: `pc:SAT9n354FTKe5a3OKtrfy`
- Account Number: `4901420895`
- Account Status: `Pending`, `Active`, etc.
- Organization Name: `Ctrl-Alt-Del Solutions`
- Primary Address: Complete address details
- Producer Codes: Agent/broker information
- Available Actions: Links to account operations

### From Job Creation Response (Step 2):
- Job ID: `pc:S9Z7G9A7dGlQCKdKlc-G6`
- Job Number: `0001563719`
- Job Status: `Draft`, `Quoted`, `Bound`, etc.
- Product: `USCyber` (Cyber Insurance)
- Effective Dates: Period start and end
- Policy Address: Business location details
- Quote Type: `Full Application`
- Term Type: `Annual`

### From Coverage Response (Step 3):
- **Aggregate Limit**: `$50,000`, `$100,000`, `$1,000,000`, etc.
- **Business Interruption**: `$10,000`, `$25,000`, etc.
- **Cyber Extortion**: `$5,000`, `$10,000`, etc.
- **Retention/Deductible**: `$1,000`, `$5,000`, `$7,500`, etc.
- **Public Relations**: Coverage for PR expenses
- **Waiting Period**: `12 hrs`, `24 hrs`, etc.
- **Computer Fraud**: Inclusion flag

### From Business Data Response (Step 4):
- Business Started Date: When company was established
- Full-Time Employees: Number count
- Part-Time Employees: Number count
- Total Revenues: Annual revenue figures
- Total Assets: Company asset valuation
- Total Liabilities: Company liability amounts
- Payroll Information: Employee payroll totals
- Policy Type: `Commercial Cyber`
- Jurisdiction: Primary business state

### From Quote Response (Step 5):
- **Total Cost**: Complete policy cost with currency
- **Total Premium**: Premium amount and currency
- **Rate Date**: When quote was generated
- **Job Status**: Updated to `Quoted`
- **Edit Lock**: Whether job is locked for editing
- **UW Company**: Underwriting company details

## 🔗 Available Guidewire Actions (API Links)

### Account-Level Actions:
- View/Edit Account Details
- Manage Contacts
- Add Activities and Notes
- Upload Documents
- View Job History
- Account Freeze/Unfreeze operations

### Job-Level Actions:
- View/Edit Submission Details
- Update Coverage Terms
- Regenerate Quotes
- Bind Policy (when quoted)
- Add Underwriting Issues
- Request Approval
- Withdraw/Decline Submission
- Release Edit Locks

### Policy-Level Actions (Post-Bind):
- View Policy Details
- Process Endorsements
- Handle Renewals
- Manage Billing
- Claims Integration

## 🎯 UI Display Recommendations

### Work Item Detail Page Enhancements:
1. **Guidewire Status Badge**: Show current job status with color coding
2. **Account Information Panel**: Display account number, organization, status
3. **Coverage Summary**: Show selected limits in tabular format
4. **Pricing Display**: Premium amount with quote date
5. **Action Buttons**: Direct links to Guidewire for further actions

### Dashboard Widgets:
1. **Submission Pipeline**: Visual pipeline of job statuses
2. **Quote Success Rate**: Percentage with trend indicators
3. **Premium Analytics**: Average premium with distribution
4. **Recent Activity Feed**: Latest Guidewire submissions

### Search & Navigation:
1. **Universal Search**: Search across accounts, jobs, organizations
2. **Status Filters**: Filter by Draft, Quoted, Bound, etc.
3. **Date Range Filters**: Filter by submission or effective dates
4. **Export Options**: Download submission reports

### Detailed Views:
1. **Account Profile**: Complete business information from Guidewire
2. **Coverage Analysis**: Visual representation of selected coverages
3. **Pricing History**: Track premium changes across quotes
4. **Audit Trail**: Link work item history with Guidewire actions

## 🚀 Implementation Status

✅ **Complete**: 
- Database schema with comprehensive Guidewire data storage
- Guidewire API integration with proper request/response mapping
- Complete set of REST APIs for UI consumption
- Search and filtering capabilities
- Export functionality

✅ **Ready for UI Integration**:
- All endpoints return structured JSON data
- Proper error handling and validation
- Pagination support for large datasets
- Flexible filtering options

✅ **Next Steps**:
- Deploy APIs to production
- Test with actual Guidewire submissions
- Add UI components to consume the APIs
- Implement real-time updates when Guidewire data changes

## 📱 Example UI Integration Code

```javascript
// Fetch work item Guidewire data
const workItemGuidewireData = await fetch(`/api/guidewire/workitem/${workItemId}/guidewire-data`);
const guidewireInfo = await workItemGuidewireData.json();

if (guidewireInfo.has_guidewire_data) {
  // Display Guidewire account and job information
  // Show coverage details and pricing
  // Provide action buttons for Guidewire operations
}
```

This comprehensive integration provides complete visibility into Guidewire PolicyCenter data while maintaining clean separation between our system and the Guidewire platform.