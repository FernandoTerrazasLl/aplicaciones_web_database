import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=256, unique=True)
    description = models.TextField('description', blank=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = 'Género'
        verbose_name_plural = 'Géneros'

    def __str__(self):
        return self.name


class FilmWork(UUIDMixin, TimeStampedMixin):
    class Type(models.TextChoices):
        MOVIE = 'movie', 'Película'
        TV_SHOW = 'tv_show', 'Serie de TV'

    title = models.CharField(_('title'), max_length=256)
    description = models.TextField('description', blank=True)
    creation_date = models.DateField('creation_date', blank=True, null=True)
    rating = models.FloatField('rating', blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    type = models.CharField('type', max_length=64, choices=Type.choices)
    certificate = models.CharField('certificate', max_length=512, blank=True)
    file_path = models.FileField('file', blank=True, null=True, upload_to='movies/')
    
    genres = models.ManyToManyField(Genre, through='GenreFilmWork')
    persons = models.ManyToManyField('Person', through='PersonFilmWork')

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = 'Obra Cinematográfica'
        verbose_name_plural = 'Obras Cinematográficas'

    def __str__(self):
        return self.title


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField('full_name', max_length=256)
    
    class Meta:
        db_table = "content\".\"person"
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return self.full_name


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "content\".\"genre_film_work"
        constraints = [
            models.UniqueConstraint(fields=['film_work', 'genre'], name='unique_film_work_genre')
        ]


class PersonFilmWork(UUIDMixin):
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.CharField('role', max_length=256)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "content\".\"person_film_work"
        constraints = [
            models.UniqueConstraint(fields=['film_work', 'person', 'role'], name='unique_film_work_person_role')
        ]