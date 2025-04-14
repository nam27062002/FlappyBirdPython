import pygame
import random
import os  # Thêm import os để đường dẫn tệp
import config as cfg  # Import tệp cấu hình chung

pygame.init()

# --- Constants ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 700
FLOOR_HEIGHT = 100
GAME_SPEED = 4

BIRD_WIDTH = 50
BIRD_HEIGHT = 50
BIRD_START_X = 100
BIRD_START_Y = 100
GRAVITY = 0.7
BIRD_JUMP_STRENGTH = 11

TUBE_WIDTH = 50
TUBE_VERTICAL_GAP = 200  # Khoảng cách dọc giữa ống trên và dưới
TUBE_HORIZONTAL_GAP = 250 # Khoảng cách ngang giữa các cặp ống
TUBE_MIN_HEIGHT = 50      # Chiều cao tối thiểu của ống (tránh ống quá ngắn)
TUBE_MAX_HEIGHT = 350     # Chiều cao tối đa của ống

WHITE = (255, 255, 255)
FONT_SIZE = 35

# --- Game Variables ---
# Screen and Display
screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird Clone")
clock = pygame.time.Clock()
game_font = pygame.font.Font('04B_19.ttf', cfg.FONT_SIZE)

# Floor
xFloor = 0

# Bird
birdMovement = 0
birdIndex = 0
posBird = [cfg.BIRD_START_X, cfg.BIRD_START_Y]
rotated_bird = None

# Tubes
tube = []
tube_up = []
xTube = []
checkScore = [0, 0, 0] # 0: chưa qua, 1: đã qua và cộng điểm

# Game State
score = 0
state = "home" # Trạng thái game: "home", "play", "game over"
die = False
running = True
e_rotated_state = 0 # Trạng thái xoay khi chết (0: chưa xoay, 1: đã xoay)
speed = cfg.GAME_SPEED # Tốc độ game hiện tại

# --- Load Assets ---
try:
    background = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.BACKGROUND_IMAGE)), 
                                       (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT)).convert()
    floor = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.FLOOR_IMAGE)), 
                                  (cfg.SCREEN_WIDTH, cfg.FLOOR_HEIGHT)).convert()
    bird_up = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.BIRD_UP_IMAGE)), 
                                    (cfg.BIRD_WIDTH, cfg.BIRD_HEIGHT)).convert_alpha()
    bird_mid = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.BIRD_MID_IMAGE)), 
                                     (cfg.BIRD_WIDTH, cfg.BIRD_HEIGHT)).convert_alpha()
    bird_down = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.BIRD_DOWN_IMAGE)), 
                                      (cfg.BIRD_WIDTH, cfg.BIRD_HEIGHT)).convert_alpha()
    tube_img = pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.TUBE_IMAGE)).convert_alpha() # Tải ảnh ống gốc
    message_img = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.MESSAGE_IMAGE)), 
                                        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)).convert_alpha()
    gameover_img = pygame.transform.scale(pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.GAMEOVER_IMAGE)), 
                                         (400, 100)).convert_alpha()

    # Sound Effects
    flap_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.FLAP_SOUND))
    hit_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.HIT_SOUND))
    score_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.SCORE_SOUND))
except pygame.error as e:
    print(f"Error loading assets: {e}")
    running = False

bird_frames = [bird_up, bird_mid, bird_down]

# --- Functions ---
def initialize_tubes():
    """Khởi tạo vị trí và kích thước ban đầu cho các ống."""
    tube.clear()
    tube_up.clear()
    xTube.clear()
    checkScore[:] = [0, 0, 0] # Reset trạng thái tính điểm
    for i in range(3):
        random_height = random.randint(cfg.TUBE_MIN_HEIGHT, cfg.TUBE_MAX_HEIGHT)
        # Vị trí X ban đầu cách nhau TUBE_HORIZONTAL_GAP, bắt đầu ngoài màn hình
        initial_x = cfg.SCREEN_WIDTH + i * cfg.TUBE_HORIZONTAL_GAP
        xTube.append(initial_x)

        # Tạo ống dưới (xoay 180 độ)
        bottom_tube_surface = pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, random_height))
        tube.append(pygame.transform.rotate(bottom_tube_surface, 180))

        # Tạo ống trên
        top_tube_height = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - random_height - cfg.TUBE_VERTICAL_GAP
        tube_up.append(pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, top_tube_height)))

