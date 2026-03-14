"""
Cloudinary Configuration & Image Upload Utilities
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
import io

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
    secure=True
)


def is_configured():
    """Check if Cloudinary is properly configured."""
    return bool(
        os.getenv("CLOUDINARY_CLOUD_NAME") and
        os.getenv("CLOUDINARY_API_KEY") and
        os.getenv("CLOUDINARY_API_SECRET")
    )


def upload_image(image_path_or_bytes, folder="smart_pharmacy", public_id=None):
    """
    Upload an image to Cloudinary.
    
    Args:
        image_path_or_bytes: File path (str) or bytes of the image
        folder: Cloudinary folder to store in
        public_id: Optional custom public ID
        
    Returns:
        dict with 'url' and 'public_id' on success, None on failure
    """
    if not is_configured():
        return None

    try:
        upload_options = {
            "folder": folder,
            "resource_type": "image",
            "overwrite": True,
        }
        if public_id:
            upload_options["public_id"] = public_id

        if isinstance(image_path_or_bytes, bytes):
            result = cloudinary.uploader.upload(
                io.BytesIO(image_path_or_bytes),
                **upload_options
            )
        else:
            result = cloudinary.uploader.upload(
                image_path_or_bytes,
                **upload_options
            )

        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None


def upload_qr_code(qr_image_path, prescription_id):
    """Upload a QR code image to Cloudinary."""
    return upload_image(
        qr_image_path,
        folder="smart_pharmacy/qr_codes",
        public_id=f"qr_{prescription_id}"
    )


def delete_image(public_id):
    """Delete an image from Cloudinary."""
    if not is_configured():
        return False
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        print(f"Cloudinary delete error: {e}")
        return False


def get_image_url(public_id, width=None, height=None):
    """Get the URL of an image with optional transformations."""
    if not is_configured():
        return None
    try:
        options = {"secure": True}
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        if width or height:
            options["crop"] = "fill"
        
        url, _ = cloudinary.utils.cloudinary_url(public_id, **options)
        return url
    except Exception as e:
        print(f"Cloudinary URL error: {e}")
        return None
