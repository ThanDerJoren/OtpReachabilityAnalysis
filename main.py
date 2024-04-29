import requests, json
from stop import Stop

allStops = requests.post("http://localhost:8080/otp/gtfs/v1", json={"query": "{stops{name, gtfsId, lat, lon}}"})
allStops =json.loads(allStops.content)
print(allStops)
