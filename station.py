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

    def queryItineraries(self, date: str, time: str, transportModes: list, start: dict = None, end: dict = None, url = "http://localhost:8080/otp/gtfs/v1"):
        if start is None and end is not None:
            start = self.getPosition()
        elif start is not None and end is None:
            end = self.getPosition()
        elif start is not None and end is not None:
            print("The current station has to be either start ot end.\n This function is not intended to plan a route, which dosen't include the current station")
        else:
            print("It has to be pass one: start or end, otherwise the route will be from 'A to A'")

        plan = "{plan"
