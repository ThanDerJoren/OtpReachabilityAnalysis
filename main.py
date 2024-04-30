import requests, json
from stop import Stop
from station import Station


def createStations (stopCollection):
    stationCollection = []
    currentStopName = stopCollection[0].name
    relatedStops = [stopCollection[0]]
    for element in stopCollection[1:]:
        if element.name == currentStopName:
            relatedStops.append(element)
        else:
            station = Station(currentStopName, relatedStops.copy())
            stationCollection.append(station)
            currentStopName = element.name
            relatedStops.clear()
            relatedStops.append(element)
    return stationCollection

def stationsToCSV(stationCollection):
    header = ["name", "meanLat", "meanLon"]
    with open("stations.csv", mode="w") as file:
        file.write(";".join(map(str, header)) + "\n")
        for station in stationCollection:
            data = [station.name, station.meanLat, station.meanLon]
            file.write(";".join(map(str, data)) + "\n")
    print("CSV file 'stations.csv' created successfully!!!")


allStops = []
allStations = []

queriedStops = requests.post("http://localhost:8080/otp/gtfs/v1", json={"query": "{stops{name, gtfsId, lat, lon, vehicleMode}}"})
queriedStops = json.loads(queriedStops.content)
queriedStops = queriedStops["data"]["stops"]
print(queriedStops[0])

for data in queriedStops:
    stop = Stop(data["name"], data["gtfsId"], data["lat"], data["lon"], data["vehicleMode"])
    allStops.append(stop)

allStations = createStations(allStops)
for station in allStations:
    print(station.name, len(station.relatedStops))

stationsToCSV(allStations)


