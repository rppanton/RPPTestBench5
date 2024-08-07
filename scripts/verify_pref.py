##########################################################################################
# Verify preferal devices on carrier board. 
#
# (C)2018 Redpoint Positioning
##########################################################################################

from time import sleep
from pynrfjprog import API

global msg

while True:
	nrf = None
	msg == 0
	try:
		if port == None:
			msg = "Cannot access the PPS port"
			break
		else:
			if not port.isOpen():
				port.open()
		port.write("REMOTE\n")
		sleep(0.5)
		# port.readline()
		# print " * Applying power..."
		port.write("OUT1\n")
		sleep(0.5)
		
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
		
		nrf.sys_reset()
		nrf.go()
		
		nrf.rtt_start()
		sleep(2)
		
		if nrf.rtt_is_control_block_found():
			out = nrf.rtt_read(0, 1024, encoding='ascii')
			data = out.split('\n')
		else:
			msg = "Unable to find RTT control block"
			print msg
			break

		print "\t* Start on data parsing..."
		# print data
		for l in data:
			if "Target:" in l:
				target = l[l.find(':')+2:].strip()
				if target == "test-station":
					print " *", l.strip()
				else: 
					msg = "Wrong target for firmware: {}".format(target)
					break
			elif "Board:" in l:
				board = l[l.find(':')+2:].strip()
				if board == desc.Platform:
					print " *", l.strip()
				else: 
					msg = "Wrong board platform: {}".format(board)
					break
			elif "Radio:" in l:
				dw = l[l.find(':')+2:].strip()
				if dw == "DW1000":
					print " *", l.strip()
				else:
					msg = "Wrong Decawaive signature:", dw
					break
			elif "IMU:" in l:
				imu = l[l.find(':')+2:].strip()
				if imu == "lsm6dsm":
					print " *", l.strip()
				else:
					msg = "Wrong IMU signature:", imu
					break
			elif "BT:" in l:
				bt = l[l.find(':')+2:].strip()
				if bt == "nRF52832":
					print " *", l.strip()
				else:
					msg = "Wrong Bluetooth signature:", bt
					break
			elif "IMU selftest" in l:
				imut = l[l.find(':')+2:].strip()
				if imut == "passed":
					print " * IMU self test:", imu
				else:
					msg = "IMU does not passed self-test: {}".format(imut)
					break
	except Exception, rex:
		msg = "RTT read error: {}".format(rex)
		if nrf.is_rtt_started():
			nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		port.close()
		break
		
	try:
		if desc.CBID:
			print "\t* Writing CBID:", desc.CBID
			nrf.rtt_write(0, "cbid {}\n".format(desc.CBID))
			sleep(0.3)
			buff = nrf.rtt_read(0, 1024)
			# print "Buffer:", buff
			for n in buff.split("\n"):
				if "CBID" in n:
					# print n
					cid = n[n.find(':')+2:].strip()
					if cid == desc.CBID:
						print " *", n.strip()
						msg = 0
						# break
					else:
						msg = "Wrong CBID set: {}".format(cid)
						break
			if not msg == 0:
				break
			
		nrf.rtt_write(0, "hw\n")
		sleep(1)
		out = nrf.rtt_read(0, 1024)
		data = out.split('\n')
		for l in data:
			if desc.Platform == "7.1" and "Ethernet" in l:
				et = l[l.find(':')+2:].strip()
				if et == desc.Ethernet:
					print " *", l.strip()
					msg = 0
				else:
					msg = "Ethernet detection error:", et
					break
			if "PreasureSensor:" in l:
				ps = l[l.find(':')+2:].strip()
				if ps == desc.PreasureSensor:
					print " *", l.strip()
					msg = 0
				else:
					msg = "Pressure Sensor detection error: {}".format(ps)
					break
			elif "FuelGauge:" in l:
				fg = l[l.find(':')+2:].strip()
				if fg == desc.FuelGauge:
					print " *", l.strip()
					msg = 0
				else:
					msg = "Fuel Gauge detection error {}:".format(fg)
					break
			elif "Charger:" in l:
				ch = l[l.find(':')+2:].strip()
				if ch == desc.Charger:
					print " *", l.strip()
					msg = 0
				else:
					msg = "Charger detection error: {}".format(ch)
					break		
	except Exception, re:
		msg = "RTT prefs error: {}".format(re)
		break
	finally:
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
	
	if nrf.open():
		nrf.close()
	break
