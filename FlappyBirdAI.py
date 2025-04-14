import pygame
import random
import os
import time
import neat
import pickle
import config as cfg  # Import tệp cấu hình

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
TUBE_VERTICAL_GAP = 150  # Giảm xuống từ 200 - Khoảng cách dọc giữa ống trên và dưới
TUBE_HORIZONTAL_GAP = 200 # Giảm xuống từ 250 - Khoảng cách ngang giữa các cặp ống
TUBE_MIN_HEIGHT = 50      # Chiều cao tối thiểu của ống
TUBE_MAX_HEIGHT = 350     # Chiều cao tối đa của ống

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
FONT_SIZE = 35

GEN = 0  # Generation counter
MAX_FITNESS = 0  # Max fitness across all generations
LAST_SAVED_SCORE = 0  # Lưu điểm số cuối cùng khi lưu best bird
SAVE_SCORE_THRESHOLD = 5  # Chỉ lưu khi điểm tăng ít nhất 5 so với lần lưu trước

# --- Game Setup ---
screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird AI")
clock = pygame.time.Clock()

# Load assets
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
    tube_img = pygame.image.load(os.path.join(cfg.ASSETS_PATH, cfg.TUBE_IMAGE)).convert_alpha()
    
    # Sound Effects
    flap_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.FLAP_SOUND))
    hit_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.HIT_SOUND))
    score_sound = pygame.mixer.Sound(os.path.join(cfg.SOUND_PATH, cfg.SCORE_SOUND))
except pygame.error as e:
    print(f"Error loading assets: {e}")
    pygame.quit()
    exit()

bird_frames = [bird_up, bird_mid, bird_down]

# Font for stats display
font = pygame.font.SysFont("Arial", 24)

class Bird:
    """Class representing the bird, controlled by AI or human."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity = 0
        self.jump_counter = 0
        self.frame_index = 0
        self.tick_count = 0
        self.rect = pygame.Rect(x, y, cfg.BIRD_WIDTH, cfg.BIRD_HEIGHT)
        self.alive = True
        self.score = 0
        self.fitness = 0
        
    def jump(self):
        """Make the bird jump."""
        self.velocity = -cfg.BIRD_JUMP_STRENGTH
        self.jump_counter += 1
        
    def move(self):
        """Update bird position."""
        if not self.alive:
            return
            
        self.tick_count += 1
        
        # Apply gravity
        self.velocity += cfg.GRAVITY
        
        # Update position
        self.y += self.velocity
        
        # Update rect for collision detection
        self.rect.y = self.y
        
        # Don't allow the bird to go above the screen
        if self.y < 0:
            self.y = 0
            self.velocity = 0
            
        # Don't allow the bird to go below the floor
        if self.y > cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT:
            self.y = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - cfg.BIRD_HEIGHT
            self.alive = False
            
    def draw(self, win):
        """Draw the bird on the screen."""
        if not self.alive:
            # Không vẽ chim đã chết
            return
        else:
            # Animate the bird flapping
            self.frame_index = (self.frame_index + 1) % len(bird_frames) if self.tick_count % 10 == 0 else self.frame_index
            win.blit(bird_frames[self.frame_index], (self.x, self.y))

class Tube:
    """Class representing a pair of tubes (obstacles)."""
    def __init__(self, x):
        self.x = x
        self.height = random.randint(cfg.TUBE_MIN_HEIGHT, cfg.TUBE_MAX_HEIGHT)
        self.passed = False
        
        # Bottom tube (upside-down)
        self.bottom_tube_surface = pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, self.height))
        self.bottom_tube = pygame.transform.rotate(self.bottom_tube_surface, 180)
        self.bottom_rect = self.bottom_tube.get_rect(topleft=(x, 0))
        
        # Top tube
        self.top_height = cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT - self.height - cfg.TUBE_VERTICAL_GAP
        self.top_tube = pygame.transform.scale(tube_img, (cfg.TUBE_WIDTH, self.top_height))
        self.top_rect = self.top_tube.get_rect(bottomleft=(x, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))
    
    def move(self):
        """Move the tube to the left."""
        self.x -= cfg.GAME_SPEED
        self.bottom_rect.x = self.x
        self.top_rect.x = self.x
    
    def draw(self, win):
        """Draw the tubes on the screen."""
        win.blit(self.bottom_tube, self.bottom_rect)
        win.blit(self.top_tube, self.top_rect)
    
    def collide(self, bird):
        """Check if the bird collides with the tubes."""
        if bird.rect.colliderect(self.bottom_rect) or bird.rect.colliderect(self.top_rect):
            return True
        return False

def draw_floor(win, floor_x):
    """Draw the moving floor."""
    win.blit(floor, (floor_x, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))
    win.blit(floor, (floor_x + cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT - cfg.FLOOR_HEIGHT))

def draw_stats(win, birds, gen, max_fitness):
    """Draw statistics on the screen during training."""
    stats = [
        f"Generation: {gen}",
        f"Birds Alive: {len([b for b in birds if b.alive])} / {len(birds)}",
        f"Max Score: {max([b.score for b in birds])}",
        f"Max Fitness: {max_fitness:.2f}"
    ]
    
    y = 20
    for stat in stats:
        text = font.render(stat, True, WHITE)
        win.blit(text, (20, y))
        y += 25

def save_best_bird(genome, config, filename="best_bird.pickle"):
    """Save the best performing bird's neural network."""
    global LAST_SAVED_SCORE
    
    # Lấy điểm số hiện tại
    current_score = 0
    if hasattr(genome, 'score'):  # Nếu genome có thuộc tính score
        current_score = genome.score
    
    # Chỉ lưu nếu vượt qua ngưỡng điểm đã đặt
    if current_score - LAST_SAVED_SCORE >= SAVE_SCORE_THRESHOLD:
        with open(filename, "wb") as f:
            pickle.dump(genome, f)
        print(f"Best bird saved to {filename} (Score: {current_score})")
        LAST_SAVED_SCORE = current_score
        return True
    return False

