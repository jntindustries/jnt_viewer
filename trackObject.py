# Import misc
import socket
import time
from threading import Thread
from tkinter import *
from PIL import Image, ImageTk
import math as m
import numbers
# import ImageTk
# Import OpenCV
import cvzone
from cvzone.ColorModule import ColorFinder
import cv2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address_port = ("127.0.0.1", 5052)  # Open socket 5052

# capture = cv2.VideoCapture(0) # Turn on camera. 0 is for computers with a single camera
# capture.set(3, 1920) # Set horizontal resolution
# capture.set(4, 1080) # Set vertical resolution

# https://stackoverflow.com/a/30384945
def clearCapture(capture):
	capture.release()
	cv2.destroyAllWindows()

# Test the ports and returns a tuple with the available ports and the ones that are working.
# thank you aiden for this
def list_ports():
	is_working = True
	dev_port = 0
	working_ports = []
	available_ports = []
	while is_working:
		camera = cv2.VideoCapture(dev_port)
		if not camera.isOpened():
			is_working = False
			print("Port %s is not working." % dev_port)
		else:
			is_reading, img = camera.read()
			w = camera.get(3)
			h = camera.get(4)
			if is_reading:
				print("Port %s is working and reads images (%s x %s)" % (dev_port, h, w))
				working_ports.append(dev_port)
			else:
				print("Port %s for camera ( %s x %s) is present but does not reads." % (dev_port, h, w))
				available_ports.append(dev_port)
		dev_port += 1
	return available_ports, working_ports

x, y = list_ports()
available_Cameras = len(y)
print("IGNORE ABOVE ERRORS ABOUT NOT OPENING CAMERAS AND PORTS NOT WORKING")
print("WE FOUND", available_Cameras, "CAMERAS YEAHHHHH!!!!1")

my_colour_finder = ColorFinder(True)  # Toggle need for calibration
hsv_values = {"hmin": 79,  # Dictionary of image HSV values
			"hmax": 128,
			"smin": 103,
			"smax": 255,
			"vmin": 63,
			"vmax": 255}

# Mangled: https://stackoverflow.com/questions/55099413/python-opencv-streaming-from-camera-multithreading-timestamps/55131226
class VideoStreamWidget():
	def __init__(self, src=0):
		self.capture_Array = []
		for camera in range(available_Cameras):  # Please work
			self.capture_Array.append(cv2.VideoCapture(camera))
			# Start the thread to read frames from each video stream
			self.thread = Thread(target=self.update, args=(self.capture_Array[camera],))  # Afaik this is calling VideoStreamWidget.update()
			self.thread.daemon = True
			self.thread.start()

	def update(self, capture):
		# Read the next frame from the stream in a different thread
		self.contours_success = False  # Default value, otherwise complains that it doesn't exist
		self.return_array = [None, None, None, None]  # Default value, yield turns func into a generator,
		while True:  # so I am forced to do this instead of return. Oh well, the return was unecessary, anyways.
			if capture.isOpened():  # Figuring out what data is from which camera will probably require some work in Unity
				self.camera_ID = self.capture_Array.index(capture)  # Hence why adding the ID of the camera to the return array
				self.success, self.img = capture.read()  # Read camera data
				self.img_colour, self.mask = my_colour_finder.update(self.img, hsv_values)  # Get colour mask
				self.img_contour, self.contours = cvzone.findContours(self.img, self.mask)  # Get threshold mask
				if type(self.contours) == list:
					self.contours_success = True
				self.return_array = [self.img_contour, \
									self.contours, \
									self.contours_success, \
									self.camera_ID]
			time.sleep(.01)  # Delay to save resources

captures = []

def main():
	video_stream_widget = VideoStreamWidget()
	# tkinter time
	window = Tk()  # Init main window
	window.title("NJT View - Camera Input")
	window.config(background="#FFFFFF")
	
	dis_Img_W = 320 * 2
	dis_Img_H = 180 * 2
	
	# Do some math to get the optimal grid for a given # of cameras
	# https://stackoverflow.com/a/16909453
	def get_dimensions(n):
		tempSqrt = m.sqrt(n)
		divisors = []
		currentDiv = 1
		for currentDiv in range(n):
			if n % float(currentDiv + 1) == 0:
				divisors.append(currentDiv+1)
		hIndex = min(range(len(divisors)), key=lambda i: abs(divisors[i]-m.sqrt(n)))
		if divisors[hIndex]*divisors[hIndex] == n:
			print("Found optimal grid dimensions (w x h):", hIndex + 1, "x", hIndex + 1)
			return divisors[hIndex], divisors[hIndex]
		else:
			wIndex = hIndex + 1
			print("Found optimal grid dimensions (w x h):", wIndex + 1, "x", hIndex + 1)
			return divisors[hIndex], divisors[wIndex]

	def create_frame(): # Make grid of camera inputs
		height, width = get_dimensions(available_Cameras)
		for row in range(height):
			for col in range(width):
				# https://stackoverflow.com/questions/32342935/using-opencv-with-tkinter#32362559
				side = m.ceil(m.sqrt(available_Cameras))
				imageFrame = Frame(window, width=dis_Img_W, height=dis_Img_H)
				imageFrame.grid(row=row, column=col, padx=10, pady=10)
				lmain = Label(imageFrame)
				lmain.grid(row=row, column=col)
				try:
					capture = video_stream_widget.capture_Array[row * side + col]
					captures.append((capture, lmain))
				except:
					pass

	def show_frame():
		for i in captures:
			capture, lmain = i
			# Comments from: https://stackoverflow.com/a/43159588
			_, frame = capture.read()  # Read frame from video stream
			#frame, _ = my_colour_finder.update(frame, hsv_values) # Get colour mask
			#frame = cv2.flip(frame, 1) # This 
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert colours from BGR to RBG
			#video_stream_widget.update(capture)
			#frame = video_stream_widget.img_contour
			img = Image.fromarray(frame)  # Convert image for PIL
			#img = img.resize((300, 300), Image.Resampling.LANCZOS)
			img = img.resize((dis_Img_W, dis_Img_H), resample=Image.LANCZOS)
			imgtk = ImageTk.PhotoImage(image=img)  # Convert image for tkinter
			lmain.imgtk = imgtk  # Anchor imgtk so it does not get deleted by garbage collector
			lmain.configure(image=imgtk)  # Show image
		window.after(10, show_frame)  # Wait 10ms, then call func again
		# ^ No, tkinter is not stuck on this (surprisingly)
	
	create_frame()
	show_frame()
	window.mainloop()

	# This code is horrifying
	# TODO: Clean this up, put in its own func?
"""
	while True:
		try:
			video_stream_widget.get_frame()
			contours = video_stream_widget.return_array[1]
			if video_stream_widget.return_array[2]:
				try: # This is suddenly broken lol
					data = contours[0]["center"][0],\
						contours[0]["center"][1],\
						int(contours[0]["area"])
					sock.sendto(str.encode(str(data)), server_address_port)
				except IndexError: # Should probably figure out why exactly this is happening, but this is funnier
					print("The object is in a weird spot, so I\'m throwing a hissy fit.")
					pass
		except AttributeError:
			pass
"""

if __name__ == "__main__":
	main()
