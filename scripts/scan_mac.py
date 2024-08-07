
from sys import exit
from scripts import mysql_connector
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QDialog, QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtWidgets import QDialogButtonBox as BBox

d = QDialog()

def bad():
	global msg
	msg = "Rejected by user"
	d.reject()

def good():
	global msg
	
	text = lineEdit.text()
	if len(text) == 12 and text.startswith("E4956EA"):
		try:
			full_mac = text[:6] + "FFFE" + text[6:]
			mysql_connector.mysql_connect()
			record = mysql_connector.search_mac(full_mac)
		except Exception, dbe:
			msg = "Error accessing database: {}".format(dbe)
			exit(msg)
		finally:
			mysql_connector.mysql_disconnect()
		
		if record > 0:
			QMessageBox.information(d, "Scan MAC address", "This MAC addres found in database:\n\tMAC address: {}\n\tDatabase record #{}\nPlease place this board into test station and press OK button to continue".format(full_mac, record), QMessageBox.Ok)
			msg = 0
			app.param_box.setItem(2, 1, QTableWidgetItem(lineEdit.text()))
			d.accept()
		elif record == -3:
			msg = "This MAC addres: {} NOT found in database".format(full_mac)
			d.reject()
		elif record == -2:
			msg = "This MAC addres: {} has DUPLICATED records".format(full_mac)
			d.reject()
		else:
			msg = "Database search returned ERROR code"
			d.reject()
	else:
		print "Scanned MAC is BAD:", text
		lineEdit.clear()
		lineEdit.setFocus()
	
try:
	d.setWindowTitle("Scan QR code")
	d.resize(200, 90)
	
	lineEdit = QLineEdit(d)
	lineEdit.resize(155, 30)
	font = lineEdit.font()
	font.setPointSize(12)
	lineEdit.setFont(font)
	lineEdit.setAlignment(Qt.AlignCenter)
	lineEdit.move(20, 10)
	
	buttonBox = BBox(BBox.Cancel|BBox.Ok, Qt.Horizontal, d)
	buttonBox.move(20, 50)
	buttonBox.accepted.connect(good)
	buttonBox.rejected.connect(bad)
	
	d.setWindowModality(Qt.ApplicationModal)
	d.exec_()
except Exception, e:
	print "ERROR initializing:", e
	d.close()
	exit(-1)