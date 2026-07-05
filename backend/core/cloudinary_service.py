"""
Cloudinary Upload Service
Streams FastAPI UploadFile objects directly to Cloudinary
without writing to local disk. Returns the secure public URL.
"""

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)


def _configure_cloudinary() -> None:
    """Lazily configure the Cloudinary SDK from environment settings."""
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


async def upload_profile_picture(file: UploadFile, tenant_id: str) -> str:
    """
    Upload a profile picture to Cloudinary.

    Args:
        file: The uploaded image file from FastAPI.
        tenant_id: Used to namespace the image in Cloudinary.

    Returns:
        The secure HTTPS URL of the uploaded image.

    Raises:
        HTTPException: If the file type is invalid or upload fails.
    """
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WebP, GIF.",
        )

    # Validate file size (max 5 MB)
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5 MB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5 MB limit.",
        )

    _configure_cloudinary()

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=f"go_chicken/avatars/{tenant_id}",
            public_id="profile",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"},
            ],
        )
        secure_url = result.get("secure_url")
        logger.info("Cloudinary upload success for tenant %s: %s", tenant_id, secure_url)
        return secure_url

    except Exception as e:
        logger.error("Cloudinary upload failed for tenant %s: %s", tenant_id, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image upload to cloud storage failed. Please try again.",
        ) from e
