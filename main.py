import pygame
import sys

pygame.init()

# ---------- KONFIGURASI DASAR ----------
CELL_SIZE = 64
GRID_ROWS = 10
GRID_COLS = 10

WIDTH = CELL_SIZE * GRID_COLS
HEIGHT = CELL_SIZE * GRID_ROWS + 80  # extra buat panel bawah

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Train Route Puzzle")

clock = pygame.time.Clock()
FPS = 60

# ---------- KODE TIPE CELL ----------
EMPTY = 0
TRACK_H = 1       # horizontal (kiri <-> kanan)
TRACK_V = 2       # vertical (atas <-> bawah)
CURVE_UR = 3      # dari bawah -> kanan, dari kiri -> atas (└ bentuknya)
CURVE_RD = 4      # dari atas -> kanan, dari kiri -> bawah (┌)
CURVE_DL = 5      # dari atas -> kiri, dari kanan -> bawah (┐)
CURVE_LU = 6      # dari bawah -> kiri, dari kanan -> atas (┘)
OBSTACLE = 7
START = 8
STATION = 9

# ---------- ARAH ----------
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

# ---------- WARNA ----------
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GRAY   = (180, 180, 180)
DARKGRAY = (70, 70, 70)
GREEN  = (50, 200, 50)
RED    = (220, 50, 50)
BLUE   = (50, 100, 220)
BROWN  = (140, 90, 40)
YELLOW = (250, 220, 50)

font = pygame.font.SysFont("consolas", 24)

# ---------- LEVEL (GRID 10x10) ----------
# 0 = kosong, 7 = obstacle, 8 = start, 9 = station
# Player nanti mengisi rel di 0 (kosong)
level_data = [
    [8, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 7, 7, 0, 0, 0, 0, 7, 0, 0],
    [0, 0, 0, 0, 7, 0, 0, 7, 0, 0],
    [0, 0, 7, 0, 0, 0, 0, 7, 0, 0],
    [0, 0, 7, 0, 0, 7, 0, 0, 0, 0],
    [0, 0, 0, 0, 7, 7, 0, 0, 7, 0],
    [0, 7, 0, 0, 0, 0, 0, 0, 7, 0],
    [0, 7, 0, 0, 0, 7, 0, 0, 0, 0],
    [0, 0, 0, 7, 0, 0, 0, 7, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 9]
]

grid = [row[:] for row in level_data]  # copy

# cari posisi start & station
start_pos = None
station_pos = None
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        if grid[r][c] == START:
            start_pos = (r, c)
        elif grid[r][c] == STATION:
            station_pos = (r, c)

