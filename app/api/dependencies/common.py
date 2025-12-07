from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth_deps import get_current_user
from app.api.dependencies.s3_deps import get_s3_service
from app.db.base_db import get_db
from app.models.users import UserDB
from app.services.s3_service import S3Service

# Database Dependency
SessionDep = Annotated[Session, Depends(get_db)]

# Authentication Dependency
CurrentUserDep = Annotated[UserDB, Depends(get_current_user)]

# S3 Service Dependency
S3ServiceDep = Annotated[S3Service, Depends(get_s3_service)]
