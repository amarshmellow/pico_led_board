import machine
import utime
from machine import Pin, ADC 
import neopixel
import random
import sys

import LCD1602

try:
    lcd = LCD1602.LCD1602(16, 2)
    lcd.clear()
    print("LCD initialized successfully using its internal I2C setup.")
except Exception as e:
    print(f"Error initializing LCD: {e}.")
    print("Please ensure:")
    print("1. 'LCD1602.py' is correctly uploaded to your Pico.")
    print("2. The SDA/SCL pins and I2C address defined INSIDE 'LCD1602.py' match your wiring.")
    print("LCD display will not work. Continuing game without LCD.")
    class DummyLCD:
        def clear(self): pass
        def setCursor(self, col, row): pass
        def printout(self, text): pass
        def print_lcd(self, message: str): pass
        def display(self): pass
    lcd = DummyLCD()


led = Pin(25, Pin.OUT)
led.value(1)

for i in range(3):
    led.value(0)
    utime.sleep(0.1)
    led.value(1)
    utime.sleep(0.1)

led.value(1)

np = neopixel.NeoPixel(machine.Pin(11), 50)
button = Pin(8, Pin.IN, Pin.PULL_UP) 

# Joystick setup - Pins remain as swapped in the previous version
joystick_x = machine.ADC(27) # X-axis (horizontal movement) connected to GP27
joystick_y = machine.ADC(26) # Y-axis (vertical movement) connected to GP26

# Tolerance for "approximately center" values
CENTER_TOLERANCE = 1000 

JOYSTICK_DEBOUNCE_TIME_MS = 100 
last_joystick_move_time = 0

map = [[0, 1, 2, 3, 4],
       [9, 8, 7, 6, 5],
       [10, 11, 12, 13, 14],
       [19, 18, 17, 16, 15],
       [20, 21, 22, 23, 24],
       [29, 28, 27, 26, 25],
       [30, 31, 32, 33, 34],
       [39, 38, 37, 36, 35],
       [40, 41, 42, 43, 44],
       [49, 48, 47, 46, 45]]

GRID_ROWS = 10
GRID_COLS = 5

possible_deltas = {
    'UP': (1, 0),    # Increases row (moves visually DOWN if row 0 is top)
    'DOWN': (-1, 0), # Decreases row (moves visually UP if row 0 is top)
    'LEFT': (0, -1), # Decreases col (moves visually LEFT)
    'RIGHT': (0, 1)  # Increases col (moves visually RIGHT)
}


APPLE_COLOR = (0, 61, 0)
SNAKE_HEAD_COLOR = (100, 0, 0)
SNAKE_TAIL_COLOR = (65, 65, 0)
SNAKE_GRADIENT_START_COLOR = (100, 0, 0)
SNAKE_GRADIENT_MIDDLE_COLOR = (0, 0, 80)
SNAKE_GRADIENT_END_COLOR = SNAKE_TAIL_COLOR
BACKGROUND_COLOR = (0, 0, 0)

GAME_SPEED = 0.2

snake = []
apple_pos = (0, 0)
direction = 'RIGHT'
score = 0
game_over = False
session_high_score = 0
play_mode = 'joystick' 

def get_led_index(row, col):
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        return map[row][col]
    return -1

def place_apple():
    global apple_pos
    while True:
        r = random.randint(0, GRID_ROWS - 1)
        c = random.randint(0, GRID_COLS - 1)
        if (r, c) not in snake:
            apple_pos = (r, c)
            break

def draw_game():
    np.fill(BACKGROUND_COLOR)

    apple_led_index = get_led_index(apple_pos[0], apple_pos[1])
    if apple_led_index != -1:
        np[apple_led_index] = APPLE_COLOR

    num_gradient_segments = len(snake) - 2

    for i, (segment_row, segment_col) in enumerate(snake):
        segment_led_index = get_led_index(segment_row, segment_col)
        if segment_led_index == -1:
            continue

        if i == 0:
            np[segment_led_index] = SNAKE_HEAD_COLOR
        elif i == len(snake) - 1:
            np[segment_led_index] = SNAKE_TAIL_COLOR
        else:
            gradient_index = i - 1

            if num_gradient_segments <= 0:
                pass
            elif num_gradient_segments == 1:
                ratio = gradient_index / (num_gradient_segments - 1) if num_gradient_segments > 1 else 0.0
                
                g1, r1, b1 = SNAKE_GRADIENT_START_COLOR
                g2, r2, b2 = SNAKE_GRADIENT_END_COLOR

                interp_g = int(g1 + (g2 - g1) * ratio)
                interp_r = int(r1 + (r2 - r1) * ratio)
                interp_b = int(b1 + (b2 - b1) * ratio)
                np[segment_led_index] = (interp_g, interp_r, interp_b)
            else:
                
                mid_point_idx = (num_gradient_segments - 1) // 2 

                if gradient_index <= mid_point_idx:
                    total_steps_in_phase = mid_point_idx
                    ratio = gradient_index / total_steps_in_phase if total_steps_in_phase > 0 else 0.0

                    g1, r1, b1 = SNAKE_GRADIENT_START_COLOR
                    g2, r2, b2 = SNAKE_GRADIENT_MIDDLE_COLOR
                else:
                    current_idx_in_phase = gradient_index - (mid_point_idx + 1)
                    total_steps_in_phase = (num_gradient_segments - 1) - (mid_point_idx + 1)
                    ratio = current_idx_in_phase / total_steps_in_phase if total_steps_in_phase > 0 else 0.0

                    g1, r1, b1 = SNAKE_GRADIENT_MIDDLE_COLOR
                    g2, r2, b2 = SNAKE_GRADIENT_END_COLOR
                
                interp_g = int(g1 + (g2 - g1) * ratio)
                interp_r = int(r1 + (r2 - r1) * ratio)
                interp_b = int(b1 + (b2 - b1) * ratio)

                np[segment_led_index] = (interp_g, interp_r, interp_b)
    np.write()

