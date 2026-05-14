from django.contrib import admin
from .models import (
    Genre,
    FilmWork,
    Person,
    GenreFilmWork,
    PersonFilmWork

)
# Register your models here.

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass

@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):

    class GenreFilmWorkInline(admin.TabularInline):
        model = GenreFilmWork
    
    class PersonFilmWorkInline(admin.TabularInline):
        model = PersonFilmWork
    
    inlines = (GenreFilmWorkInline,)
    # Campos a mostrar en la lista
    list_display = ('title', 'type', 'creation_date', 'rating', 'created', 'modified')
    # Filtrado en la lista
    list_filter = ('type',)
    # Búsqueda por campos
    search_fields = ('title', 'description', 'id')

@admin.register(Person)
class Person(admin.ModelAdmin):
    pass


