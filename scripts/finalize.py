
# from PyQt5.QtWidgets import QTableWidgetItem
from scripts import mysql_connector
from time import sleep

global msg

while True:
	batch = app.param_box.item(0, 1).text()
	serial = app.param_box.item(1, 1).text()
	short_mac = app.param_box.item(2, 1).text()
	decaw = app.param_box.item(3, 1).text()
	firmw = app.param_box.item(4, 1).text()
	bm = app.param_box.item(5, 1).text()
	ant = app.param_box.item(6, 1).text()[-4:]
	xt = app.param_box.item(7, 1).text()
	pow = app.param_box.item(8, 1).text()
	model = app.param_box.item(9, 1).text()
	user = app.user.text().encode('ascii') 
	station = app.station.text().encode('ascii')
	
	try:
		bitmask = int(bm)
		antenna = int(ant)
		xttrim = int(xt, 16)
		power = int(pow)
	except Exception, cer:
		msg = "Error converting parameter: {}".format(cer)
		break
	
	full_mac = short_mac[:6] + "FFFE" + short_mac[6:]
	try:
		mysql_connector.mysql_connect()
		id = mysql_connector.search_mac(full_mac)
		if id == -3:
			msg = "Unable to find MAC address {} in database".format(full_mac)
			break
		elif id == -1:
			msg = "Unable to search for MAC address {} in database".format(full_mac)
			break
		elif id == -2:
			msg = "Multiple records with MAC {} in database".format(full_mac)
			break
		else:
			# update_rec(id, sn, bn, mac, hw, sw, bm, stat, ant, xt, pow, mod, user, station):
			code = mysql_connector.update_rec(id, serial, batch, full_mac, decaw, firmw, bitmask, 3, antenna, xttrim, power, model, user, station)
			print "Updating record", id, "success:", bool(code)
			# print id, serial, batch, full_mac, decaw, firmw, bitmask, 3, antenna, xttrim, power, model
			msg = not code
			break
	except Exception, e:
		msg = "Error updating DB: {}".format(e)
		break
	finally:
		mysql_connector.mysql_disconnect()
		break
		
# if port == None:
	# msg = "Cannot access the PPS port"
# else:
	# if not port.isOpen(): port.open()
	# port.write("OUT0\n")
	# sleep(0.5)
	# port.write("LOCAL\n")
	# sleep(0.5)
	# print "Power down..."
	# port.close()
