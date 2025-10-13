"""
Document Management System
Handles document upload, storage, analysis, and annotation for insurance submissions
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import os
import uuid
import base64
import logging
import mimetypes
from io import BytesIO

from database import get_db, WorkItem, Submission, WorkItemHistory
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
document_router = APIRouter(prefix="/api/documents", tags=["Document Management"])

# Pydantic models
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_date: datetime
    work_item_id: int
    analysis_status: str
    download_url: str

class DocumentAnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = Field(description="Type of analysis: 'text_extraction', 'risk_analysis', 'compliance_check'")
    analyst: str = Field(default="System")

class DocumentAnnotationRequest(BaseModel):
    document_id: str
    annotations: List[Dict[str, Any]] = Field(description="List of annotations with coordinates and text")
    annotated_by: str
    notes: Optional[str] = None

class DocumentSearchRequest(BaseModel):
    work_item_id: Optional[int] = None
    filename_pattern: Optional[str] = None
    content_search: Optional[str] = None
    mime_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

# In-memory document storage (in production, use cloud storage)
class DocumentStore:
    def __init__(self):
        self.documents = {}
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
    def store_document(self, document_id: str, file_data: bytes, metadata: Dict[str, Any]) -> str:
        """Store document data and metadata"""
        file_path = self.upload_dir / f"{document_id}_{metadata['filename']}"
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        self.documents[document_id] = {
            **metadata,
            'file_path': str(file_path),
            'file_size': len(file_data)
        }
        
        return str(file_path)
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata"""
        return self.documents.get(document_id)
    
    def get_document_data(self, document_id: str) -> Optional[bytes]:
        """Retrieve document file data"""
        doc_info = self.documents.get(document_id)
        if not doc_info or not os.path.exists(doc_info['file_path']):
            return None
        
        with open(doc_info['file_path'], 'rb') as f:
            return f.read()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document and its file"""
        doc_info = self.documents.get(document_id)
        if not doc_info:
            return False
        
        try:
            if os.path.exists(doc_info['file_path']):
                os.remove(doc_info['file_path'])
            del self.documents[document_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def search_documents(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search documents based on criteria"""
        results = []
        
        for doc_id, doc_info in self.documents.items():
            matches = True
            
            # Check work_item_id
            if criteria.get('work_item_id') and doc_info.get('work_item_id') != criteria['work_item_id']:
                matches = False
            
            # Check filename pattern
            if criteria.get('filename_pattern'):
                pattern = criteria['filename_pattern'].lower()
                if pattern not in doc_info.get('filename', '').lower():
                    matches = False
            
            # Check mime type
            if criteria.get('mime_type') and doc_info.get('mime_type') != criteria['mime_type']:
                matches = False
            
            # Check date range
            upload_date = doc_info.get('upload_date')
            if isinstance(upload_date, str):
                upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            
            if criteria.get('date_from') and upload_date and upload_date < criteria['date_from']:
                matches = False
            
            if criteria.get('date_to') and upload_date and upload_date > criteria['date_to']:
                matches = False
            
            if matches:
                results.append({**doc_info, 'document_id': doc_id})
        
        return results

# Global document store instance
document_store = DocumentStore()

@document_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    work_item_id: int = Form(...),
    uploaded_by: str = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a document for a work item
    Supports various file types including PDF, Word, Excel, images
    """
    try:
        # Validate work item exists
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Check file size (limit to 10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Validate file type (security check)
        allowed_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'text/plain',
            'text/csv'
        }
        
        if mime_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported: {mime_type}. Allowed types: PDF, Word, Excel, images, text files"
            )
        
        # Create document metadata
        metadata = {
            'filename': file.filename,
            'mime_type': mime_type,
            'work_item_id': work_item_id,
            'uploaded_by': uploaded_by,
            'upload_date': datetime.utcnow().isoformat(),
            'analysis_status': 'pending',
            'annotations': [],
            'extracted_text': None
        }
        
        # Store document
        file_path = document_store.store_document(document_id, file_content, metadata)
        
        # Create history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item_id,
            action="document_uploaded",
            changed_by=uploaded_by,
            timestamp=datetime.utcnow(),
            details={
                "document_id": document_id,
                "filename": file.filename,
                "file_size": len(file_content),
                "mime_type": mime_type
            }
        )
        db.add(history_entry)
        db.commit()
        
        # Schedule background analysis
        background_tasks.add_task(
            analyze_document_content,
            document_id,
            file_content,
            mime_type
        )
        
        logger.info(f"Document uploaded: {file.filename} for work item {work_item_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(file_content),
            mime_type=mime_type,
            upload_date=datetime.utcnow(),
            work_item_id=work_item_id,
            analysis_status="pending",
            download_url=f"/api/documents/{document_id}/download"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@document_router.get("/{document_id}")
async def get_document_info(document_id: str):
    """
    Get document metadata and analysis results
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document_id,
            **doc_info,
            "download_url": f"/api/documents/{document_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving document info: {str(e)}"
        )

