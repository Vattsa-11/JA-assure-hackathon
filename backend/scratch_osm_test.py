import requests

q = '''
[out:json];
area["ISO3166-1"="SG"][admin_level=2]->.searchArea;
node["shop"="jewelry"]["name"](area.searchArea);
out center 5;
'''
r = requests.post('http://overpass-api.de/api/interpreter', data={'data': q})
print(r.status_code)
print(r.json())
