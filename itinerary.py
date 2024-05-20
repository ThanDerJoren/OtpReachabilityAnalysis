class Itinerary:
    start_time: float
    start_station: str
    end_station: str
    duration: float
    number_of_transfers: int
    walk_distance: float
    distance_to_start_station: float
    distance_from_end_station: float
    modes = []
    route_numbers = []

    def __init__(self, startTime, startStation, endStation, duration, numberOfTransfers, walkDistance, distanceToStartStation, distanceFromEndStation, modes, routeNumbers):
        self.start_time = startTime
        self.start_station = startStation
        self.end_station = endStation
        self.duration = duration
        self.number_of_transfers = numberOfTransfers
        self.walk_distance = walkDistance
        self.distance_to_start_station = distanceToStartStation
        self.distance_from_end_station = distanceFromEndStation
        self.modes = modes.copy()
        self.route_numbers = routeNumbers.copy()
        print(startStation, endStation, duration, routeNumbers)

