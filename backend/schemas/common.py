from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[List[str]] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number, 1-indexed")
    limit: int = Field(20, ge=1, le=200, description="Items per page")
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_dir: Optional[str] = "desc"


class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
