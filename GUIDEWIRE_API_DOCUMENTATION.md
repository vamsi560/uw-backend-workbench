# Guidewire API Endpoints for UI Team

## Overview

These API endpoints provide access to Guidewire submission data with human-readable numbers that can be used to search in Guidewire PolicyCenter. All endpoints return both internal Guidewire IDs (for system use) and human-readable numbers (for user search).

## Base URL
- **Production**: `https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net`
- **Local Development**: `http://localhost:8000`

## Authentication
All endpoints use the same authentication as your existing API calls.

---

## 1. List Guidewire Submissions

**GET** `/api/guidewire/submissions`

Get paginated list of work items that have Guidewire integration data.

### Query Parameters
- `limit` (int, optional): Number of results per page (default: 50, max: 100)
- `offset` (int, optional): Number of results to skip (default: 0)
- `search` (string, optional): Search across title, account numbers, job numbers, and subject
- `status` (string, optional): Filter by work item status (Pending, In Review, Approved, Rejected)

### Response Example
```json
{
  "submissions": [
    {
      "work_item_id": 87,
      "submission_id": 87,
      "title": "New test email for Cyber Submission",
      "status": "Pending",
      "priority": "Medium",
      "industry": "technology",
      "coverage_amount": 50000,
      
      "guidewire_account_id": "pc:S-v7XpouN04iLx8kW8cev",
      "guidewire_job_id": "pc:Su3nrO9cV2UMd9zYEYEmM", 
      "guidewire_account_number": "1296620652",
      "guidewire_job_number": "0001982331",
      
      "sender_email": "test@example.com",
      "assigned_to": null,
      "created_at": "2025-10-15T12:30:17.294468Z",
      "updated_at": "2025-10-15T12:30:17.294468Z",
      
      "has_guidewire_numbers": true,
      "policycenter_search_ready": true
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 50,
    "offset": 0,
    "has_more": false
  },
  "timestamp": "2025-10-15T14:25:30.123456Z"
}
```

### UI Usage
- Display submissions in a table/list
- Show search-ready status with `policycenter_search_ready` flag
- Use `guidewire_account_number` and `guidewire_job_number` for PolicyCenter search
- Implement pagination with `offset` and `limit`

---

## 2. Get Submission Detail

**GET** `/api/guidewire/submissions/{work_item_id}`

Get detailed information for a specific work item including all Guidewire data and business information.

### Path Parameters
- `work_item_id` (int): The work item ID

### Response Example
```json
{
  "work_item_id": 87,
  "submission_id": 87,
  "title": "New test email for Cyber Submission",
  "description": "Cyber insurance submission from email intake",
  "status": "Pending",
  "priority": "Medium",
  
  "guidewire": {
    "account_id": "pc:S-v7XpouN04iLx8kW8cev",
    "job_id": "pc:Su3nrO9cV2UMd9zYEYEmM",
    "account_number": "1296620652",
    "job_number": "0001982331",
    "has_complete_data": true,
    "policycenter_search_url": "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/pc/PolicyCenter.do#search",
    "search_instructions": {
      "account_search": "Use Account Number: 1296620652",
      "job_search": "Use Job Number: 0001982331"
    }
  },
  
  "business_info": {
    "industry": "technology",
    "policy_type": "cyber liability",
    "coverage_amount": 50000,
    "company_size": null,
    "risk_score": 7.2
  },
  
  "contact_info": {
    "sender_email": "test@example.com",
    "assigned_to": null,
    "contact_name": "John Smith",
    "contact_phone": "555-123-4567"
  },
  
  "address_info": {
    "business_address": "123 Business St",
    "business_city": "San Francisco",
    "business_state": "CA",
    "business_zip": "94105"
  },
  
  "extracted_fields": {
    // All extracted data from email/attachments
  },
  
  "created_at": "2025-10-15T12:30:17.294468Z",
  "updated_at": "2025-10-15T12:30:17.294468Z",
  "timestamp": "2025-10-15T14:25:30.123456Z"
}
```

### UI Usage
- Display detailed submission view
- Show PolicyCenter search instructions with copy-paste buttons
- Link to PolicyCenter with pre-filled search parameters
- Display business context and contact information

