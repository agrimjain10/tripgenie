"""Local starter routes for a useful workspace when the AI provider is unavailable.
These are planning ideas, not verified inventory or live price quotations.
"""
ROUTES = {
    'mountain': [('Old Manali', 'Hadimba Devi Temple', 'Manali Mall Road'), ('Solang Valley', 'Palchan village', 'Old Manali cafes'), ('Naggar village', 'Naggar Castle area', 'Beas riverside'), ('Vashisht village', 'Vashisht temple area', 'Manali local market'), ('Van Vihar', 'Tibetan Monastery', 'Old Manali')],
    'jaipur': [('Hawa Mahal area', 'City Palace', 'Johari Bazaar'), ('Amber Fort', 'Panna Meena ka Kund', 'Jal Mahal viewpoint'), ('Albert Hall Museum', 'Bapu Bazaar', 'MI Road')],
    'goa': [('Fontainhas', 'Panjim riverside', 'Miramar Beach'), ('Candolim Beach', 'Fort Aguada', 'Sinquerim Beach'), ('Old Goa', 'Reis Magos area', 'Panjim market'), ('Anjuna village', 'Vagator viewpoint', 'Chapora village')],
    'udaipur': [('City Palace area', 'Lake Pichola promenade', 'Gangaur Ghat'), ('Saheliyon ki Bari', 'Fateh Sagar Lake', 'Hathi Pol market'), ('Old city streets', 'Bagore ki Haveli area', 'Ambrai Ghat')],
    'rishikesh': [('Triveni Ghat', 'Rishikesh old town', 'Ganga riverside'), ('Tapovan', 'Ram Jhula area', 'Parmarth Niketan area'), ('Swarg Ashram', 'Local craft shops', 'Tapovan cafes')],
    'shimla': [('The Ridge', 'Christ Church area', 'Mall Road'), ('Jakhu area', 'Lakkar Bazaar', 'Scandal Point'), ('Kufri village', 'Himalayan Nature Park area', 'Shimla town')],
}

def enrich(trip, plan):
    name=trip.destination.lower()
    key=next((key for key in ('jaipur','goa','udaipur','rishikesh','shimla') if key in name), None)
    if any(word in name for word in ('manali','himachal','kullu')):
        key='mountain'
    route=ROUTES.get(key)
    if not route:
        return detailed_sections(trip, plan, trip.destination)
    base='Manali' if key=='mountain' else trip.destination
    plan['summary']=f"A flexible {len(plan['days'])}-day starter itinerary based around {base}. The route groups nearby places and leaves time to slow down. Costs are budget allowances, not current ticket or hotel quotations."
    if 'himachal' in name:
        plan['summary']+=' Manali is used as a single base so the plan avoids rushing across the state.'
    for index,day in enumerate(plan['days']):
        places=route[index % len(route)]
        day['title']=['A gentle arrival and a first look','A little further into the destination','Local stories and slow discoveries'][index%3]
        verbs=['Explore','Spend time around','Wind down near']
        for activity,place,verb in zip(day['activities'],places,verbs):
            activity['activity']=f'{verb} {place}'
            activity['location']=place+', '+base
    plan['stay_recommendations'][0]['area']={'mountain':'Old Manali or central Manali','goa':'Panjim or Candolim','jaipur':'C-Scheme or Bani Park','udaipur':'Old city or Fateh Sagar area','rishikesh':'Tapovan','shimla':'Mall Road outskirts'}.get(key,base)
    if key in ('mountain','shimla'):
        plan['packing_list']+=['Warm layers and a windproof jacket','Shoes with good grip']
        plan['tips'].append('Mountain weather and road access can change. Confirm conditions locally before longer outings.')
    plan['tips'].append('Check entry rules, ticket prices, and opening hours for each place before visiting.')
    plan['booking_guidance']='This locally curated starter route is available when Gemini cannot respond. All costs are rough planning allowances. Check current provider prices, opening hours, road conditions, and availability before booking.'
    return detailed_sections(trip, plan, base, key=='mountain')

