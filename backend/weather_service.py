"""Small cached public weather preview for the landing page's three sample cities."""
import time
import httpx
from functools import lru_cache

CITIES={'Manali':(32.24,77.19),'Goa':(15.50,73.83),'Jaipur':(26.91,75.79)}

@lru_cache(maxsize=12)
def _weather(city,bucket):
    lat,lon=CITIES[city]
    try:
        with httpx.Client(timeout=7) as client:
            response=client.get('https://api.open-meteo.com/v1/forecast',params={'latitude':lat,'longitude':lon,'current':'temperature_2m,weather_code','timezone':'Asia/Kolkata'})
            response.raise_for_status();current=response.json().get('current',{})
        temperature=current.get('temperature_2m')
        if not isinstance(temperature,(int,float)) or not -65<temperature<65:raise ValueError('Invalid temperature')
        return {'available':True,'city':city,'temperature':round(temperature),'time':current.get('time'),'source':'Open-Meteo'}
    except (httpx.HTTPError,ValueError,TypeError):
        return {'available':False,'city':city,'message':'Weather is temporarily unavailable.','source':'Open-Meteo'}

def destination_weather(city):
    return _weather(city,int(time.time()//900))
