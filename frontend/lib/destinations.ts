export type Destination = { name:string; region:string; image:string; category:string; description:string; tags:string[]; duration:string };
export const destinations:Destination[] = [
 {name:'Manali',region:'Himachal Pradesh',image:'/images/mountains.jpg',category:'Mountains',description:'Pine forests, mountain air, and slow mornings in the valley.',tags:['Nature','Adventure','Cafes'],duration:'4–6 days'},
 {name:'Goa',region:'Western coast',image:'/images/coast.jpg',category:'Coast',description:'Quiet beaches, colorful streets, and a little time by the sea.',tags:['Beaches','Food','Relaxation'],duration:'3–5 days'},
 {name:'Udaipur',region:'Rajasthan',image:'/images/lake.jpg',category:'Culture',description:'Lakeside evenings, old streets, and a city that rewards wandering.',tags:['Culture','Architecture','Food'],duration:'3–4 days'},
 {name:'Jaipur',region:'Rajasthan',image:'/images/city.jpg',category:'Culture',description:'Courtyards, craft markets, and stories around every corner.',tags:['History','Markets','Food'],duration:'3–4 days'},
 {name:'Rishikesh',region:'Uttarakhand',image:'/images/lake.jpg',category:'Outdoors',description:'Riverside walks, hillside cafes, and a change of pace.',tags:['Nature','Wellness','Adventure'],duration:'3–5 days'},
 {name:'Shimla',region:'Himachal Pradesh',image:'/images/mountains.jpg',category:'Mountains',description:'Hill-town streets, forest trails, and room to slow down.',tags:['Nature','History','Relaxation'],duration:'3–5 days'},
];
export function photoFor(place:string){const p=place.toLowerCase();return destinations.find(d=>p.includes(d.name.toLowerCase()))?.image || (p.includes('himachal')?'/images/mountains.jpg':p.includes('beach')?'/images/coast.jpg':'/images/lake.jpg');}
