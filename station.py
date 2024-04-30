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