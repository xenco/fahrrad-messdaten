# Fahrrad Controller Simulator
#
# Sendet Testdaten im gleichen Takt wie der Fahrrad Controller an den Server

import socket, time, random, string, os

SERVER = "192.168.1.6"
PORT = 90
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
nPackets = 0

def generateData():
	pGen = os.urandom(1)
	T = os.urandom(2)
	nLm = os.urandom(2)
	
	return b"%s%s%s" % (pGen, T, nLm)

if __name__ == "__main__":
	while 1:
		time.sleep(0.5)
		if(sock.sendto(generateData(), (SERVER, PORT))): nPackets += 1
		print("Sending Packet #", nPackets)