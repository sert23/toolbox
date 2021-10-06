from django.db import models


class Species (models.Model):
    sp_class = models.CharField(max_length=100, default='---')
    specie = models.CharField(max_length=100, default='---')
    shortName = models.CharField(max_length=100, default='---')
    db = models.CharField(max_length=100, default='---')
    db_ver = models.CharField(max_length=100, default='---')
    scientific = models.CharField(max_length=100, default='---')
    taxID = models.CharField(max_length=100, default='---')
    full = models.BooleanField(default=False)
    hasTargetSequencesAndGO = models.BooleanField(default=False)

    def __str__(self):
        return self.specie + " (" + self.db + ")"
        #return self.specie + "(" + self.db + "), " + self.scientific

    def get_value(self):
        return '{}:{}:{}'.format(self.shortName, self.db, self.db_ver)


    @staticmethod
    def create_batch(ifile):
        with open(ifile) as i:
            for line in i:
                a = line.replace('\n', '').split(',')
                if a:
                    if a[7] == 'true':
                        a[7] = True
                    else:
                        a[7] = False

                    if a[8] == 'true':
                        a[8] = True
                    else:
                        a[8] = False

                    Species.objects.create(
                        sp_class=a[0],
                        specie=a[1],
                        shortName=a[2],
                        db=a[3],
                        db_ver=a[4],
                        scientific=a[5],
                        taxID=a[6],
                        full=a[7],
                        hasTargetSequencesAndGO=a[8]

                    )

    @staticmethod
    def clear_species():
        Species.objects.all().delete()
