# Batterie Controller Simulator
#
# Sendet Testdaten im gleichen Takt wie der Batterie Controller an den Server

import socket, time, random, string, os

SERVER = "127.0.0.1"
PORT = 90
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
nPackets = 0

def generateData():
	# Spannungen Batterie: 
	#Voll =  13.8 = 5 Balken = b"\x35\xE8"
	#		 13.4 = 4 Balken = b"\x34\x58"
	#		 13.0 = 3 Balken = b"\x32\xC8"
	#		 12.6 = 2 Balken = b"\x31\x38"
	#		 12.2 = 1 Balken = b"\x2F\xA8"
	#Leer =  11.8 = 0 Balken = b"\x2E\x18"

	uBat 	= b"\x34\x47" 	# Battery Voltage (V)
	iGen	= b"\x00\xFF"	# Generator Power (mA)
	iLoad	= b"\x00\xFF"	# External Load (mA)
	
	return b"%s%s%s%s" % (bytes([nPackets]), uBat, iGen, iLoad)

if __name__ == "__main__":
	while 1:
		time.sleep(1)
		if(sock.sendto(generateData(), (SERVER, PORT))): 
			nPackets += 1
			nPackets = 0 if nPackets > 255 else nPackets
		print("Sending Battery Packet #", nPackets)