def draw_floor():
    """Vẽ sàn di chuyển liên tục."""
    global xFloor
    screen.blit(floor, (xFloor, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))
    screen.blit(floor, (xFloor + cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))
    xFloor -= speed
    # Reset vị trí sàn khi nó di chuyển hết màn hình
    if xFloor <= -cfg.SCREEN_WIDTH:
        xFloor = 0

def draw_bird():
    """Vẽ con chim (xoay nếu đang chết)."""
    if rotated_bird:
        screen.blit(rotated_bird, (posBird[0], posBird[1]))
    else:
        screen.blit(bird_frames[birdIndex], (posBird[0], posBird[1]))

def apply_gravity():
    """Áp dụng trọng lực lên con chim."""
    global birdMovement
    birdMovement += cfg.GRAVITY
    posBird[1] += birdMovement

def bird_flap():
    """Làm cho chim bay lên."""
    global birdMovement
    birdMovement = 0 # Reset trọng lực tích lũy
    birdMovement = -cfg.BIRD_JUMP_STRENGTH
    flap_sound.play()

def draw_tubes():
    """Vẽ và di chuyển các ống, kiểm tra va chạm và tính điểm."""
    global score
    for i in range(3):
        # Tính toán vị trí ống trên dựa vào chiều cao ống dưới và khoảng cách
        bottom_tube_rect = tube[i].get_rect(topleft=(xTube[i], 0))
        top_tube_rect = tube_up[i].get_rect(bottomleft=(xTube[i], cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))

        # Vẽ ống
        screen.blit(tube[i], bottom_tube_rect)
        screen.blit(tube_up[i], top_tube_rect)

        # Di chuyển ống
        xTube[i] -= speed

        # Tính điểm khi chim vượt qua ống
        bird_rect = bird_frames[0].get_rect(topleft=posBird) # Dùng rect để kiểm tra
        if checkScore[i] == 0 and bottom_tube_rect.centerx < bird_rect.left:
            checkScore[i] = 1
            score += 1
            score_sound.play()

        # Reset ống khi nó ra khỏi màn hình bên trái
        if xTube[i] <= -cfg.TUBE_WIDTH:
            # Tính lại vị trí X cho ống mới (ở ngoài màn hình bên phải)
            xTube[i] = xTube[(i - 1 + 3) % 3] + cfg.TUBE_HORIZONTAL_GAP # Đặt cách ống trước đó một khoảng
            # Tạo lại kích thước ngẫu nhiên
            random_height = random.randint(cfg.TUBE_MIN_HEIGHT, cfg.TUBE_MAX_HEIGHT)
            # Tạo lại ống dưới
            bottom_tube_surface = pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, random_height))
            tube[i] = pygame.transform.rotate(bottom_tube_surface, 180)
            # Tạo lại ống trên
            top_tube_height = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - random_height - cfg.TUBE_VERTICAL_GAP
            tube_up[i] = pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, top_tube_height))
            # Reset trạng thái tính điểm cho ống này
            checkScore[i] = 0

        # Kiểm tra va chạm
        if bird_rect.colliderect(bottom_tube_rect) or bird_rect.colliderect(top_tube_rect):
             if state == "play":
                 trigger_game_over()

def check_floor_ceiling_collision():
    """Kiểm tra va chạm với sàn và trần."""
    # Va chạm trần (không cho bay quá cao)
    if posBird[1] <= 0:
        posBird[1] = 0 # Giữ chim ở mép trên
        if state == "play": # Chỉ game over nếu đang chơi
            trigger_game_over()
    # Va chạm sàn
    if posBird[1] >= cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT:
        posBird[1] = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT # Giữ chim trên sàn
        if state == "play":
            trigger_game_over()

