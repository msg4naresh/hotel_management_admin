from pydantic import BaseModel
from datetime import datetime


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint"""

    customer_id: int
    file_url: str
    file_name: str
    uploaded_at: datetime
    document_type: str

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    """Response model for document deletion"""

    success: bool
    message: str
    customer_id: int
