import sys
import pygame

# configurations for timing of the animation

WIDTH, HEIGHT = 1080, 720   # Screen dimensions
SPLASH_MS = 1500            # Show text before the TV turn-off
SHUTTER_MS = 700           # Total TV shutter time (top+bottom close)
FLASH_MS = 700              # White scanline flash time
FLASH_ADVANCE = 150         # Start flash a bit before shutter end
FPS = 120                   # Frame rate
BAND_HEIGHT = 6     # ~1 inch on a 96-DPI-ish display
HOLD_MS = 150       # how long to hold the band
FADE_MS = 500        # how long to fade inward
TARGET_R = 55
GROW_OFFSET = 0  # start circle growth ~60% into the band fade
GROW_DUR = FADE_MS               # grow to full size by end of band fade

# we will have 5 states:

STATE_SPLASH, STATE_TV, STATE_BAND_HOLD, STATE_BAND_FADE, STATE_MAIN = range(5)         # range = (0,1,2,3,4)

# now we will make functions to help us with the animation

def clamp(x, a, b):  # bounds the value of x between a and b
    # forces x to be between a and b
    return max(a, min(b, x))

def smooth_step(x):
    # smooth 0..1 easing function for nice non-linear motion (slow start/end)
    x = clamp(x, 0, 1)
    return x * x * (3 - 2 * x)

# now we can begin drawing out shutters/rectangles


def draw_shutters(surface, rect, t, color=(0, 0, 0)):
    # draw top and bottom rectangles that close from top to bottom ending in the center of screen
    t = clamp(t, 0, 1)                             # keep t between 0 and 1
    half_height = int(rect.height / 2 * t)          # how tall is each shutter

    # top & bottom shutter
    # grows from top down
    top_rect = pygame.Rect(rect.left, rect.top, rect.width, half_height)

    bottom_rect = pygame.Rect(rect.left, rect.bottom - half_height,
                              rect.width, half_height)        # grows from bottom up

    # now we draw  the rectangles with the given color (black)
    pygame.draw.rect(surface, color, top_rect)
    pygame.draw.rect(surface, color, bottom_rect)

# now we can make the flashing line function

def draw_black_shutters(surface, rect, t, band_height=96, color=(0, 0, 0)):
    """
    Start with full white screen, then black shutters close in from top and bottom,
    leaving a horizontal white band of thickness `band_height`.
    t goes 0..1 over the duration.
    """
    #  why do we clamp?
    # because if t is less than 0 or greater than 1, the calculations for the shutter heights could produce incorrect results.
    t = clamp(t, 0, 1)
    total_close = rect.height - band_height  # total black area to cover
    half_close = int((total_close / 2) * t)

    # Top shutter grows downward
    top_rect = pygame.Rect(rect.left, rect.top, rect.width, half_close)
    # Bottom shutter grows upward
    bottom_rect = pygame.Rect(rect.left, rect.bottom - half_close, rect.width, half_close)

    # Fill both shutters
    pygame.draw.rect(surface, color, top_rect)
    pygame.draw.rect(surface, color, bottom_rect)


def draw_flash_line(surface, rect, t, duration, width=38, color=(255, 255, 255)):
    # draw a shrinking and fading horizontal line in the center of the rect
    if t < 0 or t > duration:
        return
    u = t / duration          # 0..1 over the duration
    # grow thickness will be quick, reaching thickness by 15% of duration
    if u < 0.15:
        thickness = int(width * (u / 0.15))      # grow to full width
    else:
        thickness = width

    # drop in opacticty in the remaining duration of the flash
    if u <= .15:
        opacity = 1.0
    else:
        opacity = 1.0 - ((u - 0.15) / (1.0 - 0.15))   # fade out to 0

    if thickness <= 0 or opacity <= 0:
        return
    
def draw_centered_circle(surface, color=(255,255,255), radius=75, alpha=255, width=0, start_time=None, durtion=None, now=None, ease=True):
    # Create a temporary surface with per-pixel alpha
    circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)

    # Add alpha into the color
    circle_color = (*color, alpha)

    # Draw circle onto the temp surface
    pygame.draw.circle(circle_surf, circle_color, (radius, radius), radius, width)

    # Blit onto the main surface, centered
    rect = circle_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
    surface.blit(circle_surf, rect)

    
    

def draw_white_band(surface, rect, band_height=BAND_HEIGHT, width_frac=1.0):
    """Draw a centered white horizontal band with width_frac (0..1) of screen width."""
    width_frac = clamp(width_frac, 0.0, 1.0)
    w = max(0, int(rect.width * width_frac))
    h = band_height
    cx, cy = rect.centerx, rect.centery
    band_rect = pygame.Rect(0, 0, w, h)
    band_rect.center = (cx, cy)
    pygame.draw.rect(surface, (255, 255, 255), band_rect)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TV Splash Test")
    clock = pygame.time.Clock()

    # state + timers
    state = STATE_SPLASH
    t0 = pygame.time.get_ticks()  # ms since pygame.init()

    # simple text setup for splash/main screens
    font = pygame.font.SysFont(None, 72)
    small = pygame.font.SysFont(None, 32)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = pygame.time.get_ticks()
        screen.fill((10, 10, 14))
        full = screen.get_rect()

        if state == STATE_SPLASH:
            # show a centered title
            title = font.render("Laser Tag", True, (0, 255, 255))
            sub = small.render("by Brody Holleman, Warren Roberts, Sam Kim, Mark Livingston", True, (160, 200, 200))
            screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 30)))
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 30)))

            if now - t0 >= SPLASH_MS:
                state = STATE_TV
                t0 = now  # start the white->black shutter

        elif state == STATE_TV:
            # White screen, black shutters close, leaving a white band
            elapsed = now - t0
            screen.fill((255, 255, 255))
            t = clamp(elapsed / SHUTTER_MS, 0.0, 1.0)
            draw_black_shutters(screen, full, t, band_height=BAND_HEIGHT)

            if elapsed >= SHUTTER_MS:
                state = STATE_BAND_HOLD
                t0 = now

        elif state == STATE_BAND_HOLD:
            # Keep background black, show full-width white band for HOLD_MS
            elapsed = now - t0
            screen.fill((0, 0, 0))
            draw_white_band(screen, full, BAND_HEIGHT, width_frac=1.0)

            if elapsed >= HOLD_MS:
                state = STATE_BAND_FADE
                t0 = now

        elif state == STATE_BAND_FADE:
            # Shrink white band from both sides toward center over FADE_MS
            elapsed = now - t0
            screen.fill((0, 0, 0))

            fraction = clamp(elapsed / FADE_MS, 0.0, 1.0)     
            draw_white_band(screen, full, BAND_HEIGHT,  1.0 - fraction)

            growth = clamp((elapsed - GROW_OFFSET) / GROW_DUR, 0.0, 1.0)
            growth = smooth_step(growth)           

            radius = max(1, int(TARGET_R * growth))
            alpha = max(40, int(255 * growth))

            draw_centered_circle(screen, color=(255,255,255), radius=radius, alpha=alpha, width=0)


            if elapsed >= FADE_MS:
                state = STATE_MAIN
                t0 = now


        else:  # STATE_MAIN
            msg = font.render("Main Screen", True, (240, 240, 240))
            screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2)))

        pygame.display.flip()
        clock.tick(FPS)



    pygame.quit()
    sys.exit()

