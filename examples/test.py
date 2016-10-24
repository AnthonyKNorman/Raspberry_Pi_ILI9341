# Author: Tony Norman - 2016
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import ili9341
import time
from PIL import Image, ImageFont, ImageDraw

# Raspberry Pi configuration.
DC = 18
RST = 23
SPI_PORT = 0
SPI_DEVICE = 0
	
# Create TFT LCD display class.
disp = ili9341.ili9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

# Initialize display.
disp.begin()

# set the rgb values for the background color

disp._bground = ili9341.color565(0,0,0)

# foreground color
disp._color = ili9341.color565(0,0,255)

# clear the screen
disp.fill_screen(disp._bground)

# display image at x, y
img = Image.open('/home/pi/python/flower240x320.png')
disp.p_image(0, 0, img)
time.sleep(5)

disp._bground = ili9341.color565(255,255,255)
# make an image object the size of the screen
img = Image.new('RGB', (disp.width, disp.height), ili9341.color_rgb(disp._bground))
# make a draw object
draw = ImageDraw.Draw(img)

# set the circle centre to the middle of the screen
x = disp.width/2
y = disp.height/2

# set radius
r = disp.width/2
# draw a filled blue circle on the image
draw.ellipse((x-r, y-r, x+r, y+r), fill=(0,36,125,0))
# display the image
disp.p_image(0, 0, img)

# set radius
r = disp.width/3
# draw a filled white circle on the image
draw.ellipse((x-r, y-r, x+r, y+r), fill=(255,255,255,0))
# display the image
disp.p_image(0, 0, img)

# set radius
r = disp.width/6
# draw a filled red circle on the image
draw.ellipse((x-r, y-r, x+r, y+r), fill=(206,17,38,0))
# display the image
disp.p_image(0, 0, img)
time.sleep(5)

# set the background color
disp._bground = ili9341.color565(0,0,255)
# fill the screen
disp.fill_screen(disp._bground)

# set the true-type font
disp._font = ImageFont.truetype('Lekton-Regular.ttf', 24)

# set the font color
disp._color = ili9341.color565(0,0,0)
# get some text in an image
img, width, height = disp.text('The quick brown fox')
# display the image at the top of the screen
disp.p_image(0, 0, img)

# set the font color
disp._color = ili9341.color565(255,0,0)
# get some text in an image
img, width, height = disp.text('The quick brown fox')
# display the image at the top of the screen
disp.p_image(0, 30, img)

# set the font color
disp._color = ili9341.color565(255,255,0)
# get some text in an image
img, width, height = disp.text('The quick brown fox')
# display the image at the top of the screen
disp.p_image(0, 60, img)

# set the font color
disp._color = ili9341.color565(255,255,255)
# get some text in an image
img, width, height = disp.text('The quick brown fox')
# display the image at the top of the screen
disp.p_image(0, 90, img)
time.sleep(5)

# set the background color
disp._bground = ili9341.color565(0,0,0)
# fill the screen
disp.fill_screen(disp._bground)

disp._color = ili9341.color565(255,255,255)
# set the true-type font
# get the current date in an image
img, width, height = disp.text(time.strftime('%a %d %b'), angle = 0)
# display the image at the top of the screen
disp.p_image((disp.width-width)/2, 0, img)

img = img.rotate(90)
disp.p_image(0, (disp.height - width)/2, img)

img = img.rotate(90)
disp.p_image((disp.width-width)/2, disp.height - height, img)

img = img.rotate(90)
disp.p_image(disp.width-height, (disp.height - width)/2, img)



