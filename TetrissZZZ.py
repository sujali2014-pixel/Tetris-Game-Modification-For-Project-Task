import pygame
import sys
import random
import math

# =============================================================================
# 1. KONFIGURASI & ASET
# =============================================================================
pygame.init()
pygame.mixer.init()

# --- Konstanta Game ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
WINNING_SCORE = 105  # Target poin kemenangan
GRID_HEIGHT = 20
GRID_WIDTH = 14
CELL_SIZE = 30  # Ukuran zoom/cell

# --- PATH FILE (Sesuaikan path ini) ---
ASSET_PATHS = {
    "font": "C:/Users/fahri/Downloads/assets/font.ttf",
    # Gunakan BG3.jpg sebagai background utama permainan dan menu
    "bg_image": "C:/Users/fahri/Downloads/assets/P3.png",
    "bg_gameplay": "C:/Users/fahri/Downloads/assets/JADUL.png",
    "bg_difficulty": "C:/Users/fahri/Downloads/assets/P4.png",
    "bg_options": "C:/Users/fahri/Downloads/assets/P5.png",
    "jumpscare_img": "C:/Users/fahri/Downloads/assets/jumoscare.jpeg",
    "sfx_victory": "C:/Users/fahri/Downloads/assets/pvz-victory.mp3",
    "music_bgm": "C:/Users/fahri/Downloads/assets/retro music.mp3",
    "sfx_rotate": "C:/Users/fahri/Downloads/assets/mixkit-air-zoom-vacuum-2608.wav",
    "sfx_clear": "C:/Users/fahri/Downloads/assets/mixkit-retro-game-notification-212.wav",
    "sfx_scream": "C:/Users/fahri/Downloads/assets/acumalaka_04ZUCRu.mp3",
    "sfx_gameover": "C:/Users/fahri/Downloads/assets/mixkit-arcade-retro-game-over-213.wav"
}

# --- Warna ---
COLORS = [
    (0, 0, 0),  # 0: KOSONG
    (255, 255, 0),  # 1: YELLOW
    (255, 0, 0),  # 2: RED
    (0, 255, 255),  # 3: CYAN
    (255, 165, 0),  # 4: ORANGE
    (128, 0, 128),  # 5: PURPLE
    (255, 0, 255),  # 6: MAGENTA
    (0, 150, 150)  # 7: DARK_CYAN
]
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# --- Load Aset ---
assets = {"sounds": {}, "images": {}}
SETTINGS = {"music": True, "sound": True}


def load_resources():
    """Memuat semua aset (musik, SFX, gambar) dari path yang ditentukan."""
    try:
        pygame.mixer.music.load(ASSET_PATHS["music_bgm"])
    except:
        print(f"Warning: Failed to load BGM at {ASSET_PATHS['music_bgm']}")

    for name in ["rotate", "clear", "scream", "gameover", "victory"]:
        path = ASSET_PATHS.get(f"sfx_{name}")
        if path:
            try:
                assets["sounds"][name] = pygame.mixer.Sound(path)
            except:
                print(f"Warning: Failed to load SFX '{name}' at {path}")

    for key, path in ASSET_PATHS.items():
        if key.startswith("bg_") or key == "bg_image" or key == "jumpscare_img":
            # NOTE: Ini akan menghasilkan kunci "bg", "bg_difficulty", "bg_options", "scary_img"
            img_key = key.replace("_image", "").replace("jumpscare", "scary")
            try:
                img = pygame.image.load(path)
                assets["images"][img_key] = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                assets["images"][img_key] = None
                print(f"Warning: Failed to load Image '{img_key}' at {path}")


def get_font(size, is_custom=True):
    """Mendapatkan objek font kustom atau default."""
    if is_custom:
        try:
            return pygame.font.Font(ASSET_PATHS["font"], size)
        except:
            return pygame.font.Font(None, size)
    return pygame.font.SysFont('Calibri', size, True, False)


def play_sfx(name):
    """Memutar sound effect jika diaktifkan."""
    if SETTINGS["sound"] and name in assets["sounds"]:
        assets["sounds"][name].play()


load_resources()


# =============================================================================
# 2. CLASS UTAMA
# =============================================================================

class Button:
    """Kelas untuk membuat tombol interaktif."""

    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image;
        self.x_pos = pos[0];
        self.y_pos = pos[1];
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None: self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        if self.image is not None: screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        return self.rect.collidepoint(position)

    def changeColor(self, position):
        self.text = self.font.render(self.text_input, True,
                                     self.hovering_color if self.rect.collidepoint(position) else self.base_color)


