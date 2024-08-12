from django.contrib import admin
from django import forms
from .models import Actor, Movie, AlternativeMovieTitle


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    pass


@admin.register(AlternativeMovieTitle)
class AlternativeMovieTitleAdmin(admin.ModelAdmin):
    pass


class AlternativeTitlesInline(admin.TabularInline):
    model = AlternativeMovieTitle
    fields = ("title", "language_code", "translated_title",)
    readonly_fields = ("title", "language_code", "translated_title",)
    show_change_link = True
    can_delete = False


class StopAdminForm(forms.ModelForm):
  
  class Meta:
    model = Movie
    widgets = {
       "cast": admin.widgets.FilteredSelectMultiple("Actors", is_stacked=False)
    }
    fields = '__all__'

@admin.register(Movie) 
class MovieAdmin(admin.ModelAdmin):
    inlines = (AlternativeTitlesInline,)
    form = StopAdminForm
    
