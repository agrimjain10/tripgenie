"""Transparent India getaway matching. Costs and travel times are planning estimates."""
from math import asin, ceil, cos, radians, sin, sqrt
from datetime import datetime, timezone
from urllib.parse import urlencode
import httpx

# Approximate town centres, not live routes, timetables or hotel quotations.
_DATA = '''Manali|Himachal Pradesh|32.24|77.19|1350|4|Nature,Adventure,Food|Hadimba forest;Old Manali;Solang Valley|mountains|CDG|Chandigarh; allow a long onward road transfer to Manali
Shimla|Himachal Pradesh|31.10|77.17|1450|3|Nature,History,Photography|The Ridge;Jakhu area;heritage streets|shimla|KLK|Kalka; onward hill railway or road transfer required
Dharamshala|Himachal Pradesh|32.22|76.32|1250|3|Nature,Culture,Wellness|McLeod Ganj;monastery area;tea gardens|mountains|PTK|Pathankot; onward road transfer required
Dalhousie|Himachal Pradesh|32.54|75.97|1350|3|Nature,Photography,Wellness|Pine walks;Khajjiar area;old town|mountains|PTK|Pathankot; onward hill-road transfer required
Amritsar|Punjab|31.63|74.87|1100|2|Culture,History,Food|Golden Temple;Partition Museum;old-city food|amritsar|ASR|Amritsar Junction
Chandigarh|Chandigarh|30.73|76.78|1450|2|Nature,Markets,Food|Rock Garden;Sukhna Lake;Sector 17|city|CDG|Chandigarh
Rishikesh|Uttarakhand|30.09|78.27|1200|3|Nature,Adventure,Wellness|Ganga riverside;Tapovan;Triveni Ghat|rishikesh|YNRK|Yog Nagari Rishikesh; confirm service at your chosen station
Haridwar|Uttarakhand|29.95|78.16|1000|2|Culture,Wellness,Food|Har Ki Pauri;old markets;riverside walks|rishikesh|HW|Haridwar Junction
Mussoorie|Uttarakhand|30.46|78.07|1550|3|Nature,Photography,Food|Landour;Camel Back Road;hill viewpoints|mountains|DDN|Dehradun; onward hill-road transfer required
Nainital|Uttarakhand|29.38|79.46|1550|3|Nature,Photography,Markets|Naini Lake;Tibetan market;lake viewpoints|lake|KGM|Kathgodam; onward road transfer required
Jaipur|Rajasthan|26.91|75.79|1350|3|History,Culture,Markets,Food|Amber Fort;Hawa Mahal;Johari Bazaar|jaipur|JP|Jaipur Junction
Udaipur|Rajasthan|24.59|73.71|1450|3|Culture,Photography,Food|City Palace;Lake Pichola;old-city lanes|udaipur|UDZ|Udaipur City
Jodhpur|Rajasthan|26.24|73.02|1250|3|History,Culture,Photography|Mehrangarh Fort;blue-city lanes;clock tower|jaipur|JU|Jodhpur Junction
Pushkar|Rajasthan|26.49|74.55|1050|2|Culture,Wellness,Markets|Pushkar Lake;temple lanes;local markets|jaipur|AII|Ajmer; onward road transfer to Pushkar
Agra|Uttar Pradesh|27.18|78.01|1250|2|History,Culture,Photography|Taj Mahal;Agra Fort;Mehtab Bagh|agra|AGC|Agra Cantt
Varanasi|Uttar Pradesh|25.32|82.97|1150|3|Culture,History,Food|River ghats;Sarnath;old-city food|varanasi|BSB|Varanasi Junction; other city stations may be more convenient
Lucknow|Uttar Pradesh|26.85|80.95|1250|2|History,Food,Markets|Bara Imambara;Chowk;Gomti riverfront|city|LKO|Lucknow Charbagh
Orchha|Madhya Pradesh|25.35|78.64|1100|2|History,Culture,Nature|Fort complex;Betwa riverside;cenotaphs|jaipur|VGLJ|Virangana Lakshmibai Jhansi; onward road transfer
Pachmarhi|Madhya Pradesh|22.47|78.43|1400|3|Nature,Adventure,Photography|Forest walks;waterfalls;hill viewpoints|mountains|PPI|Pipariya; onward road transfer required
Goa|Goa|15.49|73.83|1750|4|Beaches,Food,Nightlife,Culture|Fontainhas;Candolim;Old Goa|goa|MAO|Madgaon; choose a station near your accommodation area
Gokarna|Karnataka|14.55|74.32|1300|3|Beaches,Nature,Wellness|Gokarna beach;Kudle Beach;coastal walks|coast|GOK|Gokarna Road; transfer to town and beaches required
Hampi|Karnataka|15.34|76.46|1250|3|History,Culture,Adventure|Temple ruins;river views;boulder landscapes|hampi|HPT|Hosapete; onward road transfer required
Mysuru|Karnataka|12.30|76.64|1250|2|Culture,History,Food|Mysore Palace;Devaraja Market;Chamundi area|city|MYS|Mysuru Junction
Coorg|Karnataka|12.42|75.74|1750|3|Nature,Food,Wellness|Coffee estates;Madikeri;Abbey Falls area|kerala|MYS|Mysuru; onward road transfer to Coorg required
Ooty|Tamil Nadu|11.41|76.69|1550|3|Nature,Photography,Wellness|Botanical Gardens;tea estates;Ooty Lake|mountains|MTP|Mettupalayam; onward hill railway or road transfer
Pondicherry|Puducherry|11.94|79.81|1550|3|Beaches,Culture,Food|French Quarter;Promenade;local cafes|coast|PDY|Puducherry
Munnar|Kerala|10.09|77.06|1550|3|Nature,Photography,Wellness|Tea landscapes;Mattupetty area;hill walks|kerala|ERS|Ernakulam; onward hill-road transfer to Munnar
Alleppey|Kerala|9.50|76.34|1450|3|Nature,Food,Wellness|Backwater village walks;beach;canal routes|kerala|ALLP|Alappuzha; boat experiences require separate confirmation
Kochi|Kerala|9.97|76.27|1450|3|Culture,Food,History|Fort Kochi;Mattancherry;waterfront|kerala|ERS|Ernakulam Junction; onward local transfer to Fort Kochi
Lonavala|Maharashtra|18.75|73.41|1450|2|Nature,Adventure,Photography|Hill viewpoints;Karla caves;town walks|mountains|LNL|Lonavala
Mahabaleshwar|Maharashtra|17.93|73.65|1550|3|Nature,Food,Photography|Venna Lake;hill viewpoints;local produce|lake|STR|Satara; onward road transfer required
Nashik|Maharashtra|20.00|73.79|1350|2|Culture,Food,Nature|Panchavati;vineyard region;old-town walks|city|NK|Nashik Road
Darjeeling|West Bengal|27.04|88.26|1550|4|Nature,Culture,Photography|Tea gardens;heritage railway area;town walks|mountains|NJP|New Jalpaiguri; long hill-road or heritage railway transfer
Gangtok|Sikkim|27.33|88.61|1650|4|Nature,Culture,Adventure|MG Marg;monasteries;local viewpoints|mountains|NJP|New Jalpaiguri; onward road transfer and permit checks
Shillong|Meghalaya|25.58|91.89|1650|4|Nature,Food,Adventure|Ward Lake;local markets;waterfall region|lake|GHY|Guwahati; onward hill-road transfer required
Puri|Odisha|19.81|85.83|1250|3|Beaches,Culture,Food|Puri beach;heritage streets;Konark day option|coast|PURI|Puri
Ahmedabad|Gujarat|23.02|72.57|1350|2|History,Culture,Food|Old-city heritage;Sabarmati;local food|city|ADI|Ahmedabad Junction
Mount Abu|Rajasthan|24.59|72.71|1500|3|Nature,Culture,Photography|Nakki Lake;Dilwara area;hill walks|lake|ABR|Abu Road; onward hill-road transfer required'''

