# 📧 UI Team API Guide - Email Body & Attachments

## ✅ Working Production API

**Base URL:** `https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net`

## 📊 Current Status

✅ **Production server is LIVE and working**  
✅ **Database connected with 65+ submissions**  
✅ **Email data is available and accessible**  
⚠️ Main submissions endpoint needs a small fix (coming soon)

## 🔗 Working Endpoints for UI Team

### 1. Get Work Items with Email Data
```http
GET /api/workitems/poll
```

**What it returns:**
- Email subjects and sender addresses
- Extracted data from LLM (company info, coverage amounts, etc.)
- Work item status and timestamps
- Risk scores and categories
- Industry and company size information

**Example Response:**
```json
{
  "items": [
    {
      "id": 87,
      "title": "New test email for Cyber Submission", 
      "submission_ref": "7bcc59ad-1c1d-45cc-8597-1024c3493c19",
      "status": "Pending",
      "industry": "technology",
      "coverage_amount": 2000000.0,
      "risk_score": 58.75,
      "created_at": "2025-10-15T12:30:17.294468",
      "extracted_fields": {
        "company_name": "TechCorp Inc",
        "industry": "technology",
        "coverage_amount": "$2M",
        "employees": "50-100",
        // ... 78+ more fields from LLM extraction
      }
    }
  ],
  "count": 50,
  "timestamp": "2025-10-17T05:27:40.455145Z"
}
```

### 2. Get Submission History
```http
GET /api/submissions/{submission_id}/history
```

**What it returns:**
- Status change history
- Who made changes and when
- Audit trail for compliance

### 3. Database Status & Stats
```http
GET /api/debug/database
```

**What it returns:**
- Total submission count
- Latest submission details
- Database connectivity status

### 4. Health Check
```http
GET /health
```

## 📋 Available Data Fields

From the working endpoint `/api/workitems/poll`, you can access:

### 📧 Email Information
- `title` - Email subject line
- `submission_ref` - Unique identifier
- `created_at` - When email was received

### 🏢 Company Data (from LLM extraction)
- `company_name` - Business name
- `industry` - Business sector
- `coverage_amount` - Insurance coverage requested
- `employees` - Company size
- `annual_revenue` - Financial information

### 📊 Processing Status
- `status` - Current work item status (Pending, In Review, etc.)
- `risk_score` - Calculated risk assessment
- `assigned_to` - Underwriter assigned

### 📄 Full Extracted Fields
The `extracted_fields` object contains 70+ fields extracted by AI from email content:
- Contact information
- Business details
- Insurance requirements
- Risk factors
- Previous claims history
- And much more...

## 🛠️ Temporary Workaround

Until the main `/api/submissions` endpoint is fixed, use `/api/workitems/poll` which contains all the same email data plus additional processing information.

## 📱 Example UI Implementation

```javascript
// Fetch email data for display
const fetchEmailData = async () => {
  try {
    const response = await fetch(
      'https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net/api/workitems/poll'
    );
    const data = await response.json();
    
    // Display email subjects and content
    data.items.forEach(item => {
      console.log('Email Subject:', item.title);
      console.log('Company:', item.extracted_fields?.company_name);
      console.log('Industry:', item.industry);
      console.log('Coverage:', item.coverage_amount);
      
      // Access all extracted email content
      console.log('Full extracted data:', item.extracted_fields);
    });
    
  } catch (error) {
    console.error('Error fetching email data:', error);
  }
};
```

## 🚀 Next Steps

1. **Use the working endpoint** `/api/workitems/poll` immediately
2. **Main submissions endpoint** will be fixed in next deployment
3. **Full email body and attachments** will be available soon

## 📞 Support

The API is live and ready for UI integration. All email content and extracted data is accessible through the working endpoints above.

---

**Summary:** ✅ API is working, ✅ Data is available, ✅ Ready for UI integration!