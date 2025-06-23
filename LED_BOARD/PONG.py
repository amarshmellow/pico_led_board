import machine
import utime
from machine import Pin
import neopixel
import random

led = Pin(25, Pin.OUT)
led.value(1)
for i in range(3):
    led.value(0)
    utime.sleep(0.1)
    led.value(1)
    utime.sleep(0.1)
led.value(1)

analog_value1 = machine.ADC(26)
# Add a second ADC input for Player 2's joystick
analog_value2 = machine.ADC(28)

np = neopixel.NeoPixel(machine.Pin(11), 50)
beep = Pin(16, Pin.OUT)

GAME_WIDTH = 10
GAME_HEIGHT = 5

PADDLE_LENGTH = 2

LEFT_PADDLE_GAME_X = 0
RIGHT_PADDLE_GAME_X = GAME_WIDTH - 1

BALL_SPEED = 0.11
# AI_REACTION_DELAY is no longer needed as both paddles are player-controlled
SCORE_FLASH_DURATION_MS = 50

# Define colors for different game elements in GRB format (Green, Red, Blue)
PLAYER_PADDLE_1_COLOR = (0, 0, 100)      # Blue color for Player 1 Paddle (left)
PLAYER_PADDLE_2_COLOR = (0, 100, 0)      # Red color for Player 2 Paddle (right)
BALL_COLOR = (100, 100, 0)            # Yellow color for the ball

# Define the observed minimum and maximum ADC values from your joystick.
# Joystick 'up' gives approx 400, Joystick 'down' gives approx 65535.
JOYSTICK_ADC_OBSERVED_MIN = 400
JOYSTICK_ADC_OBSERVED_MAX = 65535

map = [[0,1,2,3,4],
       [9,8,7,6,5],
       [10,11,12,13,14],
       [19,18,17,16,15],
       [20,21,22,23,24],
       [29,28,27,26,25],
       [30,31,32,33,34],
       [39,38,37,36,35],
       [40,41,42,43,44],
       [49,48,47,46,45]]

player_paddle_1_y = GAME_HEIGHT // 2 - PADDLE_LENGTH // 2
player_paddle_2_y = GAME_HEIGHT // 2 - PADDLE_LENGTH // 2 # Renamed from ai_paddle_y

ball_x = GAME_WIDTH // 2
ball_y = GAME_HEIGHT // 2

ball_dx = random.choice([-1, 1])
ball_dy = random.choice([-1, 1])

player_1_score = 0 # Renamed from player_score
player_2_score = 0 # Renamed from ai_score

np.fill((0,0,0))
np.write()
beep.value(0)

