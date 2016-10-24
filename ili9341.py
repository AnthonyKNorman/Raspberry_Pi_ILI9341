# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
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
import numbers
import time
import numpy as np

from PIL import Image, ImageDraw, ImageFont

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

# Constants for interacting with display registers.
ILI9341_TFTWIDTH    = 240
ILI9341_TFTHEIGHT   = 320

ILI9341_NOP         = 0x00
ILI9341_SWRESET     = 0x01
ILI9341_RDDID       = 0x04
ILI9341_RDDST       = 0x09

ILI9341_SLPIN       = 0x10
ILI9341_SLPOUT      = 0x11
ILI9341_PTLON       = 0x12
ILI9341_NORON       = 0x13

ILI9341_RDMODE      = 0x0A
ILI9341_RDMADCTL    = 0x0B
ILI9341_RDPIXFMT    = 0x0C
ILI9341_RDIMGFMT    = 0x0A
ILI9341_RDSELFDIAG  = 0x0F

ILI9341_INVOFF      = 0x20
ILI9341_INVON       = 0x21
ILI9341_GAMMASET    = 0x26
ILI9341_DISPOFF     = 0x28
ILI9341_DISPON      = 0x29

ILI9341_CASET       = 0x2A
ILI9341_PASET       = 0x2B
ILI9341_RAMWR       = 0x2C
ILI9341_RAMRD       = 0x2E

ILI9341_PTLAR       = 0x30
ILI9341_MADCTL      = 0x36
ILI9341_PIXFMT      = 0x3A

ILI9341_FRMCTR1     = 0xB1
ILI9341_FRMCTR2     = 0xB2
ILI9341_FRMCTR3     = 0xB3
ILI9341_INVCTR      = 0xB4
ILI9341_DFUNCTR     = 0xB6

ILI9341_PWCTR1      = 0xC0
ILI9341_PWCTR2      = 0xC1
ILI9341_PWCTR3      = 0xC2
ILI9341_PWCTR4      = 0xC3
ILI9341_PWCTR5      = 0xC4
ILI9341_VMCTR1      = 0xC5
ILI9341_VMCTR2      = 0xC7

ILI9341_RDID1       = 0xDA
ILI9341_RDID2       = 0xDB
ILI9341_RDID3       = 0xDC
ILI9341_RDID4       = 0xDD

ILI9341_GMCTRP1     = 0xE0
ILI9341_GMCTRN1     = 0xE1

ILI9341_PWCTR6      = 0xFC

ILI9341_BLACK       = 0x0000
ILI9341_BLUE        = 0x001F
ILI9341_RED         = 0xF800
ILI9341_GREEN       = 0x07E0
ILI9341_CYAN        = 0x07FF
ILI9341_MAGENTA     = 0xF81F
ILI9341_YELLOW      = 0xFFE0
ILI9341_WHITE       = 0xFFFF


def color565(r, g, b):
	"""Convert red, green, blue components to a 16-bit 565 RGB value. Components
	should be values 0 to 255.
	"""
	return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def color_rgb(color):
	"""Convert 565 color format to rgb - return tuple"""
	r = (color >> 8) & 0xf8
	g = ((color >> 5) & 0x3f) << 2
	b = (color & 0x1f) << 3
	return (r,g,b)

