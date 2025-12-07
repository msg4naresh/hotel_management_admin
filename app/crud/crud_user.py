from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.users import UserCreate, UserDB, UserResponse


class CRUDUser(CRUDBase[UserDB, UserCreate, UserResponse]):
    def get_by_username(self, db: Session, *, username: str) -> UserDB | None:
        return db.query(UserDB).filter(UserDB.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserDB:
        db_obj = UserDB(
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, username: str, password: str) -> UserDB | None:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: UserDB) -> bool:
        return user.is_active


user = CRUDUser(UserDB)
