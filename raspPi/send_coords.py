import requests

#send latitude and longitude to the server

def send_coords(lat, lon, token):
    url = "http://www.example.com"
    payload = {
        "lat": lat, 
        "lon": lon,
        "token": token
        }

    try:
        #send request
        response = requests.post(url, json=payload, timeout=5)
        
        #if response is not ok
        response.raise_for_status()
        

        return response.json()
    except requests.RequestException as e:
        print("Error sending coordinates:", e)
        return None

