from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from pyzbar import pyzbar
import time
import textwrap
import csv

found = 0
filename = "capture"
flat_number = 0
starting = "undefined"
ending = "undefined"
building = "undefined"

class VideoThread(QThread):
	change_pixmap_signal = pyqtSignal(np.ndarray)
	UIready = pyqtSignal()

	def __init__(self):
		super().__init__()
		self._run_flag = True

	def decode(self,cv_img):
		decodedObjects = pyzbar.decode(cv_img)
		for obj in decodedObjects:
			print('Data : ', obj.data,'\n')
		return decodedObjects

	def annotate(self,decodedObjects,cv_img):
		global found, filename

		for decodedObject in decodedObjects:
			if found==0:
				found = 1;

			points = decodedObject.polygon

			# If the points do not form a quad, find convex hull
			if len(points) > 4 :
			  hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
			  hull = list(map(tuple, np.squeeze(hull)))
			else :
			  hull = points;

			# Number of points in the convex hull
			n = len(hull)
			# Draw the convext hull
			#for j in range(0,n):
			#  cv2.line(cv_img, hull[j], hull[ (j+1) % n], (0,102,255), 2)

			font = cv2.FONT_HERSHEY_DUPLEX
			barCode = str(decodedObject.data)

			trimmed_barcode = barCode[2:-1]
			full_text = trimmed_barcode + " " + str(building) + ", flat " + str(flat_number) + ", from " + starting + " to " + ending
			wrapped_barcode = textwrap.wrap(full_text, width=30)

			x=10
			y=25
			cv2.rectangle(cv_img, (0,0), (480,150), (255,255,255), -1)
			for i, line in enumerate(wrapped_barcode):
				textsize = cv2.getTextSize(line, font, 0.75,1)[0]
				gap = textsize[1]+10

				y = y + gap

				cv2.putText(cv_img, line, (x, y), font,0.75,(0,0,0),1,lineType = cv2.LINE_AA)

			if found == 1:
				filename=str(building)+"_"+str(flat_number)+"_"+starting+"_"+ending+"_"+time.strftime("%H%M%S")
				cv2.imwrite('export/' + filename  + '.png', cv_img)
				print(filename)
				csv = open("qr_codes.csv","a")
				csv.write(filename + ", " + trimmed_barcode + "\n")
				csv.flush()
				csv.close()
				found = 2
				self.UIready.emit()
	def run(self):
		# capture from web cam
		cap = cv2.VideoCapture(0)
		while self._run_flag:
			ret, cv_img = cap.read()
			cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

			decodedObjects = self.decode(cv_img)
			self.annotate(decodedObjects,cv_img)

			if ret:
				self.change_pixmap_signal.emit(cv_img)
		# shut down capture system
		cap.release()

	def stop(self):
		self._run_flag = False
		self.wait()

