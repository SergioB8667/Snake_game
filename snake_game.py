import turtle
import time
import random
import math
import json
import os

# ==================== CONFIGURATION ====================
delay = 0.08
score = 0
segments = []
game_running = False
start_pressed = False
paused = False
game_mode = "standard"
ai_difficulty = "medium"
return_to_menu = False

# 1v1 mode variables
ai_segments = []
ai_head = None
ai_head_vis = None
ai_eye = None
ai_score = 0
ai_color = 'blue'
ai_direction = "right"
match_time = 100
match_start_time = 0
poison_interval = 20
last_poison_time = 0
poison_items = []

# Powerup system
powerups = []
double_score_active = False
double_score_end_time = 0
immunity_active = False
immunity_end_time = 0
shield_stacks = 0
ai_shield_stacks = 0

# Damage text animations
damage_texts = []

SCORES_FILE = "snake_highscores.json"

PLAY_W = 400
PLAY_H = 400
GRID_CELLS = 24
GRID = PLAY_W / GRID_CELLS
PLAY_CENTER_Y = 80

START_X = -PLAY_W / 2
START_Y = PLAY_CENTER_Y - PLAY_H / 2

NL = chr(10)

# Futuristic neon color palette
COLOR_CHOICES = {
    'cyan': ('#00d4ff', '#00ffff'),
    'magenta': ('#ff00ff', '#ff66ff'),
    'lime': ('#00ff00', '#66ff66'),
    'orange': ('#ff6600', '#ff9933'),
    'pink': ('#ff0099', '#ff66cc'),
    'purple': ('#9900ff', '#cc66ff'),
    'yellow': ('#ffff00', '#ffff66'),
    'red': ('#ff0033', '#ff6666'),
    'blue': ('#0066ff', '#6699ff'),
    'green': ('#00cc66', '#66ff99'),
    'white': ('#ffffff', '#cccccc'),
}

COLOR_HEAD_RGB = {
    'cyan': (0, 212, 255),
    'magenta': (255, 0, 255),
    'lime': (0, 255, 0),
    'orange': (255, 102, 0),
    'pink': (255, 0, 153),
    'purple': (153, 0, 255),
    'yellow': (255, 255, 0),
    'red': (255, 0, 51),
    'blue': (0, 102, 255),
    'green': (0, 204, 102),
    'white': (255, 255, 255),
}

body_color = 'cyan'
body_shade, head_color = COLOR_CHOICES[body_color]

# Sound effects using system beep (cross-platform fallback)
def play_sound(sound_type):
    """Play sound effects - uses system sounds"""
    try:
        if sound_type == "eat":
            print("\a", end="", flush=True)
        elif sound_type == "powerup":
            for _ in range(2):
                print("\a", end="", flush=True)
        elif sound_type == "damage":
            print("\a", end="", flush=True)
        elif sound_type == "death":
            for _ in range(3):
                print("\a", end="", flush=True)
                time.sleep(0.1)
    except:
        pass

def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))

def rgb_to_hex(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(clamp(r), clamp(g), clamp(b))

def gradient_color_for_index(head_rgb, index, step=8):
    factor = 1 - (index * 0.04)
    factor = max(0.3, factor)
    r = clamp(head_rgb[0] * factor)
    g = clamp(head_rgb[1] * factor)
    b = clamp(head_rgb[2] * factor)
    return rgb_to_hex(r, g, b)

def cell_center(col, row):
    x = START_X + (col + 0.5) * GRID
    y = START_Y + (row + 0.5) * GRID
    return x, y

def pos_to_cell(x, y):
    col = int(round((x - START_X - GRID / 2) / GRID))
    row = int(round((y - START_Y - GRID / 2) / GRID))
    return col, row

# ==================== HIGH SCORES ====================
def load_high_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_high_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f, indent=2)

def add_high_score(name, score_val):
    scores = load_high_scores()
    scores.append({"name": name, "score": score_val})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:10]
    save_high_scores(scores)
    return scores

def get_player_name():
    msg = "Your score: " + str(score) + NL + "Enter your name for the leaderboard:"
    name = turtle.textinput("Game Over!", msg)
    if name is None or name.strip() == "":
        name = "Anonymous"
    return name.strip()[:15]

# ==================== SCREEN SETUP ====================
wn = turtle.Screen()
wn.title("NEON SNAKE // FUTURISTIC EDITION")
wn.bgcolor("#0a0a1a")
wn.setup(width=700, height=800)
wn.tracer(0)

def register_arch():
    points = []
    half = 10
    points.append((-half, -half))
    points.append((half, -half))
    points.append((half, 0))
    steps = 24
    for i in range(steps + 1):
        angle = math.radians(0 + 180 * i / steps)
        x = half * math.cos(angle)
        y = half * math.sin(angle)
        points.append((x, y))
    points.append((-half, 0))
    points.append((-half, -half))
    turtle.register_shape("arch", tuple(points))

register_arch()

# ==================== DRAW FUTURISTIC BORDER & GRID ====================
def draw_neon_border():
    border = turtle.Turtle()
    border.hideturtle()
    border.speed(0)
    border.penup()
    
    # Outer glow effect
    for offset, color, width in [(4, "#001133", 6), (2, "#003366", 4), (0, "#00ffff", 2)]:
        border.color(color)
        border.pensize(width)
        border.goto(START_X - offset, START_Y - offset)
        border.pendown()
        for _ in range(2):
            border.forward(PLAY_W + offset * 2)
            border.left(90)
            border.forward(PLAY_H + offset * 2)
            border.left(90)
        border.penup()
    
    # Corner accents
    corners = [
        (START_X, START_Y),
        (START_X + PLAY_W, START_Y),
        (START_X + PLAY_W, START_Y + PLAY_H),
        (START_X, START_Y + PLAY_H)
    ]
    border.color("#ff00ff")
    border.pensize(3)
    for cx, cy in corners:
        border.goto(cx, cy)
        border.dot(12, "#ff00ff")

draw_neon_border()

# Subtle grid with glow effect
grid_drawer = turtle.Turtle()
grid_drawer.hideturtle()
grid_drawer.speed(0)
grid_drawer.color("#1a1a3a")
grid_drawer.pensize(1)
grid_drawer.penup()
for i in range(1, GRID_CELLS):
    x = START_X + i * GRID
    grid_drawer.goto(x, START_Y)
    grid_drawer.pendown()
    grid_drawer.goto(x, START_Y + PLAY_H)
    grid_drawer.penup()
for i in range(1, GRID_CELLS):
    y = START_Y + i * GRID
    grid_drawer.goto(START_X, y)
    grid_drawer.pendown()
    grid_drawer.goto(START_X + PLAY_W, y)
    grid_drawer.penup()

# ==================== PLAYER SNAKE ====================
head = turtle.Turtle()
head.hideturtle()
head.speed(0)
head.penup()
head.direction = "stop"

head_vis = turtle.Turtle()
head_vis.hideturtle()
head_vis.speed(0)
head_vis.penup()
head_vis.shape("arch")
scale = GRID / 20
head_vis.shapesize(scale, scale)
head_vis.color(body_shade)

