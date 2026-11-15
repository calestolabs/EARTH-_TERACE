"""Run from project root: uvicorn backend.main:app --reload --port 8000"""
import json,os
from pathlib import Path
from datetime import date
from typing import Literal
from fastapi import FastAPI,HTTPException,Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field,model_validator
from .analysis import annual,stats
app=FastAPI(title='EARTHTRACE Analysis API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('ALLOWED_ORIGINS','http://localhost:3000').split(','),allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type'])
DATA=json.loads((Path(__file__).resolve().parents[1]/'public/data/climate.json').read_text())
class Investigation(BaseModel):
    region:str
    variables:list[Literal['rainfall','temperature','soil']]=Field(min_length=1,max_length=3)
    start:date
    end:date
    @model_validator(mode='after')
    def valid_dates(self):
        if self.end<self.start:raise ValueError('End date must be after start date')
        if len(set(self.variables))!=len(self.variables):raise ValueError('Duplicate variables')
        return self

def verify(authorization):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Firebase sign-in required')
    try:
        import firebase_admin
        from firebase_admin import auth
        if not firebase_admin._apps:firebase_admin.initialize_app()
        return auth.verify_id_token(authorization[7:])
    except Exception:raise HTTPException(401,'Invalid or expired Firebase token')

@app.get('/health')
def health():return {'status':'ok','districts':len(DATA)}

@app.post('/analyze')
def analyze(body:Investigation,authorization:str|None=Header(default=None)):
    verify(authorization)
    if body.region not in DATA:raise HTTPException(422,'Unknown district')
    results={}
    for v in body.variables:
        r=annual(DATA[body.region][v],v,str(body.start),str(body.end));r['stats']=stats(r['points'])
        if r['stats'] is None:raise HTTPException(422,f'{v}: at least 5 complete years required')
        results[v]=r
    return {'results':results,'engine':'Python FastAPI'}
