import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name('.env'), encoding='utf-8-sig')
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from database import Base, engine, get_db, SessionLocal
from models import Trip, User
from schemas import ChatIn, LoginIn, TokenOut, TripCreate, TripOut, UserCreate, UserOut
from auth import create_token, get_current_user, hash_password, verify_password
from ai_service import generate_plan, update_plan, _sample_plan, Itinerary
from pdf_service import create_pdf

logger = logging.getLogger('tripgenie')
Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
    additions = {'origin': 'VARCHAR', 'travelers': 'INTEGER NOT NULL DEFAULT 1', 'trip_brief': "TEXT DEFAULT ''", 'status': "VARCHAR DEFAULT 'draft'", 'workspace_json': "TEXT DEFAULT '{}'", 'public_slug': 'VARCHAR', 'updated_at': 'TIMESTAMP'}
    columns = {column['name'] for column in inspect(connection).get_columns('trips')}
    for name, definition in additions.items():
        if name not in columns:
            connection.exec_driver_sql(f'ALTER TABLE trips ADD COLUMN {name} {definition}')
    user_columns = {column['name'] for column in inspect(connection).get_columns('users')}
    if 'preferences_json' not in user_columns:
        connection.exec_driver_sql("ALTER TABLE users ADD COLUMN preferences_json TEXT DEFAULT '{}'")

app = FastAPI(title='TripGenie', version='3.0.0')
app.add_middleware(CORSMiddleware, allow_origins=[url.strip().rstrip('/') for url in os.getenv('FRONTEND_URL', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if url.strip()], allow_credentials=True, allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])


def owned_trip(trip_id, user, db):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise HTTPException(404, 'Trip not found')
    if trip.status in ('generating', 'updating') and trip.updated_at and datetime.utcnow() - trip.updated_at > timedelta(seconds=95):
        trip.status = 'planned' if trip.plan_json else 'draft'
        db.commit()
    return trip


def workspace(trip):
    return json.loads(trip.workspace_json or '{}')


def run_planning(trip_id, action, message='', job_token=''):
    with SessionLocal() as db:
        trip = db.get(Trip, trip_id)
        if not trip:
            return
        try:
            plan = generate_plan(trip) if action == 'generate' else update_plan(json.loads(trip.plan_json), message, trip)
            db.expire(trip)
            if trip.status not in ('generating', 'updating') or workspace(trip).get('_job') != job_token:
                return
            trip.plan_json = json.dumps(plan, ensure_ascii=False)
            trip.status = 'planned'
            trip.updated_at = datetime.utcnow()
            state = workspace(trip)
            state.pop('_job', None)
            if action == 'chat':
                success = plan.get('_meta', {}).get('source') == 'gemini'
                state.setdefault('chat', []).append({'role': 'assistant', 'content': 'Your itinerary has been updated. Take a look at the itinerary and budget tabs.' if success else 'I could not reach the planning service. Your existing itinerary is safe. You can edit activities directly or try again in a moment.', 'at': datetime.utcnow().isoformat()})
            trip.workspace_json = json.dumps(state)
            db.commit()
        except Exception as exc:
            logger.error('Planning failed: %s', type(exc).__name__)
            db.rollback()
            trip = db.get(Trip, trip_id)
            if trip and trip.status in ('generating', 'updating') and workspace(trip).get('_job') == job_token:
                trip.status = 'planned' if trip.plan_json else 'draft'
                db.commit()


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'TripGenie'}


