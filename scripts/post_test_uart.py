##########################################################################################
# Read 'VER' command, verify against expected result
#
# (C)2020 Redpoint Positioning
##########################################################################################

from PyQt5.QtWidgets import QTableWidgetItem
import serial
from time import sleep

global msg, sport

rmac = app.param_box.item(2, 1).text().encode('ascii')
module = app.release_file.currentText()
host = app.softdev_r_file.currentText()

# VER sn=e4956ea42723 hw=7.0 cbid=BE31 fw=5.10.19_rtls-radio host_fw=vmtc_1.1.0_pre-release-da63993b

while True:
	sport = None
	print "\t* Connecting to {}...".format(app.ut_port)
	try:
		# sleep(3)
		sport = serial.Serial(app.ut_port, 115200, timeout=1)
		sleep(0.5)
		sport.readline()
		sport.write("VER\n")
		sleep(0.3)
		l = sport.readline()
		cnt = 0
		ver = ""
		while cnt < 5:
			if l.startswith("#VER"):
				# print l
				ver = l.split(" ")
				# print "Pairs count:", len(ver)
				mac = ver[1][ver[1].find("=")+1:].strip()
				hw = ver[2][ver[2].find("=")+1:].strip()
				cbid = ver[3][ver[3].find("=")+1:].strip()
				mfw = ver[4][ver[4].find("=")+1:].strip()
				hfw = ver[5][ver[5].find("=")+1:].strip()
				msg = 0
				break
			else:
				l = sport.readline()
				cnt += 1
	except Exception, ex:
		msg = "Unable to open UART port: {}".format(ex)
		break
	
	if len(ver) < 5:
		msg = "Unable to read 'VER' string"
		break
	
	if mac.upper() == rmac:
		print " * MAC address verified:", mac
		msg = 0
	else:
		msg = "Wrong MAC on the board: {}. ({})".format(mac, rmac)
		break
		
	if hw == desc.Platform:
		print " * HW platform verified:", hw
		msg = 0
	else:
		msg = "Wrong hardware platform: {}. (7.0)".format(hw)
		break
		
	if cbid.lower() == desc.CBID:
		print " * CBID verified:", cbid
		msg = 0
	else:
		msg = "Wrong CBID for a board: {}. Mast be: {}".format(cbid, desc.CBID)
		break
		
	if mfw in module:
		print " * Module firmware verified:", mfw
		msg = 0
	else:
		msg = "Wrong module firmware: {}".format(mfw)
		break
		
	if "vmtc" in hfw:# VMT-C boards only
		print " * Host firmware verified:", hfw
		msg = 0
	else:
		msg = "Wrong host application firmware: {}".format(hfw)
		break

	break

if sport: sport.close()

