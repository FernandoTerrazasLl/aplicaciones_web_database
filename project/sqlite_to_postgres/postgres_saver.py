"""PostgreSQL data saver — inserta datos en la base de datos PostgreSQL en lotes (batches).

¿Por qué existe esta clase y para qué sirve su diseño?
1. Inserciones Masivas (Bulk Inserts con `execute_values`): Hacer un `INSERT` por cada fila sería 
   extremadamente lento porque requiere un viaje de red por cada registro. Al usar `execute_values`, 
   enviamos 100 registros en una sola consulta SQL, multiplicando la velocidad de migración.
2. Idempotencia (`ON CONFLICT DO NOTHING`): Esta es una pieza clave de la arquitectura. Si el script de migración 
   se interrumpe a la mitad, o si el usuario lo ejecuta 5 veces seguidas por accidente, `ON CONFLICT (id) DO NOTHING` 
   garantiza que PostgreSQL ignore los registros que ya existen (evaluando su UUID principal), evitando duplicados y errores.
3. Transacciones Seguras (`commit` / `rollback`): Cada lote de 100 se confirma (`commit`) si todo sale bien. Si ocurre 
   un fallo, se deshace (`rollback`) para no dejar datos corruptos o incompletos.
"""

import logging
from dataclasses import asdict
from typing import Type

import psycopg2
from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import execute_values

from models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork

logger = logging.getLogger(__name__)

# PG_TABLE_CONFIG mapea cada Dataclass a su tabla destino en el esquema 'content' de PostgreSQL,
# y define el orden estricto de las columnas para el INSERT.
PG_TABLE_CONFIG = {
    Genre: {
        'table': 'content.genre',
        'columns': ['id', 'name', 'description', 'created', 'modified'],
    },
    Person: {
        'table': 'content.person',
        'columns': ['id', 'full_name', 'created', 'modified'],
    },
    FilmWork: {
        'table': 'content.film_work',
        'columns': [
            'id', 'title', 'description', 'creation_date', 'file_path',
            'rating', 'type', 'certificate', 'created', 'modified',
        ],
    },
    GenreFilmWork: {
        'table': 'content.genre_film_work',
        'columns': ['id', 'film_work_id', 'genre_id', 'created'],
    },
    PersonFilmWork: {
        'table': 'content.person_film_work',
        'columns': ['id', 'film_work_id', 'person_id', 'role', 'created'],
    },
}


class PostgresSaver:
    """Guarda lotes de instancias de Dataclasses en PostgreSQL garantizando idempotencia."""

    def __init__(self, connection: pg_connection):
        self.connection = connection

    def save_batch(self, batch: list, dataclass_type: Type) -> None:
        """Inserta un lote de registros en PostgreSQL.

        Args:
            batch: Lista de instancias de dataclasses a insertar.
            dataclass_type: El tipo de dataclass (determina la tabla de destino).
        """
        if not batch:
            return

        config = PG_TABLE_CONFIG[dataclass_type]
        table = config['table']
        columns = config['columns']

        col_str = ', '.join(columns)
        # Crea un string con los placeholders necesarios, ej: (%s, %s, %s, %s, %s)
        template = '({})'.format(', '.join(['%s'] * len(columns)))

        # Consulta SQL combinada con manejo de conflictos para lograr Idempotencia.
        query = (
            f'INSERT INTO {table} ({col_str}) '
            f'VALUES %s '
            f'ON CONFLICT (id) DO NOTHING'
        )

        # Convertimos cada objeto dataclass a una tupla ordenada con sus valores exactos.
        values = []
        for record in batch:
            record_dict = asdict(record)
            row = tuple(record_dict.get(col) for col in columns)
            values.append(row)

        try:
            with self.connection.cursor() as cursor:
                # execute_values es una función de alto rendimiento de psycopg2 para bulk inserts.
                execute_values(cursor, query, values, template=template)
            self.connection.commit()
            logger.info(
                'Saved batch of %d records to table "%s".',
                len(batch),
                table,
            )
        except psycopg2.Error:
            self.connection.rollback()
            logger.exception('Error writing to PostgreSQL table "%s".', table)
            raise
