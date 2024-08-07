##########################################################################################
# Verify host-module connections for a carrier board. 
#
# (C)2020 Redpoint Positioning
##########################################################################################

from time import sleep
from pynrfjprog import API
import u3

global msg

while True:
	# convert module to dictionary
	param = {} 
	for attr in dir(desc):
		if not attr.startswith('_'):
			param[attr] = getattr(desc, attr)
	# print param
	
	nrf = None
	msg == 0
	print "\t* Switching SWD to the host MCU interface"
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0xfe)) # high for a host
		labjack.close()
	except:
		msg = "Cannot create LabJack interface"
		break

	try:
		if port == None:
			msg = "Cannot access the PPS port"
			break
		else:
			if not port.isOpen():
				port.open()
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT1\n")
		sleep(2)
		
		nrf = None
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
			b = nrf.rtt_write(0, "hw\n")
			# print "{} bytes written to RTT".format(b)
			sleep(1)
			text = nrf.rtt_read(0, 1024, encoding='ascii')
			sleep(0.1)
			data = text.split('\n')
		else:
			msg =  "Unable to find RTT control block"
			print msg
			break

		print "\t* Start data parsing..."
		for l in data:
			if "Target:" in l:
				target = l[l.find(':')+2:].strip()
				if "test-station" in target:
					print " *", l.strip()
					msg = 0
					break
				else: 
					msg = "Wrong firmware target: {}".format(target)
					break
			elif "ERROR" in l:
				msg = "Host-Module communication Error: {}".format(l.strip())
				break
		if not msg == 0:
			break
	except Exception, rex:
		msg = "RTT read error: {}".format(rex)
		break
		
	try:
		# print data
		# convert output to dictionary
		out = {} 
		mid = ":" # define the key/value separator
		for l in data:
			if mid in l:
				# print l
				k = l[:l.find(mid)]
				v = l[l.find(mid)+2:].strip()
				out[k] = v
		# print param
		# print out
		
		if "Radio" in out.keys():
			if out["Radio"] == param["Radio"]:
				print " * Radio:", out["Radio"]
				msg = 0
			else:
				msg = "Wrong DW chip signature: {}".format(out["Radio"])
				break
		else:
			msg = "DW chip is not detected"
			break
		if "IMU" in out.keys():
			if out["IMU"] == param["IMU"]:
				print " * IMU:", out["IMU"]
				msg = 0
			else:
				msg = "Wrong IMU chip signature: {}".format(out["IMU"])
				break
		else:
			msg = "IMU chip is not detected"
			break
		if "BT" in out.keys():
			if out["BT"] == param["BT"]:
				print " * Bluetooth:", out["BT"]
				msg = 0
			else:
				msg = "Wrong BT chip signature: {}".format(out["BT"])
				break
		else:
			msg = "BT chip is not detected"
			break
		
		if "PreasureSensor" in param.keys():
			if param["PreasureSensor"] != None:
				if "PreasureSensor" in out.keys():
					if out["PreasureSensor"] == param["PreasureSensor"]:
						print " * PreasureSensor:", out["PreasureSensor"]
						msg = 0
					else:
						msg = "Pressure Sensor detection error: {}".format(out["PreasureSensor"])
						break
				else:
					msg = "Pressure Sensor is not detected"
					break
					
		if "FuelGauge" in param.keys():
			if param["FuelGauge"] != None:
				if "FuelGauge" in out.keys():
					if out["FuelGauge"] == param["FuelGauge"]:
						print " * FuelGauge:", out["FuelGauge"]
						msg = 0
					else:
						msg = "Fuel Gauge detection error: {}".format(out["FuelGauge"])
						break
				else:
					msg = "Fuel Gauge is not detected"
					break
					
		if "Charger" in param.keys():
			if param["Charger"] != None:
				if "Charger" in out.keys():
					if out["Charger"] == param["Charger"]:
						print " * Charger:", out["Charger"]
						msg = 0
					else:
						msg = "Charger detection error: {}".format(out["Charger"])
						break
				else:
					msg = "Charger is not detected"
					break
					
		if "CAN" in param.keys():
			if param["CAN"] != None:
				# print "CAN:", param["CAN"]
				if "CAN" in out.keys():
					if out["CAN"] == param["CAN"]:
						print " * CAN Bus:", out["CAN"]
						msg = 0
					else:
						msg = "CAN bus detection error: {}".format(out["CAN"])
						break
				else:
					msg = "CAN bus is not detected"
					break
		# else:
			# print " * CAN Bus: none"
			# msg = 0
	except Exception, re:
		msg = "Data parsing error: {}".format(re)
		break
	break

if nrf: nrf.close()
if port.isOpen(): port.close()