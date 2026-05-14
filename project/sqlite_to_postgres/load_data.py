"""Main entry point — orquesta la migración completa de datos de SQLite a PostgreSQL.

¿Por qué se estructuró este archivo así?
1. Administradores de Contexto (Context Managers con `@contextmanager`): Manejar conexiones a bases de datos 
   es crítico. Si ocurre un error inesperado durante la migración, los context managers aseguran que las 
   conexiones (`sqlite3` y `psycopg2`) se cierren correctamente en el bloque `finally:`.
2. Conexiones Únicas: Abrir y cerrar una conexión a la base de datos es costoso. Aquí abrimos ambas conexiones 
   una sola vez en `main()` y las pasamos a lo largo del proceso.
3. Orden de Tablas (Integridad Referencial / Claves Foráneas): No podemos insertar registros en `GenreFilmWork` 
   si antes no existen las películas (`FilmWork`) y los géneros (`Genre`). Por eso, el array `TABLES_ORDER` 
   define estrictamente que las tablas padre se migran primero, seguidas por las tablas intermedias.
"""

import logging
import os
import sqlite3
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

from models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork
from postgres_saver import PostgresSaver
from sqlite_extractor import SQLiteExtractor

load_dotenv()

# Configuración de logging para registrar cada paso de la migración y cualquier posible excepción.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# Tamaño del lote (batch) de registros a extraer e insertar al mismo tiempo.
BATCH_SIZE = 100

# Ruta a la base de datos SQLite de origen (relativa a este archivo).
SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'db.sqlite',
)

# Parámetros de conexión a PostgreSQL usando variables de entorno o valores por defecto.
DSN = {
    'dbname': os.environ.get('DB_NAME', 'movies_database'),
    'user': os.environ.get('DB_USER', 'app'),
    'password': os.environ.get('DB_PASSWORD', '123qwe'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    # search_path define que PostgreSQL busque y guarde tablas en los esquemas 'public' y 'content'.
    'options': '-c search_path=public,content',
}

# El orden es fundamental para respetar las llaves foráneas (Foreign Keys).
TABLES_ORDER = [Genre, Person, FilmWork, GenreFilmWork, PersonFilmWork]


@contextmanager
def sqlite_connection(db_path: str):
    """Context manager que abre y cierra de forma segura la conexión a SQLite."""
    conn = sqlite3.connect(db_path)
    # row_factory = sqlite3.Row nos permite acceder a los campos por su nombre de columna.
    conn.row_factory = sqlite3.Row
    try:
        logger.info('Opened SQLite connection to "%s".', db_path)
        yield conn
    finally:
        conn.close()
        logger.info('Closed SQLite connection.')


@contextmanager
def postgres_connection(dsn: dict):
    """Context manager que abre y cierra de forma segura la conexión a PostgreSQL."""
    conn = psycopg2.connect(**dsn)
    try:
        logger.info('Opened PostgreSQL connection to "%s".', dsn.get('dbname'))
        yield conn
    finally:
        conn.close()
        logger.info('Closed PostgreSQL connection.')


def migrate(sqlite_conn: sqlite3.Connection, pg_conn) -> None:
    """Ejecuta el ciclo de extracción y guardado para todas las tablas.

    Args:
        sqlite_conn: Conexión abierta de SQLite.
        pg_conn: Conexión abierta de PostgreSQL.
    """
    extractor = SQLiteExtractor(sqlite_conn, batch_size=BATCH_SIZE)
    saver = PostgresSaver(pg_conn)

    # Recorremos las tablas en el orden seguro de dependencias.
    for dataclass_type in TABLES_ORDER:
        table_name = dataclass_type.__name__
        logger.info('Starting migration for table "%s"…', table_name)

        total = 0
        # extractor.extract genera lotes de hasta 100 objetos dataclass a la vez.
        for batch in extractor.extract(dataclass_type):
            saver.save_batch(batch, dataclass_type)
            total += len(batch)

        logger.info(
            'Finished migration for table "%s": %d records transferred.',
            table_name,
            total,
        )


def main():
    """Punto de entrada: abre las conexiones una vez y lanza la migración."""
    logger.info('=== Starting SQLite → PostgreSQL migration ===')

    # Usamos ambos context managers combinados.
    with sqlite_connection(SQLITE_DB_PATH) as sqlite_conn, \
         postgres_connection(DSN) as pg_conn:
        migrate(sqlite_conn, pg_conn)

    logger.info('=== Migration completed successfully ===')


if __name__ == '__main__':
    main()
