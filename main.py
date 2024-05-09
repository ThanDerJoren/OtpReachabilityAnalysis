import requests, json
from stop import Stop
from station import Station

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
import pandas as pd

import time

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

def requestItinerariesForEachStation(stationCollection, date: str, time: str, start: dict = None, end: dict = None, url = "http://localhost:8080/otp/gtfs/v1"):
    for station in stationCollection:
        station.possibleItineraries.clear()
        station.queryTransitItineraries(date, time, start, end)

def createStopObjects(queriedStops):
    stopObjects = []
    for data in queriedStops:
        stop = Stop(data["name"], data["gtfsId"], data["lat"], data["lon"], data["vehicleMode"])
        stopObjects.append(stop)
    return stopObjects.copy()

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

def create_dataframe_with_station_attributes(station_collection):
    name_collection = []
    average_trip_time_collection = []
    car_driving_time_collection = []
    travel_time_ratio_collection = []
    average_number_of_transfers_collection = []
    average_walk_distance_of_trip_collection = []
    trip_frequency_collection = []
    for station in station_collection:
        name_collection.append(station.name)
        average_trip_time_collection.append(station.averageTripTime)
        car_driving_time_collection.append(station.carDrivingTime)
        travel_time_ratio_collection.append(station.travelTimeRatio)
        average_number_of_transfers_collection.append(station.averageNumberOfTransfers)
        average_walk_distance_of_trip_collection.append(station.averageWalkDistanceOfTrip)
        trip_frequency_collection.append(station.tripFrequency)
    df = pd.DataFrame(
        {
            "Name": name_collection,
            "travel_time_ratio": travel_time_ratio_collection,
            "average_number_of_transfers": average_number_of_transfers_collection,
            "trip_frequency_collection": trip_frequency_collection,
            "average_trip_time": average_trip_time_collection,
            "car_driving_time": car_driving_time_collection,
            "average_walk_distance_of_trip": average_walk_distance_of_trip_collection
        }
    )
    return df

def create_street_network(map_data):
    nodes, edges = map_data.get_network(nodes=True, network_type="all")
    graph = map_data.to_graph(nodes, edges, graph_type="networkx")
    print("street_network berechnet")
    print("--- %s seconds ---" % (time.time() - start_time))
    return graph
def create_isoline_for_each_station(station_collection, street_network, start_time, radius = 300):
    isoline_collection = []
    for item_index, station in enumerate(station_collection):
        isoline = station.calculate_isoline(street_network, radius = radius)
        isoline_collection.append(isoline)
        print(f"{item_index}: {station.name} isoline berechnet", "--- %s seconds ---" % (time.time() - start_time))
    return isoline_collection.copy()


def export_stations_as_geopackage(station_collection):
    mean_lat_collection = []
    mean_lon_collection = []
    for station in station_collection:
        mean_lat_collection.append(station.meanLat)
        mean_lon_collection.append(station.meanLon)
    station_attributes = create_dataframe_with_station_attributes(station_collection)
    gdf = gpd.GeoDataFrame(station_attributes, geometry=gpd.points_from_xy(mean_lon_collection, mean_lat_collection), crs="EPSG:4326")
    gdf.to_file("dataframe_stations9_5.gpkg", driver='GPKG', layer='all_stations')

def export_isonline_as_geopackage(station_collection):
    name_collection = []
    isoline_collection = []
    for station in station_collection:
        name_collection.append(station.name)
        isoline_collection.append(station.isoline)
    station_attributes = create_dataframe_with_station_attributes(station_collection)
    gdf = gpd.GeoDataFrame(station_attributes, geometry=isoline_collection, crs="EPSG:4326")
    gdf.to_file("dataframe_isochrones9_5.gpkg", driver='GPKG', layer='some_isolines')

requestURL = "http://localhost:8080/otp/gtfs/v1"

start_time = time.time()
stopsAsDict = queryAllStops(requestURL)
allStops = createStopObjects(stopsAsDict)
allStations = createStations(allStops)
print("all stations are created")
print("--- %s seconds ---" % (time.time() - start_time))

export_stations_as_geopackage(allStations)
print("all stations are exported")
print("--- %s seconds ---" % (time.time() - start_time))

osm = OSM("braunschweig_OPNV-Netz.osm.pbf")
street_network = create_street_network(osm)
create_isoline_for_each_station(allStations[0:3], street_network, start_time)
export_isonline_as_geopackage(allStations[0:3])
print("isolines are exported")
print("--- %s seconds ---" % (time.time() - start_time))


# # destination = {"lat": 52.25251, "lon":  10.46810}
# # requestItinerariesForEachStation(allStations, "2024-04-18", "11:30", end=destination)




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