DESTINATIONS = []
for row in _DATA.splitlines():
    name, region, lat, lon, daily, days, tags, sights, image, station, railhead = row.split('|')
    DESTINATIONS.append(dict(name=name, region=region, lat=float(lat), lon=float(lon), daily=int(daily), ideal_days=int(days), tags=tags.split(','), highlights=sights.split(';'), image='/images/'+{'shimla':'mountains','rishikesh':'lake','hampi':'city','varanasi':'journey','city':'journey','udaipur':'lake'}.get(image,image)+'.jpg', station=station, railhead=railhead))

for place in DESTINATIONS:
    if place['name'] in ('Chandigarh','Dharamshala'):place['image']='/images/'+place['name'].lower()+'.jpg'

HUBS = [('Delhi',28.61,77.21,'NDLS'),('Jalandhar',31.33,75.58,'JUC'),('Ludhiana',30.90,75.86,'LDH'),('Pathankot',32.27,75.65,'PTK'),('Jammu',32.73,74.86,'JAT'),('Mumbai',19.08,72.88,'CSMT'),('Pune',18.52,73.86,'PUNE'),('Bengaluru',12.97,77.59,'SBC'),('Chennai',13.08,80.27,'MAS'),('Hyderabad',17.39,78.49,'SC'),('Kolkata',22.57,88.36,'HWH'),('Dehradun',30.32,78.03,'DDN'),('Guwahati',26.14,91.74,'GHY'),('Bhopal',23.26,77.41,'BPL'),('Indore',22.72,75.86,'INDB'),('Nagpur',21.15,79.09,'NGP'),('Surat',21.17,72.83,'ST'),('Vadodara',22.31,73.18,'BRC'),('Kozhikode',11.26,75.78,'CLT'),('Thiruvananthapuram',8.52,76.94,'TVC'),('Coimbatore',11.02,76.96,'CBE'),('Madurai',9.93,78.12,'MDU'),('Patna',25.59,85.14,'PNBE'),('Ranchi',23.34,85.31,'RNC'),('Bhubaneswar',20.30,85.82,'BBS'),('Raipur',21.25,81.63,'R'),('Visakhapatnam',17.69,83.22,'VSKP')]
PLACES = [dict(name=n,lat=a,lon=b,station=s,region='India',railhead=n) for n,a,b,s in HUBS] + DESTINATIONS
ALIASES = {'new delhi':'delhi','bangalore':'bengaluru','bombay':'mumbai','calcutta':'kolkata','banaras':'varanasi','kashi':'varanasi','pondicherry':'pondicherry','puducherry':'pondicherry','mysore':'mysuru','alappuzha':'alleppey','gurgaon':'delhi','gurugram':'delhi','noida':'delhi'}

