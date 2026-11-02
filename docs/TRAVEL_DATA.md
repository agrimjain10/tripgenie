# Travel data connections

## Discovery

38 curated Indian destinations and a set of starting cities are included in `backend/discovery_service.py`. Ranking is deterministic: interests, total days, estimated return travel time and the full group cost range. The upper estimate must fit the budget for an option to receive a within-budget label. If nothing fits, options are explicitly labeled as stretches or the user is asked to change constraints.

Road distance uses straight-line distance × 1.35. Times are rough mode-dependent allowances, not road routing or an actual timetable. Accommodation, food, local activities and contingency are budget assumptions, not offers. Discovery is a starting point for research, not a guarantee of feasibility or weather/access.

Location is opt-in. The browser rounds coordinates to one decimal before sending them to the authenticated location endpoint. The endpoint finds a nearby known city offline, returns a city and approximation note, and does not persist coordinates. Unknown manually entered cities can use Open-Meteo's geocoder; the entered city name is sent, not GPS coordinates.

## Indian rail information

A server-side adapter supports [IndianRailAPI trains between stations](https://indianrailapi.com/api-collection/trains-between-station). Configure `INDIAN_RAIL_API_KEY` in the backend hosting environment to enable provider timetable results. A separate provider account/key and its own limits apply. No provider account is automatically registered or paid for.

Without the key, station codes, destination railheads, onward-transfer notes and official IRCTC/NTES links are available. Users can override both station codes. With a key, results are labeled as provider timetables; they do not establish operation on the selected date, seats, class availability or fares. These must be confirmed before booking.

Keys stay on the backend. The provider places keys in URL paths, so HTTP request URL logging is suppressed. Errors return a safe fallback instead of leaking URLs or inventing trains.

## Hotels, guesthouses and hostels

The app queries the public [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) through the Private.coffee public instance for named accommodation near known destination centres. This instance permits application use; public-service availability is not guaranteed. Results are real OpenStreetMap records with OSM links, available addresses and safe property websites. Unknown prices and availability stay null. Results are cached for 15 minutes per destination in a warm process, capped at 100 cache entries; serverless restarts clear this optional cache.

Public Overpass service can be slow or unavailable. In that case, the trip still offers destination searches on Booking.com, Google Hotels and Maps. Booking searches carry dates and adults/room count; day trips omit overnight dates. Search links are not reservations and do not imply affiliate status or guaranteed inventory.

## AI plans

The planner receives the selected transport mode and known destination railhead guidance. Car/bike plans request daylight driving and breaks; rail plans request last-mile transfers. The special Delhi–Manali overnight-bus calendar applies only to Flexible/Bus trips. API data is not silently represented as checked by the language model.

Provider calls remain bounded, structured output is validated, and fallback plans are visibly labeled. Host/provider failures may interrupt a job; a durable queue would strengthen delivery guarantees at larger scale.
