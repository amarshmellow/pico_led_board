import LCD1602
import random
import utime

lcd = LCD1602.LCD1602(16,2)

while True:
    lcd.print_lcd("The number pick")
    lcd.setCursor(0,1)
    lcd.printout("is:" + str(random.randint(0,49)))
    utime.sleep(0.50) 
    
