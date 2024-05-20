import requests, json
from stop import Stop
from station import Station

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
import pandas as pd

import time

def check_grizzly_server_is_running(url ="http://localhost:8080/")->bool:
    # transferred to plugin
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
        raise SystemExit(f"{url}: is Not reachable\n openTripPlanner is not running.  \nErr: {e}")

def query_all_stops(url):
    # transferred to plugin
    if check_grizzly_server_is_running() == True:
        queried_stops = requests.post(url,json={"query": "{stops{name, gtfsId, lat, lon, vehicleMode}}"})
        queried_stops = json.loads(queried_stops.content)
        queried_stops = queried_stops["data"]["stops"]
        return queried_stops
    else:
        print("OTP is not running/ reachable")

def request_itineraries_for_each_station(station_collection, date: str, time: str, start: dict = None, end: dict = None, url ="http://localhost:8080/otp/gtfs/v1"):
    for station in station_collection:
        station.queried_itineraries.clear()
        station.query_and_create_transit_itineraries(date, time, start, end)

def request_itineraries_from_start_to_each_station(station_collection, date: str, time: str, start: dict, start_time):
    possible_start_stations = []
    for item_index, station in enumerate(station_collection):
        station.query_and_create_transit_itineraries(date, time, start=start)
        print(len(station.queried_itineraries))
        station.filter_itineraries_with_permissible_catchment_area("start")
        station.filter_shortest_itinerary()
        for itinerary in station.itineraries_with_permissible_catchment_area:
            if possible_start_stations.count(itinerary.start_station) == 0:
                possible_start_stations.append(itinerary.start_station)
        print(f"{item_index}, {station.name}, shortest itinerary calculated; ")
    print("possible start stations: ", possible_start_stations)
    for station in station_collection:
        # TODO add the 2nd step, wehere I query orutes from explicite start stations, to find itineraries to endStations, which would be otherwise not reachable
        pass
        #if len(station.itineraries_with_permissible_catchment_area) == 0:


def create_stop_objects(queried_stops):
    # transferred to plugin
    stop_objects = []
    for data in queried_stops:
        stop = Stop(data["name"], data["gtfsId"], data["lat"], data["lon"], data["vehicleMode"])
        stop_objects.append(stop)
    return stop_objects.copy()

def create_stations(stop_collection):
    # transferred to plugin
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
    # transferred to plugin
    name_collection = []
    average_trip_time_collection = []
    car_driving_time_collection = []
    travel_time_ratio_collection = []
    average_number_of_transfers_collection = []
    average_walk_distance_of_trip_collection = []
    trip_frequency_collection = []
    itineraries_collection = []
    for station in station_collection:
        itineraries_data = ""
        name_collection.append(station.name)
        average_trip_time_collection.append(station.average_trip_time)
        car_driving_time_collection.append(station.car_driving_time)
        travel_time_ratio_collection.append(station.travel_time_ratio)
        average_number_of_transfers_collection.append(station.average_number_of_transfers)
        average_walk_distance_of_trip_collection.append(station.average_walk_distance_of_trip)
        trip_frequency_collection.append(station.trip_frequency)
        for itinerary in station.selected_itineraries:
            data = f"{itinerary.route_numbers}, duration: {itinerary.duration}, startStation: {itinerary.start_station}, endStation:{itinerary.end_station}; "
            itineraries_data = itineraries_data + data
        itineraries_collection.append(itineraries_data)
    df = pd.DataFrame(
        {
            "Name": name_collection,
            "travel_time_ratio": travel_time_ratio_collection,
            "average_number_of_transfers": average_number_of_transfers_collection,
            "trip_frequency_collection": trip_frequency_collection,
            "average_trip_time": average_trip_time_collection,
            "car_driving_time": car_driving_time_collection,
            "average_walk_distance_of_trip": average_walk_distance_of_trip_collection,
            "itinerary_overview": itineraries_collection
        }
    )
    return df

