import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 720, 560
TILE = 70
ROWS, COLS = HEIGHT // TILE, WIDTH // TILE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rail Puzzle Advanced")

clock = pygame.time.Clock()
FPS = 30

WHITE = (255,255,255)
GRAY = (200,200,200)
BLACK = (40,40,40)
GREEN = (0,230,0)
BLUE = (0,130,230)
RED = (255,0,0)
YELLOW = (250,200,0)

# Tile types with connection directions: (up,right,down,left)
RAILS = {
    0: (0,0,0,0),  # empty
    1: (1,0,1,0),  # vertical
    2: (0,1,0,1),  # horizontal
    3: (0,1,1,0),  # L: ↘
    4: (0,0,1,1),  # L: ↙
    5: (1,0,0,1),  # L: ↖
    6: (1,1,0,0),  # L: ↗
    7: (1,1,1,0),  # T-split: ⊢
    8: (1,0,1,1),  # T-split: ⊣
}

grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

start = (1,2)
finish = (6,8)
train_pos = [start[0]*TILE+TILE//2, start[1]*TILE+TILE//2]
direction = None
speed = 3
running = False
message = ""

obstacles = {(4,5), (3,4)}  # batu

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            x = c*TILE
            y = r*TILE
            pygame.draw.rect(screen, GRAY, (x,y,TILE,TILE), 1)

            if (r,c) in obstacles:
                pygame.draw.rect(screen, BLACK, (x+10,y+10,TILE-20,TILE-20))
                continue

            t = grid[r][c]
            if t == 0: continue
            dirs = RAILS[t]

            # draw rail lines
            if dirs[0]: pygame.draw.line(screen, BLACK, (x+TILE//2,y), (x+TILE//2,y+TILE//2), 8)
            if dirs[1]: pygame.draw.line(screen, BLACK, (x+TILE//2,y+TILE//2), (x+TILE,y+TILE//2), 8)
            if dirs[2]: pygame.draw.line(screen, BLACK, (x+TILE//2,y+TILE), (x+TILE//2,y+TILE//2), 8)
            if dirs[3]: pygame.draw.line(screen, BLACK, (x,y+TILE//2), (x+TILE//2,y+TILE//2), 8)

    pygame.draw.circle(screen, RED, (start[1]*TILE+TILE//2, start[0]*TILE+TILE//2), 14)
    pygame.draw.rect(screen, BLUE, (finish[1]*TILE+15, finish[0]*TILE+15, 40,40), border_radius=6)

def get_tile(row, col):
    if 0 <= row < ROWS and 0 <= col < COLS:
        return grid[row][col]
    return None

def find_next_direction(r,c,from_dir):
    tile = grid[r][c]
    dirs = RAILS[tile]
    for i,d in enumerate(dirs):
        if d and i != (from_dir+2)%4:  # avoid backtracking
            return i
    return None

def train_fail(msg):
    global running, message
    running = False
    message = msg
    print(msg)

def train_win():
    global running, message
    running = False
    message = "🎉 Level Sukses!"
    print(message)

def move_train():
    global train_pos, direction
    x,y = train_pos
    row = y//TILE
    col = x//TILE

    if (row,col) != start:
        if (row,col) in obstacles:
            train_fail("💥 Nabrak batu!")
            return

    if (row,col) == finish:
        train_win()
        return

    tile = get_tile(row,col)
    if tile is None or tile == 0:
        train_fail("❌ Jalur putus!")
        return

    if direction is None:
        direction = 1  # start to right

    if direction == 0: y -= speed
    elif direction == 1: x += speed
    elif direction == 2: y += speed
    elif direction == 3: x -= speed

    train_pos[:] = [x,y]

    if x % TILE == TILE//2 and y % TILE == TILE//2:
        direction = find_next_direction(row,col,direction)
        if direction is None:
            train_fail("⚠ Jalur buntu!")

def show_message():
    if message:
        text = font.render(message, True, YELLOW)
        screen.blit(text, (20, HEIGHT-40))

font = pygame.font.SysFont("Arial", 26)

while True:
    screen.fill(WHITE)
    draw_grid()

    pygame.draw.circle(screen, GREEN, (train_pos[0],train_pos[1]), 10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if not running:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx,my = pygame.mouse.get_pos()
                r = my//TILE
                c = mx//TILE
                if (r,c) != start and (r,c) != finish and (r,c) not in obstacles:
                    if event.button == 1:
                        grid[r][c] = (grid[r][c] + 1) % len(RAILS)
                    elif event.button == 3:
                        grid[r][c] = (grid[r][c] - 1) % len(RAILS)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                running = True
                train_pos = [start[1]*TILE+TILE//2, start[0]*TILE+TILE//2]
                direction = None
                message = ""

    if running:
        move_train()

    show_message()
    pygame.display.update()
    clock.tick(FPS)