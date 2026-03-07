from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth_deps import get_current_user
from app.api.dependencies.s3_deps import StorageService, get_s3_service
from app.db.base_db import get_db
from app.models.users import UserDB

# Database Dependency
SessionDep = Annotated[Session, Depends(get_db)]

# Authentication Dependency
CurrentUserDep = Annotated[UserDB, Depends(get_current_user)]

# Storage Service Dependency (S3 or Local, depending on config)
S3ServiceDep = Annotated[StorageService, Depends(get_s3_service)]
