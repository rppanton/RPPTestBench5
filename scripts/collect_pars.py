##########################################################################################
# Collect parameters for a database record. 
#
# (C)2018 Redpoint Positioning
##########################################################################################

from PyQt5.QtWidgets import QTableWidgetItem
from time import sleep
from pynrfjprog import API
# import u3

global msg

while True:
	msg = 0
	nrf = None
	
	# print "\t* Switching SWD to the host MCU interface"
	# try: 
		# labjack = u3.U3()
		# labjack.getFeedback(u3.DAC8(0, 0xfe)) # high for a host
		# labjack.close()
	# except:
		# msg = "Cannot create LabJack interface"
		# break
		
	if port == None:
		msg = "Cannot access the PPS port"
		break
	else:
		if not port.isOpen():
			port.open()
	port.write("REMOTE\n")
	sleep(0.5)
	port.write("OUT1\n")
	sleep(3)
	
	try:
		print "\t* Opening J-Link interface..."
		nrf = API.API(desc.ChipFamily)
		
		print " * Opening DLL..."
		nrf.open()
		if nrf.is_open():
			print "DLL is open"
		else:
			msg = "Unable open DLL"
			print msg
			break
		
		print " * Connecting to emulator {}...".format(app.usnr)
		nrf.connect_to_emu_with_snr(app.usnr, jlink_speed_khz=4000)
		if nrf.is_connected_to_emu():
			print "Connected to emulator"
		else:
			msg = "Unable connect to emulator"
			print msg
			break
		
		# nrf.sys_reset()
		# nrf.go()
		
		nrf.rtt_start()
		sleep(2)
		
		if nrf.rtt_is_control_block_found():
			nrf.rtt_read(0, 1024, encoding='ascii')
		else:
			msg = "Unable to find RTT control block"
			print msg
			break
	except Exception, rex:
		msg = "RTT connection error: {}".format(rex)
		if nrf:
			# nrf.rtt_stop()
			nrf.disconnect_from_emu()
			nrf.close()
		break
	
	print "\t* Collect board parameters..."
	rmac = app.param_box.item(2, 1).text().encode('ascii')
	count = 0
	try:
		nrf.rtt_write(0, "stat\n")
		sleep(1)
		out = nrf.rtt_read(0, 1024)
		data = out.split('\n')
		# print data
		for l in data:
			if "Serial:" in l:
				serial = l[l.find(':')+2:].strip()
				if len(serial) == 32:
					print " * Chip serial number:", serial
					count += 1
					app.param_box.setItem(1, 1, QTableWidgetItem(serial))
				else:
					msg = "Serial number wrong length: {}".format(serial)
					print msg
					break
			elif "MAC:" in l:
				mac = l[l.find(':')+2:].strip()
				if mac.upper() == rmac.upper():
					print " * Board MAC address: {}".format(mac)
					count += 1
				else:
					msg = "Wrong MAC address is found: {}. Set: {}".format(mac, rmac)
					print msg
					break
			elif "Bitmask:" in l:
				bitmask = l[l.find(':')+2:].strip()
				if bitmask == desc.BitMask:
					print " * Board bitmask:", bitmask
					count += 1
					app.param_box.setItem(5, 1, QTableWidgetItem(bitmask))
				else:
					msg = "Wrong bitmask pattern: {}. Right pattern: {}".format(bitmask, desc.BitMask)
					print msg
					break
			elif "Firmware:" in l:
				fw = l[l.find(':')+2:].strip()
				print " * Current firmware:", fw
				count += 1
				app.param_box.setItem(4, 1, QTableWidgetItem(fw))
			elif "DW:" in l:
				dw = l[l.find(':')+2:].strip()
				if dw == "DECA0130":
					print " * Decawaive chip:", dw
					count += 1
					app.param_box.setItem(3, 1, QTableWidgetItem(dw))
				else: 
					msg = "Wrong Decawaive chip: {}".format(dw)
					print msg
					break
			elif "ANTD:" in l:
				ant = l[l.find(':')+2:].strip()
				if ant == "0x4050":
					print " * Antenna delay: {}".format(ant)
					count += 1
					app.param_box.setItem(6, 1, QTableWidgetItem(ant))
				else:
					msg = "Wrong antenna delay: {}".format(ant)
					print msg
					break
			elif "XTALT:" in l:
				xt = l[l.find(':')+2:].strip()
				print " * Crystal trim value:", xt
				count += 1
				app.param_box.setItem(7, 1, QTableWidgetItem(xt))
			elif "TXPWR:" in l:
				pow = l[l.find(':')+2:].strip()
				if pow[:2] == "57":
					print " * Power level value:", pow[:2]
					count += 1
					app.param_box.setItem(8, 1, QTableWidgetItem(pow[:2]))
				else:
					msg = "Wrong power value: {}".format(pow[:2])
					print msg
					break
			elif "Channel:" in l:
				chan = l[l.find(':')+2:].strip()
				if chan == "2":
					print " * Current channel set to: {}".format(chan)
					count += 1
				else:
					msg = "Wrong channel is set", chan
					print msg
					break
	except Exception, dwe:
		msg = "RTT read stat error: {}".format(dwe)
		break
	else:
		if count == 9:
			msg = 0
			break
		else:
			print "{} parameters are missing".format(9 - count)
			msg = "Unable to verify parameters"
			break
	finally:
		print "\t* Disconnecting J-link..."
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		
if nrf.is_open():
	print "\t* Disconnecting J-link..."
	if nrf.is_connected_to_emu():
		nrf.disconnect_from_emu()
	nrf.close()
	port.close()

