# Fahrrad Controller Simulator
#
# Sendet Testdaten im gleichen Takt wie der Fahrrad Controller an den Server

import socket, time, random, string, os

SERVER = "127.0.0.1"
PORT = 90
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
nPackets = 0

def generateData():
	pGen 	= os.urandom(1) #b"\x3A"
	T 		= os.urandom(2) #b"\x3A\x98"
	nLm 	= os.urandom(2) #b"\x00\xFF"
	
	return b"%s%s%s" % (pGen, T, nLm)

if __name__ == "__main__":
	while 1:
		time.sleep(5)
		if(sock.sendto(generateData(), (SERVER, PORT))): nPackets += 1
		print("Sending Packet #", nPackets)