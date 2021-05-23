from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from pyzbar import pyzbar
import time

found = 0
filename = "flat1-kitchen"

class VideoThread(QThread):
	change_pixmap_signal = pyqtSignal(np.ndarray)

	def __init__(self):
		super().__init__()
		self._run_flag = True

	def decode(self,cv_img):
		decodedObjects = pyzbar.decode(cv_img)
		for obj in decodedObjects:
			print('Data : ', obj.data,'\n')
		return decodedObjects

	def annotate(self,decodedObjects,cv_img):
		global found
		for decodedObject in decodedObjects:
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
			for j in range(0,n):
			  cv2.line(cv_img, hull[j], hull[ (j+1) % n], (255,0,0), 3)

			x = decodedObject.rect.left
			y = decodedObject.rect.top

			font = cv2.FONT_HERSHEY_PLAIN
			barCode = str(decodedObject.data)
			cv2.putText(cv_img, barCode, (x, y-10), font, 1, (0,0,0), 2, cv2.LINE_AA)

			if found == 1:
				cv2.imwrite('export/' + filename  + '.png', cv_img)
				found = 2;

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

		# hide ui elements and fullscreen
		self.showFullScreen()

		# create the video capture thread
		self.thread = VideoThread()
		# connect its signal to the update_image slot
		self.thread.change_pixmap_signal.connect(self.update_image)
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

if __name__=="__main__":
	app = QApplication(sys.argv)
	a = App()
	a.show()
	sys.exit(app.exec_())