@document_router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    Download document file
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_data = document_store.get_document_data(document_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="Document file not found")
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type=doc_info['mime_type'],
            headers={
                "Content-Disposition": f"attachment; filename=\"{doc_info['filename']}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading document: {str(e)}"
        )

@document_router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: str,
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform analysis on a document
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_data = document_store.get_document_data(document_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Update analysis status
        doc_info['analysis_status'] = 'in_progress'
        
        # Schedule background analysis
        background_tasks.add_task(
            perform_document_analysis,
            document_id,
            file_data,
            request.analysis_type,
            request.analyst
        )
        
        return {
            "document_id": document_id,
            "analysis_type": request.analysis_type,
            "status": "Analysis started",
            "analyst": request.analyst,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting document analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting document analysis: {str(e)}"
        )

@document_router.post("/{document_id}/annotate")
async def annotate_document(
    document_id: str,
    request: DocumentAnnotationRequest,
    db: Session = Depends(get_db)
):
    """
    Add annotations to a document
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Add new annotations
        if 'annotations' not in doc_info:
            doc_info['annotations'] = []
        
        for annotation in request.annotations:
            doc_info['annotations'].append({
                **annotation,
                'annotated_by': request.annotated_by,
                'annotation_date': datetime.utcnow().isoformat(),
                'annotation_id': str(uuid.uuid4())
            })
        
        # Create history entry
        history_entry = WorkItemHistory(
            work_item_id=doc_info['work_item_id'],
            action="document_annotated",
            changed_by=request.annotated_by,
            timestamp=datetime.utcnow(),
            details={
                "document_id": document_id,
                "annotations_added": len(request.annotations),
                "notes": request.notes
            }
        )
        db.add(history_entry)
        db.commit()
        
        logger.info(f"Document annotated: {document_id} by {request.annotated_by}")
        
        return {
            "document_id": document_id,
            "annotations_added": len(request.annotations),
            "total_annotations": len(doc_info['annotations']),
            "annotated_by": request.annotated_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error annotating document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error annotating document: {str(e)}"
        )

@document_router.post("/search")
async def search_documents(request: DocumentSearchRequest):
    """
    Search documents based on various criteria
    """
    try:
        criteria = {}
        
        if request.work_item_id:
            criteria['work_item_id'] = request.work_item_id
        if request.filename_pattern:
            criteria['filename_pattern'] = request.filename_pattern
        if request.mime_type:
            criteria['mime_type'] = request.mime_type
        if request.date_from:
            criteria['date_from'] = request.date_from
        if request.date_to:
            criteria['date_to'] = request.date_to
        
        results = document_store.search_documents(criteria)
        
        # Add download URLs
        for result in results:
            result['download_url'] = f"/api/documents/{result['document_id']}/download"
        
        return {
            "search_criteria": criteria,
            "results_count": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )

@document_router.get("/work-item/{work_item_id}")
async def get_work_item_documents(work_item_id: int):
    """
    Get all documents for a specific work item
    """
    try:
        criteria = {'work_item_id': work_item_id}
        results = document_store.search_documents(criteria)
        
        # Add download URLs and sort by upload date
        for result in results:
            result['download_url'] = f"/api/documents/{result['document_id']}/download"
        
        # Sort by upload date (newest first)
        results.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        return {
            "work_item_id": work_item_id,
            "document_count": len(results),
            "documents": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving work item documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving work item documents: {str(e)}"
        )

@document_router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    deleted_by: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Delete a document
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        work_item_id = doc_info.get('work_item_id')
        filename = doc_info.get('filename')
        
        # Delete the document
        success = document_store.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        # Create history entry
        if work_item_id:
            history_entry = WorkItemHistory(
                work_item_id=work_item_id,
                action="document_deleted",
                changed_by=deleted_by,
                timestamp=datetime.utcnow(),
                details={
                    "document_id": document_id,
                    "filename": filename
                }
            )
            db.add(history_entry)
            db.commit()
        
        logger.info(f"Document deleted: {document_id} ({filename}) by {deleted_by}")
        
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "deleted",
            "deleted_by": deleted_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

# Background tasks
async def analyze_document_content(document_id: str, file_data: bytes, mime_type: str):
    """
    Background task to analyze document content
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            return
        
        extracted_text = ""
        
        # Extract text based on file type
        if mime_type == 'application/pdf':
            extracted_text = extract_pdf_text(file_data)
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            extracted_text = extract_word_text(file_data)
        elif mime_type in ['text/plain', 'text/csv']:
            extracted_text = file_data.decode('utf-8', errors='ignore')
        elif mime_type.startswith('image/'):
            extracted_text = extract_image_text(file_data)
        
        # Update document info
        doc_info['extracted_text'] = extracted_text
        doc_info['analysis_status'] = 'completed'
        doc_info['analysis_date'] = datetime.utcnow().isoformat()
        
        logger.info(f"Document analysis completed for {document_id}")
        
    except Exception as e:
        logger.error(f"Error in document analysis: {str(e)}")
        doc_info = document_store.get_document(document_id)
        if doc_info:
            doc_info['analysis_status'] = 'failed'
            doc_info['analysis_error'] = str(e)

async def perform_document_analysis(document_id: str, file_data: bytes, analysis_type: str, analyst: str):
    """
    Background task to perform specific document analysis
    """
    try:
        doc_info = document_store.get_document(document_id)
        if not doc_info:
            return
        
        analysis_result = {}
        
        if analysis_type == 'text_extraction':
            analysis_result = await analyze_document_content(document_id, file_data, doc_info['mime_type'])
        elif analysis_type == 'risk_analysis':
            # Analyze document for risk factors
            extracted_text = doc_info.get('extracted_text', '')
            analysis_result = analyze_risk_factors_in_text(extracted_text)
        elif analysis_type == 'compliance_check':
            # Check for compliance issues
            extracted_text = doc_info.get('extracted_text', '')
            analysis_result = check_compliance_requirements(extracted_text)
        
        # Store analysis results
        if 'analysis_results' not in doc_info:
            doc_info['analysis_results'] = {}
        
        doc_info['analysis_results'][analysis_type] = {
            'result': analysis_result,
            'analyzed_by': analyst,
            'analysis_date': datetime.utcnow().isoformat()
        }
        
        doc_info['analysis_status'] = 'completed'
        
        logger.info(f"Document analysis '{analysis_type}' completed for {document_id} by {analyst}")
        
    except Exception as e:
        logger.error(f"Error in document analysis '{analysis_type}': {str(e)}")
        doc_info = document_store.get_document(document_id)
        if doc_info:
            doc_info['analysis_status'] = 'failed'
            doc_info['analysis_error'] = str(e)

# Utility functions for text extraction
def extract_pdf_text(file_data: bytes) -> str:
    """Extract text from PDF file"""
    try:
        # This would use a library like PyPDF2 or pdfplumber
        # For now, return placeholder
        return "[PDF text extraction not implemented - would extract actual text in production]"
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return f"Error extracting PDF text: {str(e)}"

def extract_word_text(file_data: bytes) -> str:
    """Extract text from Word document"""
    try:
        # This would use python-docx library
        # For now, return placeholder
        return "[Word document text extraction not implemented - would extract actual text in production]"
    except Exception as e:
        logger.error(f"Error extracting Word text: {str(e)}")
        return f"Error extracting Word text: {str(e)}"

def extract_image_text(file_data: bytes) -> str:
    """Extract text from image using OCR"""
    try:
        # This would use OCR library like pytesseract
        # For now, return placeholder
        return "[Image OCR not implemented - would extract text from image in production]"
    except Exception as e:
        logger.error(f"Error extracting image text: {str(e)}")
        return f"Error extracting image text: {str(e)}"

def analyze_risk_factors_in_text(text: str) -> Dict[str, Any]:
    """Analyze text for risk factors"""
    # Simple keyword-based risk analysis
    risk_keywords = {
        'cyber': ['cyber', 'hacker', 'breach', 'malware', 'ransomware'],
        'financial': ['financial', 'money', 'revenue', 'profit', 'loss'],
        'compliance': ['compliance', 'regulation', 'gdpr', 'hipaa', 'sox'],
        'operational': ['employee', 'process', 'system', 'failure']
    }
    
    text_lower = text.lower()
    risk_factors = {}
    
    for category, keywords in risk_keywords.items():
        matches = [keyword for keyword in keywords if keyword in text_lower]
        if matches:
            risk_factors[category] = {
                'detected_keywords': matches,
                'risk_level': 'medium' if len(matches) < 3 else 'high'
            }
    
    return {
        'risk_factors': risk_factors,
        'overall_risk': 'high' if len(risk_factors) > 2 else 'medium' if risk_factors else 'low'
    }

def check_compliance_requirements(text: str) -> Dict[str, Any]:
    """Check text for compliance requirements"""
    compliance_indicators = {
        'data_protection': ['gdpr', 'data protection', 'privacy policy', 'personal data'],
        'financial_regulation': ['sox', 'sarbanes', 'financial', 'audit'],
        'healthcare': ['hipaa', 'healthcare', 'medical', 'patient data'],
        'industry_specific': ['iso', 'certification', 'standard', 'compliance']
    }
    
    text_lower = text.lower()
    compliance_issues = {}
    
    for category, indicators in compliance_indicators.items():
        matches = [indicator for indicator in indicators if indicator in text_lower]
        if matches:
            compliance_issues[category] = {
                'detected_indicators': matches,
                'compliance_required': True
            }
    
    return {
        'compliance_requirements': compliance_issues,
        'requires_review': len(compliance_issues) > 0
    }

# Export router
__all__ = ["document_router"]