##########################################################################################
# Power up board. Check for overcurrent
#
# (C)2018 Redpoint Positioning
##########################################################################################

from sys import exit
from time import sleep
global msg

while True:
	if port == None:
		msg = "Cannot access the PPS port"
		break
	
	try:
		if not port.isOpen():
			port.open()
		port.write("REMOTE\n")
		port.readline()
		sleep(0.3)
		cmdVstr = "VSET2:{}\n".format(desc.SupplyVoltage)
		port.write(cmdVstr)
		sleep(0.3)
		cmdAstr = "ISET2:{}\n".format(desc.MaxCurrent)
		port.write(cmdAstr)
		sleep(0.3)
		port.write("OUT1\n")
		sleep(1)
		
		print "\t* Reading current..."
		cnt = 0
		while cnt < 3:
			try:
				port.readline() # clear buffer
				port.write("IOUT2?\n")
				sleep(0.3)
				current_str = port.readline().strip()
				if len(current_str) == 0:
					current_str = port.readline().strip()
				current = float(current_str[:-1])
				print "\t* Read current: {} Amps".format(current)
			except ValueError:
				msg = "Unable to read current: {}".format(current_str)
				break

			if current < desc.RadioNodeLowCurrent:
				msg = "Measured current value {} is too low.\nAcceptable low limit is {} Amps".format(current, desc.RadioNodeLowCurrent)
				cnt += 1
				sleep(0.5)
			elif current > desc.RadioNodeHighCurrent:
				msg = "Measured current value {} is too high.\nAcceptable high limit is {} Amps".format(current, desc.RadioNodeHighCurrent)
				cnt += 1
				sleep(0.5)
			else:
				print " * Measured current is acceptable:", current, "Amps"
				# print "\n\t*** Board smoke test finished successful"
				msg = 0
				break
		
	except Exception, e:
		msg = "Error measuring current: {}".format(e)
	finally:
		port.write("OUT0\n")
		sleep(0.5)
		port.close()
		break