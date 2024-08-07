# test_can.py
# Read the alarm message from the CAN Bus

from time import sleep
import serial

global msg

comport = 'COM3'
port = None
cnt = 0
message = "5566778899aabbcc\n"

while True:
	print "\t* Connecting to {}...".format(comport)
	# sleep(7)
	try:
		port = serial.Serial(comport, 115200, timeout=1)
		if port.isOpen():
			print " * Connected"
			# print port.readlines()
			while cnt < 3:
				port.write(message)
				sleep(0.3)
				data = port.readlines()
				if data[0] == message:
					print "Data matched: {}".format(data[0].strip())
					msg = 0
					cnt += 1
				else:
					msg = "Data mismatched: {}".format(data[0].strip())
					print msg
					break
		else:
			msg = "Unable to open port {}".format()
			break
	except Exception, ce:
		msg = "Unable connect to UART: {}".format(ce)
		break
	break
		
if port: port.close()