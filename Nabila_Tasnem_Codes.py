from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24


WIN_W, WIN_H = 1000, 800


camera_pos = [0.0, 500.0, 500.0]
fovY = 60
GRID_LENGTH = 600


score = 0
is_game_over = False
enemies_killed = 0  
breaches = 0
BREACH_LIMIT = 30

stage = 1  
frame_counter = 0
FRAMES_PER_SECOND = 60
SECONDS_PER_STAGE = 10


player_pos = [0.0, -200.0, 20.0]  
player_yaw_deg = 0.0  
player_speed = 6.0


TEMPLE_POS = [0.0, 0.0, 0.0]
TEMPLE_RADIUS = 60.0


enemies = []  
ENEMY_SPAWN_COOLDOWN = 120 
_enemy_spawn_timer = 0


red_dots = []  
RED_DOT_SPAWN_COOLDOWN = 60  
_red_spawn_timer = 0
RED_DOT_RADIUS = 22.0
RED_DOT_SPEED = 0.18  



bullets = []  
BULLET_SPEED = 20.0
BULLET_RADIUS = 6.0
BULLET_LIFETIME = 120  


keys_down = set()
cheat_mode = False  


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = WIN_W / float(WIN_H)
    gluPerspective(fovY, aspect, 0.1, 3000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], 0, 0, 0, 0, 0, 1)


def reset_game():
    global score, is_game_over, enemies, bullets, player_pos, player_yaw_deg, enemies_killed, breaches, red_dots, _enemy_spawn_timer, _red_spawn_timer, stage, frame_counter
    score = 0
    is_game_over = False
    enemies_killed = 0
    breaches = 0
    enemies = []
    red_dots = []
    bullets = []
    player_pos = [0.0, -200.0, 20.0]  
    player_yaw_deg = 0.0  
    _enemy_spawn_timer = 0
    _red_spawn_timer = 0
    stage = 1
    frame_counter = 0
    





def keyboard_down(key, x, y):
    global keys_down, cheat_mode
    try:
        k = key.decode('utf-8')
    except Exception:
        k = str(key)
    keys_down.add(k)

    if k in ('r', 'R'):
        reset_game()
    if k in ('c', 'C'):
        cheat_mode = not cheat_mode  


def keyboard_up(key, x, y):
    global keys_down
    try:
        k = key.decode('utf-8')
    except Exception:
        k = str(key)
    if k in keys_down:
        keys_down.remove(k)


def specialKeyListener(key, x, y):
    global camera_pos
    if key == GLUT_KEY_LEFT:
        camera_pos[0] -= 10.0
    elif key == GLUT_KEY_RIGHT:
        camera_pos[0] += 10.0
    elif key == GLUT_KEY_UP:
        camera_pos[2] -= 10.0
    elif key == GLUT_KEY_DOWN:
        camera_pos[2] += 10.0


def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not is_game_over:
       
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


def idle():
    update_game()
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WIN_W, WIN_H)
    glLoadIdentity()
    setupCamera()


    glutSwapBuffers()



def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Temple Defense - Guardian Statue")

    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_COLOR_MATERIAL)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    reset_game()
    glutMainLoop()


if __name__ == "__main__":
    main()
