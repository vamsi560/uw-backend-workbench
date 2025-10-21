# UW Backend Workbench

## 🚀 Overview

A comprehensive underwriting backend system for processing email submissions, risk assessment, and Guidewire integration.

## 📁 Project Structure

### Core Application Files
- **`main.py`** - FastAPI application with all API endpoints
- **`database.py`** - Database models and connection handling
- **`models.py`** - Pydantic models for API requests/responses
- **`config.py`** - Application configuration settings
- **`run.py`** - Application runner script

### Business Logic
- **`business_config.py`** - Business rules and configuration
- **`business_rules.py`** - Business logic for underwriting decisions
- **`underwriting_workflow.py`** - Underwriting workflow management
- **`risk_assessment_api.py`** - Risk assessment endpoints
- **`risk_assessment_engine.py`** - Risk calculation engine

### Integration Services
- **`guidewire_integration.py`** - Complete Guidewire API integration
- **`llm_service.py`** - LLM service for data extraction
- **`file_parsers.py`** - Email and attachment parsing
- **`azure_config.py`** - Azure service configuration

### Document & Communication
- **`document_management.py`** - Document handling and storage
- **`quote_management.py`** - Quote generation and management
- **`user_notification_system.py`** - User notifications
- **`system_dashboard.py`** - Dashboard and monitoring

### Utilities
- **`logging_config.py`** - Logging configuration
- **`startup.sh`** - Application startup script
- **`web.config`** - Web server configuration

## 📋 Dependencies

- **`requirements.txt`** - Python dependencies
- **`requirements-azure.txt`** - Azure-specific dependencies

## 📚 Documentation

- **`DOCUMENT_API_GUIDE.md`** - Document API usage guide
- **`EMAIL_API_SOLUTION.md`** - Email content API documentation
- **`GUIDEWIRE_API_DOCUMENTATION.md`** - Guidewire integration guide
- **`UI_TEAM_API_GUIDE.md`** - Complete API guide for UI team

## 🗂️ Data & Configuration

- **`guidewire/`** - Guidewire configuration files and examples
- **`uploads/`** - File upload directory
- **`production_openapi.json`** - OpenAPI specification

## 🚀 Key Features

### ✅ Email Processing Pipeline
- Email intake and parsing
- Attachment extraction and processing
- LLM-powered data extraction
- Automatic work item creation

### ✅ Underwriting Workflow
- Risk assessment and scoring
- Business rules evaluation
- Approval/Rejection workflow
- History tracking and audit trail

### ✅ Guidewire Integration
- Account and submission creation
- UW issues approval workflow
- Submission rejection (decline)
- Quote generation and document retrieval

### ✅ API Endpoints
- **Email Content APIs** - Access to email body and attachments
- **Work Item Management** - Complete CRUD operations
- **Approval/Rejection** - Underwriter decision endpoints
- **Document Access** - Quote and document retrieval
- **Risk Assessment** - Risk scoring and evaluation

### ✅ Production Ready
- Azure deployment configuration
- Comprehensive error handling
- Logging and monitoring
- Database management
- File upload handling

## 🔧 API Usage

### Work Item Management
```bash
GET /api/workitems/poll          # Get work items
GET /api/workitems/{id}          # Get specific work item
POST /api/workitems/{id}/approve # Approve submission
POST /api/workitems/{id}/reject  # Reject submission
```

### Email Content Access
```bash
GET /api/workitems/email-content # Get email content for work items
GET /api/submissions/raw         # Get raw submission data
```

### Risk Assessment
```bash
POST /api/risk-assessment        # Calculate risk scores
```

## 🚀 Deployment

The application is configured for Azure deployment with:
- FastAPI backend
- PostgreSQL database
- File storage handling
- Guidewire API integration
- Email processing pipeline

## 📊 Management Requirements: ✅ FULFILLED

- ✅ **Email body and attachment display APIs** - Fully implemented
- ✅ **Approval workflow** - Complete Guidewire integration
- ✅ **Rejection workflow** - Complete decline functionality
- ✅ **Risk assessment** - Automated scoring system
- ✅ **Document management** - Quote and document handling
- ✅ **Work item tracking** - Complete lifecycle management

**All core underwriting system requirements are implemented and production-ready.**