@app.post('/api/register', response_model=TokenOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(409, 'An account with this email already exists')
    user = User(email=payload.email.lower(), name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return {'token': create_token(user.id), 'user': user}


@app.post('/api/login', response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, 'Email or password is incorrect')
    return {'token': create_token(user.id), 'user': user}


@app.get('/api/me')
def me(user: User = Depends(get_current_user)):
    return {'id': user.id, 'email': user.email, 'name': user.name, 'preferences': json.loads(user.preferences_json or '{}')}


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    preferences: dict = Field(default_factory=dict)


@app.patch('/api/me')
def update_me(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name = payload.name.strip()
    user.preferences_json = json.dumps(payload.preferences)
    db.commit()
    return me(user)


class PasswordUpdate(BaseModel):
    current_password: str
    password: str = Field(min_length=8, max_length=128)


@app.post('/api/me/password')
def password(payload: PasswordUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, 'Current password is incorrect')
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {'message': 'Password updated'}


@app.get('/api/trips')
def list_trips(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [TripOut.from_trip(trip) for trip in db.query(Trip).filter(Trip.user_id == user.id).order_by(Trip.created_at.desc()).all()]


@app.post('/api/trips', status_code=201)
def create_trip(payload: TripCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if (payload.end_date - payload.start_date).days > 20:
        raise HTTPException(400, 'Choose a trip of 21 days or fewer')
    trip = Trip(user_id=user.id, destination=payload.destination, origin=payload.origin, start_date=payload.start_date.isoformat(), end_date=payload.end_date.isoformat(), travelers=payload.travelers, budget=payload.budget, interests=payload.interests.strip(), trip_brief=payload.trip_brief.strip(), status='draft', workspace_json='{}', updated_at=datetime.utcnow())
    db.add(trip); db.commit(); db.refresh(trip)
    return TripOut.from_trip(trip)


@app.get('/api/trips/{trip_id}')
def get_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return TripOut.from_trip(owned_trip(trip_id, user, db))


class TripEdit(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    plan: dict | None = None
    status: str | None = None


@app.patch('/api/trips/{trip_id}')
def edit_trip(trip_id: int, payload: TripEdit, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if trip.status in ('generating', 'updating'):
        raise HTTPException(409, 'Wait for planning to finish or cancel the update first')
    if payload.title is not None:
        state = workspace(trip); state['title'] = payload.title.strip(); trip.workspace_json = json.dumps(state)
    if payload.status:
        if payload.status not in ('draft', 'planned', 'archived'):
            raise HTTPException(400, 'Invalid trip status')
        trip.status = payload.status
    if payload.plan is not None:
        try:
            Itinerary.model_validate(payload.plan)
        except ValueError:
            raise HTTPException(422, 'Please complete the activity name, time, location, and nonnegative cost')
        trip.plan_json = json.dumps(payload.plan, ensure_ascii=False)
        trip.status = 'planned'
    trip.updated_at = datetime.utcnow(); db.commit(); db.refresh(trip)
    return TripOut.from_trip(trip)


class WorkspaceUpdate(BaseModel):
    checked: list[str] | None = None
    notes: str | None = Field(default=None, max_length=20000)
    expenses: list[dict] | None = None


@app.patch('/api/trips/{trip_id}/workspace')
def update_workspace(trip_id: int, payload: WorkspaceUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    state = workspace(trip)
    changes = payload.model_dump(exclude_none=True)
    if len(changes.get('expenses', [])) > 500 or len(changes.get('checked', [])) > 1000:
        raise HTTPException(400, 'Too many entries')
    for entry in changes.get('expenses', []):
        if not isinstance(entry.get('amount'), (int, float)) or entry['amount'] < 0 or not isinstance(entry.get('title'), str):
            raise HTTPException(400, 'Expense needs a name and nonnegative amount')
    state.update(changes); trip.workspace_json = json.dumps(state); db.commit(); db.refresh(trip)
    return TripOut.from_trip(trip)


@app.delete('/api/trips/{trip_id}', status_code=204)
def delete_trip(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db); db.delete(trip); db.commit()
    return Response(status_code=204)


@app.post('/api/trips/{trip_id}/duplicate', status_code=201)
def duplicate(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    copy = Trip(user_id=user.id, destination=trip.destination, origin=trip.origin, start_date=trip.start_date, end_date=trip.end_date, travelers=trip.travelers, budget=trip.budget, interests=trip.interests, trip_brief=trip.trip_brief, plan_json=trip.plan_json, status='planned' if trip.plan_json else 'draft', workspace_json=json.dumps({'title': (workspace(trip).get('title') or trip.destination) + ' (copy)'}), updated_at=datetime.utcnow())
    db.add(copy); db.commit(); db.refresh(copy)
    return TripOut.from_trip(copy)


@app.post('/api/trips/{trip_id}/generate', status_code=202)
def generate(trip_id: int, tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if trip.status not in ('generating', 'updating'):
        if not trip.plan_json:
            trip.plan_json = json.dumps(_sample_plan(trip))
        state = workspace(trip); token = secrets.token_urlsafe(12); state['_job'] = token
        trip.workspace_json = json.dumps(state)
        trip.status = 'generating'; trip.updated_at = datetime.utcnow(); db.commit()
        tasks.add_task(run_planning, trip.id, 'generate', '', token)
    return TripOut.from_trip(trip)


@app.post('/api/trips/{trip_id}/cancel')
def cancel(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    state = workspace(trip); state.pop('_job', None); trip.workspace_json = json.dumps(state)
    trip.status = 'planned' if trip.plan_json else 'draft'; db.commit()
    return TripOut.from_trip(trip)


@app.post('/api/trips/{trip_id}/chat', status_code=202)
def chat(trip_id: int, payload: ChatIn, tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if not trip.plan_json:
        raise HTTPException(400, 'Create an itinerary before requesting a change')
    if trip.status in ('generating', 'updating'):
        raise HTTPException(409, 'Your plan is already being updated')
    if not payload.message.strip():
        raise HTTPException(400, 'Enter a message first')
    state = workspace(trip)
    state.setdefault('chat', []).append({'role': 'user', 'content': payload.message.strip(), 'at': datetime.utcnow().isoformat()})
    state['chat'] = state['chat'][-100:]
    token = secrets.token_urlsafe(12); state['_job'] = token
    trip.workspace_json = json.dumps(state); trip.status = 'updating'; trip.updated_at = datetime.utcnow(); db.commit()
    tasks.add_task(run_planning, trip.id, 'chat', payload.message.strip(), token)
    return TripOut.from_trip(trip)


@app.post('/api/trips/{trip_id}/share')
def share(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if not trip.plan_json:
        raise HTTPException(400, 'Generate an itinerary before sharing')
    trip.public_slug = trip.public_slug or secrets.token_urlsafe(16); db.commit()
    return {'slug': trip.public_slug}


@app.delete('/api/trips/{trip_id}/share')
def unshare(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db); trip.public_slug = None; db.commit()
    return {'message': 'Sharing turned off'}


@app.get('/api/public/trips/{slug}')
def public_trip(slug: str, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.public_slug == slug).first()
    if not trip:
        raise HTTPException(404, 'This shared itinerary is no longer available')
    return {'destination': trip.destination, 'start_date': trip.start_date, 'end_date': trip.end_date, 'travelers': trip.travelers, 'plan_json': trip.plan_json, 'title': workspace(trip).get('title') or trip.destination}


@app.get('/api/trips/{trip_id}/pdf')
def download_pdf(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if not trip.plan_json:
        raise HTTPException(400, 'Generate an itinerary first')
    return Response(create_pdf(trip, json.loads(trip.plan_json)), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="tripgenie-{trip.id}.pdf"'})


@app.get('/api/trips/{trip_id}/ics')
def calendar(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = owned_trip(trip_id, user, db)
    if not trip.plan_json:
        raise HTTPException(400, 'Generate an itinerary first')
    def clean(value):
        return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;').replace('\r', '')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//TripGenie//Travel Plan//EN', 'CALSCALE:GREGORIAN']
    for day in json.loads(trip.plan_json).get('days', []):
        day_date = day.get('date') or (datetime.fromisoformat(trip.start_date) + timedelta(days=day['day']-1)).date().isoformat()
        for index, activity in enumerate(day.get('activities', [])):
            try:
                clock = datetime.strptime(activity['time'], '%I:%M %p').strftime('%H%M%S')
            except ValueError:
                clock = '100000'
            start = datetime.strptime(day_date.replace('-', '') + 'T' + clock, '%Y%m%dT%H%M%S')
            lines.extend(['BEGIN:VEVENT', f'UID:{trip.id}-{day["day"]}-{index}@tripgenie.local', 'DTSTAMP:' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'), 'DTSTART:' + start.strftime('%Y%m%dT%H%M%S'), 'DTEND:' + (start+timedelta(hours=1)).strftime('%Y%m%dT%H%M%S'), 'SUMMARY:' + clean(activity['activity']), 'LOCATION:' + clean(activity.get('location', trip.destination)), 'END:VEVENT'])
    lines.append('END:VCALENDAR')
    return Response('\r\n'.join(lines)+'\r\n', media_type='text/calendar', headers={'Content-Disposition': f'attachment; filename="tripgenie-{trip.id}.ics"'})


@app.get('/api/trips/{trip_id}/travel-info')
def travel_info(trip_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import httpx
    trip = owned_trip(trip_id, user, db)
    try:
        with httpx.Client(timeout=7) as client:
            query = trip.destination
            known = {'manali': 'Manali, Himachal Pradesh', 'himachal pradesh': 'Manali, Himachal Pradesh', 'goa': 'Panaji, India', 'jaipur': 'Jaipur, Rajasthan', 'udaipur': 'Udaipur, Rajasthan', 'rishikesh': 'Rishikesh, Uttarakhand', 'shimla': 'Shimla, Himachal Pradesh'}
            query = known.get(query.strip().lower(), query)
            result = client.get('https://geocoding-api.open-meteo.com/v1/search', params={'name': query, 'count': 1, 'language': 'en', 'format': 'json'})
            result.raise_for_status(); places = result.json().get('results', [])
            if not places:
                return {'available': False, 'message': 'Map location was not found. Try the map search link.'}
            place = places[0]
            response = client.get('https://api.open-meteo.com/v1/forecast', params={'latitude': place['latitude'], 'longitude': place['longitude'], 'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max', 'forecast_days': 7, 'timezone': 'auto'})
            response.raise_for_status()
            return {'available': True, 'location': place, 'weather': response.json().get('daily', {}), 'message': 'Current 7-day forecast, not a forecast for dates further ahead.', 'attribution': 'Weather data by Open-Meteo. Map by OpenStreetMap contributors.'}
    except httpx.HTTPError:
        return {'available': False, 'message': 'Live weather is temporarily unavailable. Your saved itinerary is still available.'}
