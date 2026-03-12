from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import secrets
import json
from database import SessionLocal, JugadorDB, SquadDB

app = FastAPI()

class Jugador(BaseModel):
    nombre_usuario: str
    email: str
    contrasena: str
    fecha_nacimiento: date
    pais: str
    region: str
    juegos: List[str]
    skill: str

class LoginData(BaseModel):
    email: str
    contrasena: str

class Squad(BaseModel):
    nombre: str
    juego: str
    lider: str
    max_integrantes: int

class Invitacion(BaseModel):
    squad_id: int
    nombre_usuario: str

sesiones_activas = {}

def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a Squad API"}

@app.post("/jugadores")
def crear_jugador(jugador: Jugador):
    edad = calcular_edad(jugador.fecha_nacimiento)
    if edad < 18:
        raise HTTPException(status_code=403, detail="Debes ser mayor de 18 anos")
    db = SessionLocal()
    existe = db.query(JugadorDB).filter(JugadorDB.email == jugador.email).first()
    if existe:
        db.close()
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    nuevo = JugadorDB(
        nombre_usuario=jugador.nombre_usuario,
        email=jugador.email,
        contrasena=jugador.contrasena,
        fecha_nacimiento=jugador.fecha_nacimiento,
        pais=jugador.pais,
        region=jugador.region,
        juegos=json.dumps(jugador.juegos),
        skill=jugador.skill
    )
    db.add(nuevo)
    db.commit()
    db.close()
    return {"mensaje": "Jugador creado", "jugador": jugador}

@app.get("/jugadores")
def buscar_jugadores(
    juego: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    skill: Optional[str] = Query(None)
):
    db = SessionLocal()
    jugadores = db.query(JugadorDB).all()
    db.close()
    resultados = []
    for j in jugadores:
        juegos_lista = json.loads(j.juegos)
        if juego and juego.lower() not in [x.lower() for x in juegos_lista]:
            continue
        if region and j.region.lower() != region.lower():
            continue
        if skill and j.skill.lower() != skill.lower():
            continue
        resultados.append({
            "nombre_usuario": j.nombre_usuario,
            "pais": j.pais,
            "region": j.region,
            "juegos": juegos_lista,
            "skill": j.skill
        })
    return resultados

@app.post("/login")
def login(datos: LoginData):
    db = SessionLocal()
    jugador = db.query(JugadorDB).filter(JugadorDB.email == datos.email).first()
    db.close()
    if not jugador:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if jugador.contrasena != datos.contrasena:
        raise HTTPException(status_code=401, detail="Contrasena incorrecta")
    token = secrets.token_hex(16)
    sesiones_activas[token] = jugador.nombre_usuario
    return {"mensaje": "Login exitoso", "token": token, "usuario": jugador.nombre_usuario}

@app.post("/squads")
def crear_squad(squad: Squad):
    db = SessionLocal()
    lider = db.query(JugadorDB).filter(JugadorDB.nombre_usuario == squad.lider).first()
    if not lider:
        db.close()
        raise HTTPException(status_code=404, detail="El lider no existe")
    nuevo = SquadDB(
        nombre=squad.nombre,
        juego=squad.juego,
        lider=squad.lider,
        max_integrantes=squad.max_integrantes,
        integrantes=json.dumps([squad.lider])
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    squad_id = nuevo.id
    db.close()
    return {"mensaje": "Squad creado", "squad_id": squad_id}

@app.post("/squads/invitar")
def invitar_jugador(invitacion: Invitacion):
    db = SessionLocal()
    squad = db.query(SquadDB).filter(SquadDB.id == invitacion.squad_id).first()
    if not squad:
        db.close()
        raise HTTPException(status_code=404, detail="Squad no encontrado")
    jugador = db.query(JugadorDB).filter(JugadorDB.nombre_usuario == invitacion.nombre_usuario).first()
    if not jugador:
        db.close()
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    integrantes = json.loads(squad.integrantes)
    if len(integrantes) >= squad.max_integrantes:
        db.close()
        raise HTTPException(status_code=400, detail="El squad esta lleno")
    if invitacion.nombre_usuario in integrantes:
        db.close()
        raise HTTPException(status_code=400, detail="El jugador ya esta en el squad")
    integrantes.append(invitacion.nombre_usuario)
    squad.integrantes = json.dumps(integrantes)
    db.commit()
    db.close()
    return {"mensaje": "Jugador agregado", "integrantes": integrantes}

@app.get("/squads")
def listar_squads(juego: Optional[str] = Query(None)):
    db = SessionLocal()
    squads = db.query(SquadDB).all()
    db.close()
    resultados = []
    for s in squads:
        if juego and s.juego.lower() != juego.lower():
            continue
        resultados.append({
            "id": s.id,
            "nombre": s.nombre,
            "juego": s.juego,
            "lider": s.lider,
            "max_integrantes": s.max_integrantes,
            "integrantes": json.loads(s.integrantes)
        })
    return resultados