eye = turtle.Turtle()
eye.hideturtle()
eye.speed(0)
eye.penup()
eye.shape("circle")
eye.shapesize(0.18, 0.18)
eye.color("#ffffff")

# Glow effect for head
head_glow = turtle.Turtle()
head_glow.hideturtle()
head_glow.speed(0)
head_glow.penup()
head_glow.shape("circle")
head_glow.shapesize(1.2, 1.2)

# ==================== SCORE & INFO DISPLAYS ====================
score_display = turtle.Turtle()
score_display.hideturtle()
score_display.speed(0)
score_display.color("#00ffff")
score_display.penup()
score_display.goto(0, PLAY_CENTER_Y + PLAY_H / 2 + 30)

timer_display = turtle.Turtle()
timer_display.hideturtle()
timer_display.speed(0)
timer_display.color("#ffff00")
timer_display.penup()
timer_display.goto(0, PLAY_CENTER_Y + PLAY_H / 2 + 60)

pause_display = turtle.Turtle()
pause_display.hideturtle()
pause_display.speed(0)
pause_display.color("#ff00ff")
pause_display.penup()
pause_display.goto(0, PLAY_CENTER_Y)

# Powerup status display
powerup_display = turtle.Turtle()
powerup_display.hideturtle()
powerup_display.speed(0)
powerup_display.color("#00ff00")
powerup_display.penup()
powerup_display.goto(-PLAY_W / 2 - 80, PLAY_CENTER_Y + 100)

def update_score():
    score_display.clear()
    if game_mode == "1v1":
        shield_text = " [S:" + str(shield_stacks) + "]" if shield_stacks > 0 else ""
        ai_shield_text = " [S:" + str(ai_shield_stacks) + "]" if ai_shield_stacks > 0 else ""
        score_display.write("YOU: " + str(score) + shield_text + "  |  AI: " + str(ai_score) + ai_shield_text,
                           align="center", font=("Courier", 18, "bold"))
    else:
        score_display.write("SCORE: " + str(score), align="center", font=("Courier", 22, "bold"))

def update_timer():
    if game_mode == "1v1":
        elapsed = time.time() - match_start_time
        remaining = max(0, match_time - int(elapsed))
        timer_display.clear()
        color = "#ff0000" if remaining <= 10 else "#ffff00"
        timer_display.color(color)
        timer_display.write("TIME: " + str(remaining) + "s", align="center", font=("Courier", 16, "bold"))

def update_powerup_display():
    powerup_display.clear()
    text = ""
    current_time = time.time()
    
    if double_score_active:
        remaining = max(0, int(double_score_end_time - current_time))
        text += "2X SCORE: " + str(remaining) + "s\n"
    
    if immunity_active:
        remaining = max(0, int(immunity_end_time - current_time))
        text += "IMMUNITY: " + str(remaining) + "s\n"
    
    if shield_stacks > 0:
        text += "SHIELDS: " + str(shield_stacks) + "\n"
    
    if text:
        powerup_display.color("#00ffff")
        powerup_display.write(text, align="left", font=("Courier", 10, "bold"))

# ==================== DAMAGE TEXT ANIMATION ====================
def spawn_damage_text(x, y, amount, color="#ff0000"):
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)
    t.penup()
    t.goto(x, y)
    t.color(color)
    damage_texts.append({
        "turtle": t,
        "y": y,
        "target_y": y + 50,
        "start_time": time.time(),
        "amount": amount
    })
    t.write("-" + str(amount), align="center", font=("Courier", 14, "bold"))
    play_sound("damage")

def update_damage_texts():
    current_time = time.time()
    to_remove = []
    for dt in damage_texts:
        elapsed = current_time - dt["start_time"]
        if elapsed > 1.0:
            dt["turtle"].clear()
            to_remove.append(dt)
        else:
            new_y = dt["y"] + (dt["target_y"] - dt["y"]) * elapsed
            dt["turtle"].clear()
            alpha = 1 - elapsed
            dt["turtle"].goto(dt["turtle"].xcor(), new_y)
            dt["turtle"].write("-" + str(dt["amount"]), align="center", font=("Courier", 14, "bold"))
    
    for dt in to_remove:
        damage_texts.remove(dt)

# ==================== FOOD ====================
foods = []

def make_food():
    f = turtle.Turtle()
    f.speed(0)
    f.shape("circle")
    f.color("#ff0066", "#ff3399")
    f.shapesize(GRID / 20 * 0.7, GRID / 20 * 0.7)
    f.penup()
    f.hideturtle()
    return f

for _ in range(3):
    foods.append(make_food())

# ==================== POWERUPS (1v1 mode) ====================
def make_powerup(ptype):
    p = turtle.Turtle()
    p.speed(0)
    p.shape("square")
    p.shapesize(GRID / 20 * 0.8, GRID / 20 * 0.8)
    p.penup()
    p.hideturtle()
    
    if ptype == "double":
        p.color("#0066ff", "#00ccff")  # Blue
    elif ptype == "immunity":
        p.color("#ffcc00", "#ffff00")  # Yellow
    elif ptype == "shield":
        p.color("#00ff66", "#66ff99")  # Green
    
    return p

def get_occupied_cells():
    occupied = set()
    occupied.add(pos_to_cell(head.xcor(), head.ycor()))
    for seg in segments:
        occupied.add(pos_to_cell(seg.xcor(), seg.ycor()))
    if game_mode == "1v1" and ai_head is not None:
        occupied.add(pos_to_cell(ai_head.xcor(), ai_head.ycor()))
        for seg in ai_segments:
            occupied.add(pos_to_cell(seg.xcor(), seg.ycor()))
    for f in foods:
        if f.isvisible():
            occupied.add(pos_to_cell(f.xcor(), f.ycor()))
    for p in poison_items:
        if p.isvisible():
            occupied.add(pos_to_cell(p.xcor(), p.ycor()))
    for pu in powerups:
        if pu["turtle"].isvisible():
            occupied.add(pos_to_cell(pu["turtle"].xcor(), pu["turtle"].ycor()))
    return occupied

def spawn_food(food_turtle):
    occupied = get_occupied_cells()
    available = []
    for col in range(GRID_CELLS):
        for row in range(GRID_CELLS):
            if (col, row) not in occupied:
                available.append((col, row))
    if available:
        col, row = random.choice(available)
        x, y = cell_center(col, row)
        food_turtle.goto(x, y)
        food_turtle.showturtle()
    else:
        food_turtle.hideturtle()

def spawn_powerup(ptype):
    p = make_powerup(ptype)
    occupied = get_occupied_cells()
    available = []
    for col in range(GRID_CELLS):
        for row in range(GRID_CELLS):
            if (col, row) not in occupied:
                available.append((col, row))
    if available:
        col, row = random.choice(available)
        x, y = cell_center(col, row)
        p.goto(x, y)
        p.showturtle()
        powerups.append({"turtle": p, "type": ptype, "spawn_time": time.time()})

