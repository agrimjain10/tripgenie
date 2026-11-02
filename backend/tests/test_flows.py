import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
import main
from ai_service import _sample_plan
from ai_service import Itinerary

class WorkspaceFlows(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.folder.name) / 'test.db'), connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        def dependency():
            with self.sessions() as session:
                yield session
        main.app.dependency_overrides[get_db] = dependency
        self.background = patch.object(main, 'SessionLocal', self.sessions)
        self.background.start()
        self.ai = patch.object(main, 'generate_plan', _sample_plan)
        self.ai.start()
        self.client = TestClient(main.app)
        self.owner = self.register('owner@example.com')
        self.other = self.register('other@example.com')
        self.trip = self.client.post('/api/trips', headers=self.owner, json={'destination': 'Manali', 'origin': 'Delhi', 'start_date': '2026-12-25', 'end_date': '2026-12-27', 'travelers': 2, 'budget': 18000, 'interests': 'nature'}).json()
        self.url = '/api/trips/' + str(self.trip['id'])

    def tearDown(self):
        self.client.close()
        self.ai.stop(); self.background.stop()
        main.app.dependency_overrides.clear()
        self.engine.dispose(); self.folder.cleanup()

    def register(self, email):
        response = self.client.post('/api/register', json={'email': email, 'password': 'A good long passphrase 123', 'name': 'Traveler'})
        self.assertEqual(response.status_code, 201)
        return {'Authorization': 'Bearer ' + response.json()['token']}

    def generate(self):
        response = self.client.post(self.url + '/generate', headers=self.owner)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['status'], 'generating')
        trip = self.client.get(self.url, headers=self.owner).json()
        self.assertEqual(trip['status'], 'planned')
        return trip

    def test_auth_and_ownership(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.get(self.url, headers=self.other).status_code, 404)
        self.assertEqual(self.client.delete(self.url, headers=self.other).status_code, 404)
        self.assertEqual(self.client.post('/api/login', json={'email': 'owner@example.com', 'password': 'wrong'}).status_code, 401)

    def test_background_generation_and_dates(self):
        trip = self.generate()
        plan = json.loads(trip['plan_json'])
        self.assertEqual(len(plan['days']), 3)
        self.assertEqual(plan['days'][-1]['date'], '2026-12-27')
        self.assertEqual(sum(plan['budget_breakdown'].values()), 18000)

    def test_workspace_persistence_and_invalid_expense(self):
        payload = {'notes': 'Private booking reference', 'checked': ['pack::Passport'], 'expenses': [{'id': 'one', 'title': 'Lunch', 'amount': 500, 'category': 'Food', 'paid_by': 'Me'}]}
        self.assertEqual(self.client.patch(self.url + '/workspace', headers=self.owner, json=payload).status_code, 200)
        state = self.client.get(self.url, headers=self.owner).json()['workspace']
        self.assertEqual(state['notes'], payload['notes'])
        self.assertEqual(state['expenses'][0]['amount'], 500)
        self.assertEqual(self.client.patch(self.url + '/workspace', headers=self.owner, json={'expenses': [{'title': 'Bad', 'amount': -1}]}).status_code, 400)

    def test_public_share_privacy_and_revocation(self):
        self.generate()
        self.client.patch(self.url + '/workspace', headers=self.owner, json={'notes': 'Private', 'expenses': []})
        slug = self.client.post(self.url + '/share', headers=self.owner).json()['slug']
        public = self.client.get('/api/public/trips/' + slug)
        self.assertEqual(public.status_code, 200)
        self.assertNotIn('workspace', public.json())
        self.assertNotIn('user_id', public.json())
        self.client.delete(self.url + '/share', headers=self.owner)
        self.assertEqual(self.client.get('/api/public/trips/' + slug).status_code, 404)

    def test_exports_and_manual_edit(self):
        trip = self.generate()
        plan = json.loads(trip['plan_json'])
        plan['days'][0]['activities'][0]['activity'] = 'My favorite walk'
        response = self.client.patch(self.url, headers=self.owner, json={'plan': plan, 'title': 'Our mountain trip'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['workspace']['title'], 'Our mountain trip')
        pdf = self.client.get(self.url + '/pdf', headers=self.owner)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        ics = self.client.get(self.url + '/ics', headers=self.owner)
        self.assertIn('BEGIN:VCALENDAR', ics.text)
        self.assertIn('My favorite walk', ics.text)

    def test_duplicate_and_archive(self):
        self.generate()
        self.client.patch(self.url + '/workspace', headers=self.owner, json={'notes': 'Private note'})
        copy = self.client.post(self.url + '/duplicate', headers=self.owner)
        self.assertEqual(copy.status_code, 201)
        self.assertNotEqual(copy.json()['id'], self.trip['id'])
        self.assertNotIn('notes', copy.json()['workspace'])
        self.assertIsNone(copy.json()['public_slug'])
        self.assertEqual(self.client.patch(self.url, headers=self.owner, json={'status': 'archived'}).json()['status'], 'archived')

    def test_profile_and_password(self):
        profile = self.client.patch('/api/me', headers=self.owner, json={'name': 'New Name', 'preferences': {'pace': 'Easygoing'}})
        self.assertEqual(profile.json()['preferences']['pace'], 'Easygoing')
        response = self.client.post('/api/me/password', headers=self.owner, json={'current_password': 'A good long passphrase 123', 'password': 'A much better passphrase 456'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/api/login', json={'email': 'owner@example.com', 'password': 'A much better passphrase 456'}).status_code, 200)

    def test_invalid_dates_and_duration(self):
        payload = {'destination': 'Goa', 'start_date': '2026-12-25', 'end_date': '2026-10-31'}
        self.assertEqual(self.client.post('/api/trips', headers=self.owner, json=payload).status_code, 422)
        payload['end_date'] = '2027-02-25'
        self.assertEqual(self.client.post('/api/trips', headers=self.owner, json=payload).status_code, 400)

    def test_chat_history_survives_updates(self):
        self.generate()
        def modified(plan, message, trip):
            plan['summary'] = 'Updated for a slower pace'
            plan['_meta'] = {'source': 'gemini', 'model': 'mock'}
            return plan
        with patch.object(main, 'update_plan', modified):
            response = self.client.post(self.url + '/chat', headers=self.owner, json={'message': 'Slow down day two'})
        self.assertEqual(response.status_code, 202)
        saved = self.client.get(self.url, headers=self.owner).json()
        self.assertEqual(len(saved['workspace']['chat']), 2)
        self.assertEqual(saved['workspace']['chat'][0]['content'], 'Slow down day two')
        self.assertNotIn('_job', saved['workspace'])

    def test_old_job_cannot_overwrite_new_job(self):
        with self.sessions() as db:
            trip = db.get(main.Trip, self.trip['id'])
            trip.status = 'generating'
            trip.workspace_json = json.dumps({'_job': 'new-job'})
            db.commit()
        main.run_planning(self.trip['id'], 'generate', job_token='old-job')
        with self.sessions() as db:
            trip = db.get(main.Trip, self.trip['id'])
            self.assertIsNone(trip.plan_json)
            self.assertEqual(trip.status, 'generating')

    def test_itemized_budget_and_five_day_nights(self):
        from types import SimpleNamespace
        trip = SimpleNamespace(destination='Manali', origin='Delhi', start_date='2026-12-25', end_date='2026-12-29', travelers=2, budget=18000)
        plan = _sample_plan(trip)
        self.assertEqual(plan['calendar_accounting'], {'total_days': 5, 'hotel_nights': 2, 'transit_nights': 2, 'sightseeing_days': 3})
        self.assertTrue(all(a.get('description') for d in plan['days'] for a in d['activities']))
        plan['budget_line_items'][0]['total'] = 1
        normalized = Itinerary.model_validate(plan)
        self.assertEqual(normalized.budget_line_items[0].total, normalized.budget_line_items[0].quantity * normalized.budget_line_items[0].unit_cost)
        self.assertEqual(sum(normalized.budget_breakdown.model_dump().values()), 18000)


    def test_discovery_ranking_and_budget_boundaries(self):
        payload={'origin':'Delhi','days':3,'travelers':2,'budget':20000,'travel_mode':'Train','interests':['Culture','Food']}
        result=self.client.post('/api/discovery/suggest',headers=self.owner,json=payload)
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.json()['results'])
        for place in result.json()['results']:
            self.assertTrue(place['within_budget'])
            self.assertLessEqual(place['cost_range'][1],payload['budget'])
            self.assertGreater(place['usable_hours'],0)
            self.assertAlmostEqual(sum(place['budget_breakdown'].values()),place['estimated_total'])
        payload.update(budget=500,days=1)
        result=self.client.post('/api/discovery/suggest',headers=self.owner,json=payload)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['within_budget_count'],0)
        for place in result.json()['results']:
            self.assertFalse(place['within_budget'])
            self.assertLessEqual(place['one_way_hours'],2.5)

    def test_discovery_geolocation_and_limits(self):
        result=self.client.post('/api/discovery/location',headers=self.owner,json={'latitude':31.3,'longitude':75.6})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['name'],'Jalandhar')
        self.assertTrue(result.json()['approximate'])
        self.assertNotIn('latitude',result.json())
        self.assertEqual(self.client.post('/api/discovery/location',headers=self.owner,json={'latitude':200,'longitude':75}).status_code,422)
        self.assertEqual(self.client.post('/api/discovery/location',headers=self.owner,json={'latitude':51.5,'longitude':-.1}).status_code,422)
        self.assertEqual(self.client.post('/api/discovery/suggest',json={'origin':'Delhi','days':3,'budget':10000}).status_code,401)
        self.assertEqual(self.client.post('/api/discovery/suggest',headers=self.owner,json={'origin':'Delhi','days':22,'budget':10000}).status_code,422)
        self.assertEqual(self.client.post('/api/discovery/suggest',headers=self.owner,json={'origin':'Delhi','days':3,'budget':10000,'travel_mode':'Teleport'}).status_code,422)

    def test_rail_provider_and_station_ownership(self):
        import os
        import travel_service
        self.assertEqual(self.client.get(self.url+'/rail',headers=self.other).status_code,404)
        with patch.dict(os.environ,{'INDIAN_RAIL_API_KEY':''}):
            result=self.client.get(self.url+'/rail',headers=self.owner).json()
            self.assertFalse(result['available'])
            self.assertEqual(result['from_station'],'NDLS')
            self.assertEqual(result['to_station'],'CDG')
            self.assertIn('onward',result['railhead_note'])
            self.assertEqual(result['trains'],[])
        with patch.dict(os.environ,{'INDIAN_RAIL_API_KEY':'test-provider-key'}),patch.object(travel_service.httpx,'Client') as factory:
            response=factory.return_value.__enter__.return_value.get.return_value
            response.json.return_value={'ResponseCode':'200','Trains':[{'TrainNo':'12345','TrainName':'Provider timetable fixture','DepartureTime':'08:00','ArrivalTime':'12:00','TravelTime':'04:00H'}]}
            result=self.client.get(self.url+'/rail',headers=self.owner).json()
            self.assertTrue(result['available'])
            self.assertEqual(result['trains'][0]['number'],'12345')
            self.assertNotIn('fare',result['trains'][0])
            self.assertIn('not live seat availability',result['message'])
        self.assertEqual(self.client.get(self.url+'/rail?from_station=../../secret',headers=self.owner).status_code,422)

    def test_real_stay_data_and_safe_links(self):
        import travel_service
        travel_service._stay_cache.clear()
        with patch.object(travel_service.httpx,'Client') as factory:
            response=factory.return_value.__enter__.return_value.post.return_value
            response.json.return_value={'elements':[{'type':'node','id':123,'tags':{'name':'Map-sourced guesthouse','tourism':'guest_house','website':'javascript:alert(1)'}},{'type':'way','id':456,'tags':{'name':'Map-sourced hostel','tourism':'hostel','website':'https://example.com'}}]}
            result=self.client.get(self.url+'/stays',headers=self.owner)
            self.assertEqual(result.status_code,200)
            stays=result.json()['stays']
            self.assertEqual(len(stays),2)
            self.assertIsNone(stays[0]['website'])
            self.assertIsNone(stays[0]['price'])
            self.assertIsNone(stays[0]['availability'])
            self.assertIn('checkin=2026-12-25',result.json()['booking_url'])
        self.assertEqual(self.client.get(self.url+'/stays',headers=self.other).status_code,404)
        travel_service._stay_cache.clear()

    def test_travel_mode_roundtrip_and_ai_context(self):
        from ai_service import _trip_context
        from types import SimpleNamespace
        result=self.client.post('/api/trips',headers=self.owner,json={'destination':'Manali','origin':'Delhi','start_date':'2026-12-25','end_date':'2026-12-29','travel_mode':'Car','travelers':1})
        self.assertEqual(result.status_code,201)
        self.assertEqual(result.json()['travel_mode'],'Car')
        copied=self.client.post('/api/trips/'+str(result.json()['id'])+'/duplicate',headers=self.owner).json()
        self.assertEqual(copied['travel_mode'],'Car')
        context=_trip_context(SimpleNamespace(destination='Manali',origin='Delhi',start_date='2026-12-25',end_date='2026-12-29',travelers=1,budget=15000,interests='Nature',trip_brief='',travel_mode='Car'))
        self.assertIn('Preferred travel mode: Car',context)
        self.assertNotIn('CRITICAL overnight-bus',context)
        self.assertIn('daylight driving',context)

    def test_discovery_photo_assets_exist(self):
        response=self.client.get('/api/discovery/catalog')
        self.assertEqual(response.status_code,200)
        self.assertGreaterEqual(len(response.json()['destinations']),30)
        for place in response.json()['destinations']:
            self.assertTrue((Path(__file__).resolve().parents[2]/'frontend'/'public'/place['image'].lstrip('/')).exists(),place['image'])


    def test_ai_repairs_false_budget_claim(self):
        import copy, os
        import ai_service
        from types import SimpleNamespace
        trip=SimpleNamespace(destination='Manali',origin='Delhi',start_date='2026-12-25',end_date='2026-12-27',travelers=2,budget=18000,interests='Nature',trip_brief='',travel_mode='Bus')
        valid=_sample_plan(trip)
        invalid=copy.deepcopy(valid)
        invalid['summary']='This is a comfortable trip within the budget.'
        invalid['budget_line_items'][0]['quantity']+=20
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'primary-test','GEMINI_FALLBACK_MODELS':'fallback-test'}),patch.object(ai_service.genai,'Client') as factory:
            client=factory.return_value
            client.models.generate_content.side_effect=[SimpleNamespace(text=json.dumps(invalid)),SimpleNamespace(text=json.dumps(valid))]
            result=ai_service._try_gemini('Plan this trip',trip,3)
            self.assertEqual(result['_meta']['source'],'gemini')
            self.assertLessEqual(sum(result['budget_breakdown'].values()),18000)
            self.assertEqual(client.models.generate_content.call_count,2)
            second=client.models.generate_content.call_args_list[1].kwargs
            self.assertEqual(second['model'],'primary-test')
            self.assertIn('Budget mismatch',second['contents'])

if __name__ == '__main__':
    unittest.main()
