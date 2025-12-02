import pygame
import sys

# --- KONFIGURASI & WARNA ---
pygame.init()

LEBAR_LAYAR = 800
TINGGI_LAYAR = 600
screen = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR))
pygame.display.set_caption("Game Kereta: Level & Rintangan")

# Palette Warna
PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)
TANAH = (210, 180, 140)     # Warna dasar grid
TANAH_GELAP = (139, 69, 19)
REL_WARNA = (80, 80, 80)
HIJAU_KERETA = (34, 139, 34)
MERAH = (220, 20, 60)
ABU_BATU = (105, 105, 105)  # Warna Rintangan

# Grid Config
UKURAN_SEL = 80
OFFSET_X = 120
OFFSET_Y = 100
KOLOM = 7
BARIS = 4  # Saya tambah baris biar area lebih luas

# Tipe Grid
KOSONG = 0
LURUS_HOR = 1
LURUS_VER = 2
BELOK_KN_BW = 3 # Kanan-Bawah / Kiri-Atas
BELOK_BW_KN = 4 # Bawah-Kanan / Atas-Kiri
RINTANGAN = 9   # Batu/Tembok (Tidak bisa dibangun)

# --- DATA LEVEL ---
# Disini kita mengatur desain setiap level
# Format: 'obs': [(x,y)...], 'start': (x,y), 'finish': (x,y)
LEVEL_MAPS = [
    { # LEVEL 1: Tutorial (Lurus saja, ada batu di bawah)
        "obs": [(2, 2), (3, 2), (4, 2)], 
        "start": (0, 1), 
        "finish": (6, 1)
    },
    { # LEVEL 2: Harus Memutar (Batu di tengah jalur lurus)
        "obs": [(3, 1)], 
        "start": (0, 1), 
        "finish": (6, 1)
    },
    { # LEVEL 3: Zig Zag (Stasiun pindah ke bawah)
        "obs": [(2, 0), (2, 1), (4, 2), (4, 3)], 
        "start": (0, 0), 
        "finish": (6, 3)
    }
]

# --- KELAS UTAMA ---

