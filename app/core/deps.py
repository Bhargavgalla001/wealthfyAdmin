from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM


# ---------------------------------
# Swagger Authorize button support
# ---------------------------------
security = HTTPBearer()


# ---------------------------------
# Get current user from JWT
# ---------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) :

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str  = payload.get("sub")

        if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
    except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )   
    user = db.query(User).filter(User.id == UUID(user_id)).first() 
    if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid token payload"
            )
    return user

   