def display_score():
    """Hiển thị điểm số hiện tại."""
    score_surface = game_font.render(f'Score: {int(score)}', True, cfg.WHITE)
    score_rect = score_surface.get_rect(center=(cfg.SCREEN_WIDTH / 2, 100))
    screen.blit(score_surface, score_rect)

def trigger_game_over():
    """Kích hoạt trạng thái Game Over."""
    global state, gravity, birdMovement, speed, die
    if state == "play": # Chỉ kích hoạt một lần
        state = "game over"
        hit_sound.play()
        die = True
        gravity = 0      # Dừng trọng lực
        birdMovement = 0 # Dừng chuyển động dọc
        speed = 0        # Dừng chuyển động ngang của màn hình
        # Lưu ý: Dòng `rotated_bird = None` đã được thêm lại ở đây trong các thay đổi của bạn.
        # Dòng này có thể không đúng logic và có thể gây lỗi như đã thảo luận.
        rotated_bird = None

def reset_game():
    """Reset các biến về trạng thái ban đầu để chơi lại."""
    global state, gravity, birdMovement, speed, die, score, birdIndex, e_rotated_state, rotated_bird
    posBird[0] = cfg.BIRD_START_X
    posBird[1] = cfg.BIRD_START_Y
    gravity = cfg.GRAVITY
    speed = cfg.GAME_SPEED
    birdMovement = 0
    birdIndex = 0
    score = 0
    die = False
    e_rotated_state = 0
    rotated_bird = None # Đảm bảo không có chim xoay khi bắt đầu
    initialize_tubes() # Tạo lại vị trí ống ban đầu
    state = "play"

# --- Timers ---
BIRD_FLAP_EVENT = pygame.USEREVENT
pygame.time.set_timer(BIRD_FLAP_EVENT, 200) # Tốc độ vỗ cánh

# --- Main Game Loop ---
initialize_tubes() # Khởi tạo ống lần đầu

while running:
    clock.tick(cfg.FPS) # Giới hạn FPS

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if state == "home":
                state = "play" # Bắt đầu chơi khi nhấn phím bất kỳ ở màn hình chờ
            elif event.key == pygame.K_SPACE:
                if state == "play":
                    bird_flap()
                elif state == "game over" and posBird[1] >= cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT:
                    # Chỉ cho phép reset khi chim đã chạm sàn
                    reset_game()

        if event.type == BIRD_FLAP_EVENT and state == "play":
            # Đổi frame hoạt ảnh vỗ cánh
            birdIndex = (birdIndex + 1) % len(bird_frames)

    # --- Game Logic ---
    if state == "play":
        apply_gravity()
        check_floor_ceiling_collision()
        # Va chạm ống được kiểm tra trong draw_tubes()
    elif state == "game over" and die:
        # Logic khi chim chết (rơi xuống)
        if e_rotated_state == 0:
            # Xoay chim khi chết lần đầu
            rotated_bird = pygame.transform.rotate(bird_frames[birdIndex], -90)
            e_rotated_state = 1
        # Làm chim rơi xuống sàn (nếu chưa chạm sàn)
        fall_speed = 7 # Tốc độ rơi khi chết
        if posBird[1] < cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT:
            posBird[1] += fall_speed
        else:
            # Giữ chim trên sàn khi đã chạm
            posBird[1] = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT

    # --- Drawing ---
    if state == "home":
        screen.blit(message_img, (0, 0))
    else:
        # Vẽ nền
        screen.blit(background, (0, 0))
        # Vẽ ống
        draw_tubes()
        # Vẽ sàn
        draw_floor()
        # Vẽ điểm
        display_score()
        # Vẽ chim
        draw_bird()
        # Vẽ màn hình Game Over khi cần
        if state == "game over" and posBird[1] >= cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT:
             screen.blit(gameover_img, (0, (cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT) / 2 - 50))

    # --- Update Display ---
    pygame.display.flip()

# --- Quit Pygame ---
pygame.quit() 