"""SQLite data extractor — lee datos desde la base de datos SQLite en lotes (batches).

¿Por qué existe esta clase y por qué extrae en lotes?
1. Eficiencia de Memoria: Si tuviéramos millones de registros, cargar todo SQLite en la memoria RAM 
   colapsaría el sistema. Extraer en lotes (ej. de 100 en 100 con `fetchmany`) mantiene un uso de memoria bajo y estable.
2. Mapeo de Nombres de Columnas: En SQLite las columnas de fecha se llamaban `created_at` y `updated_at`, 
   pero en PostgreSQL (y en los modelos de Django) se llaman `created` y `modified`. Esta clase hace esa conversión.
3. Coerción de Valores Nulos (NULL → ''): En SQLite hay campos de texto con valor NULL. Sin embargo, en Django, 
   los campos de texto configurados con `blank=True` se crean en PostgreSQL con la restricción `NOT NULL`. 
   Por ello, si encontramos un `None` en SQLite para un campo de texto, lo transformamos en cadena vacía `''`.
"""

import logging
import sqlite3
from typing import Generator, Type

from models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork

logger = logging.getLogger(__name__)

# TABLE_CONFIG mapea cada Dataclass a su tabla en SQLite y define qué columna de SQLite 
# corresponde a qué atributo de la Dataclass.
TABLE_CONFIG = {
    Genre: {
        'table': 'genre',
        'columns': {
            'id': 'id',
            'name': 'name',
            'description': 'description',
            'created_at': 'created',
            'updated_at': 'modified',
        },
    },
    Person: {
        'table': 'person',
        'columns': {
            'id': 'id',
            'full_name': 'full_name',
            'created_at': 'created',
            'updated_at': 'modified',
        },
    },
    FilmWork: {
        'table': 'film_work',
        'columns': {
            'id': 'id',
            'title': 'title',
            'description': 'description',
            'creation_date': 'creation_date',
            'file_path': 'file_path',
            'rating': 'rating',
            'type': 'type',
            'created_at': 'created',
            'updated_at': 'modified',
        },
    },
    GenreFilmWork: {
        'table': 'genre_film_work',
        'columns': {
            'id': 'id',
            'film_work_id': 'film_work_id',
            'genre_id': 'genre_id',
            'created_at': 'created',
        },
    },
    PersonFilmWork: {
        'table': 'person_film_work',
        'columns': {
            'id': 'id',
            'film_work_id': 'film_work_id',
            'person_id': 'person_id',
            'role': 'role',
            'created_at': 'created',
        },
    },
}


class SQLiteExtractor:
    """Extrae datos de SQLite y genera lotes (batches) de instancias de Dataclasses."""

    def __init__(self, connection: sqlite3.Connection, batch_size: int = 100):
        self.connection = connection
        # row_factory = sqlite3.Row permite acceder a las columnas por su nombre (como un diccionario) 
        # en lugar de índices numéricos.
        self.connection.row_factory = sqlite3.Row
        self.batch_size = batch_size

    def extract(self, dataclass_type: Type) -> Generator[list, None, None]:
        """Generador que produce lotes de objetos de la clase solicitada.

        ¿Por qué usar un Generador (`yield`)?
        Porque permite pausar la ejecución, entregar un lote de 100 registros para que se guarden 
        en PostgreSQL, y luego continuar exactamente donde se quedó, ahorrando memoria.

        Args:
            dataclass_type: La clase del modelo a extraer (ej. Genre, FilmWork).

        Yields:
            Listas con hasta `batch_size` instancias de la dataclass.
        """
        config = TABLE_CONFIG[dataclass_type]
        table_name = config['table']
        col_map = config['columns']

        sqlite_cols = ', '.join(col_map.keys())
        query = f'SELECT {sqlite_cols} FROM {table_name};'

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)

            while True:
                # fetchmany obtiene exactamente el número de filas indicado en batch_size
                rows = cursor.fetchmany(self.batch_size)
                if not rows:
                    break

                # Estos campos de texto en PostgreSQL tienen la restricción NOT NULL.
                TEXT_FIELDS = {'description', 'file_path', 'certificate', 'role'}

                batch = []
                for row in rows:
                    kwargs = {}
                    for sqlite_col, dc_field in col_map.items():
                        value = row[sqlite_col]
                        # Si el valor es nulo (None) y es un campo de texto obligatorio en Postgres,
                        # lo convertimos a un string vacío ('') para evitar errores de restricción.
                        if value is None and dc_field in TEXT_FIELDS:
                            kwargs[dc_field] = ''
                        else:
                            kwargs[dc_field] = value
                    
                    # Creamos la instancia de la Dataclass desempaquetando el diccionario (**kwargs)
                    batch.append(dataclass_type(**kwargs))

                logger.info(
                    'Extracted batch of %d records from table "%s".',
                    len(batch),
                    table_name,
                )
                yield batch

        except sqlite3.Error:
            logger.exception('Error reading from SQLite table "%s".', table_name)
            raise
