import pygame
import sys
import random
import os

pygame.init()
pygame.mixer.init()

#Window ko lagi
W, H = 900, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()

#  Colors 
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
YELLOW     = (255, 220,  50)
RED        = (255,  50,  50)
CYAN       = ( 50, 220, 255)
GREEN      = ( 80, 255, 120)
ORANGE     = (255, 150,  50)
PINK       = (255, 100, 200)
LIME       = (180, 255,  50)
DARK_RED   = (180,  20,  20)
SCORE_COL  = (200, 255, 200)

PIXEL_SIZE = 5

# Sound effects 
def load_sound(filename):
    if os.path.isfile(filename):
        return pygame.mixer.Sound(filename)
    return None

snd_shoot      = load_sound("mrfriends-pistol-shot-233473.wav")
snd_explosion  = load_sound("universfield-epic-cinematic-explosion-454857.wav")

def play(snd):
    if snd:
        snd.play()

# Background 
try: #if image exists load that else draw stars
    bg = pygame.image.load("beautiful-view-stars-night-sky.jpg")
    bg = pygame.transform.scale(bg, (W, H))
except Exception:
    bg = pygame.Surface((W, H))
    bg.fill((5, 5, 20))
    for _ in range(250):
        x, y = random.randint(0, W-1), random.randint(0, H-1)
        r = random.randint(100, 255)
        bg.set_at((x, y), (r, r, r))

def draw_background():
    screen.blit(bg, (0, 0))

# Ship 
try: #if ship exists load it esle not
    ship_image = pygame.image.load("space-invaders-tetris-video-game-arcade-game-space-invaders-thumbnail.png").convert_alpha()
    ship_image = pygame.transform.scale(ship_image, (14 * PIXEL_SIZE, 10 * PIXEL_SIZE))
    use_ship_image = True
except Exception:
    use_ship_image = False

ship_pixels = [
    "00010100",
    "00111110",
    "01111111",
    "11101011",
    "11111111",
]

def draw_ship_fallback(rect): #ship rectangle
    for row in range(len(ship_pixels)):
        for col in range(len(ship_pixels[row])):
            if ship_pixels[row][col] == "1":
                pygame.draw.rect(screen, CYAN,
                    (rect.x + col * PIXEL_SIZE,
                     rect.y + row * PIXEL_SIZE,
                     PIXEL_SIZE, PIXEL_SIZE))

