from django.contrib import admin
from django import forms
from .models import Person, Movie, AlternativeMovieTitle


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass


class TranslatedListFilter(admin.SimpleListFilter):
    title = "Translated"

    parameter_name = "translated"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(translated_title="")
        if self.value() == "no":
            return queryset.filter(translated_title="")


class TranslationDifferenceListFilter(admin.SimpleListFilter):
    title = "Translation Difference"

    parameter_name = "translation_difference"

    def lookups(self, request, model_admin):
        return [
            ("100", "100%"),
            ("75", "75% - 100%"),
            ("50", "50% - 75%"),
            ("25", "25% - 50%"),
            ("0", "0% - 25%"),
        ]

    def queryset(self, request, queryset):
        if self.value() is not None:

            ratio_min = int(self.value()) / 100
            ratio_max = ratio_min + 0.25

            return queryset.filter(
                translation_difference_ratio__gte=ratio_min,
                translation_difference_ratio__lt=ratio_max,
            )


@admin.register(AlternativeMovieTitle)
class AlternativeMovieTitleAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "language_code",
        "translated_title",
        "translation_difference_ratio",
        "movie",
    ]
    list_filter = [
        TranslatedListFilter,
        TranslationDifferenceListFilter,
        "language_code",
    ]


class AlternativeTitlesInline(admin.TabularInline):
    model = AlternativeMovieTitle
    fields = (
        "title",
        "language_code",
        "translated_title",
        "translation_difference_ratio",
    )
    readonly_fields = (
        "title",
        "language_code",
        "translated_title",
        "translation_difference_ratio",
    )
    show_change_link = False
    can_delete = False
    extra = 0
    ordering = ("-translation_difference_ratio",)


class PersonsAdminForm(forms.ModelForm):

    class Meta:
        model = Movie
        widgets = {
            "cast": admin.widgets.FilteredSelectMultiple("Persons", is_stacked=False)
        }
        fields = "__all__"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    inlines = (AlternativeTitlesInline,)
    form = PersonsAdminForm
