import {AlertCircle,CheckCircle2} from 'lucide-react';
import {money,Plan,Trip} from '@/lib/api';
export default function BudgetVerdict({trip,plan}:{trip:Trip;plan:Plan}){
 const estimate=Object.values(plan.budget_breakdown).reduce((total,value)=>total+value,0);
 const over=!!trip.budget&&estimate>trip.budget;
 return <div className={'budget-verdict '+(over?'budget-warning':'')} role={over?'status':undefined}>{over?<AlertCircle size={21}/>:<CheckCircle2 size={21}/>}<div><strong>{over?'This estimate exceeds your budget.':'Your planning estimate, clearly.'}</strong><p>{money(estimate)} for the group · {money(estimate/trip.travelers)} per traveler{trip.budget?` · Your cap: ${money(trip.budget)}`:''}.{over?` Reduce the plan or allow ${money(estimate-(trip.budget||0))} more before booking.`:' Estimates include the listed contingency; verify actual prices before booking.'}</p></div></div>;
}
