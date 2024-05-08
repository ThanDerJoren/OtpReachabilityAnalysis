import requests, json
from stop import Stop
from station import Station

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd

import time

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

def create_street_network(map_data):
    nodes, edges = map_data.get_network(nodes=True, network_type="walking") # statt "all"
    graph = map_data.to_graph(nodes, edges, graph_type="networkx")
    return graph

def create_isoline_for_each_station(station_collection, street_network, start_time, radius = 300):
    isoline_collection = []
    street_network_in_utm = ox.project_graph(street_network)
    print("street_network_in_utm berechnet")
    print("--- %s seconds ---" % (time.time() - start_time))

    for item_index, station in enumerate(station_collection):
        isoline = station.calculate_isoline(street_network, street_network_in_utm, radius = radius)
        isoline_collection.append(isoline)
        print(f"{item_index}: {station.name} isoline berechnet", "--- %s seconds ---" % (time.time() - start_time))
    return isoline_collection.copy()

def export_isonline_as_shapefile(isoline_collection):
    gdf = gpd.GeoDataFrame(geometry=isoline_collection)
    gdf.to_file("all_isolines.shp")

requestURL = "http://localhost:8080/otp/gtfs/v1"

start_time = time.time()
stopsAsDict = queryAllStops(requestURL)
allStops = createStopObjects(stopsAsDict)
allStations = createStations(allStops)
print("all stations are created")
print("--- %s seconds ---" % (time.time() - start_time))

osm = OSM("braunschweig_OPNV-Netz.osm.pbf")
# nodes, edges = osm.get_network(nodes=True, network_type="all")
# street_network = osm.to_graph(nodes, edges, graph_type="networkx")
street_network = create_street_network(osm)
all_isolines = create_isoline_for_each_station(allStations, street_network, start_time)
export_isonline_as_shapefile(all_isolines)
print("isolines are exported")
print("--- %s seconds ---" % (time.time() - start_time))
# destination = {"lat": 52.25251, "lon":  10.46810}
# requestItinerariesForEachStation(allStations, "2024-04-18", "11:30", end=destination)




# allStations[0].queryTransitItineraries("2024-04-18", "11:30", end=destination)
# allStations[0].filterShortestItinerary()
# for itineray in allStations[0].possibleItineraries:
#     print(itineray.startTime)
#     print(itineray.duration)
#     print(itineray.modes)
#     print(itineray.routeNumbers)
#     print()
# print(allStations[0].name, allStations[0].averageTripTime, allStations[0].averageNumberOfTransfers ,allStations[0].averageWalkDistanceOfTrip)

# for item_index, station in enumerate(allStations):
#    print(item_index, station.name, len(station.relatedStops))
# print("lat ", allStations[131].meanLat, " lon ", allStations[131].meanLon)

# stationsToCSV(allStations)


