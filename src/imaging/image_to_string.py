from pathlib import Path
from typing import Dict, List, Tuple
import cv2
import numpy as np
import config

def load_image(image_path: str) -> np.ndarray:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if path.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {path.suffix}")
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Image cannot be read by OpenCV or invalid image format: {image_path}")
    return image

def preprocess_image(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    resized = cv2.resize(image, (config.IMAGE_SIZE, config.IMAGE_SIZE))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(gray, config.CANNY_LOW_THRESHOLD, config.CANNY_HIGH_THRESHOLD)
    return gray, hsv, edges

def split_into_blocks(channel: np.ndarray) -> List[np.ndarray]:
    blocks: List[np.ndarray] = []
    count = config.IMAGE_SIZE // config.BLOCK_SIZE
    for row in range(count):
        for col in range(count):
            y0 = row * config.BLOCK_SIZE
            x0 = col * config.BLOCK_SIZE
            block = channel[y0:y0 + config.BLOCK_SIZE, x0:x0 + config.BLOCK_SIZE]
            blocks.append(block)
    return blocks

def calculate_block_features(
    gray_block: np.ndarray,
    saturation_block: np.ndarray,
    edge_block: np.ndarray,
) -> Dict[str, float]:
    brightness = float(np.mean(gray_block))
    texture = float(np.std(gray_block))
    edge_density = float(np.count_nonzero(edge_block)) / float(edge_block.size)
    contrast = float(np.max(gray_block) - np.min(gray_block))
    saturation = float(np.mean(saturation_block))
    glow_score = (brightness / 255.0) * (saturation / 255.0)
    edge_mask = edge_block > 0
    row_counts = edge_mask.sum(axis=1)
    col_counts = edge_mask.sum(axis=0)
    max_line = max(int(row_counts.max()), int(col_counts.max()))
    line_score = float(max_line) / float(config.BLOCK_SIZE)

    return {
        "brightness": brightness,
        "texture": texture,
        "edge_density": edge_density,
        "contrast": contrast,
        "saturation": saturation,
        "glow_score": glow_score,
        "line_score": line_score,
    }

def encode_block(features: Dict[str, float]) -> str:
    brightness = features["brightness"]
    texture = features["texture"]
    edge_density = features["edge_density"]
    contrast = features["contrast"]
    glow_score = features["glow_score"]
    line_score = features["line_score"]

    if glow_score > config.GLOW_THRESHOLD:
        return "G"
    if line_score > config.LINE_SCORE_THRESHOLD:
        return "L"
    if edge_density > config.EDGE_DENSITY_THRESHOLD and contrast > config.CONTRAST_THRESHOLD:
        return "E"
    if texture > config.TEXTURE_THRESHOLD:
        return "V"
    if contrast > config.CONTRAST_THRESHOLD:
        return "C"
    if brightness > config.BRIGHTNESS_THRESHOLD and texture < config.TEXTURE_THRESHOLD:
        return "T"
    if brightness < config.DARK_BRIGHTNESS_THRESHOLD and texture < config.TEXTURE_THRESHOLD:
        return "D"
    if texture < config.VERY_LOW_TEXTURE_THRESHOLD:
        return "S"
    return "H"

def image_to_visual_string(image_path: str) -> str:
    image = load_image(image_path)
    gray, hsv, edges = preprocess_image(image)
    saturation = hsv[:, :, 1]

    gray_blocks = split_into_blocks(gray)
    saturation_blocks = split_into_blocks(saturation)
    edge_blocks = split_into_blocks(edges)

    symbols: List[str] = []
    for index in range(len(gray_blocks)):
        features = calculate_block_features(
            gray_blocks[index],
            saturation_blocks[index],
            edge_blocks[index],
        )
        symbols.append(encode_block(features))
    return "".join(symbols)