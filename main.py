import requests, json
from stop import Stop
from station import Station


def createStations(stopCollection):
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

def checkGrizzlyServerIsRunning(url = "http://localhost:8080/")->bool:
    # TODO flexibel machen
    try:
        # Get Url
        get = requests.get(url)
        # if the request succeeds
        if get.status_code == 200:
            return True
        else:
            return False
        # Exception
    except requests.exceptions.RequestException as e:
        # print URL with Errs
        raise SystemExit(f"{url}: is Not reachable \nErr: {e}")


def queryAllStops(url):
    if checkGrizzlyServerIsRunning() == True:
        queriedStops = requests.post(url,json={"query": "{stops{name, gtfsId, lat, lon, vehicleMode}}"})
        queriedStops = json.loads(queriedStops.content)
        queriedStops = queriedStops["data"]["stops"]
        return queriedStops
    else:
        print("OTP is not running/ reachable")

def createStopObjects(queriedStops):
    stopObjects = []
    for data in queriedStops:
        stop = Stop(data["name"], data["gtfsId"], data["lat"], data["lon"], data["vehicleMode"])
        stopObjects.append(stop)
    return stopObjects.copy()

def requestItinerariesForEachStation(stationCollection, date: str, time: str, start: dict = None, end: dict = None, url = "http://localhost:8080/otp/gtfs/v1"):
    for station in stationCollection:
        station.possibleItineraries.clear()
        station.queryTransitItineraries(date, time, start, end)



requestURL = "http://localhost:8080/otp/gtfs/v1"


stopsAsDict = queryAllStops(requestURL)
allStops = createStopObjects(stopsAsDict)
allStations = createStations(allStops)

destination = {"lat": 52.25251, "lon":  10.46810}
#requestItinerariesForEachStation(allStations, "2024-04-18", "11:30", end=destination)




allStations[0].queryTransitItineraries("2024-04-18", "11:30", end=destination)
allStations[0].filterShortestItinerary()
for itineray in allStations[0].possibleItineraries:
    print(itineray.startTime)
    print(itineray.duration)
    print(itineray.modes)
    print(itineray.routeNumbers)
    print()
print(allStations[0].name, allStations[0].averageTripTime, allStations[0].averageNumberOfTransfers ,allStations[0].averageWalkDistanceOfTrip)

# for station in allStations:
#     print(station.name, len(station.relatedStops))

# stationsToCSV(allStations)


