#!/usr/bin/python
# -*- coding: UTF-8 -*-
#import chardet
import sys 
import time
from datetime import datetime, timedelta
import logging
import subprocess
import requests
import board
import adafruit_dht
sys.path.append("..")
from lib import LCD_1inch69,Touch_1inch69
from PIL import Image,ImageDraw,ImageFont

# Set the GPIO pin
dht_device = adafruit_dht.DHT22(board.D23, use_pulseio=False)

# Raspberry Pi BCM pin configuration:
RST = 27
DC = 25
BL = 18
TP_INT = 4
TP_RST = 17

Mode = 0
logging.basicConfig(level=logging.DEBUG)
global Flag

def getPublicIp():
    try:
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


def getIpInfo(ipAddress, ipApiKey):
    url = f"https://api.ipregistry.co/{ipAddress}?key={ipApiKey}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
    
def getLocationInfo(ipInfo):
    return ipInfo['location']['city'], ipInfo['location']['region']['name'], ipInfo['location']['latitude'],ipInfo['location']['longitude'] 

def getIndoorTemp():
    
    counter=0
    
    while True:
        try:
            # Try to get a sensor reading
            temp = dht_device.temperature
            #humid = dht_device.humidity
            
            
            if temp is not None:
                temp = f"{temp *9/5 + 32: .1f}"
                #humid = f"{humid: .1f}"
                return temp #, humid
            else:
                counter +=1
                print('Failed to get reading. Try again!' + str(counter) )

        except RuntimeError as error:
            time.sleep(0.01)
            
    
def getOutdoorTemp():

    response = requests.get(weatherURL)
  
    if response.status_code == 200:
        data = response.json()  # Use .json() to directly parse JSON response
       
        if 'data' in data and len(data['data']) > 0:
            temp = data['data'][0]['temp']
            temp = f"{temp *9/5 + 32: .2f}"
            print("The temperature is: " + temp + "°F")
            return temp
        
        else:
            print("Temperature data not found in the response.")
            response.close()
            
    else:
        print("Failed to retrieve temperature data. Status code:", response.status_code)
        return None
    
def getCpuTemp():
    result = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
    temp_str = result.stdout.decode('utf-8')
    temp_value = temp_str.split('=')[1].split('\'')[0]
    return float(temp_value)

touch = Touch_1inch69.Touch_1inch69()

def Int_Callback(TP_INT):       
    global Flag  
    if Mode == 1:       
        Flag = 1
        touch.get_point()
        
    elif Mode == 2:
        Flag = 1
        touch.Gestures = touch.Touch_Read_Byte(0x01)
        touch.get_point()
    else:
        touch.Gestures = touch.Touch_Read_Byte(0x01)
        
def screenStart():
    ''' Warning!!!Don't  creation of multiple displayer objects!!! '''
    disp = LCD_1inch69.LCD_1inch69(rst = RST,dc = DC,bl = BL,tp_int = TP_INT,tp_rst = TP_RST,bl_freq=1000)
    # Initialize library.
    disp.Init()
    # Clear display.
    disp.clear()
    disp.bl_DutyCycle(0)
    return disp
    