def km(a, b):
    lat1, lat2 = radians(a['lat']), radians(b['lat'])
    dlat, dlon = lat2-lat1, radians(b['lon']-a['lon'])
    return 6371*2*asin(min(1,sqrt(sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2)))

def known_place(name):
    query=name.strip().lower().split(',')[0].strip()
    query=ALIASES.get(query,query)
    return next((dict(p) for p in PLACES if p['name'].lower()==query),None)

def resolve_place(name):
    place=known_place(name)
    if place:return place
    with httpx.Client(timeout=5) as c:
        r=c.get('https://geocoding-api.open-meteo.com/v1/search',params={'name':name.strip(),'count':5,'language':'en','format':'json','countryCode':'IN'})
        r.raise_for_status()
        result=next((x for x in r.json().get('results',[]) if x.get('country_code')=='IN'),None)
    if not result:raise ValueError('We could not locate that Indian city. Try a nearby larger city or choose a suggestion.')
    return dict(name=result['name'],lat=result['latitude'],lon=result['longitude'],region=result.get('admin1','India'),station=None,railhead='Confirm the most convenient station for this city')

def nearest_city(lat,lon):
    if not (6<=lat<=38 and 68<=lon<=98):raise ValueError('Getaway discovery currently covers India. Enter an Indian starting city.')
    point={'lat':lat,'lon':lon}
    city=min(PLACES,key=lambda p:km(point,p));distance=round(km(point,city))
    if distance>180:raise ValueError('No nearby city is in our offline location list. Enter your starting city manually.')
    return {'name':city['name'],'region':city.get('region','India'),'approximate':True,'distance_km':distance,'message':f"Using {city['name']} as your approximate starting point ({distance} km from a known city centre). You can edit it."}