# ---------- KERETA ----------
class Train:
    def __init__(self, row, col, direction=RIGHT):
        self.row = row
        self.col = col
        self.direction = direction
        self.active = False  # jalan atau tidak
        self.alive = True
        self.finished = False
        self.move_timer = 0
        self.move_delay = 300  # ms, semakin kecil semakin cepat

    def reset(self):
        self.row, self.col = start_pos
        self.direction = RIGHT
        self.active = False
        self.alive = True
        self.finished = False
        self.move_timer = 0

    def update(self, dt, grid):
        if not self.active or not self.alive or self.finished:
            return

        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return
        self.move_timer = 0

        # gerak 1 cell ke depan
        if self.direction == UP:
            self.row -= 1
        elif self.direction == DOWN:
            self.row += 1
        elif self.direction == LEFT:
            self.col -= 1
        elif self.direction == RIGHT:
            self.col += 1

        # cek keluar grid
        if self.row < 0 or self.row >= GRID_ROWS or self.col < 0 or self.col >= GRID_COLS:
            self.alive = False
            return

        cell = grid[self.row][self.col]

        # kalau sampai stasiun
        if cell == STATION:
            self.finished = True
            self.active = False
            return

        # kalau kosong atau obstacle → mati
        if cell == EMPTY or cell == OBSTACLE or cell == START:
            self.alive = False
            return

        # atur arah baru berdasarkan tipe rel
        self.direction = self.next_direction_from_cell(cell, self.direction)
        if self.direction is None:
            # berarti rel gak cocok dengan arah datang
            self.alive = False

    def next_direction_from_cell(self, cell, direction_in):
        # Untuk setiap cell track, tentukan keluar ke mana
        if cell == TRACK_H:
            if direction_in in (LEFT, RIGHT):
                return direction_in
            else:
                return None
        elif cell == TRACK_V:
            if direction_in in (UP, DOWN):
                return direction_in
            else:
                return None
        elif cell == CURVE_UR:
            # bentuk └ (dari bawah ke kanan, dari kiri ke atas)
            if direction_in == DOWN:
                return RIGHT
            elif direction_in == LEFT:
                return UP
            else:
                return None
        elif cell == CURVE_RD:
            # bentuk ┌ (dari atas ke kanan, dari kiri ke bawah)
            if direction_in == UP:
                return RIGHT
            elif direction_in == LEFT:
                return DOWN
            else:
                return None
        elif cell == CURVE_DL:
            # bentuk ┐ (dari atas ke kiri, dari kanan ke bawah)
            if direction_in == UP:
                return LEFT
            elif direction_in == RIGHT:
                return DOWN
            else:
                return None
        elif cell == CURVE_LU:
            # bentuk ┘ (dari bawah ke kiri, dari kanan ke atas)
            if direction_in == DOWN:
                return LEFT
            elif direction_in == RIGHT:
                return UP
            else:
                return None
        else:
            return None

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        size = CELL_SIZE // 2 - 4
        pygame.draw.rect(surface, BLUE, (x - size//2, y - size//2, size, size))


train = Train(start_pos[0], start_pos[1])

# ---------- PILIHAN REL (PANEL BAWAH) ----------
# Track yang bisa dipasang player
track_types = [TRACK_H, TRACK_V, CURVE_UR, CURVE_RD, CURVE_DL, CURVE_LU]
selected_track_index = 0

def draw_track_icon(surface, rect, track_type, selected=False):
    pygame.draw.rect(surface, DARKGRAY if selected else GRAY, rect, border_radius=8)
    cx = rect.x + rect.width // 2
    cy = rect.y + rect.height // 2

    # gambar rel sederhana
    if track_type == TRACK_H:
        pygame.draw.line(surface, BROWN, (rect.x + 6, cy), (rect.right - 6, cy), 6)
    elif track_type == TRACK_V:
        pygame.draw.line(surface, BROWN, (cx, rect.y + 6), (cx, rect.bottom - 6), 6)
    elif track_type == CURVE_UR:
        pygame.draw.arc(surface, BROWN, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12), 
                        3.14/2, 3.14, 6)
    elif track_type == CURVE_RD:
        pygame.draw.arc(surface, BROWN, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12),
                        3.14, 3.14*3/2, 6)
    elif track_type == CURVE_DL:
        pygame.draw.arc(surface, BROWN, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12),
                        -3.14/2, 0, 6)
    elif track_type == CURVE_LU:
        pygame.draw.arc(surface, BROWN, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12),
                        0, 3.14/2, 6)

