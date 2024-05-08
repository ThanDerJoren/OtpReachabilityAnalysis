import json
import datetime
import requests

from pyrosm import OSM
import osmnx as ox
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point

from stop import Stop # used in relatedStops
from itinerary import Itinerary
class Station:
    name: str
    meanLat: float = 0.0
    meanLon: float = 0.0
    relatedStops = []

    averageTripTime: float
    carDrivingTime: float
    travelTimeRatio: float
    averageNumberOfTransfers: float
    averageWalkDistanceOfTrip: float
    tripFrequency: float
    carItinerary: Itinerary
    possibleItineraries = []
    filteredItineraries = []

    def __init__(self, name, relatedStops):
        self.name = name
        self.relatedStops = relatedStops  # pass by value? That's important
        for stop in self.relatedStops:
            self.meanLat += stop.lat
            self.meanLon += stop.lon
        self.meanLat = self.meanLat/len(self.relatedStops)
        self.meanLon = self.meanLon/len(self.relatedStops)

    def getPosition(self):
        position = {"lat": self.meanLat, "lon": self.meanLon}
        return position

    def queryTransitItineraries(self, date: str, time: str, start: dict = None, end: dict = None, url = "http://localhost:8080/otp/gtfs/v1"):
        date = f"\"{date}\""
        time = f"\"{time}\""

        if start is None and end is not None:
            start = self.getPosition()
        elif start is not None and end is None:
            end = self.getPosition()
        elif start is not None and end is not None:
            print("The current station has to be either start ot end.\n This function is not intended to plan a route, which dosen't include the current station")
        else:
            print("It has to be pass one: start or end, otherwise the route will be from 'A to A'")

        plan = f"""
            {{plan(
                date: {date},
                time: {time},
                from: {{ lat: {start["lat"]}, lon: {start["lon"]}}},
                to: {{ lat: {end["lat"]}, lon: {end["lon"]}}},
                transportModes: [{{mode: TRANSIT}}, {{mode: WALK}}]
                ){{
                    itineraries{{
                        startTime,
                        duration,
                        numberOfTransfers,
                        walkDistance,
                        legs{{
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
            routeNumbers = []
            for item in element["legs"]:
                modes.append(item["mode"])
                if item["route"] is not None:
                    routeNumbers.append(item["route"]["shortName"])
                else:
                    routeNumbers.append(item["route"])

            itinerary = Itinerary(
                datetime.datetime.fromtimestamp(element["startTime"]/1000.0),  #Unix timestamp in milliseconds to datetime. /1000.0 beacause of milliseconds
                round(element["duration"]/60), # seconds in minutes
                element["numberOfTransfers"],
                element["walkDistance"],
                modes,
                routeNumbers
            )
            self.possibleItineraries.append(itinerary)
        print(f"{self.name}: all itineraries added.")


    def filterShortestItinerary(self):  #ATTENTION: Only for developement purpose
        self.filteredItineraries.clear()
        self.filteredItineraries.append(self.possibleItineraries[0])
        for itinerary in self.possibleItineraries:
            if itinerary.duration < self.filteredItineraries[0].duration:
                self.filteredItineraries[0] = itinerary

        self.averageTripTime = self.filteredItineraries[0].duration
        self.averageNumberOfTransfers = self.filteredItineraries[0].numberOfTransfers
        self.averageWalkDistanceOfTrip = self.filteredItineraries[0].walkDistance


    def calculate_isoline(self, G, G_in_utm, radius = 300):
        center_node = ox.nearest_nodes(G, self.meanLon, self.meanLat)
        subgraph = nx.ego_graph(G_in_utm,center_node, radius = radius, distance = "length")
        node_points = [Point((data["x"], data["y"])) for node, data in subgraph.nodes(data=True)]
        bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
        return bounding_poly