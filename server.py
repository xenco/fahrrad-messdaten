# Server
#
# Empfängt Daten vom Fahrrad Controller und kommuniziert mit der API

import socket, requests, random

API_URL = "http://localhost/fahrrad/public/"

def computeData(data):
	reifenUmfang = 2.1													# M
	u = 25

	pGen = data[0] 														# mittlere IST-Leistung in W
	T = int.from_bytes([data[1],data[2]], byteorder='big')				# Zeit für eine Tretlagerumdrehung
	nLm = int.from_bytes([data[3],data[4]], byteorder='big')			# Umdrehungen Lichtmaschine
	
	strecke = int(nLm * (reifenUmfang / u))
	geschwindigkeit = int(strecke / T)
	istLeistung = pGen
	
	return strecke, geschwindigkeit, istLeistung

if __name__ == "__main__":
	socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	socket.bind(("", 90))

	print("waiting on port:", 90)

	while 1:
		try:
			data, addr = socket.recvfrom(1024)
			print(addr, data)

			strecke, geschwindigkeit, istLeistung = computeData(data)
			print("strecke: ", strecke, "geschwindigkeit: ", geschwindigkeit, "istLeistung: ", istLeistung)

			requests.post(API_URL + "data", data = {
				"ip": "10.0.0."+ str(random.choice([1,2,3])),
				"strecke": strecke,
				"geschwindigkeit": geschwindigkeit,
				"istLeistung": istLeistung
			})
		except:
			print("Error")