def suggest(payload):
    origin=resolve_place(payload.origin)
    ranked=[]
    interests={x.lower() for x in payload.interests}
    for place in DESTINATIONS:
        distance=km(origin,place)
        if distance<20:continue
        road=distance*1.35
        if payload.travel_mode=='Flight' and distance<350:continue
        mode=payload.travel_mode
        hours=(distance/650+4.5 if distance>350 else road/45+1) if mode=='Flight' else road/({'Car':48,'Bike':35,'Bus':40,'Train':57,'Flexible':45}[mode])+(.5 if mode in ('Car','Bike') else 1.5)
        if mode=='Train' and ';' in place['railhead']:hours+=2
        usable=payload.days*12-hours*2
        if usable<max(5,payload.days*3.5) or (payload.days==1 and hours>2.5):continue
        people=payload.travelers
        transport=(max(4500,distance*5)*2*people if mode=='Flight' and distance>350 else max(200,road*({'Car':10,'Bike':3.5,'Bus':1.8,'Train':1.4,'Flight':2,'Flexible':1.8}[mode]))*2*(ceil(people/4) if mode=='Car' else ceil(people/2) if mode=='Bike' else people))
        nights=max(payload.days-1,0)
        rooms=ceil(people/2)
        stay=nights*min(650*people,1800*rooms)
        food=450*people*payload.days
        local=max(250,place['daily']-1000)*people*max(1,payload.days-1)
        subtotal=transport+stay+food+local
        estimated=round(subtotal*1.12/100)*100
        matches=[t for t in place['tags'] if t.lower() in interests]
        fit=estimated*1.25<=payload.budget
        score=50+len(matches)*12+min(20,usable/payload.days)-hours*1.5-abs(payload.days-place['ideal_days'])*2-(0 if fit else 35+(estimated-payload.budget)/payload.budget*20)
        item={k:place[k] for k in ('name','region','tags','highlights','image','station','railhead')}
        item.update(distance_km=round(road),one_way_hours=round(hours,1),usable_hours=round(usable),estimated_total=estimated,cost_range=[round(estimated*.85/100)*100,round(estimated*1.25/100)*100],within_budget=fit,match_reasons=([f"Matches {', '.join(matches)}"] if matches else ['A different kind of escape to consider'])+[f"About {round(hours,1)} hours each way; {round(usable)} daytime hours left to explore",'The full planning range fits your budget' if fit else 'The upper planning range exceeds your budget; adjust before booking'],budget_breakdown={'return_travel':round(transport),'stay':round(stay),'food':round(food),'local_and_activities':round(local),'buffer':max(0,estimated-round(subtotal))},score=round(score),travel_mode=mode)
        ranked.append(item)
    ranked.sort(key=lambda r:(r['within_budget'],r['score']),reverse=True)
    feasible=[r for r in ranked if r['within_budget']]
    return {'origin':origin['name'],'results':(feasible or ranked)[:9],'within_budget_count':len(feasible),'message':'Destinations ranked by your time, budget, interests and travel mode.' if feasible else 'No comfortable match fits every limit. These are stretch options: increase your budget/days or try a closer starting city.' if ranked else 'No comfortable trip fits this travel window. Try another travel mode or add a day.','estimate_note':'Distances use straight-line distance × a road factor. Travel time and group costs are rough planning estimates, not mapped routes, train fares, flight availability or hotel quotations. Longer mountain transfers can take substantially more time.'}
