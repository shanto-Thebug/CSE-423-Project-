from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24

# Window size
WIN_W, WIN_H = 1000, 800

# Camera-related variables
camera_pos = [0.0, 500.0, 500.0]
fovY = 60
GRID_LENGTH = 600

# Game state
score = 0
is_game_over = False
enemies_killed = 0  # Track total enemies killed
breaches = 0
BREACH_LIMIT = 30
# Stage system
stage = 1  # 1: normal, 2: red dots added, 3: power bullets
frame_counter = 0
FRAMES_PER_SECOND = 60
SECONDS_PER_STAGE = 10

# Player state
player_pos = [0.0, -200.0, 20.0]  # In front of temple (negative Y)
player_yaw_deg = 0.0  # Facing +Y toward temple by default
player_speed = 6.0

# Temple
TEMPLE_POS = [0.0, 0.0, 0.0]
TEMPLE_RADIUS = 60.0

# Enemies
enemies = []  # list of dicts: {pos:[x,y,z], speed:float, radius:float}
ENEMY_SPAWN_COOLDOWN = 120  # frames
_enemy_spawn_timer = 0

# Red dot enemies (bonus targets)
red_dots = []  # list of dicts: {pos:[x,y,z], speed:float, radius:float}
RED_DOT_SPAWN_COOLDOWN = 60  # frames (was 140, now more frequent)
_red_spawn_timer = 0
RED_DOT_RADIUS = 22.0
RED_DOT_SPEED = 0.18  # was 2.6, now faster


# Bullets
bullets = []  # list of dicts: {pos:[x,y,z], vel:[vx,vy,vz], radius:float}
BULLET_SPEED = 20.0
BULLET_RADIUS = 6.0
BULLET_LIFETIME = 120  # frames

# Input state
keys_down = set()
cheat_mode = False  # <-- Add this line