ship_w = 14 * PIXEL_SIZE if use_ship_image else len(ship_pixels[0]) * PIXEL_SIZE
ship_h = 10 * PIXEL_SIZE if use_ship_image else len(ship_pixels)  * PIXEL_SIZE
ship_rect = pygame.Rect(W // 2 - ship_w // 2, H - 20 - ship_h, ship_w, ship_h)
ship_speed = 6

# Monster pixel art 
Zenomorph = [
    "00011000",
    "00111100",
    "01111110",
    "11011011",
    "11111111",
    "00100100",
    "01011010",
    "10100101",
]

Godzilla = [
    "00100000100",
    "00010001000",
    "00111111100",
    "01101110110",
    "11111111111",
    "10111111101",
    "10100000101",
    "00011011000",
]

Saucer = [
    "00111111000",
    "01111111100",
    "11101110111",
    "11111111111",
    "01110111010",
    "01000100010",
    "10000000001",
    "01000000010",
]

explosion_shape = [
    "0011100",
    "0111110",
    "1111111",
    "0111110",
    "0011100",
]

ROW_COLORS = [
    (RED,   ORANGE),
    (LIME,  YELLOW),
    (PINK,  CYAN),
]

def draw_monster(monster, x, y, color):
    for row in range(len(monster)):
        for col in range(len(monster[row])):
            if monster[row][col] == "1":
                pygame.draw.rect(screen, color,
                    (x + col * PIXEL_SIZE,
                     y + row * PIXEL_SIZE,
                     PIXEL_SIZE, PIXEL_SIZE))

# Alien  movements 
aliens = []
alien_direction = 1
alien_speed = 1
alien_drop = 20
wave = 1
 #for each row of monsters monster 
def create_aliens():
    aliens.clear()
    rows = [Zenomorph, Godzilla, Saucer]
    for row_index, monster in enumerate(rows):
        color = ROW_COLORS[row_index][0]
        for col in range(10):
            aliens.append({
                "monster": monster,
                "x": 60 + col * 80,
                "y": 100 + row_index * 70,
                "alive": True,
                "color": color,
                "row": row_index,
                "anim": 0,
            })

create_aliens()

# ── Bullets movements
player_bullets = []
alien_bullets  = []
bullet_speed   = 9
alien_bullet_speed = 4
last_alien_shot = 0
alien_fire_interval = 1500

#  Explosions 
explosions = []
EXPLOSION_DURATION = 30

# Game state 
score  = 0
lives  = 3
hi_score = 0
paused = False
game_state = "playing"
frame = 0

font       = pygame.font.SysFont("Consolas", 26, bold=True)
big_font   = pygame.font.SysFont("Consolas", 64, bold=True)
small_font = pygame.font.SysFont("Consolas", 20)

#  HUD 
def draw_hud():
    screen.blit(font.render(f"SCORE  {score:06d}", True, SCORE_COL), (10, 10))
    screen.blit(font.render(f"HI  {hi_score:06d}", True, YELLOW), (W//2 - 80, 10))
    screen.blit(font.render(f"WAVE {wave}", True, ORANGE), (W - 140, 10))
    for i in range(lives):
        pygame.draw.polygon(screen, CYAN, [
            (W - 160 + i * 30, H - 15),
            (W - 150 + i * 30, H - 30),
            (W - 140 + i * 30, H - 15),
        ])
    screen.blit(small_font.render("LIVES", True, WHITE), (W - 200, H - 30))
    pygame.draw.line(screen, (60, 60, 80), (0, H - 40), (W, H - 40), 2)

# Alien movement & firing 
def update_aliens():
    global alien_direction, last_alien_shot

    alive_aliens = [a for a in aliens if a["alive"]]
    if not alive_aliens:
        return

    move_down = False
    speed = alien_speed + (wave - 1) * 0.4

    for alien in alive_aliens:
        alien["x"] += speed * alien_direction #moving left right
        alien["anim"] = (alien["anim"] + 1) % 60

    xs = [a["x"] for a in alive_aliens]
    widths = [len(a["monster"][0]) * PIXEL_SIZE for a in alive_aliens]
    if min(xs) <= 5 or max(x + w for x, w in zip(xs, widths)) >= W - 5:
        move_down = True

    if move_down:
        alien_direction *= -1 #alien_direction= -1
        for alien in alive_aliens:
            alien["y"] += alien_drop #mobing down
    #random alien shooting for rANDOM ALIENS
    now = pygame.time.get_ticks()
    interval = max(400, alien_fire_interval - (wave - 1) * 150)
    if now - last_alien_shot > interval:
        shooter = random.choice(alive_aliens)
        ax = shooter["x"] + len(shooter["monster"][0]) * PIXEL_SIZE // 2
        ay = shooter["y"] + len(shooter["monster"])   * PIXEL_SIZE
        alien_bullets.append(pygame.Rect(ax - 2, ay, 4, 10))
        
        last_alien_shot = now

#  Player hit with flicker BECOMES INVINVIBLE FOR A SEC
player_invincible_until = 0

def player_hit():
    global lives, player_invincible_until
    now = pygame.time.get_ticks()
    if now < player_invincible_until:
        return
    lives -= 1
    player_invincible_until = now + 2000
    

def draw_ship():
    now = pygame.time.get_ticks()
    invincible = now < player_invincible_until
    if invincible and (frame // 5) % 2 == 0:
        return
    if use_ship_image:
        screen.blit(ship_image, ship_rect)
    else:
        draw_ship_fallback(ship_rect)

#  Next wave (INCREASES DIFFICULTY)
def next_wave():
    global wave, alien_direction
    wave += 1
    alien_direction = 1
    
    create_aliens()
    player_bullets.clear()
    alien_bullets.clear()
    explosions.clear()

#  Overlay screens 
def draw_overlay(title, subtitle, color):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    t = big_font.render(title, True, color)
    screen.blit(t, (W//2 - t.get_width()//2, H//2 - 60))
    s = font.render(subtitle, True, WHITE)
    screen.blit(s, (W//2 - s.get_width()//2, H//2 + 20))
    r = small_font.render("Press R to restart  |  ESC to quit", True, (180, 180, 180))
    screen.blit(r, (W//2 - r.get_width()//2, H//2 + 60))

# Reset game
def reset_game():
    global score, lives, wave, alien_direction, game_state
    score = 0
    lives = 3
    wave  = 1
    alien_direction = 1
    game_state = "playing"
    create_aliens()
    player_bullets.clear()
    alien_bullets.clear()
    explosions.clear()
    ship_rect.centerx = W // 2
    ship_rect.bottom  = H - 20

# MAIN LOOP 
def main():
    global score, lives, hi_score, paused, game_state, frame

    reset_game()

    while True:
        clock.tick(60) #FOR 60 FRAMES PER SECOND 
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if event.key == pygame.K_r:
                    reset_game()

                if game_state == "playing":
                    if event.key == pygame.K_p:
                        paused = not paused

                    if event.key == pygame.K_SPACE:
                        if len(player_bullets) < 4:
                            b = pygame.Rect(ship_rect.centerx - 2,
                                            ship_rect.top, 4, 12)
                            player_bullets.append(b)
                            play(snd_shoot)

        draw_background()

        if paused and game_state == "playing":
            p = font.render("── PAUSED ──", True, YELLOW)
            screen.blit(p, (W//2 - p.get_width()//2, H//2))
            draw_hud()
            pygame.display.update()
            continue

        if game_state != "playing":
            if game_state == "gameover":
                draw_overlay("GAME OVER", f"Final Score: {score:06d}", RED)
            elif game_state == "win":
                draw_overlay("YOU WIN!", f"Score: {score:06d}  |  Wave {wave}", GREEN)
            draw_hud()
            pygame.display.update()
            continue

        #  Player movement 
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and ship_rect.left  > 0: ship_rect.x -= ship_speed
        if keys[pygame.K_RIGHT] and ship_rect.right < W: ship_rect.x += ship_speed

        draw_ship()

        # Player bullets movements
        for b in player_bullets[:]:
            b.y -= bullet_speed
            if b.bottom < 0:
                player_bullets.remove(b)
                continue
            pygame.draw.rect(screen, YELLOW, b)

        #  Alien bullets 
        for ab in alien_bullets[:]:
            ab.y += alien_bullet_speed
            if ab.colliderect(ship_rect):
                alien_bullets.remove(ab)
                player_hit()
                if lives <= 0:
                    
                    game_state = "gameover"
                    hi_score = max(hi_score, score)
                continue
            if ab.top > H:
                alien_bullets.remove(ab)
                continue
            pygame.draw.rect(screen, DARK_RED, ab.inflate(4, 4))
            pygame.draw.rect(screen, RED, ab)

        # Update & draw aliens 
        update_aliens()

        alive_any = False
        for alien in aliens:
            if not alien["alive"]:
                continue
            alive_any = True

            wobble = int(3 * pygame.math.Vector2(1, 0).rotate(alien["anim"] * 6).x)
            draw_monster(alien["monster"],
                         alien["x"] + wobble,
                         alien["y"],
                         alien["color"])

            aw = len(alien["monster"][0]) * PIXEL_SIZE
            ah = len(alien["monster"])    * PIXEL_SIZE
            alien_rect = pygame.Rect(alien["x"], alien["y"], aw, ah)

            for b in player_bullets[:]:
                if alien_rect.colliderect(b):
                    alien["alive"] = False
                    player_bullets.remove(b)
                    explosions.append([alien["x"], alien["y"], EXPLOSION_DURATION])
                    score += (3 - alien["row"]) * 10 + wave * 5
                    play(snd_explosion)
                    break

            if alien["y"] + ah > ship_rect.top:
                
                game_state = "gameover"
                hi_score = max(hi_score, score)

        #  Wave clear 
        if not alive_any and game_state == "playing":
            next_wave()

        #  Draw explosions 
        for exp in explosions[:]:
            color = (255, max(0, 220 - (EXPLOSION_DURATION - exp[2]) * 5), 0)
            draw_monster(explosion_shape, exp[0], exp[1], color)
            exp[2] -= 1
            if exp[2] <= 0:
                explosions.remove(exp)

        draw_hud()
        pygame.display.update()

main()
