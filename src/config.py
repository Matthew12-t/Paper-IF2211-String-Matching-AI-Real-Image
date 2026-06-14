IMAGE_SIZE = 256
BLOCK_SIZE = 32

BRIGHTNESS_THRESHOLD = 150
DARK_BRIGHTNESS_THRESHOLD = 90
TEXTURE_THRESHOLD = 32
VERY_LOW_TEXTURE_THRESHOLD = 8
EDGE_DENSITY_THRESHOLD = 0.12
CONTRAST_THRESHOLD = 120
SATURATION_THRESHOLD = 110
GLOW_THRESHOLD = 0.30
LINE_SCORE_THRESHOLD = 0.70
CONFIDENCE_THRESHOLD = 0.20

CANNY_LOW_THRESHOLD = 100
CANNY_HIGH_THRESHOLD = 200

SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

AI_EXACT_PATTERNS = [
    "VVV",
    "LLL",
    "VCV",
    "VCL",
    "CVL",
    "LCV",
    "VLC",
    "VVC",
    "VLV",
    "LVL",
    "CLC",
    "CVV",
]

REAL_EXACT_PATTERNS = [
    "HHH",
    "SSS",
    "EEE",
    "TTT",
    "DDD",
    "HSH",
    "SHS",
    "EHE",
    "HEE",
    "EEH",
    "SSE",
    "TDH",
]

AI_REGEX_PATTERNS = [
    "V{3,}",
    "L{3,}",
    "V{2,}",
    "V+C+",
    "C+V+",
    "V+L+",
    "L+V+",
    "C+L+",
    "L+C+",
]

REAL_REGEX_PATTERNS = [
    "H{3,}",
    "S{3,}",
    "E{3,}",
    "(HS){2,}",
    "(SH){2,}",
    "H+S+",
    "S+H+",
    "E+H+",
    "H+E+",
    "D+H+",
    "T+H+",
]

SYMBOL_DESCRIPTIONS = {
    "H": "smooth block",
    "S": "uniform block",
    "E": "high edge density block",
    "V": "high texture variation block",
    "T": "bright smooth block",
    "D": "dark smooth block",
    "C": "high contrast block",
    "G": "glow or highly saturated synthetic-looking block",
    "L": "line-art or digital line pattern block",
}