def detailed_sections(trip, plan, base, mountain=False):
    count=len(plan['days']);party=trip.travelers or 1
    plan['calendar_accounting']={'total_days':count,'hotel_nights':max(count-1,0),'transit_nights':0,'sightseeing_days':count}
    plan['route_summary']=f"{trip.origin+' → ' if trip.origin else ''}{base} → nearby sights{(' → '+trip.origin) if trip.origin else ''}"
    plan['timing_notes']=f"The chosen dates cover {count} calendar days including travel. Exact arrival, departure and accommodation nights depend on the confirmed transport schedule; do not book accommodation until those timings are checked."
    plan['journey']=[]
    budget=plan['budget_breakdown']
    labels={'stay':'Accommodation allowance','food':'Meals, snacks and cafes','activities':'Entry fees and optional activities','transport':'Return journey and local travel','misc':'Unspent contingency reserve'}
    plan['budget_line_items']=[{'category':key,'item':labels[key],'quantity':1,'unit_cost':value,'total':value,'notes':'Group planning allowance, not a current price quotation.'} for key,value in budget.items()]
    for day in plan['days']:
        day['overnight']=f"Accommodation in {base}; confirm the number of hotel nights after transport timings are booked."
        day['notes']='Keep meal and rest breaks, confirm opening hours, and return before it gets too late. Day costs cover local food/activity allowances; accommodation and intercity transport are counted in the overall budget.'
        for index,activity in enumerate(day['activities']):
            activity['description']=f"Spend unhurried time around {activity['location']}. Check entry conditions on arrival and allow time for photos, a local meal, and rest rather than rushing to another part of the destination."
            activity['travel_tip']='Group this stop with nearby places. Use walking or a licensed local taxi, and confirm the fare before setting out.'
    plan['booking_checklist']=['Confirm return transport prices and pickup/drop locations for every traveler.','Check hotel cancellation rules, taxes, check-in time, and ID requirements.','Keep the contingency reserve separate from daily spending.','Check current opening hours and access conditions before committing to paid activities.']
    plan['alternatives']=['If bad weather or a closure affects an outing, replace it with a nearby indoor or local option.','If a private taxi exceeds the allowance, compare a shared tour or reduce the route.','Keep expensive adventure activities optional so the core trip remains within budget.']
    if mountain and trip.origin and 'delhi' in trip.origin.lower() and count>=3:
        nights=max(count-3,0);sightseeing=max(count-2,1)
        plan['calendar_accounting']={'total_days':count,'hotel_nights':nights,'transit_nights':2,'sightseeing_days':sightseeing}
        total=float(trip.budget) if trip.budget and trip.budget>0 else 18000
        intercity=1500*party*2
        room_night=1200*max(1,(party+1)//2)
        food=350*party*sightseeing
        local=2000 if count>=5 else 800
        activity_total=700 if count>=5 else 300
        core=intercity+room_night*nights+food+local+activity_total
        reserve=max(total-core,0)
        lines=[{'category':'transport','item':'Delhi–Manali return bus seats','quantity':party*2,'unit_cost':1500,'total':intercity,'notes':'One seat per person each way. INR 1,500 is a planning allowance per seat, not a confirmed fare; seasonal rates may be higher.'}]
        if nights:
            lines.append({'category':'stay','item':'Budget room accommodation','quantity':nights,'unit_cost':room_night,'total':room_night*nights,'notes':f'{nights} hotel nights; nights on overnight buses are separate. Check heating, hot water, taxes, and actual room occupancy.'})
        lines += [
            {'category':'food','item':'Meals, snacks and cafes','quantity':sightseeing,'unit_cost':350*party,'total':food,'notes':'A modest group allowance per day at the destination. Transit snacks may require part of the reserve.'},
            {'category':'transport','item':'Local shared sightseeing / transfers','quantity':1,'unit_cost':local,'total':local,'notes':'Confirm a shared route in advance. A private cab or long Sissu/Kasol excursion can cost substantially more.'},
            {'category':'activities','item':'Entry fees and optional experiences','quantity':1,'unit_cost':activity_total,'total':activity_total,'notes':'Keep expensive adventure activities optional; verify current charges on arrival.'},
        ]
        if reserve:
            lines.append({'category':'misc','item':'Unspent contingency reserve','quantity':1,'unit_cost':reserve,'total':reserve,'notes':'Budget still available for fare changes, delays, extra food, or emergencies. This is not a predicted expense.'})
        plan['budget_line_items']=lines
        plan['budget_breakdown']={k:sum(line['total'] for line in lines if line['category']==k) for k in ('stay','food','activities','transport','misc')}
        plan['summary']=f"For {party} travelers, Delhi to Manali works best with overnight travel and a single accommodation base. This {count}-calendar-day outline includes leaving Delhi and returning there, so it gives approximately {sightseeing} full or partial days in Manali, {nights} hotel nights, and two nights on buses. Keep local routes compact and treat long excursions and paid adventure activities as optional. The core planning allowance is INR {core:,.0f} for the group, with INR {reserve:,.0f} left as an unspent reserve from your INR {total:,.0f} budget. These are budget targets rather than live fares or bookable offers. Check dates, seat prices, road access, and room details before paying. If you meant {count} full days at the destination, extend the total travel dates to include both bus journeys."
        if core>total:
            plan['summary']+=f" The core estimate is INR {core-total:,.0f} over your target; shorten the stay or increase the budget instead of assuming lower fares."
        plan['timing_notes']=f"{count} total calendar days / {count-1} total nights: {nights} nights in accommodation and 2 overnight bus nights. Actual destination time is approximately {sightseeing} full/partial days. The last chosen date is the return arrival in Delhi, not the bus departure from Manali."
        plan['journey']=[{'title':'Outbound: Delhi to Manali','mode':'Overnight AC bus','route':'Delhi confirmed pickup point → Manali operator drop point','departure_window':'Evening on the first chosen date; confirm the actual reporting time','duration':'Allow roughly 12–16 hours, with extra buffer for traffic and road conditions','estimated_cost':intercity/2,'booking_tip':'Compare the exact date on official/state or established bus booking providers. Confirm seat type, operator, pickup point, cancellation terms, and luggage policy.'},{'title':'Return: Manali to Delhi','mode':'Overnight AC bus','route':'Manali confirmed boarding point → Delhi','departure_window':'Evening on the penultimate date, reaching Delhi on the final date','duration':'Allow roughly 12–16 hours; avoid booking a tight onward connection','estimated_cost':intercity/2,'booking_tip':'Book the return separately for the correct date. Keep the last afternoon flexible and reach the actual boarding point before the operator reporting time.'}]
        def stop(time,name,location,detail,travel,cost=0):
            return {'time':time,'activity':name,'location':location,'description':detail,'travel_tip':travel,'cost':round(cost)}
        for index,day in enumerate(plan['days']):
            if index==0:
                day['title']='Delhi departure and the overnight journey'
                day['activities']=[stop('04:00 PM','Check tickets and pack a small bus bag','Delhi','Confirm the operator pickup point and reporting time, save your ticket offline, and keep IDs, water, snacks, medication, and a warm layer accessible.','Leave a generous city-traffic buffer; pickup points differ by operator.'),stop('06:00 PM','Reach your confirmed boarding point','Delhi boarding point','Use the actual ticket timing rather than assuming every bus departs from Kashmere Gate. Have a light meal before boarding and verify the destination with the operator.','Plan to arrive before the stated reporting time; the bus fare is already counted in the overall budget.'),stop('08:00 PM','Overnight journey toward Manali','Delhi–Manali route','Settle into your confirmed seat and keep valuables with you. The arrival time is an estimate and may shift with traffic, weather, or road restrictions.','An evening departure window is indicative; follow the schedule on your confirmed ticket.')]
                day['overnight']='On the overnight bus toward Manali.'
                day['notes']='This is a travel day, not a sightseeing day. Bus fares are in the overall transport budget; keep snacks and a jacket within reach.'
            elif index==count-1:
                day['title']='Arrive back in Delhi with room for delays'
                day['activities']=[stop('08:00 AM','Estimated Delhi arrival and onward transfer','Delhi operator drop point','Arrival can be earlier or much later than this planning time. Collect all luggage and choose a suitable onward transfer from the actual operator drop point.','Confirm the drop point in advance; avoid a nonrefundable onward connection with a short buffer.'),stop('11:00 AM','Breakfast, rest, and settle trip expenses','Delhi','Allow time to recover after the road journey. Check the expense log, split the final costs, and keep receipts for any disputed provider charge.','Use your real arrival time; there is no sightseeing commitment on this date.')]
                day['overnight']='Home or your own onward arrangements in Delhi; no Manali hotel night.'
                day['notes']='This final calendar day is included for the return arrival, so no Manali sightseeing is scheduled.'
            else:
                first=index==1;last=index==count-2
                title='Arrival, deodar forests and Old Manali' if first else ('A mountain day around Solang Valley' if index==2 else 'Village lanes, markets and a slower day')
                places=('Hadimba Devi Temple','Old Manali','Manali Mall Road') if first else (('Solang Valley','Palchan village','Old Manali') if index==2 else ('Vashisht village','Van Vihar area','Manali local market'))
                day['title']=title
                day['activities']=[stop('08:00 AM','Arrival or a relaxed breakfast',base,'On the arrival day, drop luggage at your accommodation and ask about check-in; early access is not guaranteed. On other days, start with a simple breakfast such as paratha, poha, or another dietary-appropriate local option.','Use the confirmed bus arrival and accommodation rules; do not plan an immediate long excursion.',food/sightseeing*.2),stop('10:00 AM','Explore '+places[0],places[0]+', Manali','Take time for the setting, short walks, and photos rather than treating the stop as a quick tick-box. For temple areas, respect local customs; for mountain outings, check weather and access before leaving.','Keep the route local on arrival. For Solang, confirm the shared vehicle route, departure time, and return arrangement before payment.',activity_total/sightseeing*.4),stop('12:30 PM','Lunch with a local flavor',base,'Look for a straightforward dhaba or cafe and check the menu price before ordering. Vegetarian meals, dal-rice, paratha, or siddu when available can fit a modest plan; avoid treating any named dish as guaranteed stock.','Choose lunch close to the morning route to reduce backtracking.',food/sightseeing*.4),stop('02:00 PM','A slower stop around '+places[1],places[1]+', Manali','Choose an easy walk, a viewpoint, or a small cafe stop depending on the route and conditions. Snow, adventure activities, tunnel access, and specific viewpoints are never guaranteed.','For longer outings, start the return in daylight. Do not add Atal Tunnel/Sissu without a confirmed full-day route and suitable weather.',activity_total/sightseeing*.6),stop('04:00 PM','Tea, photos and time to reset',base,'Leave this block flexible for rest, a warm drink, or a nearby lane you enjoyed. Use it as delay buffer rather than adding another distant destination.','Walk where practical and confirm a taxi fare before boarding.',food/sightseeing*.1),stop('06:30 PM','Dinner and a gentle local evening',places[2]+', Manali','Pick a nearby meal and keep shopping optional. Check prices and closing times, and return at a comfortable hour rather than relying on late-night transfers.','If you are departing tonight, move dinner earlier and prioritize your actual bus reporting time.',food/sightseeing*.3)]
                if last:
                    day['title']='A flexible local day and the return bus'
                    day['activities'][-1]=stop('05:00 PM','Collect luggage and report for the return bus','Confirmed Manali boarding point','Check out according to accommodation rules and ask about luggage storage before leaving. Board only at the pickup point and time stated on the return ticket.','Allow a generous local-traffic buffer; replace late sightseeing or dinner if it conflicts with reporting time.')
                    day['overnight']='On the overnight return bus to Delhi; no hotel room needed for this night.'
                else:
                    day['overnight']=f'Manali accommodation, hotel night {index} of {nights}.'
                day['notes']='Atal Tunnel/Sissu is an optional, separately confirmed excursion rather than an automatic addition. If the route is closed, expensive, or tiring, keep the day local. Day costs below are food/activity allowances; bus, room, and overall local transport are already in the trip budget.'
            day['day_cost']=sum(a['cost'] for a in day['activities'])
        plan['booking_checklist']+=['For Delhi–Manali, verify both overnight travel dates before booking hotel nights.','In winter, ask specifically about heating charges, hot water timings, and access to the property.','Confirm Solang/Atal Tunnel road conditions with current local information before starting; snowfall is not guaranteed.']
        plan['alternatives']+=['Skip Sissu/Atal Tunnel if weather, access, budget, or return timing is uncertain; use Hadimba forest, Old Manali, and a nearby cafe instead.','A Kasol/Manikaran outing is a long separate excursion, not an automatic add-on to a short Manali trip. Only include it with a confirmed route, budget, and rest time.']
    return plan
