import requests, json
from stop import Stop
from station import Station

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
import pandas as pd

import time

def check_grizzly_server_is_running(url ="http://localhost:8080/")->bool:
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

def query_all_stops(url):
    if check_grizzly_server_is_running() == True:
        queried_stops = requests.post(url,json={"query": "{stops{name, gtfsId, lat, lon, vehicleMode}}"})
        queried_stops = json.loads(queried_stops.content)
        queried_stops = queried_stops["data"]["stops"]
        return queried_stops
    else:
        print("OTP is not running/ reachable")

def request_itineraries_for_each_station(station_collection, date: str, time: str, start: dict = None, end: dict = None, url ="http://localhost:8080/otp/gtfs/v1"):
    for station in station_collection:
        station.possible_itineraries.clear()
        station.query_transit_itineraries(date, time, start, end)

def create_stop_objects(queried_stops):
    stop_objects = []
    for data in queried_stops:
        stop = Stop(data["name"], data["gtfsId"], data["lat"], data["lon"], data["vehicleMode"])
        stop_objects.append(stop)
    return stop_objects.copy()

def create_stations(stop_collection):
    station_collection = []
    current_stop_name = stop_collection[0].name
    related_stops = [stop_collection[0]]
    for element in stop_collection[1:]:
        if element.name == current_stop_name:
            related_stops.append(element)
        else:
            station = Station(current_stop_name, related_stops.copy())
            station_collection.append(station)
            current_stop_name = element.name
            related_stops.clear()
            related_stops.append(element)
    return station_collection

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
        average_trip_time_collection.append(station.average_trip_time)
        car_driving_time_collection.append(station.car_driving_time)
        travel_time_ratio_collection.append(station.travel_time_ratio)
        average_number_of_transfers_collection.append(station.average_number_of_transfers)
        average_walk_distance_of_trip_collection.append(station.average_walk_distance_of_trip)
        trip_frequency_collection.append(station.trip_frequency)
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
def create_isochrone_for_each_station(station_collection, street_network, start_time, radius = 300):
    isochrone_collection = []
    for item_index, station in enumerate(station_collection):
        isochrone = station.calculate_isochrone(street_network, radius = radius)
        isochrone_collection.append(isochrone)
        print(f"{item_index}: {station.name} isochrone berechnet", "--- %s seconds ---" % (time.time() - start_time))
    return isochrone_collection.copy()


def export_stations_as_geopackage(station_collection):
    mean_lat_collection = []
    mean_lon_collection = []
    for station in station_collection:
        mean_lat_collection.append(station.mean_lat)
        mean_lon_collection.append(station.mean_lon)
    station_attributes = create_dataframe_with_station_attributes(station_collection)
    gdf = gpd.GeoDataFrame(station_attributes, geometry=gpd.points_from_xy(mean_lon_collection, mean_lat_collection), crs="EPSG:4326")
    gdf.to_file("dataframe_stations9_5.gpkg", driver='GPKG', layer='all_stations')

def export_isochrone_as_geopackage(station_collection):
    name_collection = []
    isochrone_collection = []
    for station in station_collection:
        name_collection.append(station.name)
        isochrone_collection.append(station.isochrone)
    station_attributes = create_dataframe_with_station_attributes(station_collection)
    gdf = gpd.GeoDataFrame(station_attributes, geometry=isochrone_collection, crs="EPSG:4326")
    gdf.to_file("dataframe_isochrones9_5.gpkg", driver='GPKG', layer='some_isochrones')

request_url = "http://localhost:8080/otp/gtfs/v1"

start_time = time.time()
stops_as_dict = query_all_stops(request_url)
all_stops = create_stop_objects(stops_as_dict)
all_stations = create_stations(all_stops)
print("all stations are created")
print("--- %s seconds ---" % (time.time() - start_time))

export_stations_as_geopackage(all_stations)
print("all stations are exported")
print("--- %s seconds ---" % (time.time() - start_time))

osm = OSM("braunschweig_OPNV-Netz.osm.pbf")
street_network = create_street_network(osm)
create_isochrone_for_each_station(all_stations[0:3], street_network, start_time)
export_isochrone_as_geopackage(all_stations[0:3])
print("isochrones are exported")
print("--- %s seconds ---" % (time.time() - start_time))


destination = {"lat": 52.25251, "lon":  10.46810}
# # requestItinerariesForEachStation(allStations, "2024-04-18", "11:30", end=destination)

all_stations[0].query_transit_itineraries("2024-04-18", "11:30", end=destination)
all_stations[0].filter_shortest_itinerary()
for itineray in all_stations[0].possible_itineraries:
    print(itineray.start_time)
    print(itineray.duration)
    print(itineray.modes)
    print(itineray.route_numbers)
    print()
print(all_stations[0].name, all_stations[0].average_trip_time, all_stations[0].average_number_of_transfers, all_stations[0].average_walk_distance_of_trip)

for item_index, station in enumerate(all_stations):
   print(item_index, station.name, len(station.related_stops))
print("lat ", all_stations[131].mean_lat, " lon ", all_stations[131].mean_lon)




