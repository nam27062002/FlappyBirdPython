"""
Tệp cấu hình chung cho các phiên bản FlappyBird
Chứa các hằng số và thông số được sử dụng trong cả hai phiên bản
"""

# --- Màn hình & Hiển thị ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
FLOOR_HEIGHT = 100
GAME_SPEED = 4
FPS = 60

# --- Chim ---
BIRD_WIDTH = 50
BIRD_HEIGHT = 50
BIRD_START_X = 100
BIRD_START_Y = 100
GRAVITY = 0.7
BIRD_JUMP_STRENGTH = 11

# --- Ống ---
TUBE_WIDTH = 50
TUBE_VERTICAL_GAP = 150  # Khoảng cách dọc giữa ống trên và dưới
TUBE_HORIZONTAL_GAP = 200  # Khoảng cách ngang giữa các cặp ống
TUBE_MIN_HEIGHT = 50  # Chiều cao tối thiểu của ống (tránh ống quá ngắn)
TUBE_MAX_HEIGHT = 350  # Chiều cao tối đa của ống

# --- Màu sắc ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# --- Font ---
FONT_SIZE = 35

# --- Đường dẫn tệp ---
ASSETS_PATH = "assets/"
SOUND_PATH = "sound/"

# --- Tên tệp hình ảnh ---
BACKGROUND_IMAGE = "background-night.png"
FLOOR_IMAGE = "floor.png"
BIRD_UP_IMAGE = "yellowbird-upflap.png"
BIRD_MID_IMAGE = "yellowbird-midflap.png"
BIRD_DOWN_IMAGE = "yellowbird-downflap.png"
TUBE_IMAGE = "pipe-green.png"
MESSAGE_IMAGE = "message.png"
GAMEOVER_IMAGE = "gameover.png"

# --- Tên tệp âm thanh ---
FLAP_SOUND = "sfx_wing.wav"
HIT_SOUND = "sfx_hit.wav"
SCORE_SOUND = "sfx_point.wav"

# --- AI Config ---
NEAT_CONFIG_PATH = "config-feedforward.txt"
AI_POPULATION_SIZE = 50
MAX_GENERATIONS = 100 