# Pygame ShadowSwap Runner

import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen setup
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('ShadowSwap Runner')

# Clock for frame rate
clock = pygame.time.Clock()
total_coins = 0
target_coins = 100
# Colors
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
# Ground level
GROUND_Y = screen_height - 50

# Game objects
player = pygame.Rect(50, GROUND_Y - 40, 40, 40)
speed = 2.0  # units/sec (initial speed set to 2.0x)
swap_mode = 'LIGHT'

# Game state
health = 100
max_health = 100
current_coins = 0
total_coins = 0
level = 1
speed_scale_timer = time.time()
last_regenerate_time = time.time()
shadow_mode_start_time = None
jump_cooldown = 0
is_jumping = False
active_notifications = []
game_over = False

# Game entities
coins = []
obstacles = []
monsters = []

# Timers for spawning
last_coin_spawn = time.time()
last_obstacle_spawn = time.time()

# Game loop
running = True
show_instructions = True  # Display tutorial overlay at start
while running:
    clock.tick(60)
    current_time = time.time()
    
    # Input handling
    key_pressed = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            key_pressed = True
            # Dismiss instruction overlay
            if show_instructions:
                show_instructions = False
            if event.key == pygame.K_SPACE and not game_over:
                # Start jump press timing
                jump_start_time = current_time
            if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if not game_over:
                    swap_mode = 'SHADOW' if swap_mode == 'LIGHT' else 'LIGHT'
            if event.key == pygame.K_r and game_over:
                # Restart game
                player = pygame.Rect(50, GROUND_Y - 40, 40, 40)
                speed = 2.0
                swap_mode = 'LIGHT'
                health = 100
                current_coins = 0
                total_coins = 0
                level = 1
                target_coins = 100
                shadow_mode_start_time = None
                is_jumping = False
                jump_cooldown = 0
                jump_start_time = 0
                active_notifications = []
                coins = []
                obstacles = []
                monsters = []
                game_over = False
                speed_scale_timer = current_time
                last_coin_spawn = current_time
                last_obstacle_spawn = current_time
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and not game_over:
                # Calculate hold duration for long jump
                hold_duration = current_time - jump_start_time if 'jump_start_time' in locals() else 0
                # Determine jump height: base 70, add up to 80 extra for holds >0.3s
                extra = min(hold_duration, 1.0) * 80  # max extra 80 at 1s hold
                jump_height = 70 + extra
                if not is_jumping and player.y >= GROUND_Y - 40 and current_time - jump_cooldown > 0.3:
                    player.y -= int(jump_height)
                    is_jumping = True
                    jump_cooldown = current_time
    # Ensure overlay is cleared after any key press
    if show_instructions and key_pressed:
        show_instructions = False



    if not game_over:
        # Update logic
        
        # Speed scaling every 10 seconds
        if current_time - speed_scale_timer >= 10:
            speed = min(speed + 0.2, 20)  # increase speed by 0.2x per interval, max 20
            speed_scale_timer = current_time

        # Apply gravity and reset jump flag
        if player.y < GROUND_Y - 40:
            player.y += 5  # Gravity
        else:
            is_jumping = False
        
        # Move player forward
        player.x += int(speed)
        
        # Keep player within screen bounds horizontally
        if player.x > screen_width - 50:
            player.x = screen_width - 50
            
        # Health regeneration in Shadow mode (every 60 frames = 1 second at 60fps)
        if swap_mode == 'SHADOW' and current_time - last_regenerate_time >= 1.0:
            health = min(health + 5, max_health)
            last_regenerate_time = current_time
        # Level progression check
        if level < 5:
            # Determine required total_coins and health thresholds per level
            thresholds = {1: (100, 80), 2: (200, 75), 3: (300, 70), 4: (400, 65)}
            req_coins, req_health = thresholds.get(level, (0, 0))
            if total_coins >= req_coins and health / max_health * 100 >= req_health:
                level += 1
                speed += 0.5
                health = min(health + 10, max_health)
                monsters.clear()
                target_coins = 100 * level
                active_notifications.append(("LEVEL UP!", current_time + 1.0))

        # Spawn coins
        if current_time - last_coin_spawn > random.uniform(1.0, 1.5):
            coin_x = random.randint(screen_width, screen_width + 200)
            coin_y = random.randint(GROUND_Y - 100, GROUND_Y - 20)
            coins.append({'rect': pygame.Rect(coin_x, coin_y, 20, 20), 'collected': False})
            last_coin_spawn = current_time

        # Spawn obstacles
        if current_time - last_obstacle_spawn > random.uniform(1.0, 2.0):
            obstacle_x = random.randint(screen_width, screen_width + 200)
            obstacle_y = GROUND_Y - 20
            obstacle_height = random.randint(20, 60)
            obstacles.append({'rect': pygame.Rect(obstacle_x, obstacle_y, 30, obstacle_height)})
            last_obstacle_spawn = current_time

        # Update coins
        for coin in coins[:]:
            coin['rect'].x -= int(speed)
            # Remove coins that go off screen
            if coin['rect'].right < 0:
                coins.remove(coin)
            # Collect coins (only in Light mode)
            elif not coin['collected'] and swap_mode == 'LIGHT' and player.colliderect(coin['rect']):
                coin['collected'] = True
                total_coins += 10
                current_coins += 10
                coins.remove(coin)

        # Update obstacles
        for obstacle in obstacles[:]:
            obstacle['rect'].x -= int(speed)
            # Remove obstacles that go off screen
            if obstacle['rect'].right < 0:
                obstacles.remove(obstacle)
            # Simple collision: if player hits obstacle, take damage and spawn monster
            elif player.colliderect(obstacle['rect']):
                health -= 10
                if health <= 0:
                    game_over = True
                monsters.append({
                    'rect': pygame.Rect(player.x, player.y, 30, 30),
                    'spawn_time': current_time,
                    'active': True
                })
                obstacles.remove(obstacle)

        # Update monsters
        for monster in monsters[:]:
            if monster['active']:
                # Move monster toward player
                if monster['rect'].x < player.x:
                    monster['rect'].x += 2
                elif monster['rect'].x > player.x:
                    monster['rect'].x -= 2
                    
                # Check collision with player
                if monster['rect'].colliderect(player):
                    health -= 30
                    if health <= 0:
                        game_over = True
                    monster['active'] = False
                    
                # Despawn after 5 seconds
                if current_time - monster['spawn_time'] > 5:
                    monsters.remove(monster)

    # Drawing
    # Camera centering
    cam_offset = player.x - 100
    screen.fill(BLACK)
    # Show tutorial overlay if needed
    if show_instructions:
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # semi‑transparent dark background
        font_big = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 32)
        lines = [
            "ShadowSwap Runner",
            "Press any key to start",
            "Controls:",
            "  Space – Jump",
            "  Shift – Toggle Light/Shadow mode",
            "  R – Restart after Game Over",
            "Collect yellow coins in Light mode for points.",
            "In Shadow mode health regenerates but coins can't be collected.",
            "Avoid obstacles and monsters.",
            "Survive as long as possible!"
        ]
        for i, txt in enumerate(lines):
            rendered = font_small.render(txt, True, (255, 255, 255))
            overlay.blit(rendered, (50, 50 + i * 40))
        screen.blit(overlay, (0, 0))
        # Skip further drawing while overlay is shown
        pygame.display.flip()
        continue

    
    # Draw ground
    pygame.draw.line(screen, WHITE, (0, GROUND_Y), (screen_width, GROUND_Y), 2)
    
    # Draw player (centered)
    player_color = YELLOW if swap_mode == 'LIGHT' else PURPLE
    player_draw_rect = pygame.Rect(100, player.y, player.width, player.height)
    pygame.draw.rect(screen, player_color, player_draw_rect)
    
    # Draw coins
    for coin in coins:
        coin_color = YELLOW if not coin['collected'] else WHITE
        draw_pos = (coin['rect'].centerx - cam_offset, coin['rect'].centery)
        pygame.draw.circle(screen, coin_color, draw_pos, 10)
        
    # Draw obstacles
    for obstacle in obstacles:
        draw_rect = obstacle['rect'].copy()
        draw_rect.x -= cam_offset
        pygame.draw.rect(screen, RED, draw_rect)
        
    # Draw monsters
    for monster in monsters:
        if monster['active']:
            draw_rect = monster['rect'].copy()
            draw_rect.x -= cam_offset
            pygame.draw.rect(screen, PURPLE, draw_rect)
    
    # Draw UI
    font = pygame.font.Font(None, 36)
    
    # Health bar
    health_bar_width = 200
    health_bar_height = 20
    health_fill = (health / max_health) * health_bar_width
    pygame.draw.rect(screen, RED, (10, 10, health_bar_width, health_bar_height))
    pygame.draw.rect(screen, GREEN, (10, 10, health_fill, health_bar_height))
    health_text = font.render(f'Health: {int(health)}%', True, WHITE)
    screen.blit(health_text, (10, 40))
    
    # Score (current coins)
    score_text = font.render(f'Score: {current_coins}', True, WHITE)
    screen.blit(score_text, (10, 80))
    # Total coins progress
    total_text = font.render(f'Total: {total_coins}/{target_coins}', True, WHITE)
    screen.blit(total_text, (10, 100))
    
    # Level
    level_text = font.render(f'Level: {level}', True, WHITE)
    screen.blit(level_text, (10, 120))
    
    # Speed multiplier
    speed_text = font.render(f'Speed: {speed:.1f}x', True, WHITE)
    screen.blit(speed_text, (10, 160))
    
    # Mode indicator
    mode_text = font.render(f'Mode: {swap_mode}', True, 
                           YELLOW if swap_mode == 'LIGHT' else PURPLE)
    screen.blit(mode_text, (10, 200))
    
    # Game over screen
    if game_over:
        game_over_font = pygame.font.Font(None, 72)
        game_over_text = game_over_font.render('GAME OVER', True, RED)
        restart_text = font.render('Press R to Restart', True, WHITE)
        screen.blit(game_over_text, (screen_width//2 - 150, screen_height//2 - 50))
        screen.blit(restart_text, (screen_width//2 - 100, screen_height//2 + 20))
    
    # Update display
    pygame.display.flip()

# Quit Pygame
pygame.quit()