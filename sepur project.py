import pygame
import sys
import math
import os

pygame.init()
# LOAD AUDIO

pygame.mixer.init()
def try_load_sound(fname):
    if os.path.exists(fname):
        try:
            return pygame.mixer.Sound(fname)
        except:
            return None
    return None

sfx_place  = try_load_sound("sfx_place.wav")
sfx_click  = try_load_sound("sfx_click.wav")
sfx_run    = try_load_sound("sfx_run.wav")
sfx_crash  = try_load_sound("sfx_crash.wav")

# BGM
if os.path.exists("bgm.mp3"):
    pygame.mixer.music.load("bgm.mp3")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)    # Loop selamanya


LEBAR_LAYAR = 800
TINGGI_LAYAR = 600
screen = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR))
pygame.display.set_caption("Game Kereta: Level & Rintangan")

# Palette Warna
PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)
TANAH = (210, 180, 140)
TANAH_GELAP = (139, 69, 19)
REL_WARNA = (80, 80, 80)
HIJAU_KERETA = (34, 139, 34)
MERAH = (220, 20, 60)
ABU_BATU = (105, 105, 105)
RUMPUT_MUDA = (150, 200, 150)
RUMPUT_TUA = (50, 100, 50)

# Grid Config
UKURAN_SEL = 80
OFFSET_X = 120
OFFSET_Y = 100
KOLOM = 7
BARIS = 4

# Tipe Grid
KOSONG = 0
LURUS_HOR = 1
LURUS_VER = 2
SIKU = 3          # SATU jenis rel siku
RINTANGAN = 9     # Batu/Tembok (Tidak bisa dibangun)

# Status Utama Game
MENU_STATE = 0
GAME_STATE = 1

# --- DATA LEVEL ---
LEVEL_MAPS = [
    {
        "deskripsi": "Hubungkan START ke FINISH dengan rel lurus.",
        "obs": [(2, 2), (3, 2), (4, 2)],
        "start": (0, 1),
        "finish": (6, 1)
    },
    {
        "deskripsi": "Gunakan rel belok pertama Anda untuk menghindari batu di jalur utama.",
        "obs": [(3, 1), (5, 0), (5, 2)],
        "start": (0, 0),
        "finish": (6, 0)
    },
    {
        "deskripsi": "Susun jalur yang berliku-liku menuju stasiun bawah.",
        "obs": [(2, 0), (2, 1), (4, 2), (4, 3)],
        "start": (0, 0),
        "finish": (6, 3)
    },
    {
        "deskripsi": "Gunakan belokan siku ganda. Hati-hati dengan posisi batu yang membatasi.",
        "obs": [(1, 0), (1, 2), (3, 1), (5, 0), (5, 2)],
        "start": (0, 1),
        "finish": (6, 1)
    },
    {
        "deskripsi": "Ini adalah jalur panjang dan kompleks. Rencanakan belokan Anda dari awal!",
        "obs": [(1, 1), (3, 0), (3, 2), (4, 1), (5, 3)],
        "start": (0, 3),
        "finish": (6, 0)
    }
]

