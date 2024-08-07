
from PyQt5.QtWidgets import QTableWidgetItem
import pylink
from time import sleep

global msg
jlink = None

while True:
	print "\t*Connecting to device..."
	try:
		jlink = pylink.JLink()
		print " * Emulator found: {}".format(app.usnr)
		jlink.open(app.usnr)
		if jlink.opened():
			print " * Emulator interface is opened"
			jlink.set_tif(1)
			print " * MCU family: {}".format(desc.ChipFamily)
			jlink.connect(desc.ChipFamily, 4000, False)
			print " * Connected to core:", jlink.core_name()
			jlink.reset()
			jlink.restart()
			sleep(0.3)
		else:
			print "Unable to open JLink interface"
			break	
		jlink.rtt_start()
		sleep(2)
		num_up = jlink.rtt_get_num_up_buffers()
		num_down = jlink.rtt_get_num_down_buffers()
		print " * RTT started, {} up bufs, {} down bufs.".format(num_up, num_down)
		jlink.rtt_read(0, 1024)
		sleep(0.3)
	except Exception, jle:
		msg = "Unable to find connected JLink: {}".format(jle)
		jlink.close()
		break
		
	try:
		smac = rmac = app.param_box.item(2, 1).text().encode('ascii')
		params = 0

		jlink.rtt_write(0, bytes("stat\n"))
		sleep(0.3)
		buf = jlink.rtt_read(0, 1024)
		if not buf:
			msg = "No data in RTT buffer found"
			break
		print "\t* Parsing {} blocks of data readed".format(len(buf))
		text = "".join(map(chr, buf))
		data = text.split("\n")
		for l in data:
			if "Serial" in l:
				sn = l[l.find(":")+2:].strip()
				if len(sn) == 32:
					print " * Serial number:", sn.lower()
					app.param_box.setItem(1, 1, QTableWidgetItem(sn.lower()))
					params += 1
				else:
					msg = "Wrong serial number length found: {}".format(len(sn))
					break
			elif "MAC:" in l:
				mac = l[l.find(":")+2:].strip()
				if mac == smac:
					print " * MAC address:", mac
					params += 1
				else:
					msg = "Wrong MAC address onboard: {}".format(mac)
					break
			elif "Bitmask:" in l:
				bm = l[l.find(":")+2:].strip()
				if bm == desc.BitMask:
					print " * Futures bitmask:", bm
					app.param_box.setItem(5, 1, QTableWidgetItem(bm))
					params += 1
				else:
					msg = "Wrong bitmask found: {}".format(bm)
					break
			elif "Firmware:" in l:
				# fw = l[l.find(":")+2:].strip()
				
				# release firmware for next step
				file = app.release_file.currentText().encode('ascii')
				fw = file[:file.find("_6.4_")]
				if fw == None or fw == "":
					msg = "Wrong firmware version found: {}".format(fw)
					break
				else:
					print " * Release firmware:", fw
					app.param_box.setItem(4, 1, QTableWidgetItem(fw))
					params += 1
			elif "DW:" in l:
				dw = l[l.find(":")+2:].strip()
				if dw == "DECA0130":
					print " * Decawave signature:", dw
					app.param_box.setItem(3, 1, QTableWidgetItem(dw))
					params += 1
				else:
					msg = "Wrong DW chip found: {}".format(dw)
					break
			elif "ANTD:" in l:
				ant = l[l.find(":")+2:].strip()
				if ant == "0x4050":
					print " * Antenna delay value:", ant
					app.param_box.setItem(6, 1, QTableWidgetItem(ant))
					params += 1
				else:
					msg = "Wrong antenna delay found: {}".format(ant)
					break
			elif "XTALT:" in l:
				xt = l[l.find(":")+2:].strip()
				if len(xt) == 2:
					print " * XT calibration value:", xt
					app.param_box.setItem(7, 1, QTableWidgetItem(xt))
					params += 1
				else:
					msg = "Wrong XT calibration value: {}".format(xt)
					break
			elif "TXPWR:" in l:
				pow = l[l.find(":")+2:].strip()
				if pow == "57575757":
					print " * DW power level", pow
					app.param_box.setItem(8, 1, QTableWidgetItem(pow[:2]))
					params += 1
				else:
					msg = "Wrong power level found: {}".format(pow)
					break
	
		if params == 8:
			msg = 0
		else:
			jlink.rtt_stop()
			jlink.close()
			break		
	except Exception, r1e:
		msg = "Error on RTT terminal: {}".format(r1e)
		if jlink.opened():
			jlink.close()
		break
	finally:
		if jlink.opened():
			jlink.rtt_stop()
			jlink.close()
		break

