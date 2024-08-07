
import u3, pylink
from time import sleep

print "\t*Connecting to device..."
jlink = None

while True:
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
			jlink.restart()
		else:
			print "Unable to open JLink interface"
			break
		print "\t*Connecting to RTT terminal..."	
		jlink.rtt_start()
		sleep(1)
		num_up = jlink.rtt_get_num_up_buffers()
		num_down = jlink.rtt_get_num_down_buffers()
		print " * RTT started, {} up bufs, {} down bufs.".format(num_up, num_down)
	except Exception, jle:
		msg = "Unable to find connected JLink: {}".format(jle)
		jlink.close()
		break

	hw = None 
	rd = None 
	bt = None 
	imu = None
	st = None
	try:
		buf = jlink.rtt_read(0, 1024)
		if not buf:
			msg = "No data in RTT buffer found"
			break
		print "\t* Parsing {} blocks of data readed".format(len(buf))
		text = "".join(map(chr, buf))
		# print text
		data = text.split("\n")
		for l in data:
			if "Board:" in l:
				hw = l[l.find(":")+2:].strip()
				if hw == "6.4":
					print " * Right platform found:", hw
				else:
					msg = "Wrong platform found: {}".format(hw)
					break
			elif "Radio" in l:
				rd = l[l.find(":")+2:].strip()
				if rd == desc.Radio:
					print " * Right radio chip found:", rd
				else:
					msg = "Wrong DW chip found: {}".format(rd)
					break
			elif "IMU:" in l:
				imu = l[l.find(":")+2:].strip()
				if imu == desc.IMU:
					print " * Right IMU chip found:", imu
				else:
					msg = "Wrong IMU chip found: {}".format(imu)
					break
			elif "BT:" in l:
				bt = l[l.find(":")+2:].strip()
				if bt == desc.HostFamily:
					print " * Right BT chip found:", bt
				else:
					msg = "Wrong BT chip found: {}".format(bt)
					break
			elif "IMU selftest:" in l:
				st = l[l.find(":")+2:].strip()
				if st == "passed":
					print " * IMU with status found:", st
				else:
					msg = "IMU self test fails: {}".format(st)
					break
					
		if hw and rd and bt and imu and st:
			msg = 0
		else:
			break		
	except Exception, rtte:
		msg = "Unabe to open RTT terminal: {}".format(rtte)
		jlink.close()
		break
	
	print "\t* Writing main parameters"
	rmac = app.param_box.item(2, 1).text()
	mac = rmac.encode('ascii')
	print " * MAC address found:", mac
	short_mac = mac[-6:].lower()

	try:
		jlink.rtt_write(0, bytes("pow 57\n"))
		sleep(0.3)
		jlink.rtt_write(0, bytes("ant 4050\n"))
		sleep(0.3)
		jlink.rtt_write(0, bytes("chan 2\n"))
		sleep(0.3)
		jlink.rtt_write(0, bytes("mac {}\n".format(short_mac)))
		sleep(0.3)
		jlink.rtt_read(0, 1024)
	except Exception, wex:
		msg = "Unable to write RTT: {}".format(wex)
		break
	else:
		print " * Parameters written successfully"
		
	print "\t* Verifying written parameters"
	bm = None
	nmac = None 
	pow = None 
	ant = None 
	chan = None
	try:
		jlink.rtt_write(0, bytes("stat\n"))
		sleep(0.3)
		buf = jlink.rtt_read(0, 1024)
		if not buf:
			msg = "No data in RTT buffer found"
			break
		text = "".join(map(chr, buf))
		# print text
		data = text.split("\n")
		for l in data:
			if "Bitmask" in l:
				bm = l[l.find(":")+2:].strip()
				if bm == desc.BitMask:
					print " * Right HW bitmask found:", bm
				else:
					msg = "Wrong HW bitmask found: {}".format(bm)
					break
			elif "MAC" in l:
				nmac = l[l.find(":")+2:].strip()
				if nmac == mac:
					print " * Right MAC address found:", nmac
				else:
					msg = "Wrong MAC address found: {}".format(nmac)
					break
			elif "TXPWR" in l:
				pow = l[l.find(":")+2:].strip()
				if pow == "57575757":
					print " * Right power level found:", pow
				else:
					msg = "Wrong power level found: {}".format(nmac)
					break
			elif "ANTD" in l:
				ant = l[l.find(":")+2:].strip()
				if ant == "0x4050":
					print " * Right antenna delay found:", ant
				else:
					msg = "Wrong antenna delay found: {}".format(ant)
					break
			elif "Channel" in l:
				chan = l[l.find(":")+2:].strip()
				if chan == "2":
					print " * Right channel set found:", chan
				else:
					msg = "Wrong channel set found: {}".format(chan)
					break
		
		if nmac and pow and ant and chan:
			msg = 0
		else:
			jlink.rtt_stop()
			jlink.close()
			break
	except Exception, rex:
		msg = "Unable to read from RTT: {}".format(wex)
		break
	finally:
		jlink.rtt_stop()
		jlink.close()
		break