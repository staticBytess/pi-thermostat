import dht
from machine import Pin, SPI
from time import sleep
import ssd1306 #OLED display library


# main function to measure room
def thermostat():
    sensor.measure()
    
    temp = (sensor.temperature() * 9/5) + 32
    temp_str = "{:.1f}".format(temp)

    humid = sensor.humidity()
    humid_str = "{:.1f}".format(humid)
    
    displayData(temp_str, humid_str)

#Displays temperature and humidty to OLED screen
def displayData(temp, humid):
    oled.fill(0)
    
    oled.text('Temperature: ', 5, 6, 1)
    oled.text(temp, 5, 16, 1)
    oled.text("Humidity: ", 5, 33, 1)
    oled.text(humid + '%', 5, 43, 1)
    
    progressBar()
    
#Helper function to display the progress bar
def progressBar():
    symbolCount = 8
    delay = .8
    
    for i in range(symbolCount):
        oled.text('*', i*16+5, 58, 1)
        oled.show()
        sleep(delay)



# initialize sensor
sensor = dht.DHT22(Pin(28))

#GPIO declaration for pins on OLED
spi_port = 1
SCK = 10
SDA = 11
RES = 12
DC = 14
CS = 15

spi = SPI(
    spi_port,
    baudrate=1000000,
    mosi=Pin(SDA),
    sck=Pin(SCK))


# Initialize OLED display
width = 128
height = 64

oled = ssd1306.SSD1306_SPI(width,height,
    spi,
    dc = Pin(DC),
    res = Pin(RES),
    cs = Pin(CS),
    external_vcc = False
    )

while (1 == 1):
    thermostat()