# --- SHAPE LOGIC ---
class Shape:
    """Kelas dasar untuk semua bentuk geometris (Tetrominoes dan Custom Shapes)."""

    def __init__(self, start_pos, color_index, rotation_data, is_polyomino=False):
        self.pos = list(start_pos)
        self.color = color_index
        self.rotation_data = rotation_data  # Data vertices atau cell relatif
        self.rotation_state = 0
        self.is_polyomino = is_polyomino  # True jika bentuk berbasis cell (standar Tetris), False jika berbasis Polygon

    def move(self, direction):
        self.pos[0] += direction[0];
        self.pos[1] += direction[1]

    def rotate(self):
        self.rotation_state = (self.rotation_state + 1) % len(self.rotation_data)

    def get_relative_polygon_data(self):
        return self.rotation_data[self.rotation_state]

    def get_absolute_vertices(self, cell_size, offset_x=0, offset_y=0):
        """Menghitung koordinat absolut untuk rendering bentuk Polygon."""
        if self.is_polyomino: return []
        absolute_polygons = []
        base_x = self.pos[0] * cell_size + offset_x
        base_y = self.pos[1] * cell_size + offset_y
        for polygon_vertices in self.get_relative_polygon_data():
            absolute_vertices = []
            for rx, ry in polygon_vertices:
                abs_x = base_x + int(rx * cell_size)
                abs_y = base_y + int(ry * cell_size)
                absolute_vertices.append((abs_x, abs_y))
            absolute_polygons.append(absolute_vertices)
        return absolute_polygons

    def get_covered_cells(self):
        """Mengidentifikasi semua cell grid yang ditempati oleh bentuk, baik Polygon maupun Polyomino."""
        covered = set()
        relative_data = self.get_relative_polygon_data()
        if self.is_polyomino:
            # Polyomino menggunakan data cell relatif langsung (selalu ada di index 0)
            relative_cells = relative_data[0]
            for r_col, r_row in relative_cells:
                covered.add((int(self.pos[0] + r_col), int(self.pos[1] + r_row)))
        else:
            # Bentuk Polygon (membutuhkan perhitungan rentang bounding box)
            all_rx = [v[0] for poly in relative_data for v in poly]
            all_ry = [v[1] for poly in relative_data for v in poly]
            if not all_rx: return []
            min_x, max_x = math.floor(min(all_rx)), math.ceil(max(all_rx))
            min_y, max_y = math.floor(min(all_ry)), math.ceil(max(all_ry))
            for r_col in range(min_x, max_x):
                for r_row in range(min_y, max_y):
                    # Asumsi: Setiap cell dalam bounding box ditempati.
                    covered.add((int(self.pos[0] + r_col), int(self.pos[1] + r_row)))
        return list(covered)