def load_best_bird(filename="best_bird.pickle", config=None):
    """Load the best bird's neural network."""
    try:
        with open(filename, "rb") as f:
            genome = pickle.load(f)
            if config:
                net = neat.nn.FeedForwardNetwork.create(genome, config)
                return net, genome
            return genome
    except:
        print(f"Error loading {filename}")
        return None

def eval_genomes(genomes, config):
    """Evaluate genomes in NEAT algorithm."""
    global GEN, MAX_FITNESS
    GEN += 1
    
    # Initialize birds and neural networks
    birds = []
    networks = []
    ge = []
    
    for _, genome in genomes:
        bird = Bird(cfg.BIRD_START_X, cfg.BIRD_START_Y)
        birds.append(bird)
        
        genome.fitness = 0
        genome.score = 0  # Thêm thuộc tính score để tracking
        ge.append(genome)
        
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        networks.append(net)
    
    # Initialize game objects
    tubes = [Tube(cfg.SCREEN_WIDTH + i * cfg.TUBE_HORIZONTAL_GAP) for i in range(3)]
    floor_x = 0
    score = 0
    running = True
    stopped_early = False  # Biến để kiểm tra xem có dừng sớm không
    
    # Thêm hướng dẫn dừng
    stop_text = font.render("Press ESC to stop training and save", True, cfg.WHITE)
    
    while running and len([bird for bird in birds if bird.alive]) > 0:
        clock.tick(cfg.FPS)
        
        # Handle quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Kiểm tra phím ESC
                    stopped_early = True
                    running = False
        
        # Determine which tube is the next one
        pipe_index = 0
        if len(tubes) > 1 and birds[0].x > tubes[0].x + cfg.TUBE_WIDTH:
            pipe_index = 1
        
        # Control each bird using its neural network
        for i, bird in enumerate(birds):
            if not bird.alive:
                continue
                
            # Give fitness for staying alive
            ge[i].fitness += 0.1
            bird.fitness += 0.1
            
            # Get network inputs:
            # 1. Bird's y position
            # 2. Distance to next tube
            # 3. Height of next tube's gap
            tube_center = tubes[pipe_index].height + cfg.TUBE_VERTICAL_GAP / 2
            inputs = (
                bird.y / cfg.SCREEN_HEIGHT,  # Normalized bird height
                (tubes[pipe_index].x - bird.x) / cfg.SCREEN_WIDTH,  # Normalized horizontal distance
                (tube_center - bird.y) / cfg.SCREEN_HEIGHT  # Normalized vertical distance to gap
            )
            
            # Get network output (jump or not)
            output = networks[i].activate(inputs)
            
            # Jump if output is > 0.5
            if output[0] > 0.5:
                bird.jump()
        
        # Move birds
        for bird in birds:
            bird.move()
        
        # Move tubes
        remove_tubes = []
        for tube in tubes:
            tube.move()
            
            # Mark tube for removal if it's off screen
            if tube.x + cfg.TUBE_WIDTH < 0:
                remove_tubes.append(tube)
            
            # Check for collisions and update score
            for i, bird in enumerate(birds):
                if not bird.alive:
                    continue
                    
                # Check if bird passed the tube
                if not tube.passed and tube.x < bird.x:
                    tube.passed = True
                    bird.score += 1
                    score = max(score, bird.score)
                    
                    # Cập nhật score trong genome để theo dõi
                    ge[i].score = bird.score
                    
                    # Extra fitness for passing tube
                    ge[i].fitness += 5
                    bird.fitness += 5
                
                # Check for collision
                if tube.collide(bird):
                    bird.alive = False
        
        # Remove tubes that are off screen and add new ones
        for tube in remove_tubes:
            tubes.remove(tube)
            # Add new tube
            tubes.append(Tube(tubes[-1].x + cfg.TUBE_HORIZONTAL_GAP))
        
        # Update floor position
        floor_x -= cfg.GAME_SPEED
        if floor_x <= -cfg.SCREEN_WIDTH:
            floor_x = 0
        
        # Draw everything
        screen.blit(background, (0, 0))
        for tube in tubes:
            tube.draw(screen)
        draw_floor(screen, floor_x)
        
        # Chỉ vẽ chim còn sống
        for bird in birds:
            if bird.alive:
                bird.draw(screen)
        
        # Draw stats
        current_max_fitness = max([g.fitness for g in ge]) if ge else 0
        MAX_FITNESS = max(MAX_FITNESS, current_max_fitness)
        draw_stats(screen, birds, GEN, MAX_FITNESS)
        
        # Hiển thị hướng dẫn dừng
        screen.blit(stop_text, (20, cfg.SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
        
        # Save best bird if it reaches a significant score
        best_genome = max(ge, key=lambda g: g.fitness) if ge else None
        if best_genome and best_genome.fitness > 100:
            # Không cần lưu mỗi frame, chỉ kiểm tra định kỳ
            if pygame.time.get_ticks() % 5000 < 100:  # Kiểm tra mỗi 5 giây
                save_best_bird(best_genome, config)
    
    # Lưu chim tốt nhất nếu dừng sớm
    if stopped_early and ge:
        best_genome = max(ge, key=lambda g: g.fitness)
        save_best_bird(best_genome, config, "stopped_best.pickle")
        # Hiển thị thông báo đã lưu
        screen.fill(cfg.BLACK)
        saved_text = font.render("Training stopped. Best bird saved!", True, cfg.WHITE)
        screen.blit(saved_text, (cfg.SCREEN_WIDTH//2 - saved_text.get_width()//2, cfg.SCREEN_HEIGHT//2))
        pygame.display.flip()
        pygame.time.delay(2000)  # Delay 2 giây để hiển thị thông báo
        
        return False  # Return False to signal early stopping
    
    # Update max fitness for this run
    if ge:
        best_fitness = max([g.fitness for g in ge])
        if best_fitness > MAX_FITNESS:
            MAX_FITNESS = best_fitness
            best_genome = max(ge, key=lambda g: g.fitness)
            save_best_bird(best_genome, config)
    
    return True  # Return True to continue training

def run_neat(config_path):
    """Run NEAT algorithm to train the AI."""
    config = neat.config.Config(
        neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet, 
        neat.DefaultStagnation,
        config_path
    )
    
    # Create population
    population = neat.Population(config)
    
    # Add reporters to show progress
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Run the algorithm
    try:
        current_gen = 0
        
        # Chạy thuật toán theo từng thế hệ để có thể dừng giữa chừng
        while current_gen < cfg.MAX_GENERATIONS:
            continue_training = population.run(eval_genomes, 1)  # Chỉ chạy 1 thế hệ mỗi lần
            current_gen += 1
            
            if not continue_training:
                print("Training stopped early by user.")
                break
                
        winner = population.best_genome
        # Save the winner
        save_best_bird(winner, config, "winner.pickle")
        return winner
    except KeyboardInterrupt:
        # Xử lý khi người dùng nhấn Ctrl+C
        print("Training stopped by keyboard interrupt.")
        if population.best_genome:
            save_best_bird(population.best_genome, config, "interrupted_best.pickle")
        return population.best_genome

def play_with_best_bird(config_path):
    """Play the game with the best trained bird."""
    config = neat.config.Config(
        neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet, 
        neat.DefaultStagnation,
        config_path
    )
    
    # Load best bird
    net, genome = load_best_bird("best_bird.pickle", config)
    if not net:
        print("No saved bird found. Train first!")
        return
    
    # Initialize game
    bird = Bird(cfg.BIRD_START_X, cfg.BIRD_START_Y)
    tubes = [Tube(cfg.SCREEN_WIDTH + i * cfg.TUBE_HORIZONTAL_GAP) for i in range(3)]
    floor_x = 0
    score = 0
    running = True
    
    while running:
        clock.tick(cfg.FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Determine which tube is the next one
        pipe_index = 0
        if len(tubes) > 1 and bird.x > tubes[0].x + cfg.TUBE_WIDTH:
            pipe_index = 1
        
        # AI decision making
        if bird.alive:
            tube_center = tubes[pipe_index].height + cfg.TUBE_VERTICAL_GAP / 2
            inputs = (
                bird.y / cfg.SCREEN_HEIGHT,
                (tubes[pipe_index].x - bird.x) / cfg.SCREEN_WIDTH,
                (tube_center - bird.y) / cfg.SCREEN_HEIGHT
            )
            
            output = net.activate(inputs)
            
            if output[0] > 0.5:
                bird.jump()
        
        bird.move()
        
        # Move tubes
        remove_tubes = []
        for tube in tubes:
            tube.move()
            
            if tube.x + cfg.TUBE_WIDTH < 0:
                remove_tubes.append(tube)
            
            # Update score and check collision
            if bird.alive:
                if not tube.passed and tube.x < bird.x:
                    tube.passed = True
                    score += 1
                
                if tube.collide(bird):
                    bird.alive = False
        
        # Remove tubes and add new ones
        for tube in remove_tubes:
            tubes.remove(tube)
            tubes.append(Tube(tubes[-1].x + cfg.TUBE_HORIZONTAL_GAP))
        
        # Update floor position
        floor_x -= cfg.GAME_SPEED
        if floor_x <= -cfg.SCREEN_WIDTH:
            floor_x = 0
        
        # Draw everything
        screen.blit(background, (0, 0))
        for tube in tubes:
            tube.draw(screen)
        draw_floor(screen, floor_x)
        
        # Chỉ vẽ chim nếu còn sống
        if bird.alive:
            bird.draw(screen)
        
        # Draw score
        score_text = font.render(f"Score: {score}", True, cfg.WHITE)
        screen.blit(score_text, (20, 20))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, cfg.NEAT_CONFIG_PATH)
    
    # Main menu
    while True:
        screen.fill(cfg.BLACK)
        
        # Draw title
        title = font.render("FLAPPY BIRD AI", True, cfg.WHITE)
        screen.blit(title, (cfg.SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        # Draw options
        options = [
            "1. Train AI",
            "2. Run Best AI",
            "3. Quit"
        ]
        
        for i, option in enumerate(options):
            text = font.render(option, True, cfg.WHITE)
            screen.blit(text, (cfg.SCREEN_WIDTH//2 - text.get_width()//2, 250 + i*50))
        
        pygame.display.flip()
        
        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    run_neat(config_path)
                elif event.key == pygame.K_2:
                    play_with_best_bird(config_path)
                elif event.key == pygame.K_3:
                    pygame.quit()
                    exit()
        
        clock.tick(30) 