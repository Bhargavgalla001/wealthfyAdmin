from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password
from app.core.deps import get_current_user
from app.models.role import Role

router = APIRouter(prefix="/users", tags=["Users"])


# -------------------- CREATE USER --------------------
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    

    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role_id=user_in.role_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -------------------- LIST USERS --------------------
@router.get("", response_model=list[UserResponse])
def list_users(
    role: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    query = db.query(User)

    # ✅ Filtering by role
    if role:
        query = query.join(User.role).filter(Role.name == role)

    # ✅ Pagination
    query = query.offset(offset).limit(limit)

    return query.all()



# -------------------- GET SINGLE USER --------------------
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# -------------------- UPDATE USER --------------------
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_in.dict(exclude_unset=True)

    # 🔐 Secure password update
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# -------------------- DELETE USER --------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()