class ili9341(object):
	"""Representation of an ILI9341 TFT LCD."""

	def __init__(self, dc, spi, rst=None, gpio=None, width=ILI9341_TFTWIDTH,
		height=ILI9341_TFTHEIGHT):
		"""Create an instance of the display using SPI communication.  Must
		provide the GPIO pin number for the D/C pin and the SPI driver.  Can
		optionally provide the GPIO pin number for the reset pin as the rst
		parameter.
		"""
		self._dc = dc
		self._rst = rst
		self._spi = spi
		self._gpio = gpio
		self.width = width
		self.height = height
		if self._gpio is None:
		    self._gpio = GPIO.get_platform_gpio()
		# Set DC as output.
		self._gpio.setup(dc, GPIO.OUT)
		# Setup reset as output (if provided).
		if rst is not None:
		    self._gpio.setup(rst, GPIO.OUT)
		# Set SPI to mode 0, MSB first.
		spi.set_mode(0)
		spi.set_bit_order(SPI.MSBFIRST)
		spi.set_clock_hz(64000000)
		# Create an image buffer.
		self.buffer = bytearray(width*height*2)
		self._row = 0
		self._col = 0
		self._color = 0
		self._bground = 0xf100
		self._font = ImageFont.truetype('Lekton-Regular.ttf', 60)


	def send(self, data, is_data=True, chunk_size=4096):
		"""Write a byte or array of bytes to the display. Is_data parameter
		controls if byte should be interpreted as display data (True) or command
		data (False).  Chunk_size is an optional size of bytes to write in a
		single SPI transaction, with a default of 4096.
		"""
		# Set DC low for command, high for data.
		self._gpio.output(self._dc, is_data)
		# Convert scalar argument to list so either can be passed as parameter.
		if isinstance(data, numbers.Number):
		    data = [data & 0xFF]
		# Write data a chunk at a time.
		for start in range(0, len(data), chunk_size):
		    end = min(start+chunk_size, len(data))
		    self._spi.write(data[start:end])

	def command(self, data):
		"""Write a byte or array of bytes to the display as command data."""
		self.send(data, False)

	def data(self, data):
		"""Write a byte or array of bytes to the display as display data."""
		self.send(data, True)

	def reset(self):
		"""Reset the display, if reset pin is connected."""
		if self._rst is not None:
		    self._gpio.set_high(self._rst)
		    time.sleep(0.005)
		    self._gpio.set_low(self._rst)
		    time.sleep(0.02)
		    self._gpio.set_high(self._rst)
		    time.sleep(0.150)

	def _init(self):
		# Initialize the display.  Broken out as a separate function so it can
		# be overridden by other displays in the future.
		self.command(0xEF)
		self.data(0x03)
		self.data(0x80)
		self.data(0x02)
		self.command(0xCF)
		self.data(0x00)
		self.data(0XC1)
		self.data(0X30)
		self.command(0xED)
		self.data(0x64)
		self.data(0x03)
		self.data(0X12)
		self.data(0X81)
		self.command(0xE8)
		self.data(0x85)
		self.data(0x00)
		self.data(0x78)
		self.command(0xCB)
		self.data(0x39)
		self.data(0x2C)
		self.data(0x00)
		self.data(0x34)
		self.data(0x02)
		self.command(0xF7)
		self.data(0x20)
		self.command(0xEA)
		self.data(0x00)
		self.data(0x00)
		self.command(ILI9341_PWCTR1)    # Power control
		self.data(0x23)                    # VRH[5:0]
		self.command(ILI9341_PWCTR2)    # Power control
		self.data(0x10)                    # SAP[2:0];BT[3:0]
		self.command(ILI9341_VMCTR1)    # VCM control
		self.data(0x3e)
		self.data(0x28)
		self.command(ILI9341_VMCTR2)    # VCM control2
		self.data(0x86)                    # --
		self.command(ILI9341_MADCTL)    #  Memory Access Control
		self.data(0x48)
		self.command(ILI9341_PIXFMT)
		self.data(0x55)
		self.command(ILI9341_FRMCTR1)
		self.data(0x00)
		self.data(0x18)
		self.command(ILI9341_DFUNCTR)    #  Display Function Control
		self.data(0x08)
		self.data(0x82)
		self.data(0x27)
		self.command(0xF2)                #  3Gamma Function Disable
		self.data(0x00)
		self.command(ILI9341_GAMMASET)    # Gamma curve selected
		self.data(0x01)
		self.command(ILI9341_GMCTRP1)    # Set Gamma
		self.data(0x0F)
		self.data(0x31)
		self.data(0x2B)
		self.data(0x0C)
		self.data(0x0E)
		self.data(0x08)
		self.data(0x4E)
		self.data(0xF1)
		self.data(0x37)
		self.data(0x07)
		self.data(0x10)
		self.data(0x03)
		self.data(0x0E)
		self.data(0x09)
		self.data(0x00)
		self.command(ILI9341_GMCTRN1)    # Set Gamma
		self.data(0x00)
		self.data(0x0E)
		self.data(0x14)
		self.data(0x03)
		self.data(0x11)
		self.data(0x07)
		self.data(0x31)
		self.data(0xC1)
		self.data(0x48)
		self.data(0x08)
		self.data(0x0F)
		self.data(0x0C)
		self.data(0x31)
		self.data(0x36)
		self.data(0x0F)
		self.command(ILI9341_SLPOUT)    # Exit Sleep
		time.sleep(0.120)
		self.command(ILI9341_DISPON)    # Display on

	def begin(self):
		"""Initialize the display.  Should be called once before other calls that
		interact with the display are called.
		"""
		self.reset()
		self._init()

	def set_window(self, x0=0, y0=0, x1=None, y1=None):
		"""Set the pixel address window for proceeding drawing commands. x0 and
		x1 should define the minimum and maximum x pixel bounds.  y0 and y1
		should define the minimum and maximum y pixel bound.  If no parameters
		are specified the default will be to update the entire display from 0,0
		to 239,319.
		"""
		if x1 is None:
			x1 = self.width-1
		if y1 is None:
			y1 = self.height-1
		self.command(ILI9341_CASET)		# Column addr set
		self.data(x0 >> 8)
		self.data(x0)				    # XSTART
		self.data(x1 >> 8)
		self.data(x1)				    # XEND
		self.command(ILI9341_PASET)		# Row addr set
		self.data(y0 >> 8)
		self.data(y0)				    # YSTART
		self.data(y1 >> 8)
		self.data(y1)                    # YEND
		self.command(ILI9341_RAMWR)        # write to RAM

		
	def pixel(self, x, y, color):
		"""Set an individual pixel to color"""
		if(x < 0) or (x >= self.width) or (y < 0) or (y >= self.height):
			return
		self.set_window(x,y,x+1,y+1)
		b=[color>>8, color & 0xff]
		self.data(b)
		
	def draw_block(self,x,y,w,h,color):
		"""Draw a solid block of color"""
		if((x >= self.width) or (y >= self.height)):
			return
		if (x + w - 1) >= self.width:
			w = self.width  - x
		if (y + h - 1) >= self.height:
			h = self.height - y
		self.set_window(x,y,x+w-1,y+h-1);
		b=[color>>8, color & 0xff]*w*h
		self.data(b)

	def draw_bmp(self,x,y,w,h,buff):
		"""Draw the contents of buff on the screen"""
		if((x >= self.width) or (y >= self.height)):
			return
		if (x + w - 1) >= self.width:
			w = self.width  - x
		if (y + h - 1) >= self.height:
			h = self.height - y
		self.set_window(x,y,x+w-1,y+h-1);
		self.data(buff)

	def fill_screen(self,color):
		"""Fill the whole screen with color"""
		self.draw_block(0,0,self.width,self.height,color)
		
	def p_char(self, ch):
		"""Print a single char at the location determined by globals row and color
			row and col will be auto incremented to wrap horizontally and vertically"""
		fp = (ord(ch)-0x20) * 5
		f = open('/home/pi/python/lib/font5x7.fnt','rb')
		f.seek(fp)
		b = f.read(5)
		char_buf = bytearray(b)
		char_buf.extend([0])

		# make 8x6 image
		char_image = []
		for bit in range(8):
			for x in range (6):
				if ((char_buf[x]>>bit) & 1)>0:
					char_image.extend([self._color >> 8])
					char_image.extend([self._color & 0xff])
				else:
					char_image.extend([self._bground >> 8])
					char_image.extend([self._bground & 0xff])
		x = self._col*6+1
		y = self._row*8+1
		
		self.set_window(x,y,x+5,y+7)
		self.data(char_image)
				
		self._col += 1
		if (self._col>30):
			self._col = 0
			self._row += 1
			if (self._row>40):
				self._row = 0

	def p_string(self, str):
		"""Print a string at the location determined by row and char"""
		for ch in (str):
			self.p_char(ch)
				
	def p_image(self, x, y, img):
		img = img.convert('RGB')
		w, h = img.size
		z = img.getdata()
		img_buf = []
		for pixel in (z):
			r,g,b = pixel
			rgb = color565(r,g,b)
			img_buf.extend([rgb >> 8])
			img_buf.extend([rgb & 0xff])
		self.draw_bmp(x,y,w,h,img_buf)
		
	def text(self, text, align='left', angle=0):
		# make a new square image the size of the display height
		# to allow rotated text to be as wide as the height
		img = Image.new('RGB', (self.height, self.height), color_rgb(self._bground))
		# make the draw object
		draw = ImageDraw.Draw(img)
		# get the width and height of the text image
		width, height = draw.textsize(text, font=self._font)
		# draw the text into the image
		draw.text((0,0),text,font=self._font,fill=color_rgb(self._color))
		# crop the image to the size of the text
		img=img.crop((0,0,width,height))
		# rotate the image
		img = img.rotate(angle)
		# return the image object and the width and height
		return img, width, height
			