---

## 3. Search Submissions

**GET** `/api/guidewire/search`

Search for submissions by various Guidewire-related criteria.

### Query Parameters
- `account_number` (string, optional): Search by Guidewire account number
- `job_number` (string, optional): Search by Guidewire job number  
- `company_name` (string, optional): Search by company name in title/subject
- `email` (string, optional): Search by sender email address

### Response Example
```json
{
  "matches": [
    {
      "work_item_id": 87,
      "title": "New test email for Cyber Submission", 
      "guidewire_account_number": "1296620652",
      "guidewire_job_number": "0001982331",
      "sender_email": "test@example.com",
      "status": "Pending",
      "created_at": "2025-10-15T12:30:17.294468Z",
      "match_score": 1.0
    }
  ],
  "total_found": 1,
  "search_criteria": {
    "account_number": "1296620652",
    "job_number": null,
    "company_name": null,
    "email": null
  },
  "timestamp": "2025-10-15T14:25:30.123456Z"
}
```

### UI Usage
- Implement search functionality
- Allow users to search by account/job numbers from PolicyCenter
- Provide reverse lookup (find submission by Guidewire numbers)

---

## 4. Integration Statistics

**GET** `/api/guidewire/stats`

Get statistics about Guidewire integration status for dashboard display.

### Response Example
```json
{
  "integration_stats": {
    "total_work_items": 87,
    "with_account_numbers": 25,
    "with_job_numbers": 25,  
    "complete_guidewire_data": 25,
    "integration_percentage": 28.74
  },
  "recent_activities": [
    {
      "work_item_id": 87,
      "title": "New test email for Cyber Submission",
      "account_number": "1296620652",
      "job_number": "0001982331", 
      "updated_at": "2025-10-15T12:30:17.294468Z"
    }
  ],
  "guidewire_status": "operational",
  "timestamp": "2025-10-15T14:25:30.123456Z"
}
```

### UI Usage
- Display integration health on dashboard
- Show percentage of submissions with complete Guidewire data
- List recent Guidewire activities

---

## Key Data Fields Explained

### Guidewire ID Types
- **Internal IDs** (`guidewire_account_id`, `guidewire_job_id`): Format `pc:xxxx` - used for API calls
- **Human-readable Numbers** (`guidewire_account_number`, `guidewire_job_number`): Used for PolicyCenter search

### Search-Ready Status
- `has_guidewire_numbers`: Boolean indicating if both account and job numbers are available
- `policycenter_search_ready`: Same as above, indicates if the submission can be searched in PolicyCenter

### PolicyCenter Integration
- Use `guidewire_account_number` (e.g., "1296620652") to search accounts in PolicyCenter
- Use `guidewire_job_number` (e.g., "0001982331") to search jobs/submissions in PolicyCenter
- These numbers are what users need to copy-paste into Guidewire PolicyCenter search

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `404`: Resource not found (for specific work item lookups)
- `500`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Implementation Notes

1. **Filtering**: Only returns work items that have Guidewire integration data
2. **Pagination**: Use `offset` and `limit` for large result sets
3. **Search**: All search fields use case-insensitive partial matching
4. **Real-time**: Data is current as of the API call (no caching)
5. **Performance**: Optimized queries with database indexes on Guidewire fields

## Sample UI Components

### Search Box Component
```javascript
// Search by account number
fetch('/api/guidewire/search?account_number=1296620652')
  .then(response => response.json())
  .then(data => {
    // Display search results
    console.log(`Found ${data.total_found} matches`);
  });
```

### Copy-to-Clipboard for PolicyCenter
```javascript
const copyAccountNumber = (accountNumber) => {
  navigator.clipboard.writeText(accountNumber);
  alert(`Copied account number ${accountNumber} - paste into PolicyCenter search`);
};
```

### Integration Status Badge
```javascript
const IntegrationBadge = ({ submission }) => {
  if (submission.policycenter_search_ready) {
    return <span className="badge badge-success">Search Ready</span>;
  } else {
    return <span className="badge badge-warning">Incomplete</span>;
  }
};
```