def create_street_network(map_data):
    nodes, edges = map_data.get_network(nodes=True, network_type="all")# TODO müsste ersetzt werden wenn kein Codna
    graph = map_data.to_graph(nodes, edges, graph_type="networkx")# TODO müsste ersetzt werden wenn kein Conda
    return graph
def create_isochrone_for_each_station(station_collection, street_network, start_time, radius = 300):
    isochrone_collection = []
    for item_index, station in enumerate(station_collection):
        isochrone = station.calculate_isochrone(street_network, radius = radius)
        isochrone_collection.append(isochrone)
        print(f"{item_index}: {station.name} isochrone berechnet", "--- %s seconds ---" % (time.time() - start_time))
    return isochrone_collection.copy()

def stationsToCSV(stationCollection):
    header = ["name", "meanLat", "meanLon"]
    with open("stations.csv", mode="w") as file:
        file.write(";".join(map(str, header)) + "\n")
        for station in stationCollection:
            data = [station.name, station.meanLat, station.meanLon]
            file.write(";".join(map(str, data)) + "\n")
    print("CSV file 'stations.csv' created successfully!!!")

def export_stations_as_geopackage(station_collection):
    # transferred to plugin
    mean_lat_collection = []
    mean_lon_collection = []
    for station in station_collection:
        mean_lat_collection.append(station.mean_lat)
        mean_lon_collection.append(station.mean_lon)
    station_attributes = create_dataframe_with_station_attributes(station_collection)
    gdf = gpd.GeoDataFrame(station_attributes, geometry=gpd.points_from_xy(mean_lon_collection, mean_lat_collection), crs="EPSG:4326")
    gdf.to_file("dataframe_Andreeplatz2.gpkg", driver='GPKG', layer='Andreeplatz2_to_all_stations')

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
#print(check_grizzly_server_is_running())

start_time = time.time()
stops_as_dict = query_all_stops(request_url)
all_stops = create_stop_objects(stops_as_dict)
all_stations = create_stations(all_stops)
print("all stations are created: ","--- %s seconds ---" % (time.time() - start_time))

andreeplatz2 = {"lat": 52.260760, "lon":  10.548780}
request_itineraries_from_start_to_each_station(all_stations[0:20], "2024-04-18", "11:30", andreeplatz2, start_time)
print("all Itineraries are calculated ","--- %s seconds ---" % (time.time() - start_time))

# export_stations_as_geopackage(all_stations[0:20])
# print("all stations are exported ","--- %s seconds ---" % (time.time() - start_time))

# osm = OSM("braunschweig_OPNV-Netz.osm.pbf") #TODO müsste ersetzt werden wenn kein Conda
# street_network = create_street_network(osm) #TODO müsste ersetzt werden wenn kein Conda
# create_isochrone_for_each_station(all_stations[0:3], street_network, start_time)
# export_isochrone_as_geopackage(all_stations[0:3])
# print("isochrones are exported")
# print("--- %s seconds ---" % (time.time() - start_time))


# destination = {"lat": 52.25251, "lon":  10.46810}
# # # requestItinerariesForEachStation(allStations, "2024-04-18", "11:30", end=destination)
# all_stations[0].query_and_create_transit_itineraries("2024-04-18", "11:30", end=destination)
# all_stations[0].filter_shortest_itinerary()

# for itineray in all_stations[0].queried_itineraries:
#     print(itineray.start_time)
#     print(itineray.duration)
#     print(itineray.modes)
#     print(itineray.route_numbers)
#     print()
# print(all_stations[0].name, all_stations[0].average_trip_time, all_stations[0].average_number_of_transfers, all_stations[0].average_walk_distance_of_trip)
#
# for item_index, station in enumerate(all_stations):
#    print(item_index, station.name, "lat:", station.mean_lat, "lon:", station.mean_lon)
# print("lat ", all_stations[131].mean_lat, " lon ", all_stations[131].mean_lon)




