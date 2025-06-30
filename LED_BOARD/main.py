import machine
import utime 
from machine import Pin
import neopixel
import random
import LCD1602
import json

from machine import Pin, Timer
led = Pin(25, Pin.OUT)

led.value(1)

for i in range(3):
    led.value(0)
    utime.sleep(0.1)
    led.value(1)
    utime.sleep(0.1)
    
led.value(1)


analog_value1 = machine.ADC(26)
analog_value2 = machine.ADC(27)
np = neopixel.NeoPixel(machine.Pin(11), 50)
button = Pin(8, Pin.IN, Pin.PULL_UP)
beep = Pin(16, Pin.OUT)
#selectedmap[user1][user2] = random.randomint(0,49) 

lcd = LCD1602.LCD1602(16,2)

target = random.randint(0,49)
wintimer = 5
losetimer = 150
LEDSGOT = 0

def write_scores():
    global scores
    with open('scores.json', 'w') as f:
        json.dump(scores, f)
        
def read_scores():
    global scores
    with open('scores.json') as f:
        scores = json.load(f)
        
read_scores()

lcd.print_lcd("SCORE:" + str(LEDSGOT))
lcd.setCursor(0,1)
lcd.printout("HIGH SCORE:" + str(scores["hi-score"]))

beep.value(0)

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

np.fill((0,0,0))
np.write()

#np[map[2][2]] = (122,0,0)

#np.write()


# while True:
#     np.fill((0,0,0))
#     np.write()
#     reading1 = analog_value1.read_u16()
#     reading2 = analog_value2.read_u16()
#     user1 = (65535-reading1) // 6554
#     user2 = (65535-reading2) // 13108
#     np[map[5][user2]] = (122,0,0)
#     np.write()
#     print("user1:", reading1, "user2:", reading2, "button:", button.value())
#     utime.sleep(0.2)

# BUTTONS =  BLUE, YELLOW, WHITE, RED, GREEN, BLACK

# FUNCTIONS = SCREENSAVER, DEV MENU, PONG, RESTART MAIN.PY, SNAKE, SET SCORES.JSON TO 0
inputs = [
    Pin(6, Pin.IN, Pin.PULL_UP),  # ARRAY 0, BLUE 
    Pin(7, Pin.IN, Pin.PULL_UP),  # ARRAY 1, BLACK 
    Pin(9, Pin.IN, Pin.PULL_UP),  # ARRAY 2, YELLOW
    Pin(10, Pin.IN, Pin.PULL_UP), # ARRAY 3, GREEN
    Pin(18, Pin.IN, Pin.PULL_UP), # ARRAY 4, WHITE
    Pin(19, Pin.IN, Pin.PULL_UP)  # ARRAY 5, RED
]

while True:
    
    target = random.randint(0,49)
    wintimer = 5
    losetimer = 150
    LEDSGOT = 0
    
    while button.value() == 1:
        if inputs[1].value() == 0: # IF BLACK PRESSED, HIGHSCORE = 0
            scores["hi-score"] = 0
            write_scores()
            lcd.clear()
            lcd.setCursor(0,0)
            lcd.printout("HIGH SCORE = 0")
        pass
    
    while True:
        if inputs[5].value() == 0: # IF RED PRESSED, BREAK MAIN GAME LOOP
            break
        printtimer = losetimer //5
        lcd.setCursor(0,0)
        lcd.print_lcd("SCORE:" + str(LEDSGOT))
        lcd.setCursor(0,1)
        lcd.printout("HIGH SCORE:" + str(scores["hi-score"]))
        lcd.setCursor(14,0)
        lcd.printout(f"{printtimer:02d}")
        
        reading1 = analog_value1.read_u16()
        reading2 = analog_value2.read_u16()
        
        user1 = (65535-reading1) // 6554
        user2 = (65535-reading2) // 13108
        
        np.fill((0,0,0))
        
        np[target] = (122, 0, 0)
        
        np[map[user1][user2]] = (0, 0, 122)
        
        if map[user1][user2] == target:
                    if wintimer == 0:
                        
                        oldtarget = target
                        
                        while target == oldtarget:
                            target = random.randint(0,49)
                            
                        LEDSGOT = LEDSGOT + 1
                        beep.value(1)
                        np.fill((10,10,10))
                        np.write()
                        utime.sleep(0.05)
                        beep.value(0)
                        np.fill((0,0,0))
                        np.write()
                        lcd.print_lcd("SCORE:" + str(LEDSGOT))
                        lcd.setCursor(0,1)
                        lcd.printout("HIGH SCORE:" + str(scores["hi-score"]))
                    else:
                        wintimer = wintimer - 1
        else:
            wintimer = 5

        if map[user1][user2] != target:
            wintimer = 5
                
        losetimer = losetimer - 1
            
        if losetimer <= 0:
            beep.value(1)
            np.fill((0,100,0))
            utime.sleep(0.1)
            beep.value(0)
        
        if losetimer <= -5:
            break
        
        #print("Time until next LED:", wintimer, " Time until loss:", losetimer, " Leds got:",LEDSGOT)
        np.write()
        utime.sleep(0.2)

    if LEDSGOT > scores["hi-score"]:
        scores["hi-score"] = LEDSGOT
        write_scores()
        lcd.print_lcd("SCORE:" + str(LEDSGOT))
        lcd.setCursor(0,1)
        lcd.printout("HIGH SCORE:" + str(LEDSGOT))




    np.fill((0,0,0))
    np.write()
    beep.value(0)


beep.value(0)