def spawn_poison():
    p = turtle.Turtle()
    p.speed(0)
    p.shape("triangle")
    p.color("#9900ff", "#cc00ff")
    p.shapesize(GRID / 20 * 0.8, GRID / 20 * 0.8)
    p.penup()
    poison_items.append(p)
    spawn_food(p)

# ==================== POWERUP SPAWNING LOGIC ====================
powerup_spawned = {"double_33": False, "double_66": False, "immunity": False, "shield_20": False,
                   "shield_40": False, "shield_60": False, "shield_80": False}

def check_powerup_spawns():
    global powerup_spawned
    if game_mode != "1v1":
        return
    
    elapsed = int(time.time() - match_start_time)
    
    # Blue (double score) at 33 and 66 seconds
    if elapsed >= 33 and not powerup_spawned["double_33"]:
        spawn_powerup("double")
        powerup_spawned["double_33"] = True
    if elapsed >= 66 and not powerup_spawned["double_66"]:
        spawn_powerup("double")
        powerup_spawned["double_66"] = True
    
    # Yellow (immunity) random between 40-60s
    if 40 <= elapsed <= 60 and not powerup_spawned["immunity"]:
        if random.random() < 0.05:  # ~5% chance per frame
            spawn_powerup("immunity")
            powerup_spawned["immunity"] = True
    
    # Green (shield) at 20, 40, 60, 80 seconds
    if elapsed >= 20 and not powerup_spawned["shield_20"]:
        spawn_powerup("shield")
        powerup_spawned["shield_20"] = True
    if elapsed >= 40 and not powerup_spawned["shield_40"]:
        spawn_powerup("shield")
        powerup_spawned["shield_40"] = True
    if elapsed >= 60 and not powerup_spawned["shield_60"]:
        spawn_powerup("shield")
        powerup_spawned["shield_60"] = True
    if elapsed >= 80 and not powerup_spawned["shield_80"]:
        spawn_powerup("shield")
        powerup_spawned["shield_80"] = True

def check_powerup_collision():
    global double_score_active, double_score_end_time, immunity_active, immunity_end_time, shield_stacks, ai_shield_stacks
    
    head_cell = pos_to_cell(head.xcor(), head.ycor())
    ai_cell = pos_to_cell(ai_head.xcor(), ai_head.ycor()) if ai_head else None
    
    to_remove = []
    for pu in powerups:
        if not pu["turtle"].isvisible():
            continue
        pu_cell = pos_to_cell(pu["turtle"].xcor(), pu["turtle"].ycor())
        
        if pu_cell == head_cell:
            play_sound("powerup")
            if pu["type"] == "double":
                double_score_active = True
                double_score_end_time = time.time() + 10
            elif pu["type"] == "immunity":
                immunity_active = True
                immunity_end_time = time.time() + 5
            elif pu["type"] == "shield":
                shield_stacks += 1
            pu["turtle"].hideturtle()
            to_remove.append(pu)
        
        elif ai_cell and pu_cell == ai_cell:
            if pu["type"] == "shield":
                ai_shield_stacks += 1
            pu["turtle"].hideturtle()
            to_remove.append(pu)
    
    for pu in to_remove:
        powerups.remove(pu)

def update_powerup_states():
    global double_score_active, immunity_active
    current_time = time.time()
    
    if double_score_active and current_time > double_score_end_time:
        double_score_active = False
    
    if immunity_active and current_time > immunity_end_time:
        immunity_active = False

