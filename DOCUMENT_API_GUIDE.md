# 📋 Guidewire Quote Document API Guide for UI Team

## Overview
Complete API endpoints for retrieving and downloading quote documents from Guidewire PolicyCenter. This enables the UI to show users their insurance quotes and related documents.

## 🏗️ **Document Workflow**

### **Step 1: Check Available Documents**
```http
GET /api/guidewire/submissions/{work_item_id}/documents
```

### **Step 2: Download Specific Document**
```http
GET /api/guidewire/submissions/{work_item_id}/documents/{document_id}/download
```

### **Step 3: Generate Quote (if needed)**
```http
POST /api/guidewire/submissions/{work_item_id}/generate-quote
```

---

## 📋 **API Endpoints**

### **1. Get Available Documents**
```http
GET /api/guidewire/submissions/{work_item_id}/documents
```

**Purpose**: Retrieve list of all available quote documents for a work item

**Example Response**:
```json
{
  "work_item_id": 87,
  "guidewire_job_id": "pc:xyz123",
  "guidewire_account_number": "1296620652",
  "guidewire_job_number": "0001982331",
  "documents": [
    {
      "document_id": "doc_123",
      "document_name": "Cyber Liability Quote.pdf",
      "document_type": "pdf",
      "file_size": "245KB",
      "created_date": "2025-01-15T10:30:00Z",
      "download_url": "/api/guidewire/submissions/87/documents/doc_123/download"
    },
    {
      "document_id": "doc_124", 
      "document_name": "Policy Terms.pdf",
      "document_type": "pdf",
      "file_size": "156KB",
      "created_date": "2025-01-15T10:31:00Z",
      "download_url": "/api/guidewire/submissions/87/documents/doc_124/download"
    }
  ],
  "documents_count": 2,
  "quote_info": {
    "premium": "$2,500",
    "coverage": "$1,000,000",
    "effective_date": "2025-02-01"
  },
  "message": "Documents retrieved successfully"
}
```

### **2. Download Document**
```http
GET /api/guidewire/submissions/{work_item_id}/documents/{document_id}/download
```

**Purpose**: Download a specific quote document (PDF, etc.)

**Response**: Binary file content with proper headers
- **Content-Type**: `application/pdf` (or appropriate type)
- **Content-Disposition**: `attachment; filename="document.pdf"`

**Usage in Frontend**:
```javascript
// Direct download link
const downloadUrl = `${baseUrl}/api/guidewire/submissions/87/documents/doc_123/download`;

// Or programmatic download
async function downloadDocument(workItemId, documentId) {
    const response = await fetch(
        `${baseUrl}/api/guidewire/submissions/${workItemId}/documents/${documentId}/download`
    );
    
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'quote-document.pdf';
        a.click();
    }
}
```

### **3. Generate Quote**
```http
POST /api/guidewire/submissions/{work_item_id}/generate-quote
```

**Purpose**: Trigger quote generation in Guidewire (creates documents if they don't exist)

**Example Response**:
```json
{
  "success": true,
  "work_item_id": 87,
  "guidewire_job_id": "pc:xyz123",
  "quote_info": {
    "premium": "$2,500",
    "coverage": "$1,000,000"
  },
  "documents_count": 2,
  "documents_url": "/api/guidewire/submissions/87/documents",
  "message": "Quote generated successfully"
}
```

---

## 🎯 **UI Integration Examples**

### **Document List Component**
```javascript
import React, { useState, useEffect } from 'react';

const DocumentsList = ({ workItemId }) => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchDocuments();
    }, [workItemId]);
    
    const fetchDocuments = async () => {
        try {
            const response = await fetch(
                `${baseUrl}/api/guidewire/submissions/${workItemId}/documents`
            );
            const data = await response.json();
            setDocuments(data.documents || []);
        } catch (error) {
            console.error('Error fetching documents:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const downloadDocument = (documentId, documentName) => {
        const downloadUrl = `${baseUrl}/api/guidewire/submissions/${workItemId}/documents/${documentId}/download`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = documentName;
        a.click();
    };
    
    if (loading) return <div>Loading documents...</div>;
    
    return (
        <div className="documents-list">
            <h3>Quote Documents</h3>
            {documents.length === 0 ? (
                <p>No documents available</p>
            ) : (
                <ul>
                    {documents.map(doc => (
                        <li key={doc.document_id}>
                            <div>
                                <strong>{doc.document_name}</strong>
                                <span>({doc.file_size})</span>
                            </div>
                            <button 
                                onClick={() => downloadDocument(doc.document_id, doc.document_name)}
                            >
                                Download
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};
```

### **Generate Quote Button**
```javascript
const GenerateQuoteButton = ({ workItemId, onQuoteGenerated }) => {
    const [generating, setGenerating] = useState(false);
    
    const generateQuote = async () => {
        setGenerating(true);
        try {
            const response = await fetch(
                `${baseUrl}/api/guidewire/submissions/${workItemId}/generate-quote`,
                { method: 'POST' }
            );
            const data = await response.json();
            
            if (data.success) {
                onQuoteGenerated(data);
                alert('Quote generated successfully!');
            } else {
                alert('Failed to generate quote: ' + data.message);
            }
        } catch (error) {
            console.error('Error generating quote:', error);
            alert('Error generating quote');
        } finally {
            setGenerating(false);
        }
    };
    
    return (
        <button 
            onClick={generateQuote} 
            disabled={generating}
            className="generate-quote-btn"
        >
            {generating ? 'Generating...' : 'Generate Quote'}
        </button>
    );
};
```

---

## 🔐 **Authentication & Headers**

All API calls should include standard headers:
```javascript
const headers = {
    'Content-Type': 'application/json',
    // Add any auth headers if required
};
```

---

## ⚡ **Error Handling**

### **Common Error Responses**:
- **404**: Work item not found
- **400**: Work item not integrated with Guidewire yet
- **500**: Server error (Guidewire connection issues)

### **Example Error Response**:
```json
{
  "work_item_id": 87,
  "documents": [],
  "documents_count": 0,
  "error": "ConnectionError",
  "message": "Failed to retrieve documents from Guidewire"
}
```

---

## 🚀 **Complete Integration Flow**

### **For UI Dashboard**:
1. **List Submissions**: Use existing `/api/guidewire/submissions` 
2. **Show Documents**: Call `/api/guidewire/submissions/{id}/documents`
3. **Download Files**: Use document `download_url` directly
4. **Generate Quotes**: POST to `/api/guidewire/submissions/{id}/generate-quote`

### **User Experience Flow**:
1. User sees list of submissions with Guidewire integration
2. User clicks "View Documents" → API calls documents endpoint
3. User sees list of available PDFs (quotes, terms, etc.)
4. User clicks "Download" → Browser downloads the file
5. If no documents exist, user can click "Generate Quote"

---

## ✅ **Testing the APIs**

### **Production Base URL**:
```
https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net
```

### **Test Work Item**:
- **Work Item ID**: 87
- **Has Guidewire Integration**: ✅ Account: 1296620652, Job: 0001982331

### **Test Endpoints**:
```bash
# Get documents for Work Item 87
curl "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net/api/guidewire/submissions/87/documents"

# Generate quote for Work Item 87
curl -X POST "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net/api/guidewire/submissions/87/generate-quote"
```

---

**🎉 The UI team now has complete document management capabilities integrated with Guidewire PolicyCenter!**