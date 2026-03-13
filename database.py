from sqlalchemy import create_engine, Column, String, Integer, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///squad.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class JugadorDB(Base):
    __tablename__ = "jugadores"
    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True)
    email = Column(String, unique=True)
    contrasena = Column(String)
    fecha_nacimiento = Column(Date)
    pais = Column(String)
    region = Column(String)
    juegos = Column(String)
    skill = Column(String)

class SquadDB(Base):
    __tablename__ = "squads"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    juego = Column(String)
    lider = Column(String)
    max_integrantes = Column(Integer)
    integrantes = Column(String)

Base.metadata.create_all(bind=engine)