
from time import sleep
from pynrfjprog import API
import serial

global msg

while True:
	nrf = None
	# port = serial.Serial("COM6", 9600)
	try:
		if port == None:
			msg = "Cannot access the PPS port"
			break
		else:
			if not port.isOpen():
				port.open()
		port.write("REMOTE\n")
		sleep(0.3)
		port.readline()
		print " * Applying power..."
		port.write("OUT1\n")
		sleep(0.3)
		
		nrf = API.API(desc.ChipFamily)
		# nrf = API.API("NRF52")
		
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
		# nrf.connect_to_emu_with_snr(260100639, jlink_speed_khz=4000)
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
			print "Unable to find RTT control block"

		print "\t* Start on data parsing..."
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
				# if board == desc.Platform:
				if board == "7.1":
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
					msg = "IMU does not passed selftest: {}".format(imut)
					break
			# else:
				# break
	except Exception, rex:
		msg = "RTT read error: {}".format(rex)
		if nrf.is_rtt_started():
			nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		port.close()
		break
					
	try:
		rmac = app.param_box.item(2, 1).text().encode('ascii')
		# rmac = "E4956EA40CF4"
		print " * MAC address to write:", rmac
		short_mac = rmac[-6:].lower()
		
		print "\t* Write board parameters..."
		nrf.rtt_write(0, "pow 57\n")
		sleep(0.1)
		nrf.rtt_write(0, "ant 4050\n")
		sleep(0.1)
		# nrf.rtt_read(0, 1024)
		nrf.rtt_write(0, "chan 2\n")
		sleep(0.1)
		nrf.rtt_write(0, "mac {}\n".format(short_mac))
		sleep(0.1)
		nrf.rtt_read(0, 1024)
	except Exception, ex:
		msg = "RTT write error: {}".format(ex)
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		break
		
	print "\t* Read board parameters..."
	try:
		nrf.rtt_write(0, "stat\n")
		sleep(1)
		out = nrf.rtt_read(0, 1024)
		data = out.split('\n')
		for l in data:
			if "Serial:" in l:
				serial = l[l.find(':')+2:].strip()
				if len(serial) == 32:
					print " * Serial found:", serial
					msg = 0
				else:
					msg = "Serial number wrong lengh: {}".format(serial)
					break
			elif "MAC:" in l:
				mac = l[l.find(':')+2:].strip()
				# wmac = l[l.find(':')+2:].strip().upper()
				# mac = wmac.replace("FFFE", "")
				if mac == rmac:
					print " * MAC address is set: {}".format(mac)
					msg = 0
				else:
					msg = "Wrong MAC address is found: {}. Set: {}".format(mac, rmac)
					break
			elif "DW:" in l:
				dw = l[l.find(':')+2:].strip()
				if dw == "DECA0130":
					print " * Decawaive chip found:", dw
					msg = 0
				else: 
					msg = "Wrong Decawaive chip: {}".format(dw)
					break
			elif "ANTD:" in l:
				ant = l[l.find(':')+2:].strip()
				if ant == "0x4050":
					print " * Current antenna delay: {}".format(ant)
					msg = 0
				else:
					msg = "Wrong antenna delay: {}".format(ant)
					break
			elif "TXPWR:" in l:
				pow = l[l.find(':')+2:].strip()
				if pow[:2] == "57":
					print " * Current power value:", pow[:2]
					msg = 0
				else:
					msg = "Wrong power value: {}".format(pow[:2])
					break
			elif "Channel:" in l:
					chan = l[l.find(':')+2:].strip()
					if chan == "2":
						print " * Current channel set to: {}".format(chan)
						msg = 0
					else:
						msg = "Wrong channel is set", chan
						break		
	except Exception, re:
		msg = "RTT stats error: {}".format(re)
		break
	finally:
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT0\n")
		sleep(0.3)
	break

print "End up with error:", msg
port.close()