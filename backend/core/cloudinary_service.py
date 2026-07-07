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
    MAGIC_BYTES = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG": "image/png",
        b"RIFF": "image/webp",
        b"GIF8": "image/gif",
    }

    def _validate_image_magic(data: bytes) -> bool:
        for magic in MAGIC_BYTES:
            if data.startswith(magic):
                return True
        return False

    MAX_SIZE = 5 * 1024 * 1024
    chunks = []
    total = 0
    while chunk := await file.read(8192):
        total += len(chunk)
        if total > MAX_SIZE:
            raise HTTPException(status_code=413, detail="File exceeds 5 MB limit")
        chunks.append(chunk)
    contents = b"".join(chunks)

    if not contents or not _validate_image_magic(contents[:12]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. File signature does not match an allowed image (JPEG, PNG, WebP, GIF).",
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
