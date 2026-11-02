"""Rail provider adapter and real OpenStreetMap stay discovery; no invented inventory."""
import logging
import os
import time
from math import ceil
from urllib.parse import quote, urlencode, urlparse
import httpx
from discovery_service import resolve_place, known_place

# IndianRailAPI puts credentials in the URL path. Do not emit request URLs.
logging.getLogger('httpx').setLevel(logging.WARNING)
_stay_cache = {}

def rail_options(trip, from_station=None, to_station=None):
    source=known_place(trip.origin or '')
    target=known_place(trip.destination)
    departure=from_station or (source or {}).get('station')
    arrival=to_station or (target or {}).get('station')
    result={'configured':bool(os.getenv('INDIAN_RAIL_API_KEY')),'available':False,'trains':[],'from_station':departure,'to_station':arrival,'railhead_note':(target or {}).get('railhead','Choose the destination railway station; there may be an onward road transfer.'),'travel_date':trip.start_date,'booking_url':'https://www.irctc.co.in/nget/train-search','enquiry_url':'https://enquiry.indianrail.gov.in/','search_url':'https://www.google.com/search?'+urlencode({'q':f'{trip.origin or ""} to {trip.destination} trains {trip.start_date}'}),'message':'Live train timetables need a connected IndianRailAPI account. Station guidance and official search links are available now.'}
    if not departure or not arrival:
        result['message']='Enter station codes to search this route. Station choice and last-mile travel matter.'
        return result
    if departure==arrival:
        result['message']='Both places use the same railhead. Plan the onward road journey rather than a train between identical stations.'
        return result
    key=os.getenv('INDIAN_RAIL_API_KEY','').strip()
    if not key:return result
    try:
        with httpx.Client(timeout=7) as client:
            response=client.get(f'https://indianrailapi.com/api/v2/TrainBetweenStation/apikey/{quote(key,safe="")}/From/{departure}/To/{arrival}/')
            response.raise_for_status();data=response.json()
        if str(data.get('ResponseCode'))!='200':raise ValueError('provider unavailable')
        result.update(available=True,source='IndianRailAPI',checked_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),message='Provider timetable results, not live seat availability or confirmed operation on your travel date. Verify running days, fares and availability before booking.',trains=[{'number':str(t.get('TrainNo','')),'name':str(t.get('TrainName','')),'departure':str(t.get('DepartureTime','')),'arrival':str(t.get('ArrivalTime','')),'duration':str(t.get('TravelTime',''))} for t in data.get('Trains',[])[:30]])
    except (httpx.HTTPError,ValueError,TypeError,KeyError):
        result['message']='The timetable provider is unavailable. Use official enquiry and booking links; no train times or fares have been guessed.'
    return result

def safe_website(value):
    if not value:return None
    if ':' in value.split('/')[0] and not value.startswith(('https://','http://')):return None
    if not value.startswith(('https://','http://')):value='https://'+value
    parsed=urlparse(value)
    return value if parsed.scheme in ('https','http') and parsed.hostname and not parsed.username else None

def stay_options(trip):
    place=resolve_place(trip.destination)
    query={'ss':trip.destination+', India','checkin':trip.start_date,'checkout':trip.end_date,'group_adults':trip.travelers or 1,'no_rooms':ceil((trip.travelers or 1)/2),'group_children':0}
    if trip.start_date==trip.end_date:
        query.pop('checkin');query.pop('checkout')
    result={'available':False,'stays':[],'destination':place['name'],'booking_url':'https://www.booking.com/searchresults.html?'+urlencode(query),'hotels_url':'https://www.google.com/travel/hotels?'+urlencode({'q':trip.destination+' hotels'}),'maps_url':'https://www.google.com/maps/search/?'+urlencode({'api':1,'query':trip.destination+' hotels hostels guesthouses'}),'message':'Real map listings, not verified rooms or live prices. Confirm dates, taxes, reviews and cancellation terms with the property.','source':'OpenStreetMap contributors','attribution_url':'https://www.openstreetmap.org/copyright'}
    key=(round(place['lat'],3),round(place['lon'],3))
    cached=_stay_cache.get(key)
    if cached and time.monotonic()-cached[0]<900:
        return {**result,'available':bool(cached[1]),'stays':cached[1],'checked_at':cached[2]}
    try:
        q=f'[out:json][timeout:5];nwr(around:5000,{place["lat"]},{place["lon"]})["tourism"~"^(hotel|guest_house|hostel)$"]["name"];out center tags 45;'
        with httpx.Client(timeout=7,headers={'User-Agent':'Wandiamo/1.0 (travel planning; cached destination lookups)'}) as client:
            response=client.post('https://overpass.private.coffee/api/interpreter',data={'data':q});response.raise_for_status()
            elements=response.json().get('elements',[])
        seen=set();stays=[]
        for item in elements:
            tags=item.get('tags',{});name=str(tags.get('name','')).strip()
            if not name or name.lower() in seen:continue
            seen.add(name.lower())
            stays.append({'name':name,'type':tags.get('tourism','hotel').replace('_',' '),'address':', '.join(str(tags[k]) for k in ('addr:street','addr:suburb','addr:city') if tags.get(k)) or place['name'],'website':safe_website(tags.get('website') or tags.get('contact:website')),'map_url':f'https://www.openstreetmap.org/{item["type"]}/{item["id"]}','price':None,'availability':None})
        stays=stays[:12];checked=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        if len(_stay_cache)>100:_stay_cache.clear()
        _stay_cache[key]=(time.monotonic(),stays,checked)
        result.update(available=bool(stays),stays=stays,checked_at=checked)
        if not stays:result['message']='No named stays were returned by the map provider here. Compare options with the destination search links.'
    except (httpx.HTTPError,ValueError,TypeError,KeyError):
        result['message']='Map listings are temporarily unavailable. Your destination, dates and group size are ready in the booking search below.'
    return result