def showTemp():
    disp = screenStart()
    touch.init()
    touch.GPIO_TP_INT.when_pressed = Int_Callback
    counter = 0
    loadInterval = 70
    showLoading = True

    # Create blank image for drawing.
    # Common HTML color names.
    image1 = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image1)
    draw.rectangle((0,0,240,300),fill = "BLACK", outline=None, width=1)
    
    #set mode to Gesture
    Mode = 0
    touch.Set_Mode(Mode)
    
    #define fonts
    Font = ImageFont.truetype("./Font/Font00.ttf",24)
    fontLarge = ImageFont.truetype("./Font/Font02.ttf",35)
    fontMed = ImageFont.truetype("./Font/Font00.ttf",30)
    fontSmall = ImageFont.truetype("./Font/Font00.ttf",18)
    
    draw.rectangle((0,0,240,240),fill = "BLACK", outline=None, width=1)
    
    lastChecked = datetime.now()
    outdoorTemp = getOutdoorTemp()
    cpuTemp = getCpuTemp()
    
    
    while True:
        backlightOn = 40 #backlight brightness (80 is max)
        backlightOff = 0 
        apiTimer = 12 #how many minutes to wait before calling api
        screenTimer = 100 #how many seconds to wait before shutting screen off
        lastActive = datetime.now() #time when user last interacted with screen
        screenOn = True #state of screen, True = on, False = off
        
        #define Gestures
        longPress = 0x0C
        swipeDown = 0x01
        swipeUp   = 0x02
        swipeRight= 0x04
        swipeLeft = 0x03
        
        disp.bl_DutyCycle(backlightOn) #turns screen on
       
       #Main Page
        while touch.Gestures != swipeLeft:
            inactiveTime = datetime.now() - lastActive
            
            #turns display off after being inactive
            if inactiveTime >= timedelta(seconds= screenTimer):
                disp.bl_DutyCycle(backlightOff)
                screenOn = False
            
            #turns screen off when user does specified gesture
            if screenOn and touch.Gestures == swipeDown :
                    disp.bl_DutyCycle(backlightOff)
                    screenOn = False
            
            #turns screen on when user does specifed gesture
            elif not screenOn and touch.Gestures == longPress:
                    lastActive = datetime.now()
                    disp.bl_DutyCycle(backlightOn)
                    screenOn = True
                
            currentTime = datetime.now() 
            timePassed = currentTime - lastChecked
            minutesPassed = int(timePassed.total_seconds()/60)
                    
            if timePassed >= timedelta(minutes = apiTimer):
                outdoorTemp = getOutdoorTemp()
                lastChecked = datetime.now()
                
            
            indoorTemp = getIndoorTemp()
            draw.rectangle((0,0,240,300),fill = "BLACK", outline=None, width=1)
            draw.text((10, 20), 'Indoor ', fill = "WHITE",font=fontMed)
            draw.text((10, 50), 'Temperature: ', fill = "WHITE",font=fontMed)
            draw.text((15, 85), indoorTemp + ' °', fill = "WHITE",font=fontLarge)
            
            if showLoading:
                draw.text((200, 20), '°', fill = "WHITE",font=fontLarge)
            
            draw.text((10, 120), 'Outdoor ', fill = "WHITE",font=fontMed)
            draw.text((13, 150), 'Temperature: ', fill = "WHITE",font=fontMed)
            draw.text((15, 190), outdoorTemp + ' °', fill = "WHITE",font=fontLarge)
            
            draw.text((15, 235), 'Updated: ', fill = "WHITE",font=fontSmall)
            draw.text((110, 235), str(minutesPassed) + ' mins ago', fill = "WHITE",font=fontSmall)
            
            counter += 1
            if counter > loadInterval:
                counter = 0
                if showLoading:
                    showLoading = False
                else:
                    showLoading = True
    
            disp.ShowImage(image1)
            time.sleep(0.01)
        
        lastActive = datetime.now()
        screenOn = True
        disp.bl_DutyCycle(backlightOn)
        
    #OUTDOOR TEMPERATURE
        while touch.Gestures != swipeRight:
            inactiveTime = datetime.now() - lastActive
            
            if inactiveTime >= timedelta(seconds= screenTimer):
                disp.bl_DutyCycle(backlightOff)
                screenOn = False
            
            if screenOn and touch.Gestures == swipeDown:
                    disp.bl_DutyCycle(backlightOff)
                    screenOn = False
            elif not screenOn and touch.Gestures == longPress:
                    lastActive = datetime.now()
                    disp.bl_DutyCycle(backlightOn)
                    screenOn = True
                
            draw.rectangle((0,0,240,300),fill = "BLACK", outline=None, width=1)
            draw.text((10, 30), 'Your Location: ', fill = "WHITE",font=fontMed)
            draw.text((13, 60), f'{city}', fill = "WHITE",font=fontMed)
            currentTime = datetime.now()
            timePassed = currentTime - lastChecked
            minutesPassed = int(timePassed.total_seconds()/60)
            
            cpuTemp = getCpuTemp()
            draw.text((10, 110), 'CPU Temp: ', fill = "WHITE",font=fontMed)
            draw.text((30, 145), str(cpuTemp) + "°C", fill = "WHITE",font=fontMed)
            
            disp.ShowImage(image1)
               
            time.sleep(0.01)

ipAddress = getPublicIp()
ipApiKey = 'insertIpRegistrykey'

ipInfo = getIpInfo(ipAddress, ipApiKey)

if ipAddress:
    print(f"Your public IP address is: {ipAddress}")
else:
    print("Failed to retrieve public IP address")

if ipInfo:
    print("IP Info:")
    print(f"IP Address: {ipInfo['ip']}")
    print(f"Location: {ipInfo['location']['city']}, {ipInfo['location']['region']['name']}, {ipInfo['location']['country']['name']}")
    print(f"Latitude: {ipInfo['location']['latitude']}")
    print(f"Longitude: {ipInfo['location']['longitude']}")
else:
    print("Failed to retrieve IP info")

city, state, latitude, longitude = getLocationInfo(ipInfo)
apiKey = "enterWeatherbitApiKey"
    
weatherURL = f"https://api.weatherbit.io/v2.0/current?lat={latitude}&lon={longitude}&key={apiKey}"

showTemp()