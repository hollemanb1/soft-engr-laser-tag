import pygame
import sys

# Initialize Pygame
pygame.init()

# Window setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Splash Screen")

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Font
font = pygame.font.SysFont("Arial", 72)

# Text surface
text = font.render("Welcome to Laser Tag!", True, BLUE)
text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))

# Animation variables
scale = 1
scale_speed = 0.01

clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill background
    screen.fill(BLACK)

    # Animate text scaling
    scaled_text = pygame.transform.rotozoom(text, 0, scale)
    scaled_rect = scaled_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(scaled_text, scaled_rect)
    
    scale += scale_speed
    if scale >= 1.5 or scale <= 1:
        scale_speed *= -1  # Bounce animation

    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()
