# Create your views here.
import os

from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from FileModels.gfreeOutParser import GFreeOutParser
from progress.models import JobStatus
from utils import pipeline_utils
from utils.sysUtils import make_dir

FS = FileSystemStorage("/shared/sRNAtoolbox/webData")


def input(request):
    return render(request, 'gfree.html', {})

def run(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    rc = request.POST["rc"]
    rl = "19"
    mm = request.POST["mm"]
    xrl = "23"
    homolog = request.POST["ajax_names"]
    name = pipeline_id + '_gfree'

    if homolog.replace(" ", "") == "":
        homolog = "false"
        #return render(request, "error_page.html", {"errors": ["Any species name must be provided. Please check the manual"]})



    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)

    if "reads_file" in request.FILES:
        file_to_update = request.FILES['reads_file']
        uploaded_file = str(file_to_update)
        FS.save(uploaded_file, file_to_update)
        input = os.path.join(FS.location, uploaded_file)

        outdir = FS.location


        os.system('qsub -v pipeline="gfree",input="' + input + '",key="' + pipeline_id + '",minReadLength="' + rl +
                  '",maxReadLength="' + xrl + '",microRNA="' + homolog + '",minRC="' + rc + '",noMM="' + mm +
                  '",outdir="' + outdir + '",name="' + name + '" -N ' + name +
                  ' /shared/sRNAtoolbox/core/bash_scripts/run_sRNAgfree.sh')

        print ('qsub -v pipeline="gfree",input="' + input + '",key="' + pipeline_id + '",minReadLength="' + rl +'",maxReadLength="' + xrl + '",microRNA="' + homolog + '",minRC="' + rc + '",noMM="' + mm +'",outdir="' + outdir + '",name="' + name + '" -N ' + name +' /shared/sRNAtoolbox/core/bash_scripts/run_sRNAgfree.sh')


        return redirect("/srnatoolbox/jobstatus/srnagfree/?id=" + pipeline_id)

    else:
        return render(request, "error_page.html", {"errors": ["Reads File must be provided"]})


def result(request):
    if 'id' in request.GET:
        job_id = request.GET['id']

        new_record = JobStatus.objects.get(pipeline_key=job_id)
        assert isinstance(new_record, JobStatus)


        if new_record.job_status == "Finished":
            parser = GFreeOutParser(new_record.info_file, new_record.micro_file)
            all_mircros = [m for m in parser.parse()]
            zip_file = "/".join(new_record.zip_file.split("/")[-2:])
            return render(request, 'gfree_result.html', {"id": job_id,"mirnas": all_mircros, "number": len(all_mircros),
                                                         "zip": zip_file})


        else:
            return redirect("/srnatoolbox/jobstatus/srnagfree/?id=" + job_id)

    else:
        return redirect("/srnatoolbox/srnagfree")


def test(request):
    pipeline_id = pipeline_utils.generate_uniq_id()
    FS.location = os.path.join("/shared/sRNAtoolbox/webData", pipeline_id)
    make_dir(FS.location)
    outdir = FS.location
    name = pipeline_id + '_gfree'
    os.system('qsub -v pipeline="gfree",input="' + "/shared/sRNAtoolbox/testData/Ddent_exo.fa" + '",key="' + pipeline_id + '",minReadLength="' + "19" +
              '",maxReadLength="' + "23" + '",microRNA="' + "sja:sma:egr:emu:sme:cel:bta" + '",minRC="' + "10" + '",noMM="' + "0" +
              '",outdir="' + outdir + '",name="' + name + '" -N ' + name +
              ' /shared/sRNAtoolbox/core/bash_scripts/run_sRNAgfree.sh')

    return redirect("/srnatoolbox/jobstatus/srnagfree/?id=" + pipeline_id)

