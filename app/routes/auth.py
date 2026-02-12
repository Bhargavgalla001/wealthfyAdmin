from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
# from fastapi.security import OAuth2PasswordRequestFormd

from app.schemas.auth import RegisterRequest
from app.core.security import hash_password

from app.models.role import Role

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])




@router.post("/register", status_code=201)
def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
     # ✅ Fetch default user role
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        raise HTTPException(status_code=500, detail="Default role not found")

    # Create new user
    new_user = User(
        email=register_data.email,
        hashed_password=hash_password(register_data.password),
        role_id=user_role.id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }



@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }