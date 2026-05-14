"""Dataclasses representing the database tables for the migration.

¿Por qué usamos Dataclasses aquí?
1. Estructura Limpia y Validada: Nos permiten definir explícitamente los campos y sus tipos (Type Hints), 
   actuando como un contrato o esquema intermedio entre SQLite y PostgreSQL.
2. Desacoplamiento: Al usar dataclasses puras en lugar de modelos del ORM de Django, hacemos que nuestro 
   script de migración sea independiente y ligero, sin requerir cargar todo el entorno de Django.
3. Transformación Fácil: Permiten convertir fácilmente cada registro en un diccionario (`asdict`) para 
   insertarlo en PostgreSQL.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Genre:
    """Representa la tabla 'genre' (Géneros de películas).
    
    Usamos `uuid.uuid4` como default_factory para generar automáticamente un UUID 
    en caso de que el registro no lo tenga, garantizando la compatibilidad con PostgreSQL.
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ''
    description: str = ''
    created: Optional[datetime] = None
    modified: Optional[datetime] = None


@dataclass
class Person:
    """Representa la tabla 'person' (Actores, directores, escritores)."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    full_name: str = ''
    created: Optional[datetime] = None
    modified: Optional[datetime] = None


@dataclass
class FilmWork:
    """Representa la tabla 'film_work' (Obras cinematográficas/Películas).
    
    Campos como rating o creation_date usan `Optional` porque en la base de datos 
    pueden ser nulos (NULL).
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    title: str = ''
    description: str = ''
    creation_date: Optional[date] = None
    file_path: str = ''
    rating: Optional[float] = None
    type: str = ''
    certificate: str = ''
    created: Optional[datetime] = None
    modified: Optional[datetime] = None


@dataclass
class GenreFilmWork:
    """Tabla intermedia (Junction table) que relaciona FilmWork con Genre (Muchos a Muchos)."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    genre_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created: Optional[datetime] = None


@dataclass
class PersonFilmWork:
    """Tabla intermedia (Junction table) que relaciona FilmWork con Person (Muchos a Muchos).
    Incluye el campo 'role' para saber si la persona fue actor, director o escritor en esa película.
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    role: str = ''
    created: Optional[datetime] = None