def update_game():
    global _enemy_spawn_timer, _red_spawn_timer, is_game_over, score, enemies_killed, breaches, frame_counter, stage, cheat_mode
    if is_game_over:
        return
    
	# player movement
    move_forward = ('w' in keys_down) or ('W' in keys_down)
    move_back = ('s' in keys_down) or ('S' in keys_down)
    turn_left = ('a' in keys_down) or ('A' in keys_down)
    turn_right = ('d' in keys_down) or ('D' in keys_down)

    if turn_left:
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] + 3.0) % 360.0
    if turn_right:
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] - 3.0) % 360.0

    yaw_rad = math.radians(globals()['player_yaw_deg'])
    dx = math.sin(yaw_rad)
    dy = -math.cos(yaw_rad)
    if move_forward:
        player_pos[0] += dx * player_speed
        player_pos[1] += dy * player_speed
    if move_back:
        player_pos[0] -= dx * player_speed
        player_pos[1] -= dy * player_speed

    # clamp to grid and keep away from temple
    player_pos[0] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[0]))
    player_pos[1] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[1]))

    dist_to_temple = math.hypot(player_pos[0] - TEMPLE_POS[0], player_pos[1] - TEMPLE_POS[1])
    if dist_to_temple < TEMPLE_RADIUS + 40:
        angle_from_temple = math.atan2(player_pos[1] - TEMPLE_POS[1], player_pos[0] - TEMPLE_POS[0])
        player_pos[0] = TEMPLE_POS[0] + math.cos(angle_from_temple) * (TEMPLE_RADIUS + 40)
        player_pos[1] = TEMPLE_POS[1] + math.sin(angle_from_temple) * (TEMPLE_RADIUS + 40)

    # --- CHEAT MODE: auto-rotate and auto-shoot ---
    if cheat_mode and not is_game_over:
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] + 5.0) % 360.0

        yaw_rad = math.radians(globals()['player_yaw_deg'])

    # stage progression based on time
    frame_counter += 1
    elapsed_seconds = frame_counter // FRAMES_PER_SECOND
    if elapsed_seconds >= SECONDS_PER_STAGE * 2:
        stage = 3
    elif elapsed_seconds >= SECONDS_PER_STAGE * 1:
        stage = 2
    else:
        stage = 1

    # spawn enemies
    _enemy_spawn_timer -= 1
    if _enemy_spawn_timer <= 0:
        spawn_enemy()
        _enemy_spawn_timer = ENEMY_SPAWN_COOLDOWN

    # spawn red dots starting stage 2
    if stage >= 2:
        _red_spawn_timer -= 1
        if _red_spawn_timer <= 0:
            spawn_red_dot()
            _red_spawn_timer = RED_DOT_SPAWN_COOLDOWN
        
    if cheat_mode and not is_game_over:
        # Rotate player
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] + 5.0) % 360.0

        # Auto-fire bullet every frame
        yaw_rad = math.radians(globals()['player_yaw_deg'])
        speed = BULLET_SPEED * (1.8 if stage >= 3 else 1.0)
        vx = math.sin(yaw_rad) * speed
        vy = -math.cos(yaw_rad) * speed
        vz = 0.0

        gun_offset_x = 15 * math.cos(yaw_rad - math.pi/2)
        gun_offset_y = 15 * math.sin(yaw_rad - math.pi/2)
        barrel_offset_x = 30 * math.sin(yaw_rad)
        barrel_offset_y = -30 * math.cos(yaw_rad)

        start_x = player_pos[0] + gun_offset_x + barrel_offset_x
        start_y = player_pos[1] + gun_offset_y + barrel_offset_y
        start_z = player_pos[2] + 2

        bullets.append({'pos': [start_x, start_y, start_z], 'vel': [vx, vy, vz], 'radius': BULLET_RADIUS, 'life': BULLET_LIFETIME})

    # move enemies toward temple center (0,0,0) in straight lines
    for enemy in enemies:
        # Calculate direction vector toward temple
        vx = TEMPLE_POS[0] - enemy['pos'][0]
        vy = TEMPLE_POS[1] - enemy['pos'][1]
        len_v = math.hypot(vx, vy) + 1e-6  # Avoid division by zero
        vx /= len_v  # Normalize
        vy /= len_v  # Normalize

        # Move enemy toward temple
        enemy['pos'][0] += vx * enemy['speed']
        enemy['pos'][1] += vy * enemy['speed']

    # bullets move
    for b in bullets:
        b['pos'][0] += b['vel'][0]
        b['pos'][1] += b['vel'][1]
        b['pos'][2] += b['vel'][2]
        b['life'] -= 1

    # remove expired bullets
    bullets[:] = [b for b in bullets if b['life'] > 0 and abs(b['pos'][0]) <= GRID_LENGTH*1.2 and abs(b['pos'][1]) <= GRID_LENGTH*1.2]

    # detect bullet-enemy collisions (regular enemies)
    remaining_enemies = []
    for enemy in enemies:
        enemy_killed = False
        for b in bullets:
            dx = enemy['pos'][0] - b['pos'][0]
            dy = enemy['pos'][1] - b['pos'][1]
            dz = enemy['pos'][2] - b['pos'][2]
            d2 = dx*dx + dy*dy + dz*dz
            if d2 <= (enemy['radius'] + b['radius'])**2:
                enemy_killed = True
                b['life'] = 0
                break
        if not enemy_killed:
            remaining_enemies.append(enemy)
        else:
            score += 10  # Add 10 points for each enemy killed
            enemies_killed += 1  # Track total enemies killed
    enemies[:] = remaining_enemies

    # detect bullet-red_dot collisions (25 points)
    remaining_dots = []
    for dot in red_dots:
        killed = False
        for b in bullets:
            dx = dot['pos'][0] - b['pos'][0]
            dy = dot['pos'][1] - b['pos'][1]
            dz = dot['pos'][2] - b['pos'][2]
            d2 = dx*dx + dy*dy + dz*dz
            if d2 <= (dot['radius'] + b['radius'])**2:
                killed = True
                b['life'] = 0
                break
        if not killed:
            remaining_dots.append(dot)
        else:
            score += 25
    red_dots[:] = remaining_dots

    # check temple collision -> count breaches, remove enemy; end after limit
    remaining_after_breach = []
    for enemy in enemies:
        dx = enemy['pos'][0] - TEMPLE_POS[0]
        dy = enemy['pos'][1] - TEMPLE_POS[1]
        if dx*dx + dy*dy <= (TEMPLE_RADIUS + enemy['radius'])**2:
            breaches += 1
            continue
        remaining_after_breach.append(enemy)
    enemies[:] = remaining_after_breach

    # red dots breaching also count
    remaining_dots_after_breach = []
    for dot in red_dots:
        dx = dot['pos'][0] - TEMPLE_POS[0]
        dy = dot['pos'][1] - TEMPLE_POS[1]
        if dx*dx + dy*dy <= (TEMPLE_RADIUS + dot['radius'])**2:
            breaches += 1
            continue
        remaining_dots_after_breach.append(dot)
    red_dots[:] = remaining_dots_after_breach
    if breaches >= BREACH_LIMIT:
        is_game_over = True

    # player movement
    move_forward = ('w' in keys_down) or ('W' in keys_down)
    move_back = ('s' in keys_down) or ('S' in keys_down)
    turn_left = ('a' in keys_down) or ('A' in keys_down)
    turn_right = ('d' in keys_down) or ('D' in keys_down)

    if turn_left:
        # rotate counter-clockwise around +Z
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] + 3.0) % 360.0
    if turn_right:
        globals()['player_yaw_deg'] = (globals()['player_yaw_deg'] - 3.0) % 360.0

    # forward/back in facing direction along XY plane
    yaw_rad = math.radians(globals()['player_yaw_deg'])
    dx = math.sin(yaw_rad)
    dy = -math.cos(yaw_rad)
    if move_forward:
        player_pos[0] += dx * player_speed
        player_pos[1] += dy * player_speed
    if move_back:
        player_pos[0] -= dx * player_speed
        player_pos[1] -= dy * player_speed

    # clamp to grid and keep away from temple
    player_pos[0] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[0]))
    player_pos[1] = max(-GRID_LENGTH + 20, min(GRID_LENGTH - 20, player_pos[1]))

    # Keep player away from temple center
    dist_to_temple = math.hypot(player_pos[0] - TEMPLE_POS[0], player_pos[1] - TEMPLE_POS[1])
    if dist_to_temple < TEMPLE_RADIUS + 40:
        # Push player away from temple
        angle_from_temple = math.atan2(player_pos[1] - TEMPLE_POS[1], player_pos[0] - TEMPLE_POS[0])
        player_pos[0] = TEMPLE_POS[0] + math.cos(angle_from_temple) * (TEMPLE_RADIUS + 40)
        player_pos[1] = TEMPLE_POS[1] + math.sin(angle_from_temple) * (TEMPLE_RADIUS + 40)


