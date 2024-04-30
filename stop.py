class Stop:
    name: str
    gtfsId: str
    lat: float
    lon: float
    vehicleMode: str

    def __init__(self, name, gtfsId, lat, lon, vehicleMode):
        self.name = name
        self.gtfsId = gtfsId
        self.lat = lat
        self.lon = lon
        self.vehicleMode = vehicleMode
