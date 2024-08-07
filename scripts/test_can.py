# test_can.py
# Read the alarm message from the CAN Bus

import can # https://python-can.readthedocs.io/en/stable/index.html#
from can.interface import Bus
from time import sleep

global msg

while True:
	try:
		bus = Bus(interface='ixxat', channel=0, bitrate=125000)
	except Exception, ce:
		msg = "Unable connect to CAN Bus: {}".format(ce)
		break	

	try:
		attempt = 0
		cnt = 0
		while attempt < 4: # 4 attempts
			message = bus.recv(timeout=0.1)
			# print message
			id = message.arbitration_id #4660
			data = "".join(map(lambda b: format(b, "02x"), message.data)) #5566778899aabbcc
			print "Message ID:", id, "Message data:", data
			attempt += 1
			if id == 4660 and data == "5566778899aabbcc":
				msg = 0
				cnt += 1
	except Exception, re:
		msg = "Unable to read CAN Bus: {}".format(re)
		break
	
	msg = 0
	break
	
if msg != 0:
	print "Exit with error message:", msg
elif cnt < 3:
	msg = "Wrong message in the CAN bus"
else:
	msg = 0
	print "Exit with error message:", msg
	