# ---------- FUNGSI DRAW GRID ----------
def draw_grid(surface, grid):
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            cell = grid[r][c]

            # background tile
            pygame.draw.rect(surface, (230, 230, 230), (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(surface, (200, 200, 200), (x, y, CELL_SIZE, CELL_SIZE), 1)

            if cell == OBSTACLE:
                pygame.draw.rect(surface, DARKGRAY, (x+8, y+8, CELL_SIZE-16, CELL_SIZE-16))
            elif cell == START:
                pygame.draw.rect(surface, GREEN, (x+8, y+8, CELL_SIZE-16, CELL_SIZE-16))
            elif cell == STATION:
                pygame.draw.rect(surface, YELLOW, (x+8, y+8, CELL_SIZE-16, CELL_SIZE-16))

            # track
            if cell in (TRACK_H, TRACK_V, CURVE_UR, CURVE_RD, CURVE_DL, CURVE_LU):
                cx = x + CELL_SIZE // 2
                cy = y + CELL_SIZE // 2
                if cell == TRACK_H:
                    pygame.draw.line(surface, BROWN, (x+4, cy), (x+CELL_SIZE-4, cy), 8)
                elif cell == TRACK_V:
                    pygame.draw.line(surface, BROWN, (cx, y+4), (cx, y+CELL_SIZE-4), 8)
                elif cell == CURVE_UR:
                    pygame.draw.arc(surface, BROWN, (x+4, y+4, CELL_SIZE-8, CELL_SIZE-8), 
                                    3.14/2, 3.14, 8)
                elif cell == CURVE_RD:
                    pygame.draw.arc(surface, BROWN, (x+4, y+4, CELL_SIZE-8, CELL_SIZE-8), 
                                    3.14, 3.14*3/2, 8)
                elif cell == CURVE_DL:
                    pygame.draw.arc(surface, BROWN, (x+4, y+4, CELL_SIZE-8, CELL_SIZE-8), 
                                    -3.14/2, 0, 8)
                elif cell == CURVE_LU:
                    pygame.draw.arc(surface, BROWN, (x+4, y+4, CELL_SIZE-8, CELL_SIZE-8), 
                                    0, 3.14/2, 8)

# ---------- PANEL BAWAH ----------
def draw_panel(surface, selected_index):
    panel_rect = pygame.Rect(0, GRID_ROWS * CELL_SIZE, WIDTH, 80)
    pygame.draw.rect(surface, (220, 220, 220), panel_rect)

    text = font.render("Klik grid utk pasang rel. Scroll / A-D utk ganti jenis. SPACE = Mulai, R = Reset", True, BLACK)
    surface.blit(text, (10, GRID_ROWS * CELL_SIZE + 5))

    # gambar icon track
    margin = 10
    icon_w = 50
    icon_h = 50
    x = margin
    y = GRID_ROWS * CELL_SIZE + 25

    for i, t in enumerate(track_types):
        rect = pygame.Rect(x, y, icon_w, icon_h)
        draw_track_icon(surface, rect, t, selected=(i == selected_index))
        x += icon_w + 10

# ---------- GAME STATE ----------
game_message = ""

def reset_game():
    global grid, game_message
    grid = [row[:] for row in level_data]
    train.reset()
    game_message = ""

# ---------- MAIN LOOP ----------
running = True
while running:
    dt = clock.tick(FPS)  # ms per frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # klik mouse utk pasang rel
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if my < GRID_ROWS * CELL_SIZE and not train.active:
                col = mx // CELL_SIZE
                row = my // CELL_SIZE

                if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                    if grid[row][col] in (EMPTY, TRACK_H, TRACK_V, CURVE_UR, CURVE_RD, CURVE_DL, CURVE_LU):
                        # pasang track yang dipilih
                        grid[row][col] = track_types[selected_track_index]
            # scroll mouse buat ganti track
            if event.button == 4:  # scroll up
                selected_track_index = (selected_track_index - 1) % len(track_types)
            elif event.button == 5:  # scroll down
                selected_track_index = (selected_track_index + 1) % len(track_types)

        # keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # mulai jalanin kereta
                if not train.active and train.alive and not train.finished:
                    train.active = True
                    game_message = ""
            if event.key == pygame.K_r:
                reset_game()
            if event.key in (pygame.K_a, pygame.K_LEFT):
                selected_track_index = (selected_track_index - 1) % len(track_types)
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                selected_track_index = (selected_track_index + 1) % len(track_types)

    # update kereta
    train.update(dt, grid)

    # cek kondisi menang / kalah
    if train.finished:
        game_message = "YOU WIN! Tekan R utk reset."
    elif not train.alive and not train.finished:
        if game_message == "":
            game_message = "GAME OVER! Tekan R utk reset."

    # ----- DRAW -----
    screen.fill(WHITE)
    draw_grid(screen, grid)
    # gambar kereta di atas rel
    if train.alive:
        train.draw(screen)

    draw_panel(screen, selected_track_index)

    if game_message:
        msg_surface = font.render(game_message, True, RED if "OVER" in game_message else GREEN)
        screen.blit(msg_surface, (10, GRID_ROWS * CELL_SIZE + 40))

    pygame.display.flip()

pygame.quit()
sys.exit()