# ==================== SEGMENT COLOR MANAGEMENT ====================
def update_segment_colors():
    head_rgb = COLOR_HEAD_RGB.get(body_color, (0, 212, 255))
    for i, seg in enumerate(segments):
        color = gradient_color_for_index(head_rgb, i)
        seg.color(color)
    head_vis.color(rgb_to_hex(*head_rgb))
    head_glow.color(rgb_to_hex(head_rgb[0]//4, head_rgb[1]//4, head_rgb[2]//4))

def update_ai_segment_colors():
    if ai_head_vis is None:
        return
    head_rgb = COLOR_HEAD_RGB.get(ai_color, (0, 102, 255))
    for i, seg in enumerate(ai_segments):
        color = gradient_color_for_index(head_rgb, i)
        seg.color(color)
    ai_head_vis.color(rgb_to_hex(*head_rgb))

# ==================== HEAD VISUAL ====================
def update_head_visual():
    hx, hy = head.xcor(), head.ycor()
    head_vis.goto(hx, hy)
    head_glow.goto(hx, hy)
    
    if head.direction == "right":
        head_vis.setheading(0)
        eye.goto(hx + GRID * 0.15, hy + GRID * 0.18)
    elif head.direction == "left":
        head_vis.setheading(180)
        eye.goto(hx - GRID * 0.15, hy + GRID * 0.18)
    elif head.direction == "up":
        head_vis.setheading(90)
        eye.goto(hx - GRID * 0.18, hy + GRID * 0.15)
    elif head.direction == "down":
        head_vis.setheading(270)
        eye.goto(hx + GRID * 0.18, hy - GRID * 0.15)
    
    head_vis.showturtle()
    head_glow.showturtle()
    eye.showturtle()

def update_ai_head_visual():
    if ai_head is None or ai_head_vis is None:
        return
    hx, hy = ai_head.xcor(), ai_head.ycor()
    ai_head_vis.goto(hx, hy)
    
    if ai_direction == "right":
        ai_head_vis.setheading(0)
        ai_eye.goto(hx + GRID * 0.15, hy + GRID * 0.18)
    elif ai_direction == "left":
        ai_head_vis.setheading(180)
        ai_eye.goto(hx - GRID * 0.15, hy + GRID * 0.18)
    elif ai_direction == "up":
        ai_head_vis.setheading(90)
        ai_eye.goto(hx - GRID * 0.18, hy + GRID * 0.15)
    elif ai_direction == "down":
        ai_head_vis.setheading(270)
        ai_eye.goto(hx + GRID * 0.18, hy - GRID * 0.15)
    
    ai_head_vis.showturtle()
    ai_eye.showturtle()

# ==================== MOVEMENT ====================
def go_up():
    if not paused and head.direction != "down":
        head.direction = "up"

def go_down():
    if not paused and head.direction != "up":
        head.direction = "down"

def go_left():
    if not paused and head.direction != "right":
        head.direction = "left"

def go_right():
    if not paused and head.direction != "left":
        head.direction = "right"

def move():
    if head.direction == "stop":
        return False
    if head.direction == "up":
        head.sety(head.ycor() + GRID)
    elif head.direction == "down":
        head.sety(head.ycor() - GRID)
    elif head.direction == "left":
        head.setx(head.xcor() - GRID)
    elif head.direction == "right":
        head.setx(head.xcor() + GRID)
    return True

def move_ai():
    if ai_head is None:
        return
    if ai_direction == "up":
        ai_head.sety(ai_head.ycor() + GRID)
    elif ai_direction == "down":
        ai_head.sety(ai_head.ycor() - GRID)
    elif ai_direction == "left":
        ai_head.setx(ai_head.xcor() - GRID)
    elif ai_direction == "right":
        ai_head.setx(ai_head.xcor() + GRID)

# ==================== AI LOGIC ====================
def ai_think():
    global ai_direction
    if ai_head is None:
        return
    
    ai_col, ai_row = pos_to_cell(ai_head.xcor(), ai_head.ycor())
    
    # Find nearest food or powerup
    nearest_target = None
    min_dist = 9999
    
    for f in foods:
        if f.isvisible():
            fc, fr = pos_to_cell(f.xcor(), f.ycor())
            dist = abs(fc - ai_col) + abs(fr - ai_row)
            if dist < min_dist:
                min_dist = dist
                nearest_target = (fc, fr)
    
    for pu in powerups:
        if pu["turtle"].isvisible():
            pc, pr = pos_to_cell(pu["turtle"].xcor(), pu["turtle"].ycor())
            dist = abs(pc - ai_col) + abs(pr - ai_row)
            if dist < min_dist:
                min_dist = dist
                nearest_target = (pc, pr)
    
    if nearest_target is None:
        possible = get_ai_safe_directions(ai_col, ai_row)
        if possible:
            ai_direction = random.choice(possible)
        return
    
    fc, fr = nearest_target
    
    preferred = []
    if fc > ai_col:
        preferred.append("right")
    elif fc < ai_col:
        preferred.append("left")
    if fr > ai_row:
        preferred.append("up")
    elif fr < ai_row:
        preferred.append("down")
    
    opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
    preferred = [d for d in preferred if d != opposite.get(ai_direction)]
    
    safe = get_ai_safe_directions(ai_col, ai_row)
    
    if ai_difficulty == "easy":
        if random.random() < 0.4:
            if safe:
                ai_direction = random.choice(safe)
                return
    elif ai_difficulty == "medium":
        if random.random() < 0.15:
            if safe:
                ai_direction = random.choice(safe)
                return
    
    for d in preferred:
        if d in safe:
            ai_direction = d
            return
    
    if safe:
        ai_direction = random.choice(safe)

def get_ai_safe_directions(col, row):
    opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
    directions = ["up", "down", "left", "right"]
    safe = []
    
    occupied = set()
    occupied.add(pos_to_cell(head.xcor(), head.ycor()))
    for seg in segments:
        occupied.add(pos_to_cell(seg.xcor(), seg.ycor()))
    for seg in ai_segments:
        occupied.add(pos_to_cell(seg.xcor(), seg.ycor()))
    
    for d in directions:
        if d == opposite.get(ai_direction):
            continue
        nc, nr = col, row
        if d == "up":
            nr += 1
        elif d == "down":
            nr -= 1
        elif d == "left":
            nc -= 1
        elif d == "right":
            nc += 1
        
        if nc < 0 or nc >= GRID_CELLS or nr < 0 or nr >= GRID_CELLS:
            continue
        if (nc, nr) in occupied:
            continue
        safe.append(d)
    
    return safe

# ==================== PAUSE & EXIT ====================
def toggle_pause():
    global paused
    paused = not paused
    if paused:
        pause_display.write("[ PAUSED ]" + NL + "P = Resume  |  M = Menu  |  ESC = Exit",
                           align="center", font=("Courier", 18, "bold"))
    else:
        pause_display.clear()

def go_to_menu():
    global return_to_menu, paused
    if paused:
        paused = False
        pause_display.clear()
    return_to_menu = True

def exit_game():
    global game_running
    game_running = False
    wn.bye()

# ==================== GAME INITIALIZATION ====================
def init_snake():
    global segments, score
    for seg in segments:
        seg.hideturtle()
    segments = []
    score = 0
    update_score()
    
    center_col = GRID_CELLS // 2
    center_row = GRID_CELLS // 2
    hx, hy = cell_center(center_col, center_row)
    head.goto(hx, hy)
    head.direction = "right"
    
    for i in range(2):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape("square")
        seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
        seg.penup()
        seg.color(body_shade)
        sx, sy = cell_center(center_col - (i + 1), center_row)
        seg.goto(sx, sy)
        segments.append(seg)
    
    update_segment_colors()
    update_head_visual()

def init_ai_snake():
    global ai_head, ai_head_vis, ai_eye, ai_segments, ai_score, ai_direction, ai_color
    
    available_colors = [c for c in COLOR_CHOICES.keys() if c != body_color]
    ai_color = random.choice(available_colors)
    
    ai_score = 0
    ai_direction = "left"
    
    if ai_head is not None:
        ai_head.hideturtle()
    if ai_head_vis is not None:
        ai_head_vis.hideturtle()
    if ai_eye is not None:
        ai_eye.hideturtle()
    for seg in ai_segments:
        seg.hideturtle()
    ai_segments = []
    
    ai_head = turtle.Turtle()
    ai_head.hideturtle()
    ai_head.speed(0)
    ai_head.penup()
    
    ai_head_vis = turtle.Turtle()
    ai_head_vis.hideturtle()
    ai_head_vis.speed(0)
    ai_head_vis.penup()
    ai_head_vis.shape("arch")
    ai_head_vis.shapesize(scale, scale)
    ai_shade = COLOR_CHOICES[ai_color][0]
    ai_head_vis.color(ai_shade)
    
    ai_eye = turtle.Turtle()
    ai_eye.hideturtle()
    ai_eye.speed(0)
    ai_eye.penup()
    ai_eye.shape("circle")
    ai_eye.shapesize(0.18, 0.18)
    ai_eye.color("#ffffff")
    
    ai_col = GRID_CELLS // 2
    ai_row = GRID_CELLS // 2 + 4
    ax, ay = cell_center(ai_col, ai_row)
    ai_head.goto(ax, ay)
    
    for i in range(2):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape("square")
        seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
        seg.penup()
        sx, sy = cell_center(ai_col + (i + 1), ai_row)
        seg.goto(sx, sy)
        ai_segments.append(seg)
    
    update_ai_segment_colors()
    update_ai_head_visual()

def cleanup_1v1():
    global ai_head, ai_head_vis, ai_eye, ai_segments, poison_items, powerups
    global double_score_active, immunity_active, shield_stacks, ai_shield_stacks, powerup_spawned
    
    if ai_head is not None:
        ai_head.hideturtle()
        ai_head = None
    if ai_head_vis is not None:
        ai_head_vis.hideturtle()
        ai_head_vis = None
    if ai_eye is not None:
        ai_eye.hideturtle()
        ai_eye = None
    for seg in ai_segments:
        seg.hideturtle()
    ai_segments = []
    for p in poison_items:
        p.hideturtle()
    poison_items = []
    for pu in powerups:
        pu["turtle"].hideturtle()
    powerups = []
    timer_display.clear()
    powerup_display.clear()
    
    double_score_active = False
    immunity_active = False
    shield_stacks = 0
    ai_shield_stacks = 0
    powerup_spawned = {"double_33": False, "double_66": False, "immunity": False, "shield_20": False,
                       "shield_40": False, "shield_60": False, "shield_80": False}

def reset_game():
    global game_running
    play_sound("death")
    if game_mode == "standard":
        if score > 0:
            name = get_player_name()
            add_high_score(name, score)
    init_snake()
    for f in foods:
        spawn_food(f)
    time.sleep(0.5)

def reset_1v1():
    global match_start_time, last_poison_time, powerup_spawned
    global double_score_active, immunity_active, shield_stacks, ai_shield_stacks
    
    init_snake()
    center_col = GRID_CELLS // 2
    center_row = GRID_CELLS // 2 - 4
    hx, hy = cell_center(center_col, center_row)
    head.goto(hx, hy)
    head.direction = "right"
    for i, seg in enumerate(segments):
        sx, sy = cell_center(center_col - (i + 1), center_row)
        seg.goto(sx, sy)
    
    init_ai_snake()
    for f in foods:
        spawn_food(f)
    match_start_time = time.time()
    last_poison_time = time.time()
    
    double_score_active = False
    immunity_active = False
    shield_stacks = 0
    ai_shield_stacks = 0
    powerup_spawned = {"double_33": False, "double_66": False, "immunity": False, "shield_20": False,
                       "shield_40": False, "shield_60": False, "shield_80": False}
    
    for pu in powerups:
        pu["turtle"].hideturtle()
    powerups.clear()

def reset_player_snake_1v1():
    global segments, score
    play_sound("death")
    for seg in segments:
        seg.hideturtle()
    segments = []
    score = max(0, score - 20)
    center_col = GRID_CELLS // 2
    center_row = GRID_CELLS // 2 - 4
    hx, hy = cell_center(center_col, center_row)
    head.goto(hx, hy)
    head.direction = "right"
    for i in range(2):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape("square")
        seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
        seg.penup()
        sx, sy = cell_center(center_col - (i + 1), center_row)
        seg.goto(sx, sy)
        segments.append(seg)
    update_segment_colors()
    update_head_visual()
    update_score()

def reset_ai_snake_1v1():
    global ai_segments, ai_score, ai_direction
    for seg in ai_segments:
        seg.hideturtle()
    ai_segments = []
    ai_score = max(0, ai_score - 20)
    ai_direction = "left"
    ai_col = GRID_CELLS // 2
    ai_row = GRID_CELLS // 2 + 4
    ax, ay = cell_center(ai_col, ai_row)
    ai_head.goto(ax, ay)
    for i in range(2):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape("square")
        seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
        seg.penup()
        sx, sy = cell_center(ai_col + (i + 1), ai_row)
        seg.goto(sx, sy)
        ai_segments.append(seg)
    update_ai_segment_colors()
    update_ai_head_visual()
    update_score()

# ==================== COLLISION CHECKS ====================
def check_wall_collision():
    col, row = pos_to_cell(head.xcor(), head.ycor())
    return col < 0 or col >= GRID_CELLS or row < 0 or row >= GRID_CELLS

def check_ai_wall_collision():
    if ai_head is None:
        return False
    col, row = pos_to_cell(ai_head.xcor(), ai_head.ycor())
    return col < 0 or col >= GRID_CELLS or row < 0 or row >= GRID_CELLS

def check_self_collision():
    """Check if snake head collides with its own body - causes death in standard mode"""
    head_cell = pos_to_cell(head.xcor(), head.ycor())
    for seg in segments:
        if pos_to_cell(seg.xcor(), seg.ycor()) == head_cell:
            return True
    return False

def check_food_collision():
    global score
    head_cell = pos_to_cell(head.xcor(), head.ycor())
    for f in foods:
        if not f.isvisible():
            continue
        if pos_to_cell(f.xcor(), f.ycor()) == head_cell:
            play_sound("eat")
            new_seg = turtle.Turtle()
            new_seg.speed(0)
            new_seg.shape("square")
            new_seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
            new_seg.penup()
            if segments:
                new_seg.goto(segments[-1].xcor(), segments[-1].ycor())
            else:
                new_seg.goto(head.xcor(), head.ycor())
            segments.append(new_seg)
            update_segment_colors()
            
            points = 20 if double_score_active else 10
            score += points
            update_score()
            spawn_food(f)
            return True
    return False

def check_ai_food_collision():
    global ai_score
    if ai_head is None:
        return False
    head_cell = pos_to_cell(ai_head.xcor(), ai_head.ycor())
    for f in foods:
        if not f.isvisible():
            continue
        if pos_to_cell(f.xcor(), f.ycor()) == head_cell:
            new_seg = turtle.Turtle()
            new_seg.speed(0)
            new_seg.shape("square")
            new_seg.shapesize(GRID / 20 * 0.9, GRID / 20 * 0.9)
            new_seg.penup()
            if ai_segments:
                new_seg.goto(ai_segments[-1].xcor(), ai_segments[-1].ycor())
            else:
                new_seg.goto(ai_head.xcor(), ai_head.ycor())
            ai_segments.append(new_seg)
            update_ai_segment_colors()
            ai_score += 10
            update_score()
            spawn_food(f)
            return True
    return False

def check_poison_collision():
    global score, ai_score
    head_cell = pos_to_cell(head.xcor(), head.ycor())
    for p in poison_items:
        if not p.isvisible():
            continue
        if pos_to_cell(p.xcor(), p.ycor()) == head_cell:
            p.hideturtle()
            remove_count = min(5, len(ai_segments))
            damage = remove_count * 10
            if ai_shield_stacks > 0:
                ai_shield_stacks -= 1
                damage = 0
                remove_count = 0
            for _ in range(remove_count):
                seg = ai_segments.pop()
                seg.hideturtle()
                ai_score = max(0, ai_score - 10)
            if damage > 0:
                spawn_damage_text(ai_head.xcor(), ai_head.ycor(), damage)
            update_ai_segment_colors()
            update_score()
            return
    
    if ai_head is not None:
        ai_cell = pos_to_cell(ai_head.xcor(), ai_head.ycor())
        for p in poison_items:
            if not p.isvisible():
                continue
            if pos_to_cell(p.xcor(), p.ycor()) == ai_cell:
                p.hideturtle()
                remove_count = min(5, len(segments))
                damage = remove_count * 10
                global shield_stacks
                if shield_stacks > 0:
                    shield_stacks -= 1
                    damage = 0
                    remove_count = 0
                for _ in range(remove_count):
                    seg = segments.pop()
                    seg.hideturtle()
                    score = max(0, score - 10)
                if damage > 0:
                    spawn_damage_text(head.xcor(), head.ycor(), damage)
                update_segment_colors()
                update_score()
                return

def check_head_vs_body():
    global score, ai_score, shield_stacks, ai_shield_stacks
    if game_mode != "1v1" or ai_head is None:
        return
    
    # Player with immunity can damage AI
    if immunity_active:
        head_cell = pos_to_cell(head.xcor(), head.ycor())
        hits = 0
        to_remove = []
        for seg in ai_segments:
            if pos_to_cell(seg.xcor(), seg.ycor()) == head_cell:
                hits += 1
                to_remove.append(seg)
        
        # Remove up to 3 segments per hit
        remove_count = min(3 * hits, len(ai_segments))
        if remove_count > 0:
            if ai_shield_stacks > 0:
                ai_shield_stacks -= 1
                remove_count = 0
            else:
                damage = remove_count * 10
                for _ in range(remove_count):
                    if ai_segments:
                        removed = ai_segments.pop()
                        removed.hideturtle()
                        ai_score = max(0, ai_score - 10)
                spawn_damage_text(ai_head.xcor(), ai_head.ycor(), damage, "#ff6600")
                update_ai_segment_colors()
                update_score()
        return
    
    # Normal collision - each snake loses 1 segment when hitting opponent body
    head_cell = pos_to_cell(head.xcor(), head.ycor())
    for seg in ai_segments:
        if pos_to_cell(seg.xcor(), seg.ycor()) == head_cell:
            if ai_shield_stacks > 0:
                ai_shield_stacks -= 1
            elif ai_segments:
                removed = ai_segments.pop()
                removed.hideturtle()
                ai_score = max(0, ai_score - 10)
                spawn_damage_text(ai_head.xcor(), ai_head.ycor(), 10)
                update_ai_segment_colors()
                update_score()
            break
    
    ai_cell = pos_to_cell(ai_head.xcor(), ai_head.ycor())
    for seg in segments:
        if pos_to_cell(seg.xcor(), seg.ycor()) == ai_cell:
            if shield_stacks > 0:
                shield_stacks -= 1
            elif segments:
                removed = segments.pop()
                removed.hideturtle()
                score = max(0, score - 10)
                spawn_damage_text(head.xcor(), head.ycor(), 10)
                update_segment_colors()
                update_score()
            break

# ==================== SHOW WINNER (1v1) ====================
def show_winner():
    pause_display.clear()
    player_len = len(segments) + 1
    ai_len = len(ai_segments) + 1
    
    if score > ai_score:
        msg = ">>> YOU WIN! <<<" + NL + "Score: " + str(score) + " vs AI: " + str(ai_score)
        pause_display.color("#00ff00")
    elif ai_score > score:
        msg = ">>> AI WINS! <<<" + NL + "Score: " + str(score) + " vs AI: " + str(ai_score)
        pause_display.color("#ff0000")
    else:
        if player_len > ai_len:
            msg = ">>> YOU WIN! <<<" + NL + "Length: " + str(player_len) + " vs AI: " + str(ai_len)
            pause_display.color("#00ff00")
        elif ai_len > player_len:
            msg = ">>> AI WINS! <<<" + NL + "Length: " + str(player_len) + " vs AI: " + str(ai_len)
            pause_display.color("#ff0000")
        else:
            msg = ">>> TIE GAME! <<<" + NL + "Both: " + str(player_len) + " segments"
            pause_display.color("#ffff00")
    
    pause_display.write(msg, align="center", font=("Courier", 22, "bold"))
    time.sleep(3)
    pause_display.clear()

# ==================== LEADERBOARD POPUP ====================
leaderboard_visible = False
leaderboard_turtles = []

def show_leaderboard():
    global leaderboard_visible, leaderboard_turtles
    
    if leaderboard_visible:
        hide_leaderboard()
        return
    
    leaderboard_visible = True
    
    # Background
    bg = turtle.Turtle()
    bg.hideturtle()
    bg.speed(0)
    bg.penup()
    bg.goto(-150, PLAY_CENTER_Y + 150)
    bg.color("#000033", "#0a0a2a")
    bg.begin_fill()
    bg.pendown()
    for _ in range(2):
        bg.forward(300)
        bg.right(90)
        bg.forward(320)
        bg.right(90)
    bg.end_fill()
    bg.penup()
    leaderboard_turtles.append(bg)
    
    # Border
    border = turtle.Turtle()
    border.hideturtle()
    border.speed(0)
    border.color("#00ffff")
    border.pensize(2)
    border.penup()
    border.goto(-150, PLAY_CENTER_Y + 150)
    border.pendown()
    for _ in range(2):
        border.forward(300)
        border.right(90)
        border.forward(320)
        border.right(90)
    border.penup()
    leaderboard_turtles.append(border)
    
    # Title
    title = turtle.Turtle()
    title.hideturtle()
    title.penup()
    title.color("#ff00ff")
    title.goto(0, PLAY_CENTER_Y + 120)
    title.write("[ LEADERBOARD ]", align="center", font=("Courier", 18, "bold"))
    leaderboard_turtles.append(title)
    
    # Scores
    scores = load_high_scores()
    score_t = turtle.Turtle()
    score_t.hideturtle()
    score_t.penup()
    score_t.color("#00ffff")
    
    y_pos = PLAY_CENTER_Y + 80
    if scores:
        for i, entry in enumerate(scores[:8]):
            score_t.goto(0, y_pos)
            rank_color = "#ffd700" if i == 0 else "#c0c0c0" if i == 1 else "#cd7f32" if i == 2 else "#00ffff"
            score_t.color(rank_color)
            text = str(i + 1) + ". " + entry['name'][:10] + " - " + str(entry['score'])
            score_t.write(text, align="center", font=("Courier", 12, "bold"))
            y_pos -= 30
    else:
        score_t.goto(0, y_pos)
        score_t.write("No scores yet!", align="center", font=("Courier", 12, "normal"))
    
    leaderboard_turtles.append(score_t)
    
    # Close instruction
    close_t = turtle.Turtle()
    close_t.hideturtle()
    close_t.penup()
    close_t.color("#666666")
    close_t.goto(0, PLAY_CENTER_Y - 150)
    close_t.write("Press L to close", align="center", font=("Courier", 10, "normal"))
    leaderboard_turtles.append(close_t)

def hide_leaderboard():
    global leaderboard_visible, leaderboard_turtles
    leaderboard_visible = False
    for t in leaderboard_turtles:
        t.clear()
    leaderboard_turtles = []

def toggle_leaderboard():
    if leaderboard_visible:
        hide_leaderboard()
    else:
        show_leaderboard()

# ==================== MAIN MENU ====================
def show_menu():
    global start_pressed, body_color, body_shade, head_color, game_mode, ai_difficulty
    
    head_vis.hideturtle()
    head_glow.hideturtle()
    eye.hideturtle()
    for f in foods:
        f.hideturtle()
    
    colors = list(COLOR_CHOICES.keys())
    state = [0, 0, 1, 0]
    modes = ["Standard", "1v1 vs AI"]
    difficulties = ["Easy", "Medium", "Hard"]
    
    # Futuristic menu background
    menu_bg = turtle.Turtle()
    menu_bg.hideturtle()
    menu_bg.speed(0)
    menu_bg.penup()
    menu_bg.goto(-280, PLAY_CENTER_Y - 200)
    menu_bg.color("#000011", "#050520")
    menu_bg.begin_fill()
    menu_bg.pendown()
    for side in [560, 440, 560, 440]:
        menu_bg.forward(side)
        menu_bg.left(90)
    menu_bg.end_fill()
    menu_bg.penup()
    
    # Neon border for menu
    menu_border = turtle.Turtle()
    menu_border.hideturtle()
    menu_border.speed(0)
    menu_border.color("#00ffff")
    menu_border.pensize(3)
    menu_border.penup()
    menu_border.goto(-280, PLAY_CENTER_Y - 200)
    menu_border.pendown()
    for side in [560, 440, 560, 440]:
        menu_border.forward(side)
        menu_border.left(90)
    menu_border.penup()
    
    title_t = turtle.Turtle()
    title_t.hideturtle()
    title_t.penup()
    title_t.color("#ff00ff")
    title_t.goto(0, PLAY_CENTER_Y + 160)
    title_t.write("N E O N   S N A K E", align="center", font=("Courier", 32, "bold"))
    
    subtitle = turtle.Turtle()
    subtitle.hideturtle()
    subtitle.penup()
    subtitle.color("#00ffff")
    subtitle.goto(0, PLAY_CENTER_Y + 120)
    subtitle.write("// FUTURISTIC EDITION //", align="center", font=("Courier", 14, "normal"))
    
    preview = turtle.Turtle()
    preview.speed(0)
    preview.shape("square")
    preview.shapesize(2.5, 2.5)
    preview.penup()
    preview.goto(0, PLAY_CENTER_Y + 60)
    preview.color(COLOR_CHOICES[colors[0]][0])
    preview.showturtle()
    
    # Glow effect for preview
    preview_glow = turtle.Turtle()
    preview_glow.speed(0)
    preview_glow.shape("circle")
    preview_glow.shapesize(3.5, 3.5)
    preview_glow.penup()
    preview_glow.goto(0, PLAY_CENTER_Y + 60)
    col_rgb = COLOR_HEAD_RGB[colors[0]]
    preview_glow.color(rgb_to_hex(col_rgb[0]//4, col_rgb[1]//4, col_rgb[2]//4))
    preview_glow.showturtle()
    
    label1 = turtle.Turtle()
    label1.hideturtle()
    label1.penup()
    label1.color("#ffffff")
    label1.goto(0, PLAY_CENTER_Y + 5)
    
    label2 = turtle.Turtle()
    label2.hideturtle()
    label2.penup()
    label2.color("#00ffff")
    label2.goto(0, PLAY_CENTER_Y - 35)
    
    label3 = turtle.Turtle()
    label3.hideturtle()
    label3.penup()
    label3.color("#ff6600")
    label3.goto(0, PLAY_CENTER_Y - 70)
    
    instr = turtle.Turtle()
    instr.hideturtle()
    instr.penup()
    instr.color("#666666")
    instr.goto(0, PLAY_CENTER_Y - 120)
    
    # Leaderboard button
    lb_btn = turtle.Turtle()
    lb_btn.hideturtle()
    lb_btn.penup()
    lb_btn.color("#ffff00")
    lb_btn.goto(0, PLAY_CENTER_Y - 160)
    
    def update_display():
        label1.clear()
        label2.clear()
        label3.clear()
        instr.clear()
        lb_btn.clear()
        
        col = colors[state[0]]
        preview.color(COLOR_CHOICES[col][0])
        col_rgb = COLOR_HEAD_RGB[col]
        preview_glow.color(rgb_to_hex(col_rgb[0]//4, col_rgb[1]//4, col_rgb[2]//4))
        
        arrow = ">> "
        if state[3] == 0:
            label1.write(arrow + "COLOR: " + col.upper(), align="center", font=("Courier", 14, "bold"))
            label2.write("   MODE: " + modes[state[1]], align="center", font=("Courier", 12, "normal"))
            if state[1] == 1:
                label3.write("   AI: " + difficulties[state[2]], align="center", font=("Courier", 12, "normal"))
        elif state[3] == 1:
            label1.write("   COLOR: " + col.upper(), align="center", font=("Courier", 12, "normal"))
            label2.write(arrow + "MODE: " + modes[state[1]], align="center", font=("Courier", 14, "bold"))
            if state[1] == 1:
                label3.write("   AI: " + difficulties[state[2]], align="center", font=("Courier", 12, "normal"))
        elif state[3] == 2:
            label1.write("   COLOR: " + col.upper(), align="center", font=("Courier", 12, "normal"))
            label2.write("   MODE: " + modes[state[1]], align="center", font=("Courier", 12, "normal"))
            label3.write(arrow + "AI: " + difficulties[state[2]], align="center", font=("Courier", 14, "bold"))
        
        instr.write("< > SELECT  |  UP/DOWN NAVIGATE  |  ENTER START  |  L LEADERBOARD",
                   align="center", font=("Courier", 9, "normal"))
        lb_btn.write("[ L ] VIEW LEADERBOARD", align="center", font=("Courier", 11, "bold"))
    
    update_display()
    
    def menu_left():
        if state[3] == 0:
            state[0] = (state[0] - 1) % len(colors)
        elif state[3] == 1:
            state[1] = (state[1] - 1) % len(modes)
        elif state[3] == 2:
            state[2] = (state[2] - 1) % len(difficulties)
        update_display()
    
    def menu_right():
        if state[3] == 0:
            state[0] = (state[0] + 1) % len(colors)
        elif state[3] == 1:
            state[1] = (state[1] + 1) % len(modes)
        elif state[3] == 2:
            state[2] = (state[2] + 1) % len(difficulties)
        update_display()
    
    def menu_up():
        max_phase = 2 if state[1] == 1 else 1
        state[3] = (state[3] - 1) % (max_phase + 1)
        update_display()
    
    def menu_down():
        max_phase = 2 if state[1] == 1 else 1
        state[3] = (state[3] + 1) % (max_phase + 1)
        update_display()
    
    def menu_start():
        nonlocal start_pressed_local
        start_pressed_local = True
    
    def menu_exit():
        nonlocal start_pressed_local
        start_pressed_local = True
        state.append("exit")
    
    def menu_leaderboard():
        toggle_leaderboard()
    
    start_pressed_local = False
    
    wn.onkey(menu_left, "Left")
    wn.onkey(menu_right, "Right")
    wn.onkey(menu_up, "Up")
    wn.onkey(menu_down, "Down")
    wn.onkey(menu_start, "Return")
    wn.onkey(menu_start, "space")
    wn.onkey(menu_exit, "Escape")
    wn.onkey(menu_leaderboard, "l")
    wn.listen()
    
    while not start_pressed_local:
        wn.update()
        time.sleep(0.03)
    
    hide_leaderboard()
    
    if len(state) > 4 and state[4] == "exit":
        exit_game()
        return
    
    col = colors[state[0]]
    body_color = col
    body_shade, head_color = COLOR_CHOICES[col]
    game_mode = "standard" if state[1] == 0 else "1v1"
    ai_difficulty = difficulties[state[2]].lower()
    
    for t in [menu_bg, menu_border, title_t, subtitle, preview, preview_glow, label1, label2, label3, instr, lb_btn]:
        t.clear()
        try:
            t.hideturtle()
        except:
            pass
    
    wn.onkey(go_up, "Up")
    wn.onkey(go_up, "w")
    wn.onkey(go_down, "Down")
    wn.onkey(go_down, "s")
    wn.onkey(go_left, "Left")
    wn.onkey(go_left, "a")
    wn.onkey(go_right, "Right")
    wn.onkey(go_right, "d")
    wn.onkey(toggle_pause, "p")
    wn.onkey(go_to_menu, "m")
    wn.onkey(exit_game, "Escape")
    wn.onkey(toggle_leaderboard, "l")
    wn.listen()
    
    start_pressed = True

# ==================== ON-SCREEN BUTTONS ====================
button_turtles = []

def draw_neon_button(x, y, width, height, text, color, text_color, click_func):
    btn = turtle.Turtle()
    btn.speed(0)
    btn.penup()
    btn.goto(x, y)
    btn.shape("square")
    btn.shapesize(height / 20, width / 20)
    btn.color(color)
    btn.showturtle()
    btn.onclick(lambda bx, by, f=click_func: f())
    button_turtles.append(btn)
    
    lbl = turtle.Turtle()
    lbl.hideturtle()
    lbl.penup()
    lbl.goto(x, y - 6)
    lbl.color(text_color)
    lbl.write(text, align="center", font=("Courier", 10, "bold"))
    button_turtles.append(lbl)

def draw_arrow_buttons():
    base_y = PLAY_CENTER_Y - PLAY_H / 2 - 70
    
    # Direction buttons with neon style
    draw_neon_button(0, base_y + 35, 35, 30, "^", "#003366", "#00ffff", go_up)
    draw_neon_button(0, base_y - 35, 35, 30, "v", "#003366", "#00ffff", go_down)
    draw_neon_button(-50, base_y, 35, 30, "<", "#003366", "#00ffff", go_left)
    draw_neon_button(50, base_y, 35, 30, ">", "#003366", "#00ffff", go_right)
    
    # Pause button
    draw_neon_button(180, base_y, 60, 30, "PAUSE", "#333300", "#ffff00", toggle_pause)
    
    # Menu button
    draw_neon_button(180, base_y - 40, 60, 30, "MENU", "#330033", "#ff00ff", go_to_menu)
    
    # Exit button
    draw_neon_button(-180, base_y, 50, 30, "EXIT", "#330000", "#ff0000", exit_game)

# ==================== MAIN GAME FLOW ====================
show_menu()

if game_mode == "standard":
    cleanup_1v1()
    init_snake()
    for f in foods:
        spawn_food(f)
else:
    reset_1v1()

draw_arrow_buttons()
game_running = True

while game_running:
    try:
        wn.update()
    except turtle.Terminator:
        break
    except Exception:
        break
    
    if return_to_menu:
        return_to_menu = False
        cleanup_1v1()
        for seg in segments:
            seg.hideturtle()
        segments = []
        head.direction = "stop"
        head_vis.hideturtle()
        head_glow.hideturtle()
        eye.hideturtle()
        for f in foods:
            f.hideturtle()
        score_display.clear()
        timer_display.clear()
        powerup_display.clear()
        hide_leaderboard()
        show_menu()
        if game_mode == "standard":
            cleanup_1v1()
            init_snake()
            for f in foods:
                spawn_food(f)
        else:
            reset_1v1()
        continue
    
    if paused:
        time.sleep(delay)
        continue
    
    if head.direction == "stop":
        time.sleep(delay)
        continue
    
    # Update damage text animations
    update_damage_texts()
    
    if game_mode == "standard":
        old_hx, old_hy = head.xcor(), head.ycor()
        move()
        
        # Self collision = death in standard mode
        if check_self_collision():
            reset_game()
            time.sleep(delay)
            continue
        
        if segments:
            prev_x, prev_y = old_hx, old_hy
            for seg in segments:
                sx, sy = seg.xcor(), seg.ycor()
                seg.goto(prev_x, prev_y)
                prev_x, prev_y = sx, sy
        
        update_head_visual()
        
        if check_wall_collision():
            reset_game()
            time.sleep(delay)
            continue
        
        check_food_collision()
    
    else:
        elapsed = time.time() - match_start_time
        if elapsed >= match_time:
            show_winner()
            cleanup_1v1()
            game_mode = "standard"
            show_menu()
            if game_mode == "standard":
                cleanup_1v1()
                init_snake()
                for f in foods:
                    spawn_food(f)
            else:
                reset_1v1()
            continue
        
        update_timer()
        update_powerup_states()
        update_powerup_display()
        check_powerup_spawns()
        
        if time.time() - last_poison_time >= poison_interval:
            spawn_poison()
            last_poison_time = time.time()
        
        ai_think()
        
        old_hx, old_hy = head.xcor(), head.ycor()
        move()
        if segments:
            prev_x, prev_y = old_hx, old_hy
            for seg in segments:
                sx, sy = seg.xcor(), seg.ycor()
                seg.goto(prev_x, prev_y)
                prev_x, prev_y = sx, sy
        update_head_visual()
        
        old_ax, old_ay = ai_head.xcor(), ai_head.ycor()
        move_ai()
        if ai_segments:
            prev_x, prev_y = old_ax, old_ay
            for seg in ai_segments:
                sx, sy = seg.xcor(), seg.ycor()
                seg.goto(prev_x, prev_y)
                prev_x, prev_y = sx, sy
        update_ai_head_visual()
        
        # Self collision penalty in 1v1 (removes segments, doesn't kill)
        if not immunity_active:
            head_cell = pos_to_cell(head.xcor(), head.ycor())
            for seg in segments:
                if pos_to_cell(seg.xcor(), seg.ycor()) == head_cell:
                    remove_count = min(2, len(segments))
                    damage = remove_count * 10
                    for _ in range(remove_count):
                        removed = segments.pop()
                        removed.hideturtle()
                        score = max(0, score - 10)
                    if damage > 0:
                        spawn_damage_text(head.xcor(), head.ycor(), damage)
                    update_segment_colors()
                    update_score()
                    break
        
        # AI self collision penalty
        if ai_head is not None:
            ai_cell = pos_to_cell(ai_head.xcor(), ai_head.ycor())
            for seg in ai_segments:
                if pos_to_cell(seg.xcor(), seg.ycor()) == ai_cell:
                    remove_count = min(2, len(ai_segments))
                    damage = remove_count * 10
                    for _ in range(remove_count):
                        removed = ai_segments.pop()
                        removed.hideturtle()
                        ai_score = max(0, ai_score - 10)
                    if damage > 0:
                        spawn_damage_text(ai_head.xcor(), ai_head.ycor(), damage)
                    update_ai_segment_colors()
                    update_score()
                    break
        
        check_head_vs_body()
        check_powerup_collision()
        
        if check_wall_collision():
            reset_player_snake_1v1()
        
        if check_ai_wall_collision():
            reset_ai_snake_1v1()
        
        check_food_collision()
        check_ai_food_collision()
        check_poison_collision()
    
    time.sleep(delay)

wn.mainloop()

