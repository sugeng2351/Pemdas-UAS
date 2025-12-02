import pygame
import sys
import math  # untuk math.pi

# --- KONFIGURASI & WARNA ---
pygame.init()

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
    # PERBAIKAN: Gunakan double underscore (__init__)
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

# --- FUNGSI GAMBAR ---


def draw_track_piece(surface, x, y, piece):
    """piece = (type, rot)"""
    tipe, rot = piece
    cx = x + UKURAN_SEL // 2
    cy = y + UKURAN_SEL // 2

    if tipe == RINTANGAN:
        pygame.draw.rect(
            surface,
            ABU_BATU,
            (x + 10, y + 10, UKURAN_SEL - 20, UKURAN_SEL - 20),
            border_radius=10
        )
        pygame.draw.circle(surface, (80, 80, 80), (x + 25, y + 30), 8)
        pygame.draw.circle(surface, (80, 80, 80), (x + 55, y + 50), 10)
        return

    tebal = 6
    if tipe == LURUS_HOR:
        for i in range(10, UKURAN_SEL, 20):
            pygame.draw.line(surface, TANAH_GELAP,
                             (x + i, cy - 10), (x + i, cy + 10), 4)
        pygame.draw.line(surface, REL_WARNA,
                         (x, cy - tebal // 2), (x + UKURAN_SEL, cy - tebal // 2), 2)
        pygame.draw.line(surface, REL_WARNA,
                         (x, cy + tebal // 2), (x + UKURAN_SEL, cy + tebal // 2), 2)

    elif tipe == LURUS_VER:
        for i in range(10, UKURAN_SEL, 20):
            pygame.draw.line(surface, TANAH_GELAP,
                             (cx - 10, y + i), (cx + 10, y + i), 4)
        pygame.draw.line(surface, REL_WARNA,
                         (cx - tebal // 2, y), (cx - tebal // 2, y + UKURAN_SEL), 2)
        pygame.draw.line(surface, REL_WARNA,
                         (cx + tebal // 2, y), (cx + tebal // 2, y + UKURAN_SEL), 2)

    elif tipe == SIKU:
        # Arc besar, pusat di tengah tile
        cx = x + UKURAN_SEL // 2
        cy = y + UKURAN_SEL // 2

        # radius besar, tapi masih ada margin dikit dari tepi
        margin = 8
        radius = UKURAN_SEL // 2 - margin

        # rect lingkaran dengan pusat (cx, cy)
        arc_rect = (
            cx - radius,
            cy - radius,
            2 * radius,
            2 * radius
        )

        # Orientasi sama dengan logika belok:
        # 0   : kiri -> bawah
        # 90  : atas -> kanan
        # 180 : kanan -> atas
        # 270 : bawah -> kiri
        if rot == 0:
            start_ang = 0
            end_ang = math.pi / 2
        elif rot == 90:
            start_ang = math.pi / 2
            end_ang = math.pi
        elif rot == 180:
            start_ang = math.pi
            end_ang = 3 * math.pi / 2
        else:  # 270
            start_ang = 3 * math.pi / 2
            end_ang = 2 * math.pi

        pygame.draw.arc(surface, REL_WARNA, arc_rect, start_ang, end_ang, 6)


def draw_train(surface, pos, direction):
    lebar_body = 30
    tinggi_body = 20

    body_color = HIJAU_KERETA
    window_color = (173, 216, 230)

    if direction[0] != 0:
        body_rect = (
            pos[0] - lebar_body // 2,
            pos[1] - tinggi_body // 2,
            lebar_body,
            tinggi_body
        )
        pygame.draw.rect(surface, window_color, (pos[0] - 10, pos[1] - 5, 8, 10))
        pygame.draw.rect(surface, window_color, (pos[0] + 2, pos[1] - 5, 8, 10))
    else:
        body_rect = (
            pos[0] - tinggi_body // 2,
            pos[1] - lebar_body // 2,
            tinggi_body,
            lebar_body
        )
        pygame.draw.rect(surface, window_color, (pos[0] - 5, pos[1] - 10, 10, 8))
        pygame.draw.rect(surface, window_color, (pos[0] - 5, pos[1] + 2, 10, 8))

    pygame.draw.rect(surface, body_color, body_rect, border_radius=5)
    pygame.draw.circle(surface, HITAM, (pos[0], pos[1] + 10), 3)


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


# --- FUNGSI BARU UNTUK TOMBOL ESTETIK ---
def draw_button_3d(surface, rect, text, base_color, hover_color, action_func=None):
    """
    Menggambar tombol dengan efek 3D dan hover.
    Mengembalikan True jika tombol diklik.
    """
    mx, my = pygame.mouse.get_pos()
    x, y, w, h = rect
    
    # Cek apakah mouse ada di atas tombol
    is_hover = x < mx < x + w and y < my < y + h
    
    # Tentukan warna (terang jika di-hover)
    color = hover_color if is_hover else base_color
    
    # Warna bayangan (lebih gelap dari warna dasar)
    shadow_color = (max(0, base_color[0]-50), max(0, base_color[1]-50), max(0, base_color[2]-50))
    
    # 1. Gambar Bayangan (geser sedikit ke bawah kanan)
    shadow_offset = 6
    pygame.draw.rect(surface, shadow_color, (x, y + shadow_offset, w, h), border_radius=15)
    
    # 2. Gambar Tombol Utama (bergeser turun dikit kalau di-klik/hover biar kerasa 'pencet')
    btn_y = y + 2 if is_hover else y
    pygame.draw.rect(surface, color, (x, btn_y, w, h), border_radius=15)
    
    # 3. Garis highlight di bagian atas (efek kilau)
    pygame.draw.line(surface, (255, 255, 255), (x+15, btn_y+5), (x+w-15, btn_y+5), 2)

    # 4. Teks Tombol
    font = pygame.font.SysFont("Segoe UI", 40, bold=True) # Pakai font sistem yang lebih bagus
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(x + w//2, btn_y + h//2))
    
    # Efek shadow teks tipis
    text_shadow = font.render(text, True, (0, 0, 0))
    surface.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
    surface.blit(text_surf, text_rect)

    return rect # Kembalikan rect untuk logika klik di main loop


def draw_menu():
    """Menggambar menu dengan gaya estetik."""
    
    # 1. Background Gradient Sederhana (Langit Sore)
    # Kita gambar persegi panjang dari atas ke bawah dengan warna yang makin gelap
    top_color = (70, 130, 180)    # Steel Blue
    bottom_color = (25, 25, 112)  # Midnight Blue
    
    for y in range(TINGGI_LAYAR):
        # Interpolasi warna secara manual
        ratio = y / TINGGI_LAYAR
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (LEBAR_LAYAR, y))

    # 2. Hiasan Latar Belakang (Garis-garis rel abstrak)
    for i in range(-200, LEBAR_LAYAR, 150):
        pygame.draw.line(screen, (255, 255, 255, 50), (i, TINGGI_LAYAR), (i + 300, 0), 5)
        pygame.draw.line(screen, (0, 0, 0, 30), (i+10, TINGGI_LAYAR), (i + 310, 0), 5)

    # 3. Judul Game dengan Style
    title_font = pygame.font.SysFont("Impact", 100) # Font tebal
    title_text = "KERETA RINTANGAN"
    
    # Bayangan Judul (Layer belakang)
    shadow_surf = title_font.render(title_text, True, (0, 0, 0))
    screen.blit(shadow_surf, (LEBAR_LAYAR // 2 - shadow_surf.get_width() // 2 + 8, TINGGI_LAYAR // 4 + 8))
    
    # Outline Judul (Tengah)
    outline_surf = title_font.render(title_text, True, (255, 140, 0)) # Oranye gelap
    screen.blit(outline_surf, (LEBAR_LAYAR // 2 - outline_surf.get_width() // 2 + 4, TINGGI_LAYAR // 4 + 4))

    # Utama Judul (Depan)
    main_surf = title_font.render(title_text, True, (255, 215, 0)) # Emas
    screen.blit(main_surf, (LEBAR_LAYAR // 2 - main_surf.get_width() // 2, TINGGI_LAYAR // 4))

    # --- GAMBAR TOMBOL ---
    # Kita hanya menggambar visualnya di sini. Logika klik tetap di 'main loop'
    # menggunakan koordinat rect yang kita definisikan.
    
    start_rect_coord = (LEBAR_LAYAR // 2 - 120, TINGGI_LAYAR // 2 + 20, 240, 70)
    exit_rect_coord  = (LEBAR_LAYAR // 2 - 120, TINGGI_LAYAR // 2 + 120, 240, 70)

    # Panggil fungsi tombol estetik kita
    # Warna tombol: Hijau untuk Start, Merah Bata untuk Exit
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
            print("Level Selesai!")
        return

    if curr_gx < 0:
        return

    if curr_gx >= KOLOM or curr_gy >= BARIS or curr_gy < 0:
        state.game_over = True
        return

    center_tile_x = OFFSET_X + curr_gx * UKURAN_SEL + (UKURAN_SEL // 2)
    center_tile_y = OFFSET_Y + curr_gy * UKURAN_SEL + (UKURAN_SEL // 2)

    dx_sq = (state.train_pixel_pos[0] - center_tile_x) ** 2
    dy_sq = (state.train_pixel_pos[1] - center_tile_y) ** 2
    dist = (dx_sq + dy_sq) ** 0.5

    if dist < speed:
        tipe, rot = state.grid[curr_gy][curr_gx]

        if tipe == KOSONG or tipe == RINTANGAN:
            state.game_over = True
            return

        if tipe == LURUS_HOR:
            if state.train_dir[1] != 0:
                state.game_over = True
        elif tipe == LURUS_VER:
            if state.train_dir[0] != 0:
                state.game_over = True

        elif tipe == SIKU:
            # Definisi arah:
            # 0   derajat: kiri -> bawah,  bawah -> kiri
            # 90  derajat: atas -> kanan,  kanan -> atas
            # 180 derajat: kanan -> atas,  atas -> kanan (kebalikan 0)
            # 270 derajat: bawah -> kiri,  kiri -> bawah (kebalikan 90)

            d = state.train_dir

            if rot == 0:
                if d == [1, 0]:      # dari kiri
                    state.train_dir = [0, 1]   # ke bawah
                elif d == [0, -1]:   # dari bawah (naik)
                    state.train_dir = [-1, 0]  # ke kiri
                else:
                    state.game_over = True
                    return

            elif rot == 90:
                if d == [0, -1]:     # dari bawah (naik)
                    state.train_dir = [1, 0]   # ke kanan
                elif d == [-1, 0]:   # dari kanan (gerak kiri)
                    state.train_dir = [0, 1]   # ke bawah
                else:
                    state.game_over = True
                    return

            elif rot == 180:
                if d == [-1, 0]:     # dari kanan
                    state.train_dir = [0, -1]  # ke atas
                elif d == [0, 1]:    # dari atas (turun)
                    state.train_dir = [1, 0]   # ke kanan
                else:
                    state.game_over = True
                    return

            elif rot == 270:
                if d == [0, 1]:      # dari atas
                    state.train_dir = [-1, 0]  # ke kiri
                elif d == [1, 0]:    # dari kiri
                    state.train_dir = [0, -1]  # ke atas
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
                # Panggil draw_menu HANYA untuk mendapatkan posisi rect
                start_rect = (LEBAR_LAYAR // 2 - 150, TINGGI_LAYAR // 2, 300, 70)
                exit_rect = (LEBAR_LAYAR // 2 - 150, TINGGI_LAYAR // 2 + 100, 300, 70)

                # Klik Mulai
                if start_rect[0] < mx < start_rect[0] + start_rect[2] and \
                   start_rect[1] < my < start_rect[1] + start_rect[3]:
                    state.state = GAME_STATE # Pindah ke game
                    state.load_level(0)      # Pastikan mulai dari Level 1

                # Klik Keluar
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

                    if not state.train_running and not state.win:
                        tipe, rot = state.grid[gy][gx]
                        if tipe != RINTANGAN:
                            # pasang tipe baru, rotasi awal 0°
                            state.grid[gy][gx] = (state.selected_piece, 0)

                # Klik inventory
                if my > TINGGI_LAYAR - 100:
                    idx = (mx - 50) // 90
                    types = [KOSONG, LURUS_HOR, LURUS_VER, SIKU]
                    if 0 <= idx < len(types):
                        state.selected_piece = types[idx]

                # Tombol aksi
                if (LEBAR_LAYAR - 220 < mx < LEBAR_LAYAR - 20 and
                        TINGGI_LAYAR - 90 < my < TINGGI_LAYAR - 30):
                    if state.win:
                        state.current_level_idx += 1
                        state.load_level(state.current_level_idx)
                    elif state.train_running or state.game_over:
                        state.reset_train()
                    else:
                        state.train_running = True

    # --- LOGIKA GAMBAR ---
    if state.state == MENU_STATE:
        draw_menu() # Hanya gambar menu
    
    elif state.state == GAME_STATE:
        screen.fill((135, 206, 235))

        # Gambar Latar (langit, awan, rumput)
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

        # Gambar Overlay (CRASH/HEBAT)
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