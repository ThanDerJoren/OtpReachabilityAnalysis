import json
import datetime
import requests

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point
from shapely.geometry import Polygon

from stop import Stop # used in relatedStops
from itinerary import Itinerary
class Station:




    def __init__(self, name, related_stops):
        self.name = name
        self.related_stops = related_stops  # pass by value? That's important
        for stop in self.related_stops:
            self.mean_lat += stop.lat
            self.mean_lon += stop.lon
        self.mean_lat = self.mean_lat / len(self.related_stops)
        self.mean_lon = self.mean_lon / len(self.related_stops)
        self.isochrone: Polygon

        self.average_trip_time: float = None
        self.car_driving_time: float = None
        self.travel_time_ratio: float = None
        self.average_number_of_transfers: float = None
        self.average_walk_distance_of_trip: float = None
        self.trip_frequency: float = None
        self.car_itinerary: Itinerary
        self.queried_itineraries = []
        self.itineraries_with_permissible_catchment_area = []
        self.selected_itineraries = []

    def get_position(self):
        position = {"lat": self.mean_lat, "lon": self.mean_lon}
        return position

    def query_and_create_transit_itineraries(self, date: str, time: str, start: dict = None, end: dict = None, url ="http://localhost:8080/otp/gtfs/v1"):
        date = f"\"{date}\""
        time = f"\"{time}\""

        if start is None and end is not None:
            start = self.get_position()
        elif start is not None and end is None:
            end = self.get_position()
        elif start is not None and end is not None:
            print("The current station has to be either start or end.\n This function is not intended to plan a route, which dosen't include the current station")
        else:
            print("It has to be pass one: start or end, otherwise the route will be from 'A to A'")
        plan = f"""
            {{plan(
                date: {date},
                time: {time},
                from: {{ lat: {start["lat"]}, lon: {start["lon"]}}},
                to: {{ lat: {end["lat"]}, lon: {end["lon"]}}},
                transportModes: [{{mode: TRANSIT}}, {{mode: WALK}}]
                numItineraries: 20
                walkReluctance: 3.0
                searchWindow: 3600
                ){{
                    itineraries{{
                        startTime,
                        duration,
                        numberOfTransfers,
                        walkDistance,
                        legs{{
                            from{{name}}
                            to{{name}}
                            distance                            
                            mode
                            route{{shortName}}
                        }}       
                    }}
                }}
            }}
        """
        queriedPlan = requests.post(url, json={"query": plan})
        queriedPlan = json.loads(queriedPlan.content)
        itineraries = queriedPlan["data"]["plan"]["itineraries"]
        for element in itineraries:
            modes = []
            route_numbers = []
            start_station = "" # hierdurch entseht der leere eintrag in possible start stations. it needs to be an empty string. If the shortest route is walking, there will be no start station
            end_station = ""
            distance_to_start_station: float
            distance_from_end_station: float
            first_transit_mode = True
            for item in element["legs"]:
                modes.append(item["mode"])
                if first_transit_mode and item["mode"] != "WALK":
                    start_station = item["from"]["name"]
                    first_transit_mode = False
                if item["mode"] != "WALK":
                    end_station = item["to"]["name"]
                if item["route"] is not None:
                    route_numbers.append(item["route"]["shortName"])
                else:
                    route_numbers.append(item["mode"])
            if element["legs"][0]["mode"] == "WALK":
                distance_to_start_station = element["legs"][0]["distance"]
            else:
                distance_to_start_station = 0
            if element["legs"][-1]["mode"] == "WALK":
                distance_from_end_station = element["legs"][-1]["distance"]
            else:
                distance_from_end_station = 0
            itinerary = Itinerary(
                datetime.datetime.fromtimestamp(element["startTime"]/1000.0),  #Unix timestamp in milliseconds to datetime. /1000.0 beacause of milliseconds
                start_station,
                end_station,
                round(element["duration"]/60), # seconds in minutes
                element["numberOfTransfers"],
                element["walkDistance"],
                distance_to_start_station,
                distance_from_end_station,
                modes,
                route_numbers
            )
            self.queried_itineraries.append(itinerary)

    def filter_itineraries_with_permissible_catchment_area(self, start_or_end_station, catchment_area = 300):
        if start_or_end_station == "start":
            for itinerary in self.queried_itineraries:
                if itinerary.distance_to_start_station <= catchment_area:
                    self.itineraries_with_permissible_catchment_area.append(itinerary)
        elif start_or_end_station == "end":
            print("from all station to one end is not implemented yet")
        else:
            print("It has to be pass either 'start' or 'end'")

    def filter_shortest_itinerary(self):
        if len(self.itineraries_with_permissible_catchment_area)>0:
            self.selected_itineraries.append(self.itineraries_with_permissible_catchment_area[0])
            for itinerary in self.itineraries_with_permissible_catchment_area:
                if itinerary.duration < self.selected_itineraries[0].duration:
                    self.selected_itineraries[0] = itinerary

            self.average_trip_time = self.selected_itineraries[0].duration
            self.average_number_of_transfers = self.selected_itineraries[0].number_of_transfers
            self.average_walk_distance_of_trip = self.selected_itineraries[0].walk_distance


    def calculate_isochrone(self, G, radius = 300):
        center_node = ox.nearest_nodes(G, self.mean_lon, self.mean_lat) #TODO müsste ersetzt werden, wenn kein conda
        subgraph = nx.ego_graph(G,center_node, radius = radius, distance = "length")
        node_points = [Point((data["x"], data["y"])) for node, data in subgraph.nodes(data=True)]
        self.isochrone = gpd.GeoSeries(node_points).unary_union.convex_hull