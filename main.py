
from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QLabel, QCheckBox, QFileDialog, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

import sys, time, serial, subprocess, traceback
import u3, socket, resources

import xml.etree.ElementTree as ET
from serial.tools import list_ports
from os import listdir, path
from imp import load_source

from scripts import mysql_connector

comports = []
repo_dir = "firmware"

class TestBench(QMainWindow):
	def __init__(self, parent = None):
		super(TestBench, self).__init__(parent)
		loadUi("TestBench.ui", self)
		self.setWindowIcon(QIcon(":/logo/logo.ico"))
		self.rpp_logo.setPixmap(QPixmap(":/banner/RedPoint_Logo.png"))
		
		# init flags
		self.db_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.lj_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.pps_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.sa_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.usb_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.jlu_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.jlg_flag.setPixmap(QPixmap(":/start/maybe.png"))
		self.user_flag.setPixmap(QPixmap(":/bad/not.png"))
		self.steps = []
		
		# connectors
		self.run_sch.clicked.connect(self.run_schedule)
		self.sch_box.currentIndexChanged.connect(self.selectionchange)
		self.checkBox.stateChanged.connect(self.selection)
		self.batch.textChanged.connect(self.update_batch)
		self.user.textChanged.connect(self.update_user)
		
		# init parameters table
		self.param_box.setHorizontalHeaderItem(0, QTableWidgetItem("Parameter"))
		self.param_box.setHorizontalHeaderItem(1, QTableWidgetItem("Value"))
		self.param_box.horizontalHeader().setStretchLastSection(True)
		self.param_box.setColumnWidth(0, 150)
		for i in range (0, 10):
			self.param_box.setRowHeight(i, 15)
		
		# init spectran comboboxes
		db = range(-70, -15, 5)
		for n in db:
			self.cb_noise.addItem(str(n))
			self.cb_peak.addItem(str(n))
			
		# read config file
		self.sa_port = None
		self.ps_port = None
		self.ut_port = None
		self.dbuser = None
		
		print "\t** Read configuration file..."
		if not path.isfile("configuration.xml"):
			QMessageBox.critical(self, "Configuration file not found", "Configuration file (configuration.xml) is missing!", QMessageBox.Ok)
			sys.exit(1)
		else:
			tree = ET.parse("configuration.xml")
			root = tree.getroot()
			try:
				self.ps_port = root.find("port_pps").text
				self.sa_port = root.find("port_sa").text
				self.ut_port = root.find("port_uut").text
				noise = int(root.find("noise_level").text)
				jl_ut = root.find("sn_jl_uut").text
				self.jlu_comm.setText(jl_ut)
				self.usnr = int(jl_ut)
				jl_gn = root.find("sn_jl_gn").text
				self.jlg_comm.setText(jl_gn)
				self.gsnr = int(jl_gn)
				self.def_sch = root.find("schedule").text
				
				self.cb_noise.setCurrentIndex(self.cb_noise.findText(str(noise), 
					Qt.MatchFixedString))
				self.cb_peak.setCurrentIndex(self.cb_peak.findText(str(noise+5), 
					Qt.MatchFixedString))
					
				self.batch.setText(root.find("batch_name").text)
				self.station.setText(socket.gethostname())
				self.dbuser = root.find("username").text
			except Exception, pe:
				QMessageBox.critical(self, "Configuration not found", "Error reading configuration file: {}".format(pe), QMessageBox.Ok)
				sys.exit(1)
			else:
				print " * 'configuration.xml' found and processed"

		print "\t** Setting up connections and interfaces..."
		self.com_test = self.test_connections()
		self.db_test = self.test_database()
		self.lj_test = self.test_labjack()
		
		# set variables for SpectrAn
		print "\t** Setting up Spectrum Analyzer..."
		setArg = ["set",
			"StartFrequency=3993.500000",
			"StopFrequency=3993.700000",
			"ResolutionBandwidth=8",
			"SweepTime=10",
			"AttenuationFactor=-10",
			"ReferenceLevel=-10",
			"DemodulatorMode=0",
			"DetectorMode=0",
			"CableType=0",
			"ReceiverConfiguration=0",
			"PulseMode=0",
			"Preamplifier=0",
			"DetectorMode=0"]
		setArg.append("MinPowerMarker={}".format(self.cb_noise.currentText()))
		try:
			output = subprocess.check_output(["Spectran/spectran.exe"] + setArg, stderr=subprocess.PIPE)
			print output
		except Exception, e:
			print "Error communicate SpectrAn: {}".format(e)
			sys.exit(1)
		
		# create interface for a Power Supply
		self.pport = None
		try:
			self.pport = serial.Serial(self.ps_port, 9600, timeout=1)
			self.pport.write("REMOTE\n")
			time.sleep(0.3)
			self.pport.readline()
			self.pport.write("*IDN?\n")
			time.sleep(0.3)
			ver = self.pport.readline()
			if "GPD-3303S" in ver:
				self.pport.write("VSET2:0.0\n")
				time.sleep(0.3)
				self.pport.write("LOCAL\n")
				time.sleep(0.3)
				self.pport.close()
				print " * Power supply interface created"
			else:
				print "Wrong version string for PPS:", ver.strip()
		except Exception, pse:
			QMessageBox.critical(self, "PPS not responsible", "Unable connect to PPS unit:\n\n{}".format(pse), QMessageBox.Ok)
			
		# read schedules
		print "\t** Creating schedules list..."
		if path.isdir("schedules"):
			for name in listdir("schedules"):
				if name.endswith(".xml"):
					self.sch_box.addItem(name[:-4])
			print " * {} schedules found".format(self.sch_box.count())
			ind = self.sch_box.findText(self.def_sch)
			if ind == -1:
				QMessageBox.warning(self, "Default schedule", "Unable to find '{}' in the schedules list".format(self.def_sch), QMessageBox.Ok)
			else:
				self.sch_box.setCurrentIndex(ind) # set default sch
				print " * Default schedule:", self.def_sch
		else:
			QMessageBox.critical(self, "Read schedules", "'schedules' folder is not found", QMessageBox.Ok)
			return
			
		
	
	def run_schedule(self):
		self.sch_box.setEnabled(False)
		self.checkBox.setEnabled(False)
		self.run_sch.setEnabled(False)

		# clear parameters table
		for i in range (1, 9):
			self.param_box.setItem(i, 1, QTableWidgetItem(None))
		
		# reset steps icons
		for x in range(0, self.steps_box.count()):
			self.steps_box.item(x).setIcon(QIcon(":/start/maybe.png"))
		
		# grab descriptor file accordingly to selected schedule
		sch = self.sch_box.currentText()
		descriptor = load_source("", "descriptors/{}.py".format(sch))
		
		# reset globals
		flag = True
		
		# terminate if any process of JLink is running
		cmd = ["taskkill", "/f", "/t", "/im", "JLink.exe"]
		p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		output, error = p.communicate()
		if error:
			pass
		else:
			print output
		
		# get a TruePeak value from config
		TruePeak = int(self.cb_peak.currentText())

		# set variables to pass in subprocess
		vars = {"app":self, "port":self.pport, "desc":descriptor, 
			"peak":TruePeak, "file":None, "msg":None}
		
		start_time = time.clock()
		
		# grub all checked steps in schedule
		for i, step in enumerate(self.steps):
			if self.steps_box.item(i).checkState() == 2:
				self.statusbar.showMessage("Executing: {}".format(step[1]))
				print "\n\t*** Executing: {}".format(step[1])
				if step[0] == "load_image.py" or step[0] == "program_SAMD.py":
					if "test firmware" in step[1]:
						vars["file"] = self.test_file.currentText().encode('ascii')
					elif "release firmware" in step[1]:
						vars["file"] = self.release_file.currentText().encode('ascii')
					else:
						print "Firmware file not specified"
						break
				try:
					execfile("{}/{}".format("scripts", step[0]), vars)
				except Exception, me:
					QMessageBox.critical(self, step[1], "Module error: {}\n{}".format(me, traceback.print_exc()), QMessageBox.Ok)
				res = vars["msg"]
				print "\t*** Finished {} with error code: {}".format(step[0], res)

				if res == 0:
					self.steps_box.item(i).setIcon(QIcon(":/good/yes.png"))
				else:
					self.steps_box.item(i).setIcon(QIcon(":/bad/not.png"))
					self.statusbar.showMessage("ERROR executing {}: {}".format(step[1], res))

					mysql_connector.mysql_connect()
					try:
						short_mac = self.param_box.item(2, 1).text().encode('ascii')
						full_mac = short_mac[:6] + "FFFE" + short_mac[6:]
						# avoid escape chars in the string to pass
						if not res == None and res[0].find("'") > 0:
							text = res.replace("'", "*")
						else:
							text = res
						# # fail_test(mac, step, user, error, station, batch) # single record
						# log = mysql_connector.fail_test(full_mac, step[1], self.user.text().encode('ascii'), text, self.station.text().encode('ascii'), self.batch.text().encode('ascii'))
						
						# fail_test_all(mac, step, user, error, station, batch) # multiple records
						log = mysql_connector.fail_test_all(full_mac, step[1], self.user.text().encode('ascii'), text, self.station.text().encode('ascii'), self.batch.text().encode('ascii'))
						
						print "Error recorded:", log
					except Exception, err:
						QMessageBox.critical(self, "Error logging:", "DB error: {}\n{}".format(err, traceback.print_exc()), QMessageBox.Ok)
						sys.exit(1)
					finally:
						mysql_connector.mysql_disconnect()
					
					# if not self.pport.isOpen(): self.pport.open()
					# self.pport.write("OUT0\n")
					# time.sleep(0.3)
					# self.pport.write("LOCAL\n")
					# time.sleep(0.3)
					# self.pport.close()
					flag = False
					break
					
				QApplication.processEvents()
				time.sleep(0.1)
		
		if flag:
			self.statusbar.showMessage("Test completed. Execution time: {} seconds".format(time.clock() - start_time))
		else:
			self.statusbar.showMessage("Test FAILED")
		if not self.pport.isOpen(): self.pport.open()
		self.pport.write("OUT0\n")
		time.sleep(0.3)
		self.pport.write("LOCAL\n")
		time.sleep(0.3)
		self.pport.close()
		self.sch_box.setEnabled(True)
		self.checkBox.setEnabled(True)
		self.run_sch.setEnabled(True)

	def selection(self, state):
		if state == 0:
			self.checkBox.setText("Select All")
		else:
			self.checkBox.setText("Unselect All")
		for x in range (0, self.steps_box.count()):
			self.steps_box.item(x).setCheckState(state)
		
	def update_batch(self):
		self.param_box.setItem(0, 1, QTableWidgetItem(self.batch.text()))
		
	def update_user(self, txt):
		if len(txt) < 3:
			self.user_flag.setPixmap(QPixmap(":/bad/not.png"))
			self.run_sch.setEnabled(False)
		else:
			self.user_flag.setPixmap(QPixmap(":/good/yes.png"))	
			if self.com_test and self.db_test and self.lj_test:
				self.run_sch.setEnabled(True)
				self.statusbar.showMessage("TestBench is ready to start")
		
	def test_connections(self):
		flag = 0
		jlink = None
		import pylink

		try:
			jlink = pylink.JLink()
			
			em_list = jlink.connected_emulators()

			for e in em_list:
				# print "Compare {} : {}, {}".format(e.SerialNumber, self.jl_ut, self.jl_gn)
				if e.SerialNumber == self.usnr:
					self.jlu_flag.setPixmap(QPixmap(":/good/yes.png"))
					flag += 1
				if e.SerialNumber == self.gsnr:
					self.jlg_flag.setPixmap(QPixmap(":/good/yes.png"))
					flag += 1
			jlink.close()
		except Exception, jle:
			msg = "Unabe to find connected JLink: {}".format(jle)
			jlink.close()
			sys.exit(1)
		if flag < 2:
			QMessageBox.critical(self, "J-Link not connected", "'Only {} of 2 J-Links found connected".format(flag), QMessageBox.Ok)
		else:
			print " * J-Link connections: OK"
			# sys.exit(1)
		coms = list(list_ports.comports())
		for com in coms:
			if com.manufacturer == "Aaronia AG":
				if com.device == self.sa_port:
					self.sa_flag.setPixmap(QPixmap(":/good/yes.png"))
					self.sa_comm.setText(self.sa_port)
					print " * SprctrAn port found"
					flag += 1
				else:
					QMessageBox.critical(self, "Wrong COM port", "Spectrum analyzer found on {}\nPlease change {} port in configuration.xml file".format(com.device, self.sa_port), QMessageBox.Ok)
					self.sa_flag.setPixmap(QPixmap(":/bad/not.png"))
					return
			if com.manufacturer == "FTDI":
				if com.device == self.ut_port:
					self.usb_flag.setPixmap(QPixmap(":/good/yes.png"))
					self.usb_comm.setText(self.ut_port)
					print " * FTDI (USB) port found"
					flag += 1
				elif com.device == self.ps_port:
					self.pps_flag.setPixmap(QPixmap(":/good/yes.png"))
					self.pps_comm.setText(self.ps_port)
					print " * Power Supply port found"
					flag += 1
		if flag >= 4:
			return True
		else:
			return False

	def test_database(self):
		try:
			con = mysql_connector.mysql_connect()
			print " * DB connector created: {}".format(con.open)
		except Exception, dbe:
			QMessageBox.critical(self, "Unable connect to database:\n\n{}".format(dbe), QMessageBox.Ok)
		finally:
			if con != None:
				self.db_flag.setPixmap(QPixmap(":/good/yes.png"))
				mysql_connector.mysql_disconnect()
				self.db_comm.setText("<{}>".format(self.dbuser))
				return True
			else:
				self.db_flag.setPixmap(QPixmap(":/bad/not.png"))
				return False
				
	def test_labjack(self):
		try:
			self.labjack = u3.U3()
			version_str = self.labjack.configU3()['SerialNumber']
			if isinstance(version_str, int):
				self.labjack.getFeedback(u3.DAC8(0, 0x00)) #0xfe))
				self.lj_flag.setPixmap(QPixmap(":/good/yes.png"))
				self.labjack.close()
				self.lj_comm.setText(str(version_str))
				print " * LabJack interface is ready"
				return True
			else:
				self.lj_flag.setPixmap(QPixmap(":/bad/not.png"))
				print "Wrong version string: {}".format(version_str)
				self.labjack.close()
				return False
		except Exception, ljex:
			QMessageBox.critical(self, "LabJack is not connected", "Unable connect to LabJack unit:\n{}".format(ljex), QMessageBox.Ok)
			return False

	def selectionchange(self):
		sch = self.sch_box.currentText()
		if ("-MOD-" in sch) or ("-GPT-" in sch): # v7 Tags
			self.get_files("_7.0")
		elif "-BDG-V6" in sch: # v6 PB
			self.get_files("_6.4")
		elif "-PBG-V7" in sch: # v7 PB
			self.get_files("3E0D")
		# elif "-PBL-V7" in sch: # v7 PB Lite (rev.A)
			# self.get_files("BEC4")
		elif "-PBL-V7" in sch: # v7 PB Lite (rev.B)
			self.get_files("BEC8")
		elif "-VTC-V7" in sch: # v7 VMT-C
			self.get_files("BECE")
		elif ("-CMA-" in sch) or ("-WMA-" in sch): # v7 Anchors
			self.get_files("_7.1")
		else:
			QMessageBox.critical(self, "Schedule not found", "Schedule is not in current schedules list", QMessageBox.Ok)
			return
			# self.device.setText("Unknown schedule")
		self.checkBox.setCheckState(2)
		self.param_box.setItem(9, 1, QTableWidgetItem(self.sch_box.currentText()))
		self.param_box.setItem(0, 1, QTableWidgetItem(self.batch.text()))
		
		# iterate schedule, get testing steps info
		del self.steps[:]
		self.steps_box.clear()
		tree = ET.parse("schedules\\" + sch + ".xml")
		root = tree.getroot()
		for item in root.findall('./StepReference'):
			step = []
			step.append(item.find("ScriptFile").text)
			step.append(item.find("Description").text)
			self.steps.append(step)
		for group in self.steps:
			item = QListWidgetItem(QIcon(":/start/maybe.png"), group[1])
			item.setCheckState(2) # enable checkbox
			self.steps_box.addItem(item)

	def get_files(self, platform):
		set = []
		self.boot_file.clear()
		self.softdev_r_file.clear()
		self.softdev_file.clear()
		self.test_file.clear()
		self.release_file.clear()

		# test = filter(lambda f: 'node-test' in f, set)
		# rlse = filter(lambda f: 'rtls' in f, set)
		
		if path.isdir(repo_dir):
			for f in listdir(repo_dir):
				if platform == "_7.1" and "eth" in f:
					self.softdev_file.addItem(f)
				elif platform == "_6.4" and "ble" in f:
					self.softdev_file.addItem(f)
				else:
					set.append(f)
		else:
			QMessageBox.critical(self, "Firmware folder is not found", "Unable to find firmware files", QMessageBox.Ok)
			sys.exit(1)
		
		for f in set:
			if "bootloader" in f and platform in f:
				self.boot_file.addItem(f)
				set.remove(f)
			elif "node-test-host" in f and platform in f:
				self.softdev_file.addItem(f)
				set.remove(f)
		
		for f in set:
			if platform == "_6.4" or platform == "_7.1":
				if platform in f and "node-test" in f:
					self.test_file.addItem(f)
					set.remove(f)
			else:
				if "node-test_7.0" in f:
					self.test_file.addItem(f)
					set.remove(f)
		
		for f in set:
			if platform == "_6.4" or platform == "_7.1":
				if platform == "_6.4":
					if platform in f and "rtls-radio" in f:
						self.release_file.addItem(f)
						set.remove(f)
				elif "_7.1" in f and "rtls-radio" in f:
					self.release_file.addItem(f)
					set.remove(f)
			else:
				if "rtls-radio_7.0" in f:
					self.release_file.addItem(f)
					set.remove(f)
					
		for f in set:
			if "v7pb-host" in f and platform in f:
				self.softdev_r_file.addItem(f)
				set.remove(f)
			elif "vmtc" in f and platform in f:
				self.softdev_r_file.addItem(f)
				set.remove(f)
	
if __name__ == '__main__':
	app = QApplication(sys.argv)
	tb = TestBench()
	tb.show()
	sys.exit(app.exec_())