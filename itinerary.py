class Itinerary:
    duration: float
    numberOfTransfers: int
    walkDistance: float
    car: bool

    def __init(self, duration, numberOfTransfers, walkDistance, car):
        self.duration = duration
        self.numberOfTransfers = numberOfTransfers
        self.walkDistance = walkDistance
        self.car = car