# Definisi Bentuk Polygon Kustom
class Jajargenjang(Shape):
    def __init__(self, start_pos):
        data = [[[(0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (1.0, 1.0)]],
                [[(1.0, 0.0), (1.0, 1.0), (0.0, 2.0), (0.0, 1.0)]]]
        super().__init__(start_pos, 1, data)


class SegitigaSiku(Shape):
    def __init__(self, start_pos):
        data = [[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]],
                [[(1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]],
                [[(1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]],
                [[(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]]]
        super().__init__(start_pos, 2, data)


class Diamond(Shape):
    def __init__(self, start_pos):
        data = [[[(0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5)]]]
        super().__init__(start_pos, 3, data)


class Kotak(Shape):
    def __init__(self, start_pos):
        data = [[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]]]
        super().__init__(start_pos, 4, data)


class Trapesium(Shape):
    def __init__(self, start_pos):
        data = [[[(0.0, 1.0), (2.0, 1.0), (1.5, 0.0), (0.5, 0.0)]],
                [[(1.0, 0.0), (1.0, 2.0), (0.0, 1.5), (0.0, 0.5)]]]
        super().__init__(start_pos, 6, data)


class SegiLima(Shape):
    def __init__(self, start_pos):
        data = [[[(1.0, 0.0), (1.95, 0.69), (1.59, 1.81), (0.41, 1.81), (0.05, 0.69)]]]
        super().__init__(start_pos, 7, data)


class ArrowShape(Shape):
    def __init__(self, start_pos):
        data = [
            # Rotasi 0 (Panah Atas)
            [[(0.0, 2.0), (0.0, 1.0), (1.0, 0.0), (2.0, 1.0), (2.0, 2.0)]],
            # Rotasi 1 (Panah Kanan)
            [[(0.0, 0.0), (1.0, 0.0), (2.0, 1.0), (1.0, 2.0), (0.0, 2.0)]],
            # Rotasi 2 (Panah Bawah)
            [[(2.0, 0.0), (2.0, 1.0), (1.0, 2.0), (0.0, 1.0), (0.0, 0.0)]],
            # Rotasi 3 (Panah Kiri)
            [[(2.0, 2.0), (1.0, 2.0), (0.0, 1.0), (1.0, 0.0), (2.0, 0.0)]],
        ]
        # Color Index 7 = DARK_CYAN
        super().__init__(start_pos, 7, data, is_polyomino=False)


# Definisi Bentuk Polyomino Standar
class LShape(Shape):
    def __init__(self, start_pos):
        data = [[[(1, 0), (1, 1), (1, 2), (0, 2)]],
                [[(0, 1), (1, 1), (2, 1), (2, 2)]],
                [[(0, 0), (1, 0), (0, 1), (0, 2)]],
                [[(0, 0), (0, 1), (1, 0), (2, 0)]]]
        super().__init__(start_pos, 5, data, is_polyomino=True)


class TShape(Shape):
    def __init__(self, start_pos):
        data = [
            [[(0, 1), (1, 1), (2, 1), (1, 0)]],  # Tepi Bawah
            [[(1, 0), (1, 1), (1, 2), (2, 1)]],  # Tepi Kanan
            [[(0, 0), (1, 0), (2, 0), (1, 1)]],  # Tepi Atas
            [[(0, 1), (1, 0), (1, 1), (1, 2)]],  # Tepi Kiri
        ]
        super().__init__(start_pos, 5, data, is_polyomino=True)


class JShape(Shape):
    def __init__(self, start_pos):
        data = [
            [[(0, 0), (0, 1), (1, 1), (2, 1)]],  # Tepi Kiri Bawah (Indeks 0)
            [[(1, 0), (2, 0), (1, 1), (1, 2)]],  # Tepi Kanan Atas
            [[(0, 1), (1, 1), (2, 1), (2, 2)]],  # Tepi Kanan Bawah
            [[(1, 0), (1, 1), (0, 2), (1, 2)]],  # Tepi Kiri Atas
        ]
        super().__init__(start_pos, 4, data, is_polyomino=True)


class SShape(Shape):
    def __init__(self, start_pos):
        data = [
            [[(1, 0), (2, 0), (0, 1), (1, 1)]],  # Rotasi 0 (Horizontal Skew)
            [[(0, 0), (0, 1), (1, 1), (1, 2)]],  # Rotasi 1 (Vertikal Skew)
        ]
        super().__init__(start_pos, 2, data, is_polyomino=True)


AVAILABLE_SHAPES = [Jajargenjang, SegitigaSiku, Diamond, Kotak, LShape, Trapesium, SegiLima, TShape, JShape, SShape,
                    ArrowShape]


# =============================================================================
# 3. GAME ENGINE
# =============================================================================

class TetrisGame:
    """Logika inti permainan Tetris, termasuk pergerakan, tumbukan, dan fitur level."""

    def __init__(self, height, width, initial_level=2):
        self.height = height;
        self.width = width;
        self.level = initial_level
        self.score = 0;
        self.state = "start"
        self.field = [[0] * width for _ in range(height)]

        self.zoom = CELL_SIZE
        self.x = (SCREEN_WIDTH - (self.width * self.zoom)) // 2  # Posisi X grid
        self.y = 50  # Posisi Y grid

        # Variabel Khusus Medium (Earthquake)
        self.last_quake_time = pygame.time.get_ticks()
        self.quake_interval = random.randint(10000, 15000)
        self.is_quaking = False
        self.quake_count = 0
        self.trigger_special_math = False

        self.figure = None;
        self.next_figure = None
        self._generate_new_figure()

    def _get_random_shape(self):
        """Memilih bentuk secara acak."""
        ShapeClass = random.choice(AVAILABLE_SHAPES)
        # Menyesuaikan posisi awal agar sesuai dengan kebutuhan bounding box Polygon
        start_x = self.width // 2 - 1
        if issubclass(ShapeClass, ArrowShape):
            # ArrowShape memiliki lebar 2, jadi pusat di self.width // 2 - 1
            start_x = self.width // 2 - 1
        elif ShapeClass in [Jajargenjang, SegitigaSiku, Diamond, Kotak, Trapesium, SegiLima]:
            # Bentuk 1x1 atau 2x2, pusat di self.width // 2 - 1
            start_x = self.width // 2 - 1
        return ShapeClass((start_x, 0))

    def _generate_new_figure(self):
        """Membuat bentuk baru dan memajukan 'next figure'."""
        if self.next_figure is None:
            self.figure = self._get_random_shape()
            self.next_figure = self._get_random_shape()
        else:
            self.figure = self.next_figure
            self.figure.pos = [self.width // 2 - 1, 0]  # Reset posisi ke tengah atas
            self.next_figure = self._get_random_shape()

        if self.check_collision(self.figure):
            self.state = "gameover"

    def apply_earthquake(self):
        """Logic Gempa untuk Level Medium (menggeser setiap baris secara acak)."""
        play_sfx('gameover')
        self.is_quaking = True
        self.quake_count += 1

        for i in range(self.height - 1, -1, -1):
            if any(self.field[i]):
                direction = random.choice([-1, 1])
                new_row = [0] * self.width
                if direction == 1:  # Geser Kanan
                    new_row[1:] = self.field[i][:-1]
                else:  # Geser Kiri
                    new_row[:-1] = self.field[i][1:]
                self.field[i] = new_row

        self.last_quake_time = pygame.time.get_ticks()
        self.quake_interval = random.randint(10000, 15000)

        # Trigger Soal setelah 5x Gempa
        if self.quake_count >= 5:
            self.trigger_special_math = True
            self.quake_count = 0

    def check_collision(self, shape, direction=(0, 0)):
        """Memeriksa tumbukan bentuk pada posisi baru."""
        original_pos = shape.pos[:]
        shape.pos = [shape.pos[0] + direction[0], shape.pos[1] + direction[1]]
        collision = False
        for col, row in shape.get_covered_cells():
            # Cek batas grid
            if col < 0 or col >= self.width or row >= self.height:
                collision = True;
                break
            # Cek blok lain di grid
            if row >= 0 and self.field[row][col] > 0:
                collision = True;
                break
        shape.pos = original_pos  # Kembalikan posisi
        return collision

    def go_down(self):
        if not self.check_collision(self.figure, (0, 1)):
            self.figure.move((0, 1))
        else:
            self.freeze()

    def go_side(self, dx):
        if not self.check_collision(self.figure, (dx, 0)):
            self.figure.move((dx, 0))

    def go_space(self):
        while not self.check_collision(self.figure, (0, 1)):
            self.figure.move((0, 1))
        self.freeze()

    def rotate(self):
        old_state = self.figure.rotation_state
        self.figure.rotate()
        if self.check_collision(self.figure):
            self.figure.rotation_state = old_state  # Kembali jika nabrak
        else:
            play_sfx('rotate')

    def freeze(self):
        """Membekukan bentuk ke dalam grid."""
        for col, row in self.figure.get_covered_cells():
            if 0 <= row < self.height and 0 <= col < self.width:
                c_idx = self.figure.color
                if c_idx >= len(COLORS): c_idx = 1
                self.field[row][col] = c_idx
        self.break_lines()
        self._generate_new_figure()

    def break_lines(self):
        """Menghapus baris yang penuh dan menghitung skor."""
        lines = 0
        new_field = [[0] * self.width for _ in range(self.height)]
        current_row = self.height - 1

        for i in range(self.height - 1, -1, -1):
            if all(self.field[i]):  # Jika baris penuh
                lines += 1
            else:  # Jika tidak penuh, salin baris
                new_field[current_row] = self.field[i]
                current_row -= 1

        self.field = new_field

        if lines > 0:
            self.score += lines * 30
            play_sfx('clear')


class MathChallenge:
    """Kelas untuk mengelola tantangan matematika yang memicu Jumpscare."""

    def __init__(self):
        self.active = False;
        self.passed = False
        self.question = "";
        self.answer = "";
        self.user_input = ""
        self.start_time = 0;
        self.duration = 5

    def start(self, custom_duration=5):
        """Membuat soal matematika acak."""
        if not self.active and not self.passed:
            ops = ['+', '-', '*']
            op = random.choice(ops)
            a, b = random.randint(5, 10), random.randint(5, 15)
            if op == '+':
                ans = a + b
            elif op == '-':
                ans = a - b
            else:
                ans = a * b

            self.question = f"{a} {op} {b} = ?"
            self.answer = str(ans)
            self.user_input = ""
            self.start_time = pygame.time.get_ticks()
            self.active = True
            self.duration = custom_duration

    def update_timer(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
        return max(0, self.duration - elapsed)

    def check_input(self, key_char):
        if key_char.isnumeric() or key_char == '-':
            self.user_input += key_char

    def submit(self):
        """Memeriksa jawaban yang dimasukkan pengguna."""
        if self.user_input == self.answer:
            self.passed = True;
            self.active = False
            play_sfx('clear')
            return True
        return False


# =============================================================================
# 4. GAMBAR & UI
# =============================================================================

def trigger_jumpscare():
    """Menampilkan gambar jumpscare, memainkan SFX, dan kembali ke menu."""
    pygame.mixer.music.stop()
    play_sfx('scream')
    img = assets["images"].get("scary_img")
    if img:
        SCREEN.blit(img, (0, 0))
    else:
        SCREEN.fill(COLOR_BLACK)
    pygame.display.flip()
    pygame.time.delay(3000)
    if SETTINGS["music"]: pygame.mixer.music.play(-1)
    main_menu()


def victory_screen(final_score):
    """Layar kemenangan."""

    pygame.mixer.music.stop()
    play_sfx('victory')

    while True:
        SCREEN.fill((255, 215, 0))
        title = get_font(80).render("VICTORY!", True, COLOR_BLACK)
        score_text = get_font(50).render(f"Final Score: {final_score}", True, "Blue")
        msg = get_font(30).render("Congratulations!", True, COLOR_BLACK)
        btn = Button(None, (640, 550), "MENU", get_font(50), COLOR_BLACK, COLOR_WHITE)
        mouse_pos = pygame.mouse.get_pos()
        SCREEN.blit(title, title.get_rect(center=(640, 200)))
        SCREEN.blit(score_text, score_text.get_rect(center=(640, 350)))
        SCREEN.blit(msg, msg.get_rect(center=(640, 400)))
        btn.changeColor(mouse_pos);
        btn.update(SCREEN)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn.checkForInput(mouse_pos):
                    if SETTINGS["music"]: pygame.mixer.music.play(-1)
                    main_menu();
                    return
        pygame.display.flip()


def draw_glitch_effect(surface):
    """Menambahkan efek visual Glitch (untuk Hard Mode)."""
    width, height = surface.get_size()

    # 1. Efek Geser Horizontal (Slicing)
    num_slices = random.randint(3, 10)
    for _ in range(num_slices):
        y = random.randint(0, height - 20)
        h = random.randint(5, 40)
        shift = random.randint(-30, 30)
        try:
            slice_rect = pygame.Rect(0, y, width, h)
            slice_surf = surface.subsurface(slice_rect).copy()
            surface.blit(slice_surf, (shift, y))
        except:
            pass

    # 2. Efek Noise Warna (Artifacts)
    for _ in range(random.randint(5, 15)):
        w = random.randint(10, 100);
        h = random.randint(2, 10)
        x = random.randint(0, width);
        y = random.randint(0, height)
        color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)])
        pygame.draw.rect(surface, color, (x, y, w, h))

    # 3. Efek RGB Split
    if random.choice([True, False]):
        offset = random.randint(2, 5)
        rgb_surf = surface.copy()
        rgb_surf.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(rgb_surf, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)


def draw_game_board(game):
    """Menggambar grid, blok yang sudah beku, dan bentuk yang sedang jatuh."""
    shake_x, shake_y = 0, 0
    if game.is_quaking:
        shake_x = random.randint(-5, 5)
        shake_y = random.randint(-5, 5)
        if random.randint(0, 20) == 0: game.is_quaking = False  # Akhiri goyangan acak

    # **********************************************
    # MODIFIKASI: Gambar latar belakang hitam di area grid
    # **********************************************
    grid_width_px = game.width * game.zoom
    grid_height_px = game.height * game.zoom

    # Buat Rect yang menutupi area grid
    grid_rect = pygame.Rect(game.x + shake_x, game.y + shake_y, grid_width_px, grid_height_px)

    # Isi Rect dengan warna hitam (COLOR_BLACK)
    pygame.draw.rect(SCREEN, COLOR_BLACK, grid_rect)

    # Tambahkan bingkai putih (opsional)
    pygame.draw.rect(SCREEN, COLOR_WHITE, grid_rect, 2)

    # Gambar Grid dan Blok beku
    for i in range(game.height):
        for j in range(game.width):
            # Posisi sel, disesuaikan dengan goyangan
            rect = [game.x + game.zoom * j + shake_x, game.y + game.zoom * i + shake_y, game.zoom, game.zoom]

            # Gambar sel beku (di atas latar belakang hitam)
            if game.field[i][j] > 0:
                c_idx = game.field[i][j]
                color = COLORS[c_idx] if c_idx < len(COLORS) else COLOR_WHITE
                inner = [game.x + game.zoom * j + 1 + shake_x, game.y + game.zoom * i + 1 + shake_y, game.zoom - 2,
                         game.zoom - 2]
                pygame.draw.rect(SCREEN, color, inner)

                # Garis Grid
            pygame.draw.rect(SCREEN, (128, 128, 128), rect, 1)

            # Fungsi pembantu untuk menggambar Shape

    def draw_single_shape(shape, offset_x, offset_y, zoom):
        color_idx = shape.color if shape.color < len(COLORS) else 1
        actual_color = COLORS[color_idx]

        if shape.is_polyomino:  # Polyomino (kotak cell)
            cells = shape.rotation_data[shape.rotation_state][0]
            base_x = shape.pos[0] * zoom + offset_x + shake_x
            base_y = shape.pos[1] * zoom + offset_y + shake_y
            for r_col, r_row in cells:
                r = pygame.Rect(base_x + r_col * zoom, base_y + r_row * zoom, zoom, zoom)
                pygame.draw.rect(SCREEN, actual_color, r)
                pygame.draw.rect(SCREEN, COLOR_WHITE, r, 2)
        else:  # Polygon (bentuk custom)
            verts_list = shape.get_absolute_vertices(zoom, offset_x + shake_x, offset_y + shake_y)
            for v in verts_list:
                pygame.draw.polygon(SCREEN, actual_color, v)
                pygame.draw.polygon(SCREEN, COLOR_WHITE, v, 2)

    # Gambar bentuk yang sedang jatuh
    if game.figure:
        draw_single_shape(game.figure, game.x, game.y, game.zoom)

    # UI Samping (Next Shape, Score, Goal)
    next_x = game.x + game.width * game.zoom + 50
    next_y = game.y + 100
    pygame.draw.rect(SCREEN, (50, 50, 80), [next_x - 10, next_y - 10, 170, 250], 0)
    pygame.draw.rect(SCREEN, (200, 200, 200), [next_x - 10, next_y - 10, 170, 250], 2)

    font_s = get_font(25, False)
    SCREEN.blit(font_s.render("NEXT SHAPE", True, COLOR_WHITE), [next_x + 10, next_y])
    SCREEN.blit(font_s.render(f"Score: {game.score}", True, COLOR_WHITE), [next_x + 10, next_y + 150])
    SCREEN.blit(font_s.render(f"Goal: {WINNING_SCORE}", True, "Yellow"), [next_x + 10, next_y + 180])

    if hasattr(game, 'quake_count') and game.level == 3:
        lbl = get_font(20, False).render(f"Quakes: {game.quake_count}/5", True, "Red")
        SCREEN.blit(lbl, [next_x + 10, next_y + 220])

    if game.next_figure:
        # Gambar next figure
        orig_pos = game.next_figure.pos[:]
        game.next_figure.pos = [0, 0]  # Atur posisi relatif untuk preview
        draw_single_shape(game.next_figure, next_x + 40, next_y + 50, game.zoom)
        game.next_figure.pos = orig_pos  # Kembalikan posisi
        
def _draw_overlay(logic, time_rem, title, color):
    """Fungsi bantuan untuk menggambar layar pertanyaan matematika."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200) # Transparansi background
    overlay.fill(COLOR_BLACK) 
    SCREEN.blit(overlay, (0, 0))
    
    # Daftar teks yang akan ditampilkan: (Teks, Ukuran Font, Warna, Posisi Y)
    texts = [
        (title, 60, color, 200),
        (logic.question, 80, COLOR_WHITE, 350),
        (logic.user_input + "_", 60, "Yellow", 450),
        (f"{time_rem:.1f}s", 80, color, 550)
    ]
    
    for txt, size, col, y in texts:
        surf = get_font(size).render(txt, True, col)
        SCREEN.blit(surf, surf.get_rect(center=(SCREEN_WIDTH//2, y)))


# =============================================================================
# 5. FUNGSI UTAMA MENU & PLAY
# =============================================================================
def play(level_speed):
    """Loop utama permainan Tetris."""
    pygame.mixer.music.set_volume(0.5)
    if not pygame.mixer.music.get_busy() and SETTINGS["music"]:
        pygame.mixer.music.play(-1)

    game = TetrisGame(GRID_HEIGHT, GRID_WIDTH, initial_level=level_speed)
    math_logic = MathChallenge()
    clock = pygame.time.Clock()
    counter = 0
    pressing_down = False

    # [MODIFIKASI] Variabel Limitasi Jantung (Hanya untuk Hard Mode)
    hard_mode_revives = 0
    MAX_REVIVES = 1  # Pemain hanya bisa bangkit 1 kali

    btn_menu = Button(None, (1100, 680), "MENU", get_font(40), COLOR_WHITE, "Red")
    restart_x = SCREEN_WIDTH // 2
    btn_restart = Button(None, (restart_x, 450), "PLAY AGAIN", get_font(40, False), (255, 125, 0), (255, 215, 0))

    # Variabel untuk Glitch (KHUSUS HARD / Level 6)
    glitch_active = False
    glitch_end_time = 0
    next_glitch_time = pygame.time.get_ticks() + random.randint(2000, 5000)

    while True:
        current_time = pygame.time.get_ticks()

        # Cek Kemenangan
        if game.score >= WINNING_SCORE:
            victory_screen(game.score);
            return

        # --- Trigger Fitur Level ---
        # MEDIUM (Level 3): Gempa
        if level_speed == 3 and not game.trigger_special_math:
            if current_time - game.last_quake_time > game.quake_interval:
                game.apply_earthquake()

        # HARD (Level 6): Glitch
        if level_speed == 6 and game.state == "start":
            if current_time > next_glitch_time:
                glitch_active = True
                glitch_end_time = current_time + random.randint(100, 400)
                next_glitch_time = current_time + random.randint(2000, 6000)

            if current_time > glitch_end_time:
                glitch_active = False

        mouse_pos = pygame.mouse.get_pos()

        # === GAME LOGIC (Dropping) ===
        if game.state == "start" and not game.trigger_special_math:
            counter += 1
            speed_mult = 2
            if level_speed == 6 and glitch_active: speed_mult = 4

            drop_speed = max(1, FPS // (game.level * speed_mult))

            if counter % drop_speed == 0 or pressing_down:
                game.go_down()

        # === EVENT HANDLING ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_menu.checkForInput(mouse_pos):
                    if SETTINGS["music"]: pygame.mixer.music.unpause()
                    main_menu();
                    return

                if game.state == "gameover" and math_logic.passed and level_speed != 3 and level_speed != 1:
                    if btn_restart.checkForInput(mouse_pos):
                        # Reset total game (revive limit juga reset)
                        game = TetrisGame(GRID_HEIGHT, GRID_WIDTH, level_speed)
                        math_logic = MathChallenge()
                        hard_mode_revives = 0 # Reset counter revive jika main dari awal
                        if SETTINGS["music"]: pygame.mixer.music.play(-1)

            if event.type == pygame.KEYDOWN:
                # Kontrol Game Normal
                if game.state == "start" and not game.trigger_special_math:
                    direction = 1
                    if glitch_active and random.choice([True, False]): direction = -1

                    if event.key == pygame.K_UP: game.rotate()
                    if event.key == pygame.K_DOWN: pressing_down = True
                    if event.key == pygame.K_LEFT: game.go_side(-1 * direction)
                    if event.key == pygame.K_RIGHT: game.go_side(1 * direction)
                    if event.key == pygame.K_SPACE: game.go_space()

                # Kontrol Matematika SPESIAL (Medium: 5x Gempa)
                elif game.state == "start" and game.trigger_special_math and level_speed == 3:
                    if math_logic.active:
                        if event.key == pygame.K_BACKSPACE:
                            math_logic.user_input = math_logic.user_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            if math_logic.submit():
                                game.score += 10
                                game.field = [[0] * game.width for _ in range(game.height)]
                                game.trigger_special_math = False
                                game.quake_count = 0
                                math_logic = MathChallenge()
                            else:
                                trigger_jumpscare(); return
                        else:
                            math_logic.check_input(event.unicode)

                # Kontrol Matematika BIASA (Game Over Easy/Hard)
                elif game.state == "gameover" and not math_logic.passed and level_speed != 3:
                    if math_logic.active:
                        if event.key == pygame.K_BACKSPACE:
                            math_logic.user_input = math_logic.user_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            if math_logic.submit():
                                # --- [MODIFIKASI] LOGIKA HARD MODE (Level 6) ---
                                if level_speed == 6:
                                    # 1. Cek Limitasi Jantung (Max Revive)
                                    if hard_mode_revives < MAX_REVIVES:
                                        hard_mode_revives += 1 # Pakai 1 nyawa
                                        game.score += 10
                                        
                                        # 2. Sistem Glitch Residue (Papan Kotor)
                                        # Buat papan baru yang kosong
                                        new_field = [[0] * game.width for _ in range(game.height)]
                                        
                                        # Isi setengah papan terbawah dengan sampah acak
                                        start_row = game.height // 2 # Mulai dari tengah ke bawah
                                        for r in range(start_row, game.height):
                                            for c in range(game.width):
                                                # 70% kemungkinan terisi blok acak, 30% lubang
                                                if random.random() > 0.3:
                                                    # Warna random 1-7
                                                    new_field[r][c] = random.randint(1, 7)
                                                else:
                                                    new_field[r][c] = 0
                                        
                                        game.field = new_field # Terapkan papan kotor
                                        game.state = "start"   # Lanjutkan game
                                        math_logic = MathChallenge()
                                        
                                        print(f"Revived! Uses: {hard_mode_revives}/{MAX_REVIVES}")
                                    else:
                                        # Jika nyawa habis, langsung mati total
                                        trigger_jumpscare()
                                        return
                                
                                # --- MODIFIKASI EASY MODE (Level 1) ---
                                elif level_speed == 1:
                                    game.score += 25
                                    game.field = [[0] * game.width for _ in range(game.height)]
                                    game.state = "start"
                                    math_logic = MathChallenge()

                                if game.score >= WINNING_SCORE: victory_screen(game.score); return
                            else:
                                trigger_jumpscare(); return
                        else:
                            math_logic.check_input(event.unicode)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN: pressing_down = False

        # === RENDERING ===
        background_img = assets["images"].get("bg_gameplay")
        if background_img: SCREEN.blit(background_img, (0, 0))
        else: SCREEN.fill((20, 20, 30))

        draw_game_board(game)
        btn_menu.changeColor(mouse_pos); btn_menu.update(SCREEN)

        if glitch_active and level_speed == 6:
            draw_glitch_effect(SCREEN)

        # LOGIKA TAMPILAN
        if level_speed == 3:
            if game.state == "gameover": trigger_jumpscare(); return
            if game.trigger_special_math:
                if not math_logic.active:
                    if pygame.mixer.music.get_busy(): pygame.mixer.music.pause()
                    math_logic.start(custom_duration=3)
                rem = math_logic.update_timer()
                if rem <= 0: trigger_jumpscare(); return
                
                # ... (code overlay medium sama seperti sebelumnya) ...
                _draw_overlay(math_logic, rem, "EARTHQUAKE!", "Red") # Helper function opsional atau copy code lama

        # 2. TAMPILAN HARD (Quick Math + Info Nyawa)
        elif level_speed == 6:
            if game.state == "gameover":
                # Cek dulu apakah nyawa masih ada SEBELUM menampilkan soal
                if hard_mode_revives >= MAX_REVIVES:
                    trigger_jumpscare()
                    return

                if not math_logic.passed:
                    if pygame.mixer.music.get_busy(): pygame.mixer.music.pause()
                    math_logic.start(custom_duration=3)
                    
                    rem = math_logic.update_timer()
                    if rem <= 0: trigger_jumpscare(); return

                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                    overlay.set_alpha(220); overlay.fill((0, 0, 0))
                    SCREEN.blit(overlay, (0, 0))

                    # Tampilkan sisa nyawa di layar
                    revive_text = f"REVIVE: {MAX_REVIVES - hard_mode_revives} LEFT"
                    
                    texts = [
                        ("LAST CHANCE (3s)!", 60, "Red", 150), 
                        (revive_text, 40, "Orange", 220), # Info nyawa
                        (math_logic.question, 100, "White", 350),
                        (math_logic.user_input + "_", 80, "Yellow", 500), 
                        (f"{rem:.1f}s", 100, "Red", 650)
                    ]
                    for txt, s, c, y in texts:
                        surf = get_font(s).render(txt, True, c)
                        SCREEN.blit(surf, surf.get_rect(center=(640, y)))

        # 3. TAMPILAN EASY
        elif level_speed == 1:
            if game.state == "gameover":
                # ... (Code lama easy mode) ...
                if not math_logic.passed:
                    if pygame.mixer.music.get_busy(): pygame.mixer.music.pause()
                    math_logic.start(custom_duration=5)
                    rem = math_logic.update_timer()
                    if rem <= 0: trigger_jumpscare(); return

                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                    overlay.set_alpha(200); overlay.fill((50, 50, 50))
                    SCREEN.blit(overlay, (0, 0))
                    texts = [("SOLVE TO REVIVE", 50, "Green", 150), (math_logic.question, 80, "White", 300),
                             (math_logic.user_input + "_", 60, "Yellow", 400), (f"{rem:.1f}s", 80, "White", 550)]
                    for txt, s, c, y in texts:
                        surf = get_font(s).render(txt, True, c)
                        SCREEN.blit(surf, surf.get_rect(center=(640, y)))

        pygame.display.flip()
        clock.tick(FPS)
        

def options():
    """Layar Opsi/Pengaturan (Musik dan SFX)."""
    clock = pygame.time.Clock()
    while True:
        mouse_pos = pygame.mouse.get_pos()
        if assets["images"]["bg_options"]:
            SCREEN.blit(assets["images"]["bg_options"], (0, 0))
        else:
            SCREEN.fill((30, 30, 50))

        title = get_font(40).render("SETTINGS", True, "#000000")
        SCREEN.blit(title, title.get_rect(center=(640, 50)))
        btn_back = Button(None, (1090, 680), "BACK", get_font(40), COLOR_WHITE, "Red")
        mus_txt = "ON" if SETTINGS["music"] else "OFF"
        snd_txt = "ON" if SETTINGS["sound"] else "OFF"
        btn_music = Button(None, (290, 200), f"MUSIC: {mus_txt}", get_font(20), COLOR_WHITE, "Red")
        btn_sound = Button(None, (290, 290), f"SFX: {snd_txt}", get_font(20), COLOR_WHITE, "Red")

        for b in [btn_back, btn_music, btn_sound]:
            b.changeColor(mouse_pos);
            b.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.checkForInput(mouse_pos): main_menu(); return
                if btn_music.checkForInput(mouse_pos):
                    SETTINGS["music"] = not SETTINGS["music"]
                    if SETTINGS["music"]:
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.pause()
                if btn_sound.checkForInput(mouse_pos): SETTINGS["sound"] = not SETTINGS["sound"]
        pygame.display.update()
        clock.tick(60)


def difficulty_selection():
    """Layar pemilihan tingkat kesulitan."""
    while True:
        if assets["images"]["bg_difficulty"]:
            SCREEN.blit(assets["images"]["bg_difficulty"], (0, 0))
        else:
            SCREEN.fill((20, 20, 50))
        mouse_pos = pygame.mouse.get_pos()

        btns = [
            Button(None, (640, 280), "EASY", get_font(75), "#d9e3ce", "#009621"),  # Level 1
            Button(None, (640, 430), "MEDIUM", get_font(75), "#d9e3ce", "#009621"),  # Level 3 (Earthquake)
            Button(None, (640, 580), "HARD", get_font(75), "#d9e3ce", "#009621")  # Level 6 (Glitch)
        ]
        btn_back = Button(None, (1090, 680), "BACK", get_font(40), COLOR_WHITE, "Red")
        speeds = [1, 3, 6]

        for b in btns + [btn_back]: b.changeColor(mouse_pos); b.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back.checkForInput(mouse_pos): main_menu(); return
                for i, b in enumerate(btns):
                    if b.checkForInput(mouse_pos): play(speeds[i]); return
        pygame.display.update()


def main_menu():
    """Loop utama menu game."""

    pygame.mixer.music.set_volume(0.7)
    if SETTINGS["music"] and not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.play(-1)
        except:
            pass

    while True:
        # Menggunakan kunci "bg" dari "bg_image"
        if assets["images"]["bg"]:
            SCREEN.blit(assets["images"]["bg"], (0, 0))
        else:
            SCREEN.fill((50, 50, 50))
        mouse_pos = pygame.mouse.get_pos()
        

        btns = [
            Button(None, (640, 285), "PLAY", get_font(75), "#b8dd91", "#6b008f"),
            Button(None, (640, 435), "OPTIONS", get_font(75), "#b8dd91", "#6b008f"),
            Button(None, (640, 580), "QUIT", get_font(75), "#b8dd91", "#6b008f")
        ]

        for b in btns: b.changeColor(mouse_pos); b.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btns[0].checkForInput(mouse_pos): difficulty_selection()
                if btns[1].checkForInput(mouse_pos): options()
                if btns[2].checkForInput(mouse_pos): pygame.quit(); sys.exit()

        pygame.display.update()


if __name__ == "__main__":
    main_menu()