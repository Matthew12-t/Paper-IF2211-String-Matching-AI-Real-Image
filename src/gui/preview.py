import base64
from typing import Optional
import cv2

def load_thumbnail(image_path: str, size: int = 256) -> Optional[str]:
    image = cv2.imread(image_path)
    if image is None:
        return None
    height, width = image.shape[:2]
    if height == 0 or width == 0:
        return None
    scale = size / float(max(height, width))
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    resized = cv2.resize(image, (new_width, new_height))
    success, buffer = cv2.imencode(".png", resized)
    if not success:
        return None
    return base64.b64encode(buffer.tobytes()).decode("ascii")