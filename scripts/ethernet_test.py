##########################################################################################
# Test LPC and WIZnet chips on CMA (WMA) board
#
# (C)2018 Redpoint Positioning
##########################################################################################

import subprocess
from pynrfjprog import API
from time import sleep

global msg
ping_num = 4

manual_ip = False #True
addr = 200

while True:
	test_ip = None
	test_mask = None
	sub = None
	sleep(2)
	print "\t* Getting IP for a Test Station..."
	# ret = os.system("ipconfig")
	ret = subprocess.check_output(['ipconfig'])
	text = ret.split("\n")
	for l in text:
		# print l
		if manual_ip:
			if "Autoconfiguration IPv4 Address" in l:
				test_ip = l[l.find(":")+2:].strip()
				print " * Default Gateway IP found:", test_ip
			if "Subnet Mask" in l:
				test_mask = l[l.find(":")+2:].strip()
				break
		else:
			if "IPv4 Address" in l:
				test_ip = l[l.find(":")+2:].strip()
				print " * IPv4 address found:", test_ip
			if "Subnet Mask" in l:
				test_mask = l[l.find(":")+2:].strip()
				break
	
	if not test_ip:
		msg = "Default Gateway not found"
		break
	else:
		sub = test_ip.split('.')
		print " * Gateway is: {}.{}.{}.X".format(sub[0], sub[1], sub[2])
		print " * Subnet mask is:", test_mask

	nrf = None
	icm_ip = None

	print "\t* Getting IP for a ICM Anchor..."
	print " * Opening J-Link interface..."
	try:
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
			nrf.rtt_read(0, 1024, encoding='ascii')
			print "RTT started"
		else:
			print "Unable to find RTT control block"
	except Exception, rex:
		msg = "RTT connection error: {}".format(rex)
		if nrf:
			# nrf.rtt_stop()
			nrf.disconnect_from_emu()
			nrf.close()
		break
	
	try:
		if manual_ip:
			manip = "{}.{}.{}.{}".format(sub[0], sub[1], sub[2], addr)
			print "\t* Assigning IP:", manip
			if test_mask == "255.255.255.0":
				cmd = "eth ip {}\n".format(manip)
			else:
				print " * Assigning mask:", test_mask
				cmd = "eth ip {} {}\n".format(manip, test_mask)
				nrf.rtt_write(0, cmd)
				sleep(0.3)

			abc = nrf.rtt_read(0, 1024)
			print " * ", abc.strip()
		else:
			sleep(2) # wait for DHCP service
		
		nrf.rtt_write(0, "eth ip\n")
		sleep(0.5)
		buf = nrf.rtt_read(0, 1024)
		if len(buf) == 0:
			msg = "No data in RTT buffer found"
			break

		data = buf.split("\n")
		for l in data:
			if "IPv4" in l:
				icm_ip = l[l.find(":")+2:].strip()
				print " * Anchor IP found:", icm_ip
				msg = 0
				break
	except Exception, e:
		msg = "Unable to read RTT: {}".format(e)
		break
	finally:
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()

	if not icm_ip:
		msg = "ICM Anchor IP not found"
		break
	elif icm_ip == "0.0.0.0":
		msg = "ICM Anchor IP is not set: {}".format(icm_ip)
		break
	
	msk = icm_ip.split('.')
	if int(sub[0]) == int(msk[0]) and int(sub[1]) == int(msk[1]) and int(sub[2]) == int(msk[2]):
		print " * ICM Anchor IP {} is a part of subnet {}.{}.{}.X".format(icm_ip, sub[0], sub[1], sub[2])
	else:
		msg = "ICM Anchor IP {} is NOT a part of subnet {}.{}.{}.X".format(icm_ip, sub[0], sub[1], sub[2])
		break
	
	sleep(2)
	print "\t* Ping {} with 32 bytes of data".format(icm_ip)
	cnt = 1
	while cnt <= ping_num:
		try:
			ret = subprocess.check_output(["ping", "-n", "1", icm_ip])
			# print ret
		except Exception, se:
			msg = "{}".format(se)
			break
		
		if "TTL=" in ret:
			print " * Attempt {}: Pass".format(cnt)
			msg = 0
			cnt += 1
		else:
			print "Attempt {}: Fail".format(cnt)
			msg = "Failed to ping ICM anchor"
			break
	break


