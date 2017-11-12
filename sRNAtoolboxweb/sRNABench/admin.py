from django.contrib import admin

from .models import Species


class SpeciesAdmin(admin.ModelAdmin):

    pass
    # search_fields = ('gene_symbol', 'gene_name',)

admin.site.register(Species, SpeciesAdmin)