class GameState:
    def __init__(self): 
        self.state = MENU_STATE  # Status Awal: MENU
        self.current_level_idx = 0

        # Inventory Pilihan
        self.selected_piece = LURUS_HOR

        # Status game
        self.train_running = False
        self.game_over = False
        self.win = False

        # Sel terakhir yang diklik (buat rotasi dengan tombol R)
        self.last_clicked = None  # (gx, gy)

        self.load_level(self.current_level_idx)

    def load_level(self, level_idx):
        if level_idx >= len(LEVEL_MAPS):
            print("Semua Level Selesai! Kembali ke Level 1.")
            self.current_level_idx = 0
            level_idx = 0

        data = LEVEL_MAPS[level_idx]

        # grid menyimpan (type, rot)
        self.grid = [[(KOSONG, 0) for _ in range(KOLOM)] for _ in range(BARIS)]

        # Rintangan
        for (bx, by) in data['obs']:
            self.grid[by][bx] = (RINTANGAN, 0)

        self.start_pos = data['start']
        self.finish_pos = data['finish']

        self.reset_train()

        print(f"Level {level_idx + 1} Dimuat!")

    def reset_train(self):
        self.train_running = False
        self.game_over = False
        self.win = False

        sx, sy = self.start_pos
        self.train_dir = [1, 0]  # ke kanan

        start_pixel_x = OFFSET_X + (sx * UKURAN_SEL) - UKURAN_SEL
        start_pixel_y = OFFSET_Y + (sy * UKURAN_SEL) + (UKURAN_SEL // 2)
        self.train_pixel_pos = [start_pixel_x, start_pixel_y]

state = GameState()

# LOAD ASET GAMBAR
def try_load_image(fname, size=None):
    if os.path.exists(fname):
        try:
            img = pygame.image.load(fname).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except Exception as e:
            print(f"Error loading {fname}: {e}")
            return None
    return None

rel_hor_img = try_load_image("rel_hor.png", (UKURAN_SEL, UKURAN_SEL))
rel_ver_img = try_load_image("rel_ver.png", (UKURAN_SEL, UKURAN_SEL))
rel_siku_img = try_load_image("rel_siku.png", (UKURAN_SEL, UKURAN_SEL))
batu_img = try_load_image("batu.png", (UKURAN_SEL, UKURAN_SEL))
train_img = try_load_image("train.png", (UKURAN_SEL, UKURAN_SEL))

# Jika ada gambar tidak ditemukan, buat placeholder sederhana agar game tetap jalan
if rel_hor_img is None:
    rel_hor_img = pygame.Surface((UKURAN_SEL, UKURAN_SEL), pygame.SRCALPHA)
    # draw simple rails
    for i in range(10, UKURAN_SEL, 20):
        pygame.draw.line(rel_hor_img, TANAH_GELAP, (i, UKURAN_SEL//2 - 10), (i, UKURAN_SEL//2 + 10), 4)
    pygame.draw.line(rel_hor_img, REL_WARNA, (0, UKURAN_SEL//2 - 3), (UKURAN_SEL, UKURAN_SEL//2 - 3), 2)
    pygame.draw.line(rel_hor_img, REL_WARNA, (0, UKURAN_SEL//2 + 3), (UKURAN_SEL, UKURAN_SEL//2 + 3), 2)

if rel_ver_img is None:
    rel_ver_img = pygame.transform.rotate(rel_hor_img, 90)

if rel_siku_img is None:
    rel_siku_img = pygame.Surface((UKURAN_SEL, UKURAN_SEL), pygame.SRCALPHA)
    pygame.draw.arc(rel_siku_img, REL_WARNA, (8,8,UKURAN_SEL-16,UKURAN_SEL-16), 0, math.pi/2, 6)

if batu_img is None:
    batu_img = pygame.Surface((UKURAN_SEL, UKURAN_SEL), pygame.SRCALPHA)
    pygame.draw.rect(batu_img, ABU_BATU, (10, 10, UKURAN_SEL-20, UKURAN_SEL-20), border_radius=10)
    pygame.draw.circle(batu_img, (80,80,80), (25,30), 8)
    pygame.draw.circle(batu_img, (80,80,80), (55,50), 10)

if train_img is None:
    train_img = pygame.Surface((50,30), pygame.SRCALPHA)
    pygame.draw.rect(train_img, HIJAU_KERETA, (0,0,50,30), border_radius=5)
    pygame.draw.rect(train_img, (173,216,230), (8,5,10,20))
    pygame.draw.rect(train_img, (173,216,230), (28,5,10,20))
    pygame.draw.circle(train_img, HITAM, (25, 25), 3)

# FUNGSI GAMBAR

def draw_track_piece(surface, x, y, piece):
    """piece = (type, rot)"""
    tipe, rot = piece
    cx = x + UKURAN_SEL // 2
    cy = y + UKURAN_SEL // 2

    if tipe == RINTANGAN:
        surface.blit(batu_img, (x, y))
        return

    if tipe == LURUS_HOR:
        surface.blit(rel_hor_img, (x, y))

    elif tipe == LURUS_VER:
        surface.blit(rel_ver_img, (x, y))

    elif tipe == SIKU:
        img = pygame.transform.rotate(rel_siku_img, -rot)
        surface.blit(img, (x, y))
        return

def draw_train(surface, pos, direction):
    lebar_body = 30
    tinggi_body = 20

    # Select correct image orientation
    if direction[0] != 0:
        if direction[0] == 1:
            img = train_img
        else:
            img = pygame.transform.flip(train_img, True, False)
    else:
        if direction[1] == -1:
            img = pygame.transform.rotate(train_img, 90)
        else:
            img = pygame.transform.rotate(train_img, -90)

    rect = img.get_rect(center=(pos[0], pos[1]))
    surface.blit(img, rect)

def draw_grid():
    for r in range(BARIS):
        for c in range(KOLOM):
            rect_x = OFFSET_X + c * UKURAN_SEL
            rect_y = OFFSET_Y + r * UKURAN_SEL

            color = TANAH
            if (c, r) == state.start_pos:
                color = (200, 255, 200)
            if (c, r) == state.finish_pos:
                color = (255, 255, 200)

            pygame.draw.rect(screen, color, (rect_x, rect_y, UKURAN_SEL, UKURAN_SEL))
            pygame.draw.rect(screen, (180, 150, 100),
                             (rect_x, rect_y, UKURAN_SEL, UKURAN_SEL), 2)

            piece = state.grid[r][c]
            draw_track_piece(screen, rect_x, rect_y, piece)

            font = pygame.font.Font(None, 20)
            if (c, r) == state.start_pos:
                screen.blit(font.render("START", True, HITAM), (rect_x + 5, rect_y + 5))
            if (c, r) == state.finish_pos:
                screen.blit(font.render("FINISH", True, HITAM), (rect_x + 5, rect_y + 5))

def draw_ui():
    inv_y = TINGGI_LAYAR - 100
    labels = ["Hapus", "Hor", "Ver", "Siku"]
    types = [KOSONG, LURUS_HOR, LURUS_VER, SIKU]

    for i, t in enumerate(types):
        bx = 50 + i * 90
        col = PUTIH if state.selected_piece != t else (100, 255, 100)
        pygame.draw.rect(screen, col, (bx, inv_y, 80, 60))
        pygame.draw.rect(screen, HITAM, (bx, inv_y, 80, 60), 2)

        cx = bx + 40
        cy = inv_y + 35
        tebal = 4

        if t == LURUS_HOR:
            pygame.draw.line(screen, REL_WARNA, (bx + 10, cy), (bx + 70, cy), tebal)
        elif t == LURUS_VER:
            pygame.draw.line(screen, REL_WARNA,
                             (cx, inv_y + 10), (cx, inv_y + 50), tebal)
        elif t == SIKU:
            pygame.draw.arc(screen, REL_WARNA,
                            (cx - 30, cy - 30, 40, 40),
                            0, math.pi / 2, tebal)
        elif t == RINTANGAN:
            pygame.draw.rect(screen, ABU_BATU,
                             (bx + 20, inv_y + 20, 40, 20), border_radius=5)

        font = pygame.font.Font(None, 20)
        screen.blit(font.render(labels[i], True, HITAM), (bx + 10, inv_y + 5))

    font_lvl = pygame.font.Font(None, 40)
    screen.blit(font_lvl.render(f"LEVEL: {state.current_level_idx + 1}",
                                True, HITAM), (50, 30))

    font_desc = pygame.font.Font(None, 24)
    desc_text = LEVEL_MAPS[state.current_level_idx]["deskripsi"]
    screen.blit(font_desc.render(desc_text, True, HITAM), (50, 65))

    btn_rect = (LEBAR_LAYAR - 220, TINGGI_LAYAR - 90, 200, 60)
    if state.win:
        pygame.draw.rect(screen, (0, 0, 200), btn_rect, border_radius=10)
        txt = "LEVEL SELANJUTNYA >>"
    elif state.train_running:
        pygame.draw.rect(screen, MERAH, btn_rect, border_radius=10)
        txt = "RESET"
    else:
        pygame.draw.rect(screen, HIJAU_KERETA, btn_rect, border_radius=10)
        txt = "JALANKAN KERETA"

    font_btn = pygame.font.Font(None, 24)
    text_surf = font_btn.render(txt, True, PUTIH)
    screen.blit(text_surf, (LEBAR_LAYAR - 200, TINGGI_LAYAR - 70))
    
    if state.selected_piece == SIKU:
        font_hint = pygame.font.Font(None, 22)
        hint_text = "Tekan R pada keyboard untuk mengubah arah rel"
        text_surf = font_hint.render(hint_text, True, (50, 50, 50))

        # posisi teks (di atas inventory)
        screen.blit(
            text_surf,
            (50, TINGGI_LAYAR - 130)
        )
# FUNGSI UNTUK TOMBOL
def draw_button_3d(surface, rect, text, base_color, hover_color, action_func=None):
    mx, my = pygame.mouse.get_pos()
    x, y, w, h = rect
    is_hover = x < mx < x + w and y < my < y + h
    color = hover_color if is_hover else base_color
    shadow_color = (max(0, base_color[0]-50), max(0, base_color[1]-50), max(0, base_color[2]-50))
    shadow_offset = 6
    pygame.draw.rect(surface, shadow_color, (x, y + shadow_offset, w, h), border_radius=15)
    btn_y = y + 2 if is_hover else y
    pygame.draw.rect(surface, color, (x, btn_y, w, h), border_radius=15)
    pygame.draw.line(surface, (255, 255, 255), (x+15, btn_y+5), (x+w-15, btn_y+5), 2)
    font = pygame.font.SysFont("Segoe UI", 40, bold=True)
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(x + w//2, btn_y + h//2))
    text_shadow = font.render(text, True, (0, 0, 0))
    surface.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
    surface.blit(text_surf, text_rect)
    return rect

def draw_menu():
    top_color = (70, 130, 180)
    bottom_color = (25, 25, 112)
    for y in range(TINGGI_LAYAR):
        ratio = y / TINGGI_LAYAR
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (LEBAR_LAYAR, y))

    for i in range(-200, LEBAR_LAYAR, 150):
        # alpha lines not directly supported by draw.line without surface; skip alpha blending for safety
        pygame.draw.line(screen, (230,230,230), (i, TINGGI_LAYAR), (i + 300, 0), 5)
        pygame.draw.line(screen, (20,20,20), (i+10, TINGGI_LAYAR), (i + 310, 0), 5)

    title_font = pygame.font.SysFont("Impact", 100)
    title_text = "KERETA RINTANGAN"

    shadow_surf = title_font.render(title_text, True, (0, 0, 0))
    screen.blit(shadow_surf, (LEBAR_LAYAR // 2 - shadow_surf.get_width() // 2 + 8, TINGGI_LAYAR // 4 + 8))
    outline_surf = title_font.render(title_text, True, (255, 140, 0))
    screen.blit(outline_surf, (LEBAR_LAYAR // 2 - outline_surf.get_width() // 2 + 4, TINGGI_LAYAR // 4 + 4))
    main_surf = title_font.render(title_text, True, (255, 215, 0))
    screen.blit(main_surf, (LEBAR_LAYAR // 2 - main_surf.get_width() // 2, TINGGI_LAYAR // 4))

    start_rect_coord = (LEBAR_LAYAR // 2 - 120, TINGGI_LAYAR // 2 + 20, 240, 70)
    exit_rect_coord  = (LEBAR_LAYAR // 2 - 120, TINGGI_LAYAR // 2 + 120, 240, 70)
    draw_button_3d(screen, start_rect_coord, "MULAI", (46, 139, 87), (60, 179, 113))
    draw_button_3d(screen, exit_rect_coord, "KELUAR", (178, 34, 34), (205, 92, 92))
    return start_rect_coord, exit_rect_coord

def update_logic():
    if not state.train_running or state.game_over or state.win:
        return

    speed = 5
    state.train_pixel_pos[0] += state.train_dir[0] * speed
    state.train_pixel_pos[1] += state.train_dir[1] * speed

    curr_gx = int((state.train_pixel_pos[0] - OFFSET_X) // UKURAN_SEL)
    curr_gy = int((state.train_pixel_pos[1] - OFFSET_Y) // UKURAN_SEL)

    if (curr_gx, curr_gy) == state.finish_pos:
        center_target_x = OFFSET_X + curr_gx * UKURAN_SEL + UKURAN_SEL // 2
        dist = abs(state.train_pixel_pos[0] - center_target_x)
        if dist < speed * 2:
            state.win = True
            state.train_running = False
            if sfx_run:
             sfx_run.stop()
            print("Level Selesai!")
        return

    if curr_gx < 0:
        return

    if curr_gx >= KOLOM or curr_gy >= BARIS or curr_gy < 0:
      state.game_over = True
      if sfx_crash: sfx_crash.play()
      return

    center_tile_x = OFFSET_X + curr_gx * UKURAN_SEL + (UKURAN_SEL // 2)
    center_tile_y = OFFSET_Y + curr_gy * UKURAN_SEL + (UKURAN_SEL // 2)

    dx_sq = (state.train_pixel_pos[0] - center_tile_x) ** 2
    dy_sq = (state.train_pixel_pos[1] - center_tile_y) ** 2
    dist = (dx_sq + dy_sq) ** 0.5

    if dist < speed:
        tipe, rot = state.grid[curr_gy][curr_gx]

        print("Train dir:", state.train_dir, "rot:", rot)


        if tipe == KOSONG or tipe == RINTANGAN:
          state.game_over = True
          if sfx_crash: sfx_crash.play()
          return
        if tipe == LURUS_HOR:
            if state.train_dir[1] != 0:
                state.game_over = True
        elif tipe == LURUS_VER:
            if state.train_dir[0] != 0:
                state.game_over = True


        elif tipe == SIKU:
            d = state.train_dir

            if rot == 0:
                if d == [1, 0]:
                    state.train_dir = [0, 1]
                elif d == [0, -1]:
                    state.train_dir = [-1, 0]
                else:
                    state.game_over = True
                    return

            elif rot == 90:
                if d == [0, 1]:
                    state.train_dir = [-1, 0]
                elif d == [1, 0]:
                    state.train_dir = [0, -1]
                else:
                    state.game_over = True
                    return

            elif rot == 180:
                if d == [-1, 0]:
                    state.train_dir = [0, -1]
                elif d == [0, 1]:
                    state.train_dir = [1, 0]
                else:
                    state.game_over = True
                    return

            elif rot == 270:
                if d == [0, -1]:
                    state.train_dir = [1, 0]
                elif d == [-1, 0]:
                    state.train_dir = [0, 1]
                else:
                    state.game_over = True
                    return

            state.train_pixel_pos = [center_tile_x, center_tile_y]

clock = pygame.time.Clock()
running = True

while running:
    # --- PENANGANAN EVENT ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if state.state == MENU_STATE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                start_rect = (LEBAR_LAYAR // 2 - 150, TINGGI_LAYAR // 2, 300, 70)
                exit_rect = (LEBAR_LAYAR // 2 - 150, TINGGI_LAYAR // 2 + 100, 300, 70)

                if start_rect[0] < mx < start_rect[0] + start_rect[2] and \
                   start_rect[1] < my < start_rect[1] + start_rect[3]:
                    state.state = GAME_STATE
                    state.load_level(0)

                elif exit_rect[0] < mx < exit_rect[0] + exit_rect[2] and \
                     exit_rect[1] < my < exit_rect[1] + exit_rect[3]:
                    running = False

        elif state.state == GAME_STATE:
            # Tombol R -> rotasi 90°
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if state.last_clicked is not None:
                        gx, gy = state.last_clicked
                        tipe, rot = state.grid[gy][gx]
                        if tipe == SIKU:
                            rot = (rot + 90) % 360
                            state.grid[gy][gx] = (tipe, rot)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                gx = (mx - OFFSET_X) // UKURAN_SEL
                gy = (my - OFFSET_Y) // UKURAN_SEL

                if 0 <= gx < KOLOM and 0 <= gy < BARIS:
                  state.last_clicked = (gx, gy)

                if 0 <= gx < KOLOM and 0 <= gy < BARIS:
                 state.last_clicked = (gx, gy)
                 if not state.train_running and not state.win:
                    tipe, rot = state.grid[gy][gx]
                    if tipe != RINTANGAN:
                        state.grid[gy][gx] = (state.selected_piece, 0)
                        if sfx_place: sfx_place.play()


                # Klik inventory
                if my > TINGGI_LAYAR - 100:
                    idx = (mx - 50) // 90
                    types = [KOSONG, LURUS_HOR, LURUS_VER, SIKU]
                    if 0 <= idx < len(types):
                        state.selected_piece = types[idx]

                # Tombol aksi
                if (LEBAR_LAYAR - 220 < mx < LEBAR_LAYAR - 20 and
                        TINGGI_LAYAR - 90 < my < TINGGI_LAYAR - 30):
                      if sfx_click: sfx_click.play()
                      if state.win:
                         state.current_level_idx += 1
                         state.load_level(state.current_level_idx)
                      elif state.train_running or state.game_over:
                          state.reset_train()

                      else:
                        state.train_running = True
                        if sfx_run: sfx_run.play()

    # --- LOGIKA GAMBAR ---
    if state.state == MENU_STATE:
        draw_menu()

    elif state.state == GAME_STATE:
        screen.fill((135, 206, 235))

        land_rect = (OFFSET_X - 20, OFFSET_Y - 20,
                     KOLOM * UKURAN_SEL + 40, BARIS * UKURAN_SEL + 40)
        pygame.draw.rect(screen, RUMPUT_MUDA, land_rect, border_radius=15)
        pygame.draw.rect(screen, RUMPUT_TUA, land_rect, 5, border_radius=15)

        pygame.draw.circle(screen, PUTIH, (150, 80), 30)
        pygame.draw.circle(screen, PUTIH, (200, 70), 40)
        pygame.draw.circle(screen, PUTIH, (250, 85), 25)

        update_logic()
        draw_grid()
        draw_ui()
        draw_train(screen, state.train_pixel_pos, state.train_dir)

        if state.game_over:
            overlay = pygame.Surface((LEBAR_LAYAR, TINGGI_LAYAR), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            f = pygame.font.Font(None, 100)
            text_surf = f.render("CRASH!!", True, PUTIH)
            shake_offset = clock.get_rawtime() % 10 - 5
            screen.blit(
                text_surf,
                (LEBAR_LAYAR // 2 - text_surf.get_width() // 2 + shake_offset,
                 TINGGI_LAYAR // 2)
            )

        elif state.win:
            overlay = pygame.Surface((LEBAR_LAYAR, TINGGI_LAYAR), pygame.SRCALPHA)
            overlay.fill((0, 0, 200, 80))
            screen.blit(overlay, (0, 0))

            f = pygame.font.Font(None, 100)
            text_surf = f.render("HEBAT!", True, (255, 255, 0))
            screen.blit(
                text_surf,
                (LEBAR_LAYAR // 2 - text_surf.get_width() // 2,
                 TINGGI_LAYAR // 2)
            )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
