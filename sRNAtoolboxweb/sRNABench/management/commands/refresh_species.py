from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from sRNABench.models import Species

class Command(BaseCommand):
    help = 'refreshes the species database'


    def handle(self):

        CONF = settings.CONF
        path_to_species = CONF["species"]
        self.stdout.write(path_to_species)
        # print(path_to_species)


    #     for poll_id in options['poll_ids']:
    #         try:
    #             poll = Poll.objects.get(pk=poll_id)
    #         except Poll.DoesNotExist:
    #             raise CommandError('Poll "%s" does not exist' % poll_id)
    #
    #         poll.opened = False
    #         poll.save()
    #
    #         self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))