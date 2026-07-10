#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞机大战 - Airplane Shooter
A vertical scrolling shooter game using Tkinter.
Runs natively on macOS.
"""

import tkinter as tk
import math
import random
import os
import json
try:
    import soundfx
except ImportError:
    soundfx = None

# ─── Constants ───────────────────────────────────────────────

WIDTH = 800
HEIGHT = 650
HUD_HEIGHT = 40
PLAY_AREA_TOP = HUD_HEIGHT
PLAY_AREA_HEIGHT = HEIGHT - HUD_HEIGHT

# Colors
BG_COLOR = "#0a0e27"
HUD_BG = "#141838"
HUD_TEXT = "#ffffff"
PLAYER_COLOR = "#00d4ff"
PLAYER_HIT_COLOR = "#ff4444"
BULLET_COLOR = "#ffee44"
ENEMY_BASIC_COLOR = "#ff3344"
ENEMY_FAST_COLOR = "#ff8800"
ENEMY_TANK_COLOR = "#cc44ff"
ENEMY_BOSS_COLOR = "#ff0044"
POWERUP_COLORS = {"P": "#ff8800", "S": "#4488ff", "L": "#44ff88"}
STAR_COLOR = "#ffffff"
SHIELD_COLOR = "#44aaff"

# Game settings
PLAYER_SPEED = 8
BULLET_SPEED = 42
BASE_FIRE_DELAY = 250  # ms
MAX_POWER_LEVEL = 3
INITIAL_LIVES = 3
ENEMY_SPAWN_DELAY = 1200  # ms, decreases with difficulty
MIN_SPAWN_DELAY = 300
POWERUP_DROP_CHANCE = 0.12
DIFFICULTY_INTERVAL = 15000  # ms per difficulty increase
BOSS_INTERVAL = 15  # enemies between bosses


# ─── Game ────────────────────────────────────────────────────

class AirplaneGame:
    """Main game controller."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("飞机大战 - Airplane Shooter")
        self.root.resizable(False, False)

        # Center window on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - WIDTH) // 2
        y = (screen_h - HEIGHT) // 2
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=WIDTH, height=HEIGHT,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Load high score
        self.high_score = self._load_high_score()

        # Game state
        self.state = "menu"  # menu, playing, paused, game_over
        self.score = 0
        self.lives = INITIAL_LIVES
        self.power_level = 1
        self.shield_active = False
        self.shield_timer = 0
        self.difficulty = 1
        self.enemy_spawn_delay = ENEMY_SPAWN_DELAY
        self.enemies_since_boss = 0
        self.combo_count = 0
        self.combo_timer = 0

        # Entities
        self.player = None
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []
        self.stars = []
        self.explosions = []
        self.float_texts = []

        # Keyboard state
        self.keys_pressed = set()
        if soundfx: soundfx.init()

        # Timers
        self._fire_timer = 0
        self._spawn_timer = 0
        self._difficulty_timer = 0
        self._game_loop_id = None

        # HUD items (created once)
        self._hud_bg = None
        self._score_text = None
        self._lives_text = None
        self._high_score_text = None
        self._shield_indicator = None

        # Bind keys
        self._bind_keys()

        # Create HUD
        self._create_hud()

        # Show menu
        self._show_menu()

    # ── High Score ──────────────────────────────────────────

    def _load_high_score(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "highscore.dat")
            with open(path, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return 0

    def _save_high_score(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "highscore.dat")
            with open(path, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    # ── Keyboard ────────────────────────────────────────────

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self._on_key_down)
        self.root.bind("<KeyRelease>", self._on_key_up)
        # Handle focus
        self.canvas.focus_set()
        self.root.bind("<Button-1>", lambda e: self.canvas.focus_set())

    def _on_key_down(self, event):
        key = event.keysym
        self.keys_pressed.add(key)

        if self.state == "menu":
            if key == "space" or key == "Return":
                self._start_game()
        elif self.state == "game_over":
            if key == "space" or key == "Return":
                self._show_menu()
        elif self.state == "playing":
            if key == "p" or key == "P" or key == "space":
                self._pause()
        elif self.state == "paused":
            if key == "p" or key == "P" or key == "r" or key == "R":
                self._resume()



    def _on_key_up(self, event):
        key = event.keysym
        self.keys_pressed.discard(key)

    # ── HUD ─────────────────────────────────────────────────

    def _create_hud(self):
        self._hud_bg = self.canvas.create_rectangle(
            0, 0, WIDTH, HUD_HEIGHT,
            fill=HUD_BG, outline="", tags="hud"
        )
        # Separator line
        self.canvas.create_line(
            0, HUD_HEIGHT, WIDTH, HUD_HEIGHT,
            fill="#2a2e48", width=1, tags="hud"
        )
        self._score_text = self.canvas.create_text(
            20, HUD_HEIGHT // 2,
            text="SCORE: 0", fill=HUD_TEXT,
            font=("Courier", 14, "bold"), anchor="w", tags="hud"
        )
        self._high_score_text = self.canvas.create_text(
            WIDTH - 20, HUD_HEIGHT // 2,
            text=f"HIGH: {self.high_score}", fill="#888899",
            font=("Courier", 12, "bold"), anchor="e", tags="hud"
        )
        self._lives_text = self.canvas.create_text(
            WIDTH // 2, HUD_HEIGHT // 2,
            text="", fill=HUD_TEXT,
            font=("Courier", 14, "bold"), tags="hud"
        )
        self._shield_indicator = self.canvas.create_text(
            WIDTH // 2, HUD_HEIGHT - 5,
            text="", fill=SHIELD_COLOR,
            font=("Courier", 9, "bold"), tags="hud"
        )
        # Power level indicator
        self._power_text = self.canvas.create_text(
            20, HUD_HEIGHT - 5,
            text="", fill="#ffaa44",
            font=("Courier", 9, "bold"), anchor="w", tags="hud"
        )

    def _update_hud(self):
        self.canvas.itemconfig(self._score_text, text=f"SCORE: {self.score}")
        self.canvas.itemconfig(
            self._high_score_text,
            text=f"HIGH: {self.high_score}"
        )
        hearts = "♥" * self.lives
        self.canvas.itemconfig(self._lives_text, text=hearts)

        if self.shield_active:
            remaining = self.shield_timer // 1000
            self.canvas.itemconfig(
                self._shield_indicator,
                text=f"SHIELD {remaining}s"
            )
        else:
            self.canvas.itemconfig(self._shield_indicator, text="")

        pwr_text = "POWER: " + "█" * self.power_level + "░" * (
            MAX_POWER_LEVEL - self.power_level
        )
        self.canvas.itemconfig(self._power_text, text=pwr_text)

    # ── Menu / Game Over Screens ────────────────────────────

    def _clear_overlays(self):
        self.canvas.delete("overlay")

    def _show_menu(self):
        self._clear_overlays()
        self.state = "menu"
        self._create_stars()

        cx, cy = WIDTH // 2, HEIGHT // 3
        self.canvas.create_text(
            cx, cy - 40,
            text="✈ 飞机大战", fill=PLAYER_COLOR,
            font=("Helvetica", 36, "bold"),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 20,
            text="AIRPLANE SHOOTER", fill="#667799",
            font=("Courier", 14),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 70,
            text="PRESS SPACE TO START", fill=HUD_TEXT,
            font=("Courier", 16, "bold"),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 110,
            text="← → ↑ ↓ / WASD  Move    Auto-fire    Space/P  Pause",
            fill="#556688",
            font=("Courier", 10),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 150,
            text=f"HIGH SCORE: {self.high_score}",
            fill="#ffcc44",
            font=("Courier", 12, "bold"),
            tags="overlay"
        )

        # Start menu animation
        self._menu_animate()

    def _menu_animate(self):
        if self.state != "menu":
            return
        # Scroll stars
        self._update_stars()
        self.root.after(33, self._menu_animate)

    def _show_game_over(self):
        soundfx and soundfx.stop_music()
        self._clear_overlays()
        self.state = "game_over"

        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

        cx, cy = WIDTH // 2, HEIGHT // 3
        self.canvas.create_text(
            cx, cy - 40,
            text="GAME OVER", fill="#ff3344",
            font=("Helvetica", 32, "bold"),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 10,
            text=f"SCORE: {self.score}",
            fill=HUD_TEXT,
            font=("Courier", 18, "bold"),
            tags="overlay"
        )

        if self.score == self.high_score and self.score > 0:
            self.canvas.create_text(
                cx, cy + 50,
                text="★ NEW HIGH SCORE! ★",
                fill="#ffcc44",
                font=("Courier", 14, "bold"),
                tags="overlay"
            )

        self.canvas.create_text(
            cx, cy + 90,
            text=f"HIGH SCORE: {self.high_score}",
            fill="#888899",
            font=("Courier", 12, "bold"),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 140,
            text="PRESS SPACE TO CONTINUE",
            fill=HUD_TEXT,
            font=("Courier", 14, "bold"),
            tags="overlay"
        )

    # ── Start / Pause / Resume ──────────────────────────────

    def _start_game(self):
        self._clear_overlays()
        self.state = "playing"
        self.score = 0
        self.lives = INITIAL_LIVES
        self.power_level = 1
        self.shield_active = False
        self.shield_timer = 0
        self.difficulty = 1
        self.enemy_spawn_delay = ENEMY_SPAWN_DELAY
        self.enemies_since_boss = 0
        self.combo_count = 0
        self.combo_timer = 0

        # Clear entities
        self._clear_entities()

        # Create player
        self.player = {
            "x": WIDTH // 2,
            "y": HEIGHT - 60,
            "w": 30,
            "h": 36,
            "canvas_id": None,
            "invincible": 0,
            "hit_flash": 0,
        }
        self._draw_player()

        # Create stars
        self._create_stars()

        # Reset timers
        self._fire_timer = 0
        self._spawn_timer = 0
        self._difficulty_timer = 0

        # Update HUD
        self._update_hud()

        # Start game loop
        soundfx and soundfx.start_music()
        self._game_loop()

    def _pause(self):
        self.state = "paused"
        cx, cy = WIDTH // 2, HEIGHT // 2
        self.canvas.create_text(
            cx, cy - 10,
            text="PAUSED", fill=HUD_TEXT,
            font=("Helvetica", 24, "bold"),
            tags="overlay"
        )
        self.canvas.create_text(
            cx, cy + 25,
            text="Press P or R to resume",
            fill="#667788",
            font=("Courier", 12),
            tags="overlay"
        )

    def _resume(self):
        self._clear_overlays()
        self.keys_pressed.clear()
        self.state = "playing"
        self._game_loop()

    # ── Background Stars ────────────────────────────────────

    def _create_stars(self):
        self.stars = []
        for _ in range(80):
            self.stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(PLAY_AREA_TOP, HEIGHT),
                "speed": random.uniform(0.5, 2.5),
                "size": random.choice([1, 1, 1, 2, 2, 3]),
                "brightness": random.uniform(0.3, 1.0),
                "id": None,
            })
            cid = self.canvas.create_oval(
                self.stars[-1]["x"], self.stars[-1]["y"],
                self.stars[-1]["x"] + self.stars[-1]["size"],
                self.stars[-1]["y"] + self.stars[-1]["size"],
                fill=STAR_COLOR,
                stipple="gray50",
                tags="stars"
            )
            self.stars[-1]["id"] = cid

    def _update_stars(self):
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = PLAY_AREA_TOP
                star["x"] = random.randint(0, WIDTH)
            self.canvas.coords(
                star["id"],
                star["x"], star["y"],
                star["x"] + star["size"],
                star["y"] + star["size"]
            )

    # ── Player Drawing ──────────────────────────────────────

    def _draw_player(self):
        # Delete all previous player items (plane body + shield)
        self.canvas.delete("player")
        self.player["canvas_id"] = None

        x, y = self.player["x"], self.player["y"]
        level = self.power_level
        invincible = self.player["invincible"] > 0

        color = PLAYER_HIT_COLOR if self.player["hit_flash"] > 0 else PLAYER_COLOR
        if invincible and (self.player["invincible"] // 100) % 2 == 0:
            self.player["canvas_id"] = None
            return

        # Main body (fighter jet shape)
        body = [
            x, y - 18,                    # nose
            x + 10, y - 4,                # right wing mid
            x + 16, y + 2,                # right wingtip
            x + 8, y + 6,                 # right engine
            x + 8, y + 14,                # right tail
            x + 4, y + 14,                # right tail inner
            x + 4, y + 6,                 # right body
            x - 4, y + 6,                 # left body
            x - 4, y + 14,                # left tail inner
            x - 8, y + 14,                # left tail
            x - 8, y + 6,                 # left engine
            x - 16, y + 2,                # left wingtip
            x - 10, y - 4,                # left wing mid
        ]

        # Level 2+: extra wing details
        if level >= 2:
            extra = [x + 12, y + 8, x + 20, y + 14, x + 12, y + 16]
            extra2 = [x - 12, y + 8, x - 20, y + 14, x - 12, y + 16]
            body.extend(extra)
            body.extend(extra2)

        # Level 3: extra tail wings
        if level >= 3:
            body.extend([x + 10, y + 10, x + 24, y + 4, x + 10, y + 14])
            body.extend([x - 10, y + 10, x - 24, y + 4, x - 10, y + 14])

        cid = self.canvas.create_polygon(
            body, fill=color, outline="#ffffff",
            width=1, tags="player"
        )
        self.player["canvas_id"] = cid

        # Shield effect
        if self.shield_active:
            self.canvas.create_oval(
                x - 25, y - 25, x + 25, y + 25,
                outline=SHIELD_COLOR, width=2,
                dash=(4, 4), tags=("player", "shield")
            )

    # ── Bullets ─────────────────────────────────────────────

    def _fire_bullets(self):
        if not self.player or self.lives <= 0:
            return
        soundfx and soundfx.play("shoot")

        x, y = self.player["x"], self.player["y"]
        speed = BULLET_SPEED

        if self.power_level == 1:
            self._create_bullet(x, y - 18, 0, -speed)
        elif self.power_level == 2:
            self._create_bullet(x - 6, y - 14, 0, -speed)
            self._create_bullet(x + 6, y - 14, 0, -speed)
        elif self.power_level >= 3:
            self._create_bullet(x, y - 18, 0, -speed)
            self._create_bullet(x - 10, y - 12, -0.5, -speed * 0.9)
            self._create_bullet(x + 10, y - 12, 0.5, -speed * 0.9)

    def _create_bullet(self, x, y, vx, vy):
        cid = self.canvas.create_rectangle(
            x - 2, y - 6, x + 2, y + 6,
            fill=BULLET_COLOR, outline="", tags="bullet"
        )
        self.bullets.append({
            "x": x, "y": y, "vx": vx, "vy": vy,
            "w": 4, "h": 12,
            "id": cid,
        })

    def _create_enemy_bullet(self, x, y, vx, vy):
        cid = self.canvas.create_oval(
            x - 3, y - 3, x + 3, y + 3,
            fill="#ff6644", outline="", tags="enemy_bullet"
        )
        self.enemy_bullets.append({
            "x": x, "y": y, "vx": vx, "vy": vy,
            "w": 6, "h": 6,
            "id": cid,
        })

    # ── Enemies ─────────────────────────────────────────────

    def _spawn_enemy(self):
        if self.enemies_since_boss >= BOSS_INTERVAL:
            self._spawn_boss()
            self.enemies_since_boss = 0
            return

        self.enemies_since_boss += 1
        difficulty = self.difficulty

        # Choose type
        roll = random.random()
        if roll < 0.5 or difficulty < 2:
            etype = "basic"
        elif roll < 0.8:
            etype = "fast"
        else:
            etype = "tank"

        x = random.randint(40, WIDTH - 40)
        speed = 1.5 + difficulty * 0.3 + random.uniform(-0.3, 0.3)

        if etype == "basic":
            hp = 1
            points = 100
            size = 16
            color = ENEMY_BASIC_COLOR
            shape = "triangle"
        elif etype == "fast":
            hp = 1
            points = 150
            speed *= 1.4
            size = 14
            color = ENEMY_FAST_COLOR
            shape = "diamond"
        else:
            hp = 2
            points = 250
            size = 20
            color = ENEMY_TANK_COLOR
            shape = "hexagon"

        self._create_enemy(x, -size, speed, hp, points, size, color, shape)

    def _spawn_boss(self):
        x = WIDTH // 2
        hp = 5 + self.difficulty * 2
        points = 1000 + self.difficulty * 200
        size = 30
        speed = 1.0 + self.difficulty * 0.2
        self._create_enemy(x, -size, speed, hp, points, size, ENEMY_BOSS_COLOR, "boss")

    def _create_enemy(self, x, y, speed, hp, points, size, color, etype):
        # Draw based on type
        s = size
        if etype == "triangle":
            # Basic enemy - small fighter plane
            points_list = [
                x, y - s,              # nose
                x + s*0.7, y - s*0.2,  # right wing tip
                x + s*0.6, y + s*0.3,  # right body
                x + s*0.3, y + s*0.7,  # right tail
                x - s*0.3, y + s*0.7,  # left tail
                x - s*0.6, y + s*0.3,  # left body
                x - s*0.7, y - s*0.2,  # left wing tip
            ]
        elif etype == "diamond":
            # Fast enemy - sleek delta wing plane
            points_list = [
                x, y - s * 1.0,              # sharp nose
                x + s * 0.3, y - s * 0.3,    # right inner wing
                x + s * 0.7, y + s * 0.0,    # right delta wing
                x + s * 0.5, y + s * 0.2,    # right body
                x + s * 0.3, y + s * 0.7,    # right tail
                x + s * 0.1, y + s * 0.9,    # right tail cone
                x - s * 0.1, y + s * 0.9,    # left tail cone
                x - s * 0.3, y + s * 0.7,    # left tail
                x - s * 0.5, y + s * 0.2,    # left body
                x - s * 0.7, y + s * 0.0,    # left delta wing
                x - s * 0.3, y - s * 0.3,    # left inner wing
            ]
        elif etype == "hexagon":
            # Tank enemy - heavy bomber
            points_list = [
                x, y - s*0.7,          # nose
                x + s*0.8, y - s*0.1,  # right wing
                x + s, y + s*0.2,      # right wing tip
                x + s*0.7, y + s*0.4,  # right body
                x + s*0.5, y + s,      # right tail
                x - s*0.5, y + s,      # left tail
                x - s*0.7, y + s*0.4,  # left body
                x - s, y + s*0.2,      # left wing tip
                x - s*0.8, y - s*0.1,  # left wing
            ]
        elif etype == "boss":
            # Boss - large octagonal star
            pts = []
            for i in range(8):
                angle = math.radians(45 * i)
                r = size if i % 2 == 0 else size * 0.6
                pts.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
            points_list = pts
        else:
            points_list = [x, y - size, x + size, y + size, x - size, y + size]

        # Inner glow for boss
        if etype == "boss":
            inner_pts = []
            for i in range(8):
                angle = math.radians(45 * i)
                r = (size * 0.5) if i % 2 == 0 else (size * 0.35)
                inner_pts.extend([
                    x + r * math.cos(angle),
                    y + r * math.sin(angle)
                ])

        cid = self.canvas.create_polygon(
            points_list, fill=color, outline="#cccccc",
            width=1, tags="enemy"
        )

        inner_cid = None
        if etype == "boss":
            inner_cid = self.canvas.create_polygon(
                inner_pts, fill="#cccccc", outline="",
                tags="enemy"
            )

        enemy = {
            "x": x, "y": y, "vx": 0, "vy": speed,
            "hp": hp, "max_hp": hp,
            "points": points,
            "size": size,
            "type": etype,
            "color": color,
            "id": cid,
            "inner_id": inner_cid,
            "timer": 0,
            "flash": 0,
        }

        # Fast enemies weave
        if etype == "fast":
            enemy["vx"] = random.choice([-0.8, 0.8]) * speed
            enemy["timer_offset"] = random.uniform(0, math.pi * 2)

        # Boss moves horizontally
        if etype == "boss":
            enemy["vx"] = 1.5
            enemy["vy"] = speed * 0.3

        self.enemies.append(enemy)

    # ── Power-ups ──────────────────────────────────────────

    def _spawn_powerup(self, x, y):
        if random.random() > POWERUP_DROP_CHANCE:
            return

        ptype = random.choice(["P", "S", "L"])
        color = POWERUP_COLORS[ptype]

        # Bright outer glow ring
        glow = self.canvas.create_oval(
            x - 18, y - 18, x + 18, y + 18,
            outline=color, width=4, dash=(6, 3),
            tags="powerup"
        )
        # Star shape
        pts = []
        for i in range(8):
            angle = math.radians(45 * i - 22.5)
            r = 14 if i % 2 == 0 else 6
            pts.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
        star = self.canvas.create_polygon(
            pts, fill=color, outline="#ffffff",
            width=2, tags="powerup"
        )
        # Label
        label = self.canvas.create_text(
            x, y, text=ptype,
            fill="#ffffff", font=("Courier", 14, "bold"),
            tags="powerup"
        )

        self.powerups.append({
            "x": x, "y": y, "type": ptype,
            "vy": 1.5,
            "id": star, "label_id": label, "glow_id": glow,
            "timer": 0,
        })

    # ── Explosions / Effects ────────────────────────────────

    def _create_explosion(self, x, y, color, size=20):
        particles = []
        for _ in range(random.randint(8, 16)):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            psize = random.randint(2, 5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            cid = self.canvas.create_oval(
                x - psize // 2, y - psize // 2,
                x + psize // 2, y + psize // 2,
                fill=color, outline="", tags="explosion"
            )
            particles.append({
                "x": x, "y": y, "vx": dx, "vy": dy,
                "life": 20, "max_life": 20,
                "id": cid, "size": psize,
            })
        self.explosions.append(particles)

    def _create_float_text(self, x, y, text, color="#ffffff"):
        cid = self.canvas.create_text(
            x, y, text=str(text), fill=color,
            font=("Courier", 10, "bold"), tags="float_text"
        )
        self.float_texts.append({
            "x": x, "y": y, "id": cid,
            "life": 30, "max_life": 30, "text": str(text),
        })

    # ── Entity Clearing ─────────────────────────────────────

    def _clear_entities(self):
        self.canvas.delete("player")
        self.canvas.delete("bullet")
        self.canvas.delete("enemy")
        self.canvas.delete("enemy_bullet")
        self.canvas.delete("powerup")
        self.canvas.delete("explosion")
        self.canvas.delete("float_text")
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []
        self.explosions = []
        self.float_texts = []

    # ── Collision Detection ─────────────────────────────────

    def _check_collisions(self):
        now = self._game_time

        # Bullets vs Enemies
        for b in self.bullets[:]:
            if b is None:
                continue
            bx, by = b["x"], b["y"]
            for e in self.enemies[:]:
                if e is None or e["hp"] <= 0:
                    continue
                ex, ey = e["x"], e["y"]
                es = e["size"]
                if abs(bx - ex) < es + 4 and abs(by - ey) < es + 4:
                    # Hit!
                    e["hp"] -= 1
                    e["flash"] = 3

                    # Remove bullet
                    self._remove_bullet(b)

                    if e["hp"] <= 0:
                        # Score
                        self.score += e["points"]

                        # Combo
                        if self.combo_timer > 0:
                            self.combo_count += 1
                        else:
                            self.combo_count = 1
                        self.combo_timer = 3000  # ms

                        # Combo bonus
                        combo_bonus = min(self.combo_count // 3, 10)
                        bonus_text = ""
                        if combo_bonus >= 1:
                            bonus = e["points"] * combo_bonus // 5
                            self.score += bonus
                            bonus_text = f" +{bonus}x{combo_bonus}"

                        # Effects
                        soundfx and soundfx.play("explosion")
                        self._create_explosion(ex, ey, e["color"], e["size"])
                        self._create_float_text(
                            ex, ey - 10,
                            f"+{e['points']}{bonus_text}",
                            e["color"]
                        )

                        # Power-up drop
                        self._spawn_powerup(ex, ey)

                        # Remove enemy
                        self._remove_enemy(e)

                    break

        # Enemy bullets vs Player
        if self.player and self.player["invincible"] <= 0:
            px, py = self.player["x"], self.player["y"]
            for b in self.enemy_bullets[:]:
                bx, by = b["x"], b["y"]
                if abs(bx - px) < 20 and abs(by - py) < 20:
                    self._remove_bullet(b, enemy=True)
                    self._player_hit()
                    break

        # Enemies vs Player
        if self.player and self.player["invincible"] <= 0:
            px, py = self.player["x"], self.player["y"]
            for e in self.enemies[:]:
                if e is None or e["hp"] <= 0:
                    continue
                ex, ey = e["x"], e["y"]
                es = e["size"]
                if abs(px - ex) < es + 12 and abs(py - ey) < es + 12:
                    # Destroy enemy too
                    self._create_explosion(ex, ey, e["color"], e["size"])
                    self._remove_enemy(e)
                    self._player_hit()
                    break

        # Power-ups vs Player
        if self.player:
            px, py = self.player["x"], self.player["y"]
            for p in self.powerups[:]:
                if abs(p["x"] - px) < 20 and abs(p["y"] - py) < 20:
                    self._collect_powerup(p)
                    break

    def _player_hit(self):
        soundfx and soundfx.play("hit")
        if self.shield_active:
            self.shield_active = False
            self.shield_timer = 0
            self.player["invincible"] = 1500
            self._create_explosion(
                self.player["x"], self.player["y"],
                SHIELD_COLOR, 25
            )
            return

        self.lives -= 1
        self.player["invincible"] = 2000
        self.player["hit_flash"] = 5
        self._create_explosion(
            self.player["x"], self.player["y"],
            PLAYER_COLOR, 25
        )

        # Lose power on hit
        if self.power_level > 1:
            self.power_level -= 1

        self._update_hud()

        if self.lives <= 0:
            self.state = "game_over_prep"

    def _collect_powerup(self, p):
        ptype = p["type"]
        if ptype == "P":
            self.power_level = min(self.power_level + 1, MAX_POWER_LEVEL)
            self._create_float_text(p["x"], p["y"] - 5, "POWER UP!", "#ffaa44")
        elif ptype == "S":
            self.shield_active = True
            self.shield_timer = 8000
            self._create_float_text(p["x"], p["y"] - 5, "SHIELD!", SHIELD_COLOR)
        elif ptype == "L":
            self.lives = min(self.lives + 1, 5)
            self._create_float_text(p["x"], p["y"] - 5, "1UP!", "#44ff88")

        soundfx and soundfx.play("powerup")
        self._remove_powerup(p)
        self._update_hud()

    # ── Entity Removal ──────────────────────────────────────

    def _remove_bullet(self, b, enemy=False):
        if b is None:
            return
        lst = self.enemy_bullets if enemy else self.bullets
        if b in lst:
            lst.remove(b)
        if b["id"]:
            try:
                self.canvas.delete(b["id"])
            except tk.TclError:
                pass

    def _remove_enemy(self, e):
        if e is None or e not in self.enemies:
            return
        self.enemies.remove(e)
        if e["id"]:
            try:
                self.canvas.delete(e["id"])
            except tk.TclError:
                pass
        if e.get("inner_id"):
            try:
                self.canvas.delete(e["inner_id"])
            except tk.TclError:
                pass

    def _remove_powerup(self, p):
        if p is None or p not in self.powerups:
            return
        self.powerups.remove(p)
        for key in ["id", "label_id", "glow_id"]:
            if p.get(key):
                try:
                    self.canvas.delete(p[key])
                except tk.TclError:
                    pass

    # ── Update Logic ────────────────────────────────────────

    def _update(self):
        now = self._game_time

        # ── Stars ──
        self._update_stars()

        # ── Difficulty ──
        self._difficulty_timer += 33  # ~30 FPS
        if self._difficulty_timer >= DIFFICULTY_INTERVAL:
            self._difficulty_timer = 0
            self.difficulty += 1
            self.enemy_spawn_delay = max(
                MIN_SPAWN_DELAY,
                ENEMY_SPAWN_DELAY - (self.difficulty - 1) * 80
            )

        # ── Spawn enemies ──
        self._spawn_timer += 33
        if self._spawn_timer >= self.enemy_spawn_delay:
            self._spawn_timer = 0
            self._spawn_enemy()

        # ── Player movement ──
        if self.player and self.lives > 0:
            dx = 0
            dy = 0
            if "Left" in self.keys_pressed or "a" in self.keys_pressed:
                dx = -PLAYER_SPEED
            if "Right" in self.keys_pressed or "d" in self.keys_pressed:
                dx = PLAYER_SPEED
            if "Up" in self.keys_pressed or "w" in self.keys_pressed:
                dy = -PLAYER_SPEED
            if "Down" in self.keys_pressed or "s" in self.keys_pressed:
                dy = PLAYER_SPEED

            self.player["x"] = max(20, min(WIDTH - 20, self.player["x"] + dx))
            self.player["y"] = max(
                PLAY_AREA_TOP + 10,
                min(HEIGHT - 20, self.player["y"] + dy)
            )

            # Invincibility timer
            if self.player["invincible"] > 0:
                self.player["invincible"] -= 33
            if self.player["hit_flash"] > 0:
                self.player["hit_flash"] -= 1

            # Auto-fire (always on)
            self._fire_timer += 33
            if self._fire_timer >= BASE_FIRE_DELAY // self.power_level:
                self._fire_timer = 0
                self._fire_bullets()

            # Redraw player
            self._draw_player()

        # ── Shield timer ──
        if self.shield_active:
            self.shield_timer -= 33
            if self.shield_timer <= 0:
                self.shield_active = False
                self.shield_timer = 0

        # ── Update bullets ──
        for b in self.bullets[:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["y"] < PLAY_AREA_TOP - 20 or b["y"] > HEIGHT + 20:
                self._remove_bullet(b)
                continue
            self.canvas.coords(
                b["id"],
                b["x"] - 2, b["y"] - 6,
                b["x"] + 2, b["y"] + 6
            )

        # ── Update enemy bullets ──
        for b in self.enemy_bullets[:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["y"] > HEIGHT + 20 or b["y"] < PLAY_AREA_TOP - 20:
                self._remove_bullet(b, enemy=True)
                continue
            self.canvas.coords(
                b["id"],
                b["x"] - 3, b["y"] - 3,
                b["x"] + 3, b["y"] + 3
            )

        # ── Update enemies ──
        for e in self.enemies[:]:
            # Movement
            if e["type"] == "fast":
                e["timer"] += 0.05
                e["x"] += e["vx"] + math.sin(e["timer"] + e.get("timer_offset", 0)) * 1.5
                e["y"] += e["vy"]
            elif e["type"] == "boss":
                e["x"] += e["vx"]
                e["y"] += e["vy"]
                if e["x"] < 40 or e["x"] > WIDTH - 40:
                    e["vx"] *= -1
            else:
                e["y"] += e["vy"]


            # Flash
            if e["flash"] > 0:
                e["flash"] -= 1

            # Off screen
            if e["y"] > HEIGHT + 50:
                self._remove_enemy(e)
                continue

            # Boss shoots
            if e["type"] == "boss" and e["timer"] % 60 == 0:
                self._create_enemy_bullet(
                    e["x"], e["y"] + e["size"],
                    0, 12
                )
                # Spread shot 2x speed
                self._create_enemy_bullet(
                    e["x"], e["y"] + e["size"],
                    -0.8, 11.2
                )
                self._create_enemy_bullet(
                    e["x"], e["y"] + e["size"],
                    0.8, 11.2
                )
            e["timer"] += 1

            # Redraw enemy
            self._redraw_enemy(e)

        # ── Update power-ups ──
        for p in self.powerups[:]:
            p["y"] += p["vy"]
            if p["y"] > HEIGHT + 20:
                self._remove_powerup(p)
                continue

            # Rotating star + pulsing glow
            p["timer"] += 0.1
            pulse = 14 + math.sin(self._game_time * 0.006) * 3

            # Redraw star with rotation
            pts = []
            for i in range(8):
                angle = math.radians(45 * i - 22.5 + p["timer"] * 30)
                r = pulse if i % 2 == 0 else pulse * 0.4
                pts.extend([p["x"] + r * math.cos(angle), p["y"] + r * math.sin(angle)])
            self.canvas.coords(p["id"], *pts)

            # Pulsing glow ring
            glow_r = 20 + math.sin(self._game_time * 0.004) * 3
            self.canvas.coords(
                p["glow_id"],
                p["x"] - glow_r, p["y"] - glow_r,
                p["x"] + glow_r, p["y"] + glow_r
            )
            self.canvas.coords(p["label_id"], p["x"], p["y"])

        # ── Update explosions ──
        for particles in self.explosions[:]:
            alive = False
            for p in particles:
                p["life"] -= 1
                if p["life"] <= 0:
                    continue
                alive = True
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                fade = p["life"] / p["max_life"]
                size = max(1, int(p["size"] * fade))
                self.canvas.coords(
                    p["id"],
                    p["x"] - size, p["y"] - size,
                    p["x"] + size, p["y"] + size
                )
            if not alive:
                for p in particles:
                    try:
                        self.canvas.delete(p["id"])
                    except tk.TclError:
                        pass
                self.explosions.remove(particles)

        # ── Update float texts ──
        for ft in self.float_texts[:]:
            ft["life"] -= 1
            ft["y"] -= 1
            if ft["life"] <= 0:
                try:
                    self.canvas.delete(ft["id"])
                except tk.TclError:
                    pass
                self.float_texts.remove(ft)
                continue
            self.canvas.coords(ft["id"], ft["x"], ft["y"])
            fade = ft["life"] / ft["max_life"]
            color = ft["id"] and self.canvas.itemcget(ft["id"], "fill") or "#ffffff"
            # Just move it, color fade handled by deletion

        # ── Combo timer ──
        if self.combo_timer > 0:
            self.combo_timer -= 33

        # ── Collision ──
        self._check_collisions()

        # ── HUD ──
        self._update_hud()

    def _redraw_enemy(self, e):
        x, y = e["x"], e["y"]
        size = e["size"]
        etype = e["type"]

        color = e["color"]
        if e["flash"] > 0:
            color = "#ffffff"

        s = size
        if etype == "triangle":
            # Small fighter plane - swept wings, pointed nose, double tail fins
            pts = [
                x, y - s * 1.0,              # nose tip
                x + s * 0.6, y - s * 0.2,    # right wing tip
                x + s * 0.4, y + s * 0.2,    # right body mid
                x + s * 0.25, y + s * 0.7,   # right tail wing tip
                x + s * 0.1, y + s * 0.8,    # right tail
                x - s * 0.1, y + s * 0.8,    # left tail
                x - s * 0.25, y + s * 0.7,   # left tail wing tip
                x - s * 0.4, y + s * 0.2,    # left body mid
                x - s * 0.6, y - s * 0.2,    # left wing tip
            ]
        elif etype == "diamond":
            # Fast enemy - needle-like dart fighter
            pts = [
                x, y - s * 1.3,              # sharp nose
                x + s * 0.15, y - s * 0.4,   # right nose
                x + s * 0.5, y - s * 0.1,    # right wing
                x + s * 0.7, y + s * 0.2,    # right wing outer
                x + s * 0.45, y + s * 0.4,   # right body
                x + s * 0.25, y + s * 0.8,   # right tail
                x + s * 0.08, y + s * 0.95,  # right tail cone
                x - s * 0.08, y + s * 0.95,  # left tail cone
                x - s * 0.25, y + s * 0.8,   # left tail
                x - s * 0.45, y + s * 0.4,   # left body
                x - s * 0.7, y + s * 0.2,    # left wing outer
                x - s * 0.5, y - s * 0.1,    # left wing
                x - s * 0.15, y - s * 0.4,   # left nose
            ]
        elif etype == "hexagon":
            # Tank enemy - heavy bomber with distinct wings
            pts = [
                x, y - s * 1.0,              # nose
                x + s * 0.15, y - s * 0.4,   # right cockpit
                x + s * 0.7, y - s * 0.15,   # right wing inner
                x + s * 1.3, y + s * 0.2,    # right wing tip
                x + s * 1.0, y + s * 0.35,   # right wing back
                x + s * 0.6, y + s * 0.5,    # right body
                x + s * 0.5, y + s * 1.0,    # right tail fin
                x + s * 0.15, y + s * 1.2,   # right tail
                x - s * 0.15, y + s * 1.2,   # left tail
                x - s * 0.5, y + s * 1.0,    # left tail fin
                x - s * 0.6, y + s * 0.5,    # left body
                x - s * 1.0, y + s * 0.35,   # left wing back
                x - s * 1.3, y + s * 0.2,    # left wing tip
                x - s * 0.7, y - s * 0.15,   # left wing inner
                x - s * 0.15, y - s * 0.4,   # left cockpit
            ]
        elif etype == "boss":
            pts = []
            for i in range(8):
                angle = math.radians(45 * i)
                r = size if i % 2 == 0 else size * 0.6
                pts.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
        else:
            pts = [x, y - size, x + size, y + size, x - size, y + size]

        try:
            self.canvas.coords(e["id"], *pts)
            self.canvas.itemconfig(e["id"], fill=color)
        except tk.TclError:
            pass

        # Boss - large command ship with airplane shape
        if etype == "boss":
            # Swept wings, canards, twin tail fins
            boss_pts = [
                x, y - s * 1.2,              # nose
                x + s * 0.3, y - s * 0.7,    # right canard
                x + s * 0.6, y - s * 0.5,    # right wing inner
                x + s * 1.3, y + s * 0.0,    # right wing tip
                x + s * 1.0, y + s * 0.25,   # right wing back
                x + s * 0.7, y + s * 0.5,    # right body
                x + s * 0.6, y + s * 0.7,    # right outer engine
                x + s * 0.3, y + s * 0.8,    # right engine
                x + s * 0.5, y + s * 1.3,    # right tail outer
                x + s * 0.15, y + s * 1.4,   # right tail
                x + s * 0.05, y + s * 1.3,   # right tail inner
                x - s * 0.05, y + s * 1.3,   # left tail inner
                x - s * 0.15, y + s * 1.4,   # left tail
                x - s * 0.5, y + s * 1.3,    # left tail outer
                x - s * 0.3, y + s * 0.8,    # left engine
                x - s * 0.6, y + s * 0.7,    # left outer engine
                x - s * 0.7, y + s * 0.5,    # left body
                x - s * 1.0, y + s * 0.25,   # left wing back
                x - s * 1.3, y + s * 0.0,    # left wing tip
                x - s * 0.6, y - s * 0.5,    # left wing inner
                x - s * 0.3, y - s * 0.7,    # left canard
            ]
            try:
                self.canvas.coords(e["id"], *boss_pts)
                self.canvas.itemconfig(e["id"], fill=color)
            except tk.TclError:
                pass

        # Remove old inner star

        # HP bar for tank/boss
        if e["max_hp"] > 1 and e["hp"] > 0:
            bar_w = size * 2
            bar_h = 4
            fill_pct = e["hp"] / e["max_hp"]
            # Just use a simple approach: we'll draw a small rectangle behind
            # Since we can't easily update canvas rectangles, skip for performance

    # ── Game Loop ───────────────────────────────────────────

    def _game_loop(self):
        if self.state != "playing":
            return

        self._game_time = getattr(self, "_game_time", 0) + 33
        self._update()
        self._game_loop_id = self.root.after(33, self._game_loop)

        # Check if player died (game_over_prep state)
        if self.state == "game_over_prep":
            # Wait a moment then show game over screen
            self.root.after(500, self._show_game_over)
            return

    def run(self):
        self.root.mainloop()


# ─── Entry Point ─────────────────────────────────────────────

if __name__ == "__main__":
    game = AirplaneGame()
    game.run()