class App(QWidget):
	def __init__(self):
		super().__init__()
		self.disply_width = 800
		self.display_height = 480

		#matches window size to display size
		self.setFixedWidth(800)
		self.setFixedHeight(480)

		# create the label that holds the image
		self.image_label = QLabel(self)
		self.image_label.resize(480, 480)

		# button to scan new code
		self.btn_next = QtWidgets.QPushButton("Next Code", self)
		self.btn_next.move(385,25)
		self.btn_next.clicked.connect(self.nextCode)

		# button to exit program
		self.btn_exit = QtWidgets.QPushButton("Exit", self)
		self.btn_exit.move(500,25)
		self.btn_exit.clicked.connect(self.close)

		# button to decrement flat number
		self.btn_dec = QtWidgets.QPushButton("-",self)
		self.btn_dec.move(650,134)
		self.btn_dec.resize(25,25)
		self.btn_dec.clicked.connect(self.decrement)

		# button to increment flat number
		self.btn_dec = QtWidgets.QPushButton("+",self)
		self.btn_dec.move(750,134)
		self.btn_dec.resize(25,25)
		self.btn_dec.clicked.connect(self.increment)

		# combobox for starting location
		self.combo_starting = QtWidgets.QComboBox(self)
		self.combo_starting.addItems(["Unknown","Hall","Kitchen","Bedroom1","Bedroom2","Bedroom3","Bathroom1","Bathroom2","Living Room","Cupboard1","Cupboard2","Other1","Other2","Other3"])
		self.combo_starting.move(650,200)
		self.combo_starting.resize(140,25)
		self.combo_starting.currentIndexChanged.connect(self.startingchange)

		# combobox for ending location
		self.combo_ending = QtWidgets.QComboBox(self)
		self.combo_ending.addItems(["Unknown","Hall","Kitchen","Bedroom1","Bedroom2","Bedroom3","Bathroom1","Bathroom2","Living Room","Cupboard1","Cupboard2","Other1","Other2","Other3"])
		self.combo_ending.move(650,250)
		self.combo_ending.resize(140,25)
		self.combo_ending.currentIndexChanged.connect(self.endingchange)

		# combobox for building name
		self.combo_building = QtWidgets.QComboBox(self)
		self.combo_building.addItems(["Unknown","Meridian Bay SGB","Meridian Bay Tower1","Meridian Wharf A", "Meridian Bay Tower2"])
		self.combo_building.move(650,300)
		self.combo_building.resize(140,25)
		self.combo_building.currentIndexChanged.connect(self.buildingchange)

		# label to display starting location
		self.lbl_starting = QtWidgets.QLabel("Starting",self)
		self.lbl_starting.resize(60,25)
		self.lbl_starting.move(650,175)

		# label to display ending location
		self.lbl_ending = QtWidgets.QLabel("Ending",self)
		self.lbl_ending.resize(60,25)
		self.lbl_ending.move(650,225)

		# lbael to display building
		self.lbl_building = QtWidgets.QLabel("Building",self)
		self.lbl_building.resize(60,25)
		self.lbl_building.move(650,275)

		# label to display flat number
		self.lbl_flat = QtWidgets.QLabel("Flat 0", self)
		self.lbl_flat.resize(60,25)
		self.lbl_flat.move(680,134)

		# label to tell user that image is saved
		self.lbl_saved = QtWidgets.QLabel("Scanning for QR Code", self)
		self.lbl_saved.resize(415,25)
		self.lbl_saved.move(390,75)

		# label to show most recent capture
		self.lbl_image = QtWidgets.QLabel("most recent image", self)
		self.lbl_image.resize(250,350)
		self.lbl_image.move(390,125)

		# branding
		self.lbl_branding = QtWidgets.QLabel("Swan Media Ltd.",self)
		self.lbl_branding.resize(150,150)
		self.lbl_branding.move(650,322)
		pixmap2 = QPixmap('logo.png')
		smaller_pixmap2 = pixmap2.scaled(140, 140, Qt.KeepAspectRatio)
		self.lbl_branding.setPixmap(smaller_pixmap2)

		# create csv file

		# hide ui elements and fullscreen
		self.showFullScreen()

		# create the video capture thread
		self.thread = VideoThread()
		# connect its signal to the update_image slot
		self.thread.change_pixmap_signal.connect(self.update_image)
		self.thread.UIready.connect(self.updateUI)
		# start the thread
		self.thread.start()

	def closeEvent(self, event):
		self.thread.stop()
		event.accept()

	@pyqtSlot(np.ndarray)
	def update_image(self, cv_img):

		"""Updates the image_label with a new opencv image"""
		qt_img = self.convert_cv_qt(cv_img)
		self.image_label.setPixmap(qt_img)

	def convert_cv_qt(self, cv_img):
		"""Convert from an opencv image to QPixmap"""
		rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
		h, w, ch = rgb_image.shape
		bytes_per_line = ch * w
		convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
		p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
		return QPixmap.fromImage(p)

	@pyqtSlot()
	def nextCode(self):
		global found
		found=0
		print('[INFO] Ready for next code')

	@pyqtSlot()
	def updateUI(self):
		self.lbl_saved.setText(filename)

		pixmap = QPixmap("export/" + filename + ".png")
		smaller_pixmap = pixmap.scaled(250, 350, Qt.KeepAspectRatio, Qt.FastTransformation)
		self.lbl_image.setPixmap(smaller_pixmap)

	@pyqtSlot()
	def decrement(self):
		global flat_number
		flat_number -= 1
		self.lbl_flat.setText("Flat " + str(flat_number))

	@pyqtSlot()
	def increment(self):
		global flat_number
		flat_number += 1
		self.lbl_flat.setText("Flat " + str(flat_number))

	@pyqtSlot()
	def startingchange(self):
		global starting
		starting = str(self.combo_starting.currentText())

	@pyqtSlot()
	def endingchange(self):
		global ending
		ending = str(self.combo_ending.currentText())

	@pyqtSlot()
	def buildingchange(self):
		global building
		building = str(self.combo_building.currentText())

if __name__=="__main__":
	app = QApplication(sys.argv)
	a = App()
	a.show()
	sys.exit(app.exec_())