while True:
    # 1. Read Joystick Input for Player 1 Paddle Control
    reading1 = analog_value1.read_u16() 
    
    clamped_reading1 = max(JOYSTICK_ADC_OBSERVED_MIN, min(reading1, JOYSTICK_ADC_OBSERVED_MAX))
    effective_adc_range = JOYSTICK_ADC_OBSERVED_MAX - JOYSTICK_ADC_OBSERVED_MIN
    
    if effective_adc_range == 0:
        player_paddle_1_y_raw = GAME_HEIGHT // 2 - PADDLE_LENGTH // 2
    else:
        player_paddle_1_y_raw = round(
            (JOYSTICK_ADC_OBSERVED_MAX - clamped_reading1) / effective_adc_range * (GAME_HEIGHT - PADDLE_LENGTH)
        )
    
    player_paddle_1_y = max(0, min(player_paddle_1_y_raw, GAME_HEIGHT - PADDLE_LENGTH))

    # --- Debugging Output for Player 1 Joystick ---
    print(f"P1 Raw ADC: {reading1:5d}, P1 Clamped Paddle Y: {player_paddle_1_y:2d}")
    # --- End Debugging Output ---

    # 2. Read Joystick Input for Player 2 Paddle Control
    reading2 = analog_value2.read_u16() 
    
    clamped_reading2 = max(JOYSTICK_ADC_OBSERVED_MIN, min(reading2, JOYSTICK_ADC_OBSERVED_MAX))
    
    if effective_adc_range == 0: # Use the same effective range calculated from player 1's joystick
        player_paddle_2_y_raw = GAME_HEIGHT // 2 - PADDLE_LENGTH // 2
    else:
        # Player 2's joystick likely also needs inversion, assuming identical joystick type
        player_paddle_2_y_raw = round(
            (JOYSTICK_ADC_OBSERVED_MAX - clamped_reading2) / effective_adc_range * (GAME_HEIGHT - PADDLE_LENGTH)
        )

    player_paddle_2_y = max(0, min(player_paddle_2_y_raw, GAME_HEIGHT - PADDLE_LENGTH))

    # --- Debugging Output for Player 2 Joystick ---
    print(f"P2 Raw ADC: {reading2:5d}, P2 Clamped Paddle Y: {player_paddle_2_y:2d}")
    # --- End Debugging Output ---

    next_ball_x = ball_x + ball_dx
    next_ball_y = ball_y + ball_dy

    if next_ball_y < 0:
        next_ball_y = 0
        ball_dy *= -1
    elif next_ball_y >= GAME_HEIGHT:
        next_ball_y = GAME_HEIGHT - 1
        ball_dy *= -1

    # Collision with Player 1 Paddle (Left side of the screen)
    if next_ball_x <= LEFT_PADDLE_GAME_X:
        if player_paddle_1_y <= next_ball_y < (player_paddle_1_y + PADDLE_LENGTH):
            ball_dx *= -1
            next_ball_x = LEFT_PADDLE_GAME_X + 1
            
            hit_point_relative = next_ball_y - player_paddle_1_y
            if hit_point_relative == 0:
                ball_dy = -1
            elif hit_point_relative == PADDLE_LENGTH - 1:
                ball_dy = 1
        else:
            # Ball missed Player 1 Paddle - Player 2 scores a point!
            player_2_score += 1
            
            np.fill(PLAYER_PADDLE_2_COLOR) # Flash Player 2's color
            np.write()
            utime.sleep_ms(SCORE_FLASH_DURATION_MS)
            np.fill((0,0,0))
            
            ball_x = GAME_WIDTH // 2
            ball_y = GAME_HEIGHT // 2
            ball_dx = random.choice([-1, 1])
            ball_dy = random.choice([-1, 1])
            next_ball_x = ball_x
            next_ball_y = ball_y

    # Collision with Player 2 Paddle (Right side of the screen)
    elif next_ball_x >= RIGHT_PADDLE_GAME_X:
        if player_paddle_2_y <= next_ball_y < (player_paddle_2_y + PADDLE_LENGTH):
            ball_dx *= -1
            next_ball_x = RIGHT_PADDLE_GAME_X - 1
            
            hit_point_relative = next_ball_y - player_paddle_2_y
            if hit_point_relative == 0:
                ball_dy = -1
            elif hit_point_relative == PADDLE_LENGTH - 1:
                ball_dy = 1
        else:
            # Ball missed Player 2 Paddle - Player 1 scores a point!
            player_1_score += 1
            
            np.fill(PLAYER_PADDLE_1_COLOR) # Flash Player 1's color
            np.write()
            utime.sleep_ms(SCORE_FLASH_DURATION_MS)
            np.fill((0,0,0))
            
            ball_x = GAME_WIDTH // 2
            ball_y = GAME_HEIGHT // 2
            ball_dx = random.choice([-1, 1])
            ball_dy = random.choice([-1, 1])
            next_ball_x = ball_x
            next_ball_y = ball_y

    ball_x = next_ball_x
    ball_y = next_ball_y

    np.fill((0, 0, 0))

    # Draw Player 1 Paddle
    for i in range(PADDLE_LENGTH):
        if 0 <= LEFT_PADDLE_GAME_X < GAME_WIDTH and 0 <= (player_paddle_1_y + i) < GAME_HEIGHT:
            np[map[LEFT_PADDLE_GAME_X][player_paddle_1_y + i]] = PLAYER_PADDLE_1_COLOR

    # Draw Player 2 Paddle
    for i in range(PADDLE_LENGTH):
        if 0 <= RIGHT_PADDLE_GAME_X < GAME_WIDTH and 0 <= (player_paddle_2_y + i) < GAME_HEIGHT:
            np[map[RIGHT_PADDLE_GAME_X][player_paddle_2_y + i]] = PLAYER_PADDLE_2_COLOR

    if 0 <= ball_x < GAME_WIDTH and 0 <= ball_y < GAME_HEIGHT:
        np[map[ball_x][ball_y]] = BALL_COLOR

    np.write()

    utime.sleep(BALL_SPEED)
