import cv2
import numpy as np


def _load_image(source):
    """Load an image from a path, bytes, or file-like object."""
    if isinstance(source, (bytes, bytearray)):
        arr = np.frombuffer(source, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if hasattr(source, "read"):
        data = source.read()
        if isinstance(data, str):
            data = data.encode()
        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if isinstance(source, str):
        return cv2.imread(source)

    return None


def scan_qr(image_source):
    img = _load_image(image_source)
    if img is None:
        return None

    detector = cv2.QRCodeDetector()

    data, bbox, _ = detector.detectAndDecode(img)
    if data:
        return data

    # Fallback preprocessing to improve QR detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    data, bbox, _ = detector.detectAndDecode(thresh)
    if data:
        return data

    adapt = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    data, bbox, _ = detector.detectAndDecode(adapt)
    if data:
        return data

    return None