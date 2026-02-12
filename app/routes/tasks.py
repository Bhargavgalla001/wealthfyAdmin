from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.core.deps import get_current_user
from app.models.user import User
from sqlalchemy import asc, desc

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ✅ CREATE TASK
@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        owner_id=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ✅ LIST TASKS (Admin can see all)
@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    sort_by: str | None = None,
    order: str = "asc",
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 🔥 ADMIN CAN SEE ALL TASKS
    if current_user.role and current_user.role.name == "admin":
        query = db.query(Task)
    else:
        query = db.query(Task).filter(Task.owner_id == current_user.id)

    # ✅ Filtering
    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    # ✅ Sorting
    if sort_by:
        column = getattr(Task, sort_by, None)
        if column:
            if order == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

    # ✅ Pagination
    query = query.offset(offset).limit(limit)

    return query.all()


# ✅ GET SINGLE TASK
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 🔥 Admin can access any task
    if not (current_user.role and current_user.role.name == "admin"):
        if task.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

    return task


# ✅ UPDATE TASK
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 🔥 Admin can update any task
    if not (current_user.role and current_user.role.name == "admin"):
        if task.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# ✅ DELETE TASK
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 🔥 Admin can delete any task
    if not (current_user.role and current_user.role.name == "admin"):
        if task.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(task)
    db.commit()