"""文件上传路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.core.dependencies import get_current_user
from backend.core.exceptions import AppError
from backend.schemas.ai import FileUploadResponse
from backend.schemas.common import ApiResponse
from backend.services.file import FileService

router = APIRouter(prefix="/api/file", tags=["文件"])


@router.post(
    "/upload",
    summary="上传文件",
    response_model=ApiResponse[FileUploadResponse],
)
async def upload_file(
    file: UploadFile,
    section_id: str,
    user: dict = Depends(get_current_user),
) -> ApiResponse[FileUploadResponse]:
    """上传文件到当前会话，仅支持文本（md/txt/doc/docx）、图片（png/jpg）、PDF。"""
    service = FileService()
    try:
        result = await service.upload(file, user, section_id)
        return ApiResponse.ok(
            data=FileUploadResponse(**result),
            message="上传成功",
        )
    except AppError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
