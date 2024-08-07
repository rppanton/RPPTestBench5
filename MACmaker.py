##########################################################################################
# create_mac.py
#
# Creates new record in database
# with new MAC addresses
#
# (C)2018 Red Point Positioning
##########################################################################################

import sys, pymysql, os, csv, socket
import xml.etree.ElementTree as ET

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QFileDialog, QInputDialog, QLineEdit
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.uic import loadUi

from scripts import mysql_connector
import resources

# from time import sleep

class GUI(QMainWindow):
	def __init__(self, parent = None):
		super(GUI, self).__init__(parent)
		loadUi("MACmaker.ui", self)
		self.setWindowIcon(QIcon(":/logo/logo.ico"))
		self.db_status_ico.setPixmap(QPixmap(":/start/maybe.png"))
		self.statusbar.showMessage("Ready")
		
		self.cb_region.currentIndexChanged.connect(self.get_mac)
		self.btn_create.clicked.connect(self.create_records)
		self.btn_dialog.clicked.connect(self.file_dialog)
		
		curr_dir = r'%s' % os.getcwd().replace('\\','/')
		self.outfile = curr_dir + "/new_mac_list.csv"
		self.file_path.setText(self.outfile)
		self.t_station.setText(socket.gethostname())

		self.btn_create.setEnabled(False)
		conn = None
		try:
			tree = ET.parse("configuration.xml")
			root = tree.getroot()
			rds_host = root.find("rds_host").text
			soc = int(root.find("socket").text)
			name = root.find("username").text
			password = root.find("password").text
			db_name = root.find("db_name").text
			
			self.conn = pymysql.connect(host=rds_host, port=soc, user=name, password=password, database=db_name, connect_timeout=5)
		except Exception, e:
			QMessageBox.critical(self, "Error connecting to DB", "ERROR: {}".format(e), QMessageBox.Ok)
			self.db_status_ico.setPixmap(QPixmap(":/bad/not.png"))
			self.stat.setText("Not connected")
			self.statusbar.showMessage("Database is not connected")
			self.btn_create.setEnabled(False)
			return
		else:
			self.cur = self.conn.cursor()
			sql = "SELECT region FROM mac_current"
			self.cur.execute(sql)
			regs = self.cur.fetchall()
			for n in regs:
				self.cb_region.addItem(str(n[0]))
			self.cb_region.setCurrentIndex(0)
			self.get_mac()
			
			self.db_status_ico.setPixmap(QPixmap(":/good/yes.png"))
			self.stat.setText("Connected")
			self.statusbar.showMessage("Database is connected")
			self.btn_create.setEnabled(True)
			
	def file_dialog(self):
		self.outfile = None
		fileName = QFileDialog.getSaveFileName(self, "Select an output file name and path", "", "Comma separated values (*.csv)")
		self.outfile = fileName[0]
		if self.outfile:
			if not self.outfile.endswith(".csv"):
				self.outfile = self.outfile + ".csv"
			self.file_path.setText(self.outfile)
		else:
			print "File not chosed"
			return

	
	def create_records(self):
		if self.t_user.text() == "":
			QMessageBox.critical(self, "User name is not set", "The valid user name is required", QMessageBox.Ok)
			self.statusbar.showMessage("Please enter valid user name")
			return
		else:
			try:
				self.num = int(self.amount.text())
				self.progress.setMaximum(self.num)
			except ValueError:
				QMessageBox.critical(self, "Error amount value", "Amount value has to be an integer", QMessageBox.Ok)
				self.statusbar.showMessage("Please enter valid amount value")
				return
			
		try:
			reg = self.cb_region.currentText()
			self.statusbar.showMessage("Creating records...")
			for i in range (0, self.num):
				sql = "SELECT * FROM mac_current WHERE region = {}".format(reg)
				rec = self.cur.execute(sql)
				row = self.cur.fetchone()
				
				# get new mac
				new_mac = "{}{:x}{:04x}".format(row[0], row[1], row[2] + 1).upper()
				if len(new_mac) == 16:
					sql = "UPDATE mac_current SET generated = {} WHERE region = {}".format(row[2] + 1, reg)
					rec = self.cur.execute(sql)
					self.conn.commit() # update db
					print "New MAC address created:", new_mac.upper()
				else:
					print "Wrong MAC length! No update made to DB", new_mac.upper()
					
				#create new record in db with mac
				sql = "INSERT INTO passed (mac_address, station_id, user_id, device_status_id) VALUES ('{}', '{}', '{}', {})".format(new_mac, self.t_station.text(), self.t_user.text(), 1)
				try:
					rec = self.cur.execute(sql)
					self.conn.commit()
				except Exception, ex:
					print "ERROR creating a record: {}".format(ex)
					sys.exit(1)

				if rec == 1:
					sql = "SELECT device_id FROM passed WHERE mac_address = '{}'".format(new_mac)
					rec = self.cur.execute(sql)
					row = self.cur.fetchone()
					print "Record #{} created in database".format(row[0])
					
				short_mac = new_mac[:6] + new_mac[10:]
				# rec#, 16-char mac, 12-char mac
				line = [row[0], new_mac, short_mac]
				file = open(self.outfile, 'ab')
				with file: 
					writer = csv.writer(file)
					writer.writerow(line)
				self.progress.setValue(i + 1)
				# sleep(1)
		except Exception, fe:
			QMessageBox.critical(self, "Error creating a records", "ERROR: {}".format(fe), QMessageBox.Ok)
			return
		finally:
			self.get_mac()
		self.statusbar.showMessage("{} records created".format(self.progress.maximum()))
			
			
	def get_mac(self):
		reg = self.cb_region.currentText()
		sql = "SELECT * FROM mac_current WHERE region = {}".format(reg)
		self.cur.execute(sql)
		parts = self.cur.fetchall()[0]
		# print "Return: {}".format(parts)
		mac = "{}{:x}{:04x}".format(parts[0], parts[1], parts[2]).upper()
		self.mac_cur.setText(mac)

	def closeEvent(self, event):
		if self.conn: 
			self.cur.close()
			self.conn.close()
		print "Connection closed"
		app.quit()

		
if __name__ == '__main__':
	app = QApplication(sys.argv)
	tb = GUI()
	tb.show()
	sys.exit(app.exec_())