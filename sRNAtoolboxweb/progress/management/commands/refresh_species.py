from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from sRNABench.models import Species





class Command(BaseCommand):
    help = 'refreshes the species database'


    def handle(self, *args, **options):

        try:
            CONF = settings.CONF
            path_to_species = CONF["species"]
            Species.clear_species()
            self.stdout.write(self.style.SUCCESS("old species database cleared"))
            Species.create_batch(path_to_species)
            self.stdout.write(self.style.SUCCESS("updating new species"))
            self.stdout.write(self.style.SUCCESS("species database succesfully updated using:"))
            self.stdout.write(self.style.SUCCESS(path_to_species))
        except:
            self.stdout.write(self.style.ERROR("There was some error, the database wasn't updated"))
            self.stdout.write(self.style.ERROR("Check that " + path_to_species + " is the correct file"))
            self.stdout.write(self.style.ERROR("Check file format"))
            self.stdout.write(self.style.ERROR("species database might be empty now!!"))