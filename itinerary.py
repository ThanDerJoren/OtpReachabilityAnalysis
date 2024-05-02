class Itinerary:
    startTime: float
    duration: float
    numberOfTransfers: int
    walkDistance: float
    modes = []
    routeNumbers = []

    def __init__(self, startTime, duration, numberOfTransfers, walkDistance, modes, routeNumbers):
        self.startTime = startTime
        self.duration = duration
        self.numberOfTransfers = numberOfTransfers
        self.walkDistance = walkDistance
        self.modes = modes.copy()
        self.routeNumbers = routeNumbers.copy()

