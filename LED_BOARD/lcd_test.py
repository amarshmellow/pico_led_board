import LCD1602
import random
import utime
from machine import Pin,I2C

# device I2C pins
LCD1602_SDA = Pin(4)
LCD1602_SCL = Pin(5)

LCD1602_I2C = I2C(0,sda = LCD1602_SDA,scl = LCD1602_SCL ,freq = 400000)

print(LCD1602_I2C.scan())

utime.sleep(10)

lcd = LCD1602.LCD1602(16,2)

while True:
    lcd.print_lcd("The number pick")
    lcd.setCursor(0,1)
    lcd.printout("is:" + str(random.randint(0,49)))
    utime.sleep(0.50) 
    
