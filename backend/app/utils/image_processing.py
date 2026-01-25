import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image for better OCR accuracy.
    
    Steps:
    1. Convert to grayscale
    2. Apply Gaussian blur to reduce noise
    3. Apply adaptive thresholding
    4. Denoise
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised


def resize_image(image: np.ndarray, max_width: int = 2000) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    Larger images generally give better OCR results up to a point.
    """
    height, width = image.shape[:2]
    
    if width > max_width:
        scale = max_width / width
        new_width = max_width
        new_height = int(height * scale)
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized
    
    return image


def detect_text_regions(image: np.ndarray) -> list:
    """
    Detect text regions in the image using contour detection.
    Returns list of bounding boxes (x, y, w, h).
    """
    # Find contours
    contours, _ = cv2.findContours(
        image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Filter contours by area and get bounding boxes
    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # Filter out very small or very large regions
        if 100 < area < 50000:
            text_regions.append((x, y, w, h))
    
    # Sort by y-coordinate (top to bottom)
    text_regions.sort(key=lambda box: box[1])
    
    return text_regions


def image_to_pil(image: np.ndarray) -> Image.Image:
    """
    Convert numpy array to PIL Image.
    """
    return Image.fromarray(image)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    return enhanced


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew image if it's rotated.
    """
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated
