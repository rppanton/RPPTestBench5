from PyQt5.QtWidgets import QTableWidgetItem
import serial
from time import sleep

global msg, sport
_ubaud = 115200
_uport = app.ut_port
rmac = app.param_box.item(2, 1).text().encode('ascii')

while True:
	sport = None
	print "\t* Connecting to {} with baudrate {}".format(_uport, _ubaud)
	try:
		sport = serial.Serial(_uport, _ubaud, timeout=1)
		sleep(0.5)
		sport.readline()
		sport.write("VER\n")
		# sleep(1)
		l = sport.readline()
		cnt = 0
		ver = ""
		while cnt < 5:
			if l.startswith("#VER"):
				# print l
				ver = l.split(" ")
				# print "Par count:", len(ver)
				mac = ver[1][ver[1].find("=")+1:].strip()
				hw = ver[2][ver[2].find("=")+1:].strip()
				fw = ver[4][ver[4].find("=")+1:].strip()
				# bt = ver[5][ver[5].find("=")+1:].strip()
				msg = 0
				break
			else:
				l = sport.readline()
				cnt += 1
	except Exception, ex:
		msg = "Unable to open UART port:", ex.message
		break
	
	if cnt == 5 or len(ver) < 5:
		msg = "Unable to read VER string"
		break
	
	if mac == rmac:
		print " * MAC address verifyed:", mac
	else:
		msg = "Wrong MAC on the board: {}. ({})".format(mac, rmac)
		break
		
	if hw == "7.0":
		print " * HW platform verifyed:", hw
	else:
		msg = "Wrong hardware platform: {}. (7.0)".format(hw)
		break
		
	# if bt == "52.0":
		# print " * BT platform verifyed:", bt
	# else:
		# msg = "Wrong bluetooth platform: {}. (52.0)".format(bt)
		# break
		
	if len(fw) > 0:
		print " * Current firmware version:", fw
		app.param_box.setItem(4, 1, QTableWidgetItem(fw))
	else:
		msg = "Unable to read FW version"
		break
	
	break

if sport: sport.close()

