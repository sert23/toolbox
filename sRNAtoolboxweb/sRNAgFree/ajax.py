from django.shortcuts import render
import itertools
from FileModels.gfreeOutParser import GFreeOutParser
from progress.models import JobStatus
from FileModels.organimsParser import OrganimsParser

__author__ = 'antonior'
import random
# from dajax.core import Dajax
import json
# from dajaxice.decorators import dajaxice_register
import django_tables2 as tables
counter = itertools.count()
ORGANIMS_FILE = "/home/antonior/organisms.txt"


class TableStatic(tables.Table):
    """
    Class to serialize table of results
    """

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("name",)

class TableResult(tables.Table):
    """
    Class to serialize table of results
    """

    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                 "id": lambda: "table_%d" % next(counter)}
        empty_text = "Results not found!"
        order_by = ("name",)


def define_table(columns, typeTable):
    """
    :param columns: Array with names of columns to show
    :return: a class of type TableResults
    """

    attrs = dict((c, tables.Column()) for c in columns if c != "url")
    print attrs
    attrs2 = dict((c, tables.URLColumn()) for c in columns if c == "url")
    attrs.update(attrs2)
    if typeTable == "TableResult":
        attrs['Meta'] = type('Meta', (),
                             dict(attrs={'class': 'table table-striped table-bordered table-hover dataTable no-footer',
                                         "id": lambda: "table_%d" % next(counter)},
                                  ordenable=False,
                                  empty_text="Results not found!",
                                  order_by=("name",)))
    else:
        attrs['Meta'] = type('Meta', (),
                             dict(attrs={'class': 'table table-striped',
                                         "id": "notformattable"},
                                  ordenable=False,
                                  empty_text="Results not found!",
                                  order_by=("name",)))



    klass = type('TableResult', (tables.Table,), attrs)
    return klass


class Result():
    """
    Class to manage tables results and meta-info
    """

    def __init__(self, name, table):
        self.name = name.capitalize()
        self.content = table
        self.id = name.replace(" ", "_")

@dajaxice_register
def ajax_name_organisms(request, list_name):
   dajax = Dajax()
   parser = OrganimsParser(ORGANIMS_FILE)
   names = list_name.split(":")
   organisms = set()
   for name in names:
       organism = parser.get_organims_from_name(name)
       if organism is not None:
           organisms.add(organism)
   if len(organisms) > 0:
       dajax.assign("#ajax_names", 'value', ":".join(organisms))
   else:
       dajax.assign("#ajax_names", 'value', " ")
   return dajax.json()



@dajaxice_register
def ajax_result(request, option, id):
    dajax = Dajax()

    new_record = JobStatus.objects.get(pipeline_key=id)
    assert isinstance(new_record, JobStatus)

    parser = GFreeOutParser(new_record.info_file, new_record.micro_file)
    all_mircros = {m.name: m for m in parser.parse()}
    results = {}
    micros = all_mircros[option]
    matures = all_mircros[option].matures
    header_micros = micros.get_sorted_attr()
    header_mature = matures[0].get_sorted_attr()

    mirna_result = Result("micros", define_table(header_micros, 'noTableResult')([micros]))
    matures_result = Result("micros", define_table(header_mature, 'noTableResult')(matures))

    fd = file("/shared/sRNAtoolbox/webData/test_free/align/" + option + ".align")

    results["mirnas"] = mirna_result
    results["matures"] = matures_result
    results["align"] = "\n"+"".join(fd.readlines())
    dajax.assign('#result_ajax', 'innerHTML',   render(request, 'ajax_result.html', results).content)

    return dajax.json()