def get_joystick_move():
    global direction, last_joystick_move_time
    
    current_time_ms = utime.ticks_ms()
    
    if utime.ticks_diff(current_time_ms, last_joystick_move_time) < JOYSTICK_DEBOUNCE_TIME_MS:
        return direction 

    x_value = joystick_x.read_u16() 
    y_value = joystick_y.read_u16() 

    # Removed debugging print: print(f"X: {x_value}, Y: {y_value} -> Current Direction: {direction}") 

    new_direction = direction 

    is_x_center = abs(x_value - 32767) < CENTER_TOLERANCE
    is_y_center = abs(y_value - 32767) < CENTER_TOLERANCE

    # Apply your hardcoded conditions:

    # UP (Physical Joystick UP) - y_value < 500, x_value approx 32767
    if y_value < 2000 and is_x_center:
        if direction != 'DOWN': # Anti-180-degree turn for visual UP
            new_direction = 'UP' 
    
    # DOWN (Physical Joystick DOWN) - y_value > 65000, x_value approx 32767
    elif y_value > 59000 and is_x_center:
        if direction != 'UP': # Anti-180-degree turn for visual DOWN
            new_direction = 'DOWN' 
            
    # LEFT (Physical Joystick LEFT)
    elif x_value > 59000 and is_y_center:
        if direction != 'RIGHT': 
            new_direction = 'LEFT' 
    
    # RIGHT (Physical Joystick RIGHT)
    elif x_value < 2000 and is_y_center:
        if direction != 'LEFT': 
            new_direction = 'RIGHT' 

    if new_direction != direction:
        last_joystick_move_time = current_time_ms 
        # Removed debugging print: print(f"Direction changed to: {new_direction}") 
    
    return new_direction

# Main game loop - continuously runs in joystick mode
while True:
    print("\n--- Starting Snake Game (Joystick Control) ---")
    print(f"Session High Score: {session_high_score}")
    
    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.printout("JOYSTICK SNAKE") 
    lcd.setCursor(0, 1)
    lcd.printout(f"HIGHSCORE:{session_high_score}")
    utime.sleep(1) 

    # Game initialization
    snake = [(GRID_ROWS // 2, GRID_COLS // 2)]
    direction = 'RIGHT' 
    score = 0
    game_over = False
    place_apple()

    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.printout("SCORE: 0")
    lcd.setCursor(0, 1)
    lcd.printout(f"HIGHSCORE:{session_high_score}")

    while not game_over:
        draw_game()

        new_direction = get_joystick_move()
        direction = new_direction
        
        utime.sleep(GAME_SPEED) 

        head_row, head_col = snake[0]
        dr, dc = possible_deltas[direction]
        new_head_row, new_head_col = head_row + dr, head_col + dc

        # Check for collision with walls
        if not (0 <= new_head_row < GRID_ROWS and 0 <= new_head_col < GRID_COLS):
            game_over = True
            print("Game Over: Hit wall!")
            break

        # Check for self-collision 
        if (new_head_row, new_head_col) in snake[:-1]:
            game_over = True
            print("Game Over: Self-collision!")
            break

        snake.insert(0, (new_head_row, new_head_col))

        if new_head_row == apple_pos[0] and new_head_col == apple_pos[1]:
            score += 1
            place_apple()
            lcd.setCursor(7, 0) 
            lcd.printout(f"{score:<2}") 
        else:
            snake.pop() 

    # Game over sequence
    if score > session_high_score:
        session_high_score = score
        print(f"NEW HIGH SCORE! {session_high_score}")
        
    print(f"Game Over! Your Score: {score}")
    print(f"Session High Score: {session_high_score}")

    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.printout("SCORE:" + str(score))
    lcd.setCursor(0, 1)
    lcd.printout("HIGHSCORE:" + str(session_high_score))

    # Flash LEDs on game over
    for _ in range(5):
        np.fill((0, 100, 0)) 
        np.write()
        utime.sleep(0.1)
        np.fill(BACKGROUND_COLOR) 
        np.write()
        utime.sleep(0.1)

    utime.sleep(1)