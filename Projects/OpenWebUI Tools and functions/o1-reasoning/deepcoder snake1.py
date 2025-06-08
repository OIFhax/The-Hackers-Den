import pygame
import random

# Initialize Pygame and set up the game window
pygame.init()
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Simple Snake Game")

# Colors and game settings
black = (0, 0, 0)
white = (255, 255, 255)

# Snake and food properties
snake_block = 15
speed = 0.15

# Initialize snake and food
snake_x = screen.get_width() // 2
snake_y = screen.get_height() // 2
food_x = round(random.randrange(0, screen.get_width() - snake_block) / snake_block) * snake_block
food_y = round(random.randrange(0, screen.get_height() - snake_block) / snake_block) * snake_block

# Game variables
direction = 'right'
snake_list = [[snake_x, snake_y]]
score = 0
clock = pygame.time.Clock()

def display_score():
    font = pygame.font.SysFont(None, 25)
    score_text = font.render(f"Score: {score}", True, white)
    screen.blit(score_text, (0, 0))

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and direction != 'right':
                direction = 'left'
            elif event.key == pygame.K_RIGHT and direction != 'left':
                direction = 'right'
            elif event.key == pygame.K_UP and direction != 'down':
                direction = 'up'
            elif event.key == pygame.K_DOWN and direction != 'up':
                direction = 'down'

    # Move the snake
    if direction == 'right':
        snake_x += snake_block
    elif direction == 'left':
        snake_x -= snake_block
    elif direction == 'up':
        snake_y -= snake_block
    elif direction == 'down':
        snake_y += snake_block

    # Wrap around the screen edges
    if snake_x >= screen.get_width():
        snake_x = 0
    elif snake_x < 0:
        snake_x = screen.get_width() - snake_block
    if snake_y >= screen.get_height():
        snake_y = 0
    elif snake_y < 0:
        snake_y = screen.get_height() - snake_block

    # Check for collisions
    snake_head = (snake_x, snake_y)
    if snake_head in snake_list[:-1]:
        break
    
    # Check if food is eaten
    if snake_x == food_x and snake_y == food_y:
        food_x = round(random.randrange(0, screen.get_width() - snake_block) / snake_block) * snake_block
        food_y = round(random.randrange(0, screen.get_height() - snake_block) / snake_block) * snake_block
        score += 1
    else:
        snake_list.pop(0)

    # Update the snake's position
    snake_list.append([snake_x, snake_y])

    # Draw everything on the screen
    screen.fill(black)
    pygame.draw.rect(screen, (255, 0, 0), (food_x, food_y, snake_block, snake_block))
    for x in snake_list:
        pygame.draw.rect(screen, (0, 255, 0), (x[0], x[1], snake_block, snake_block))
    
    display_score()
    pygame.display.update()
    clock.tick(1 / speed)

# Exit the game
pygame.quit()