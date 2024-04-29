from itinerary import Itinerary
class Stop:
    name: str
    gtfsId: str
    lat: float
    lon: float
    averageTripTime: float
    carDrivingTime: float
    travelTimeRatio: float
    averageNumberOfTransfers: float
    averageWalkDistanceOfTrip: float
    tripFrequency: float
    possibleItineraries: list
    filteredItineraries: list
    carItinerary: Itinerary

    def __init__(self, name, gtfsId, lat, lon):
        self.name = name
        self.gtfsId = gtfsId
        self.lat = lat
        self.lon = lon