class GameState:
    def __init__(self):
        self.current_level_idx = 0
        self.load_level(self.current_level_idx)
        
        # Inventory Pilihan
        self.selected_piece = LURUS_HOR

    def load_level(self, level_idx):
        """Memuat konfigurasi level berdasarkan index"""
        if level_idx >= len(LEVEL_MAPS):
            print("Semua Level Selesai!")
            self.current_level_idx = 0 # Loop balik ke level 1
            level_idx = 0

        data = LEVEL_MAPS[level_idx]
        
        # 1. Reset Grid
        self.grid = [[KOSONG for _ in range(KOLOM)] for _ in range(BARIS)]
        
        # 2. Pasang Rintangan
        for (bx, by) in data['obs']:
            self.grid[by][bx] = RINTANGAN
            
        # 3. Set Start & Finish
        self.start_pos = data['start'] # (grid_x, grid_y)
        self.finish_pos = data['finish']
        
        # 4. Reset Status Kereta
        self.reset_train()
        
        print(f"Level {level_idx + 1} Dimuat!")

    def reset_train(self):
        self.train_running = False
        self.game_over = False
        self.win = False
        
        # Posisi pixel awal (di sebelah kiri kotak Start)
        sx, sy = self.start_pos
        self.train_dir = [1, 0] # Default gerak ke kanan
        
        # Set posisi pixel tepat sebelum masuk grid start
        start_pixel_x = OFFSET_X + (sx * UKURAN_SEL) - UKURAN_SEL
        start_pixel_y = OFFSET_Y + (sy * UKURAN_SEL) + (UKURAN_SEL // 2)
        
        self.train_pixel_pos = [start_pixel_x, start_pixel_y]

state = GameState()

# --- FUNGSI GAMBAR ---

def draw_track_piece(surface, x, y, type):
    cx = x + UKURAN_SEL // 2
    cy = y + UKURAN_SEL // 2
    
    if type == RINTANGAN:
        # Gambar Batu
        pygame.draw.rect(surface, ABU_BATU, (x+10, y+10, UKURAN_SEL-20, UKURAN_SEL-20), border_radius=10)
        pygame.draw.circle(surface, (80,80,80), (x+30, y+30), 10)
        return

    if type == KOSONG: return

    # Gambar Rel (Sederhana)
    tebal = 6
    if type == LURUS_HOR:
        pygame.draw.line(surface, REL_WARNA, (x, cy), (x+UKURAN_SEL, cy), tebal)
        # Bantalan
        for i in range(10, UKURAN_SEL, 20):
            pygame.draw.line(surface, TANAH_GELAP, (x+i, cy-10), (x+i, cy+10), 4)

    elif type == LURUS_VER:
        pygame.draw.line(surface, REL_WARNA, (cx, y), (cx, y+UKURAN_SEL), tebal)
        for i in range(10, UKURAN_SEL, 20):
            pygame.draw.line(surface, TANAH_GELAP, (cx-10, y+i), (cx+10, y+i), 4)
            
    elif type == BELOK_KN_BW: # Kiri <-> Bawah (Siku)
        pygame.draw.line(surface, REL_WARNA, (x, cy), (cx, cy), tebal)
        pygame.draw.line(surface, REL_WARNA, (cx, cy), (cx, y+UKURAN_SEL), tebal)
        
    elif type == BELOK_BW_KN: # Bawah <-> Kanan (Siku)
        pygame.draw.line(surface, REL_WARNA, (cx, y+UKURAN_SEL), (cx, cy), tebal)
        pygame.draw.line(surface, REL_WARNA, (cx, cy), (x+UKURAN_SEL, cy), tebal)

def draw_grid():
    for r in range(BARIS):
        for c in range(KOLOM):
            rect_x = OFFSET_X + c * UKURAN_SEL
            rect_y = OFFSET_Y + r * UKURAN_SEL
            
            # Warna tanah
            color = TANAH
            if (c, r) == state.start_pos: color = (200, 255, 200) # Hijau muda utk Start
            if (c, r) == state.finish_pos: color = (255, 255, 200) # Kuning muda utk Finish
            
            pygame.draw.rect(screen, color, (rect_x, rect_y, UKURAN_SEL, UKURAN_SEL))
            pygame.draw.rect(screen, (180, 150, 100), (rect_x, rect_y, UKURAN_SEL, UKURAN_SEL), 2)

            # Gambar isi grid (Rel / Batu)
            piece = state.grid[r][c]
            draw_track_piece(screen, rect_x, rect_y, piece)
            
            # Label Start/Finish
            font = pygame.font.Font(None, 20)
            if (c, r) == state.start_pos:
                screen.blit(font.render("START", True, HITAM), (rect_x+5, rect_y+5))
            if (c, r) == state.finish_pos:
                screen.blit(font.render("FINISH", True, HITAM), (rect_x+5, rect_y+5))

def draw_ui():
    # Tombol Inventory
    inv_y = TINGGI_LAYAR - 100
    labels = ["Hapus", "Hor", "Ver", "Siku 1", "Siku 2"]
    types = [KOSONG, LURUS_HOR, LURUS_VER, BELOK_KN_BW, BELOK_BW_KN]
    
    for i, t in enumerate(types):
        bx = 50 + i * 90
        col = (255, 255, 255) if state.selected_piece != t else (100, 255, 100)
        pygame.draw.rect(screen, col, (bx, inv_y, 80, 60))
        pygame.draw.rect(screen, HITAM, (bx, inv_y, 80, 60), 2)
        
        font = pygame.font.Font(None, 20)
        screen.blit(font.render(labels[i], True, HITAM), (bx+10, inv_y+20))
    
    # Info Level
    font_lvl = pygame.font.Font(None, 40)
    screen.blit(font_lvl.render(f"LEVEL: {state.current_level_idx + 1}", True, HITAM), (50, 30))

    # Tombol Aksi (Jalan / Next Level)
    btn_rect = (LEBAR_LAYAR - 220, TINGGI_LAYAR - 90, 200, 60)
    if state.win:
        pygame.draw.rect(screen, (0, 0, 200), btn_rect) # Biru
        txt = "LEVEL SELANJUTNYA >>"
    elif state.train_running:
        pygame.draw.rect(screen, MERAH, btn_rect)
        txt = "RESET"
    else:
        pygame.draw.rect(screen, HIJAU_KERETA, btn_rect)
        txt = "JALANKAN KERETA"
        
    font_btn = pygame.font.Font(None, 24)
    text_surf = font_btn.render(txt, True, PUTIH)
    screen.blit(text_surf, (LEBAR_LAYAR - 200, TINGGI_LAYAR - 70))

def update_logic():
    if not state.train_running or state.game_over or state.win:
        return

    speed = 5
    state.train_pixel_pos[0] += state.train_dir[0] * speed
    state.train_pixel_pos[1] += state.train_dir[1] * speed

    # Konversi pixel ke grid
    curr_gx = int((state.train_pixel_pos[0] - OFFSET_X) // UKURAN_SEL)
    curr_gy = int((state.train_pixel_pos[1] - OFFSET_Y) // UKURAN_SEL)

    # Cek Menang (Sampai di grid Finish)
    if (curr_gx, curr_gy) == state.finish_pos:
        # Cek apakah sudah agak ke tengah grid finish
        center_target_x = OFFSET_X + curr_gx * UKURAN_SEL + UKURAN_SEL//2
        dist = abs(state.train_pixel_pos[0] - center_target_x)
        if dist < speed * 2:
            state.win = True
            state.train_running = False
            print("Level Selesai!")
        return

    # Cek Keluar Batas / Masuk Grid Start lagi
    if curr_gx < 0: return # Masih fase keberangkatan
    
    if curr_gx >= KOLOM or curr_gy >= BARIS or curr_gy < 0:
        state.game_over = True
        return

    # LOGIKA UTAMA: BELOKAN & TABRAKAN
    center_tile_x = OFFSET_X + curr_gx * UKURAN_SEL + (UKURAN_SEL // 2)
    center_tile_y = OFFSET_Y + curr_gy * UKURAN_SEL + (UKURAN_SEL // 2)
    
    dist = ((state.train_pixel_pos[0] - center_tile_x)**2 + (state.train_pixel_pos[1] - center_tile_y)**2)**0.5
    
    if dist < speed: # Saat kereta tepat di tengah kotak
        track = state.grid[curr_gy][curr_gx]
        
        if track == KOSONG or track == RINTANGAN:
            state.game_over = True # Tabrakan
        
        # Logika Belokan Sederhana
        # 1. Jika rel Lurus, arah tidak berubah (tapi harus sesuai arah datang)
        elif track == LURUS_HOR:
            if state.train_dir[1] != 0: state.game_over = True # Datang dari atas/bawah ke rel horizontal = Crash
        elif track == LURUS_VER:
            if state.train_dir[0] != 0: state.game_over = True

        # 2. Belokan Siku (Disederhanakan)
        elif track == BELOK_KN_BW: 
            # Bisa dipakai: Dari Kiri ke Bawah, ATAU Dari Bawah ke Kiri
            if state.train_dir == [1, 0]: # Dari Kiri
                state.train_dir = [0, 1] # Ke Bawah
                state.train_pixel_pos = [center_tile_x, center_tile_y] # Snap
            elif state.train_dir == [0, -1]: # Dari Bawah (naik)
                state.train_dir = [-1, 0] # Ke Kiri
                state.train_pixel_pos = [center_tile_x, center_tile_y]
            else:
                state.game_over = True # Arah datang salah

        elif track == BELOK_BW_KN:
            # Dari Atas ke Kanan, ATAU Dari Kanan ke Atas (Logic ini bisa dibalik tergantung gambar rel)
            # Anggap: Dari Kiri lurus -> Belok Kanan (Lanjut) -> Salah
            # Kita anggap ini siku: Dari Bawah ke Kanan, ATAU Kanan ke Bawah
            if state.train_dir == [0, -1]: # Kereta naik (dari bawah)
                state.train_dir = [1, 0] # Ke Kanan
                state.train_pixel_pos = [center_tile_x, center_tile_y]
            elif state.train_dir == [-1, 0]: # Kereta dari kanan (gerak kiri)
                state.train_dir = [0, 1] # Ke Bawah
                state.train_pixel_pos = [center_tile_x, center_tile_y]
            # Tambahan logika untuk Start dari kiri menuju siku ini
            elif state.train_dir == [1, 0]: # Dari kiri
                 state.game_over = True # Nabrak siku
                 
# --- LOOP UTAMA ---
clock = pygame.time.Clock()
running = True

while running:
    screen.fill((135, 206, 235)) # Langit biru

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            
            # 1. Klik Grid (Taruh Rel)
            gx = (mx - OFFSET_X) // UKURAN_SEL
            gy = (my - OFFSET_Y) // UKURAN_SEL
            
            if 0 <= gx < KOLOM and 0 <= gy < BARIS:
                # Hanya boleh edit jika kereta mati, tidak menang, dan BUKAN RINTANGAN
                if not state.train_running and not state.win:
                    if state.grid[gy][gx] != RINTANGAN:
                        # Cek start/finish tidak boleh ditimpa (opsional, disini kita bolehkan timpa rel di start/finish)
                        state.grid[gy][gx] = state.selected_piece

            # 2. Klik Inventory
            if my > TINGGI_LAYAR - 100:
                idx = (mx - 50) // 90
                types = [KOSONG, LURUS_HOR, LURUS_VER, BELOK_KN_BW, BELOK_BW_KN]
                if 0 <= idx < len(types):
                    state.selected_piece = types[idx]

            # 3. Tombol Aksi (Kanan Bawah)
            btn_area = (LEBAR_LAYAR - 220, TINGGI_LAYAR - 90, 200, 60)
            if LEBAR_LAYAR - 220 < mx < LEBAR_LAYAR - 20 and TINGGI_LAYAR - 90 < my < TINGGI_LAYAR - 30:
                if state.win:
                    # Next Level
                    state.current_level_idx += 1
                    state.load_level(state.current_level_idx)
                elif state.train_running or state.game_over:
                    state.reset_train()
                else:
                    state.train_running = True

    update_logic()
    
    draw_grid()
    draw_ui()
    
    # Draw Train
    pygame.draw.rect(screen, HIJAU_KERETA, (state.train_pixel_pos[0]-15, state.train_pixel_pos[1]-15, 30, 30))
    
    # Pesan Status
    if state.game_over:
        f = pygame.font.Font(None, 80)
        screen.blit(f.render("CRASH!!", True, MERAH), (LEBAR_LAYAR//2-100, TINGGI_LAYAR//2))
    elif state.win:
        f = pygame.font.Font(None, 80)
        screen.blit(f.render("HEBAT!", True, (0, 0, 200)), (LEBAR_LAYAR//2-100, TINGGI_LAYAR//2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()