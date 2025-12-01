from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import FileResponse
from .models import *
from django.utils import translation
from .forms import * 
from django.core import signing
from django.http import FileResponse, HttpResponseForbidden,HttpResponseBadRequest, HttpResponse
from urllib.parse import quote
from django.urls import reverse
from django.db.models import Q, F
from django.db.models.functions import Cast
from django.db.models import TextField
from django.forms import inlineformset_factory
from django.utils.translation import gettext as _
import os
import re
import csv
from django.conf import settings



def icontains_ntext(queryset, field, val):
    """
    Apply icontains filter on ntext fields by casting to nvarchar(max) using raw SQL.
    `field` is the exact column name in DB (with table alias if needed).
    """
    if not val:
        return queryset
    return queryset.extra(
        where=[f"CAST({field} AS NVARCHAR(MAX)) LIKE %s"],
        params=[f"%{val}%"]
    )
    
    
    
def home(request):
    lang = translation.get_language()
    is_arabic = lang.startswith('ar')

    title_field = "Title_ar" if is_arabic else "Title"
    abstract_field = "Abstract_ar" if is_arabic else "abstract"
    report_type_field = "Arabic_Value" if is_arabic else "English_Value"

    # Filter reports by publishability = 1 or 2
    reports = Report.objects.select_related('company', 'Type_of_report_ID')\
        .filter(publishability__in=[1, 2])

    top_reports = reports.order_by('-read_count')[:3]

    query = request.GET.get("q")
    if query:
        keywords = query.strip().split()

        reports = reports.annotate(
            title_text=Cast(F(title_field), TextField()),
            ref_text=Cast(F('Library_Reference'), TextField()),
            Keywords_text=Cast(F('Keywords'), TextField())
        )

        filter_q = Q()
        for word in keywords:
            word_q = Q(title_text__icontains=word) | Q(ref_text__icontains=word) | Q(Keywords_text__icontains=word)
            filter_q &= word_q

        reports = reports.filter(filter_q)

    company_id = request.GET.get("company")
    author = request.GET.get("author")
    report_id = request.GET.get("report_id")
    title = request.GET.get("title")
    report_type = request.GET.get("report_type")
    year = request.GET.get("year")

    report_table = Report._meta.db_table
    type_report_table = Type_Report._meta.db_table

    if company_id:
        reports = reports.filter(company_id=company_id)
    if author:
        reports = icontains_ntext(reports, f"{report_table}.Authors_Name", author)
    if report_id:
        reports = icontains_ntext(reports, f"{report_table}.Library_Reference", report_id)
    if title:
        reports = icontains_ntext(reports, f"{report_table}.{title_field}", title)
    if report_type and report_type:
        reports = reports.filter(Type_of_report_ID__id=report_type)
    if year and year.isdigit():
        reports = reports.filter(Date_Issue=int(year))

    # for report in reports:
    #     report.appendices = Appendix_table.objects.filter(Library_Reference=report)

    paginator = Paginator(reports, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    query_params = "".join(
        [f"&{key}={value}" for key, value in request.GET.items() if key != "page"]
    )

    companies = Company.objects.all()
    report_types = Type_Report.objects.all()
    report_type_dict = {
        str(rt.id): rt.Arabic_Value if is_arabic else rt.English_Value
        for rt in report_types
    }
    total_appendices = 0
    for report in reports:
        appendix_files = get_appendix_files(report.Library_Reference)
        total_appendices += len(appendix_files)
        appendix_tokens = []
        for appendix_file in appendix_files:
            display_name = appendix_file.replace("MAP", "Appendix").replace(".pdf", "").strip()
            appendix_tokens.append({
                'filename': display_name,
            })
        report.appendices = appendix_tokens
        
        
    # If user clicked "Export CSV"
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="reports.csv"'
        writer = csv.writer(response)

        # CSV Header
        writer.writerow(["Library Reference", "Title", "Date Issue", "Report Type", "Appendices"])

        # CSV Rows
        for r in reports:
            appendices_list = ", ".join(a['filename'] for a in r.appendices)
            writer.writerow([
                r.Library_Reference,
                r.Title_ar if request.LANGUAGE_CODE == "ar" else r.Title,
                r.Date_Issue,
                r.Type_of_report_ID.Arabic_Value if request.LANGUAGE_CODE == "ar" else r.Type_of_report_ID.English_Value,
                appendices_list
            ])

        return response
        

    context = {
        "reports": page_obj,
        "count": reports.count(),
        "query_params": query_params,
        "is_arabic": is_arabic,
        "top_reports": top_reports,
        "companies": companies,
        "report_types": report_types,
        "report_type_dict": report_type_dict,
        'total_appendices':total_appendices 

    }

    return render(request, "home.html", context)


    
SIGNING_SALT = 'secure_pdf_salt'



#  for get the pdf file from the folder not from the column field_path of the database 



# this is old report details that can get the pdf files with pdf_file path on the database 
# def report_detail(request, pk):
#     report = get_object_or_404(Report, Library_Reference=pk)
#     # Handle None case
#     if report.read_count is None:
#         report.read_count = 1
#     else:
#         report.read_count += 1
#     report.save(update_fields=['read_count'])

#     appendices = Appendix_table.objects.filter(Library_Reference=report)

#     for appendix in appendices:
#         # Token with prefix for source
#         appendix.token = signing.dumps(f"appendix:{appendix.pk}", salt=SIGNING_SALT)

#     # Token for main report
#     pdf_token = signing.dumps(f"report:{report.pk}", salt=SIGNING_SALT)

#     return render(request, 'report_detail.html', {
#         'report': report,
#         'related_reports': appendices,
#         'pdf_token': pdf_token,
#     })

# get the pdf files from the folder
def report_detail(request, pk):
    report = get_object_or_404(Report, Library_Reference=pk)

    # Update read count
    report.read_count = (report.read_count or 0) + 1
    report.save(update_fields=['read_count'])

    # Main report
    pdf_token = signing.dumps(f"report:{report.pk}", salt=SIGNING_SALT)
    main_pdf_filename = f"{report.Library_Reference}"

    # Appendices
    appendix_files = get_appendix_files(report.Library_Reference)
    appendix_tokens = []
    for appendix_file in appendix_files:
        display_name = appendix_file.replace("MAP", "Appendix").replace(".pdf", "").strip()
        token_data = f"{report.Library_Reference}:{appendix_file}"
        token = signing.dumps(f"appendix_file:{token_data}", salt=SIGNING_SALT)
        appendix_tokens.append({
            'filename': display_name,
            'token': token
        })

    return render(request, 'report_detail.html', {
        'report': report,
        'pdf_token': pdf_token,
        'main_pdf_filename': main_pdf_filename,
        'appendices': appendix_tokens,
    })


# old for the path of the pdf from the column pdf_path
# def secure_pdf_viewer(request, token):
#     try:
#         decoded = signing.loads(token, salt=SIGNING_SALT)
#         file_type, obj_id = decoded.split(":")
#     except (signing.BadSignature, ValueError):
#         return HttpResponseBadRequest("Invalisecure_urld or expired token")

#     secure_url = request.build_absolute_uri(reverse('secure_pdf_file', args=[token]))
#     encoded = quote(secure_url, safe='')

#     return redirect(f'/static/pdfjs/web/viewer.html?file={encoded}')
# def secure_pdf_file(request, token):
#     try:
#         decoded = signing.loads(token, salt=SIGNING_SALT)
#         file_type, obj_id = decoded.split(":")
#     except (signing.BadSignature, ValueError):
#         return HttpResponseForbidden("Invalid or expired token")

#     if file_type == "report":
#         obj = get_object_or_404(Report, pk=obj_id)
#         file_path = obj.pdf_file.path
#     elif file_type == "appendix":
#         obj = get_object_or_404(Appendix_table, pk=obj_id)
#         file_path = obj.pdf_file.path  # update to your field name if different
#     else:
#         return HttpResponseForbidden("Unknown file type")

#     return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
# def secure_pdf_download(request, token):
#     try:
#         decoded = signing.loads(token, salt=SIGNING_SALT)
#         file_type, obj_id = decoded.split(":")
#     except (signing.BadSignature, ValueError):
#         return HttpResponseForbidden("Invalid or expired token")

#     if file_type == "report":
#         obj = get_object_or_404(Report, pk=obj_id)
#         file_path = obj.pdf_file.path
#         filename = obj.Title.replace(" ", "_") + ".pdf"
#     elif file_type == "appendix":
#         obj = get_object_or_404(Appendix_table, pk=obj_id)
#         file_path = obj.pdf_file.path  # update this field name if needed
#         filename = obj.Name_of_appendix.replace(" ", "_") + ".pdf"
#     else:
#         return HttpResponseForbidden("Unknown file type")

#     response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'
#     return response


# generate a file path from the folder not from the column 
def secure_pdf_viewer(request, token):
    try:
        decoded = signing.loads(token, salt=SIGNING_SALT)
        # Can be: "report:<report_id>" or "appendix_file:<Library_Reference>:<filename>"
    except (signing.BadSignature, ValueError):
        return HttpResponseBadRequest("Invalid or expired token")

    secure_url = request.build_absolute_uri(reverse('secure_pdf_file', args=[token]))
    encoded = quote(secure_url, safe='')

    return redirect(f'/static/pdfjs/web/viewer.html?file={encoded}')


def get_report_file_path(library_reference):
    base_path = os.path.join(settings.MEDIA_ROOT, "TECHNICAL_REPORTS", library_reference)
    filename = f"{library_reference}.pdf"
    return os.path.join(base_path, filename)
def get_appendix_files(library_reference):
    """
    Returns a list of appendix PDF filenames from the filesystem
    for the given Library_Reference. Only files with 'MAP' in their name
    (excluding the main PDF) are included.
    """
    folder_path = os.path.join(settings.MEDIA_ROOT, "TECHNICAL_REPORTS", library_reference)
    
    if not os.path.exists(folder_path):
        return []

    appendix_files = []
    main_pdf_name = f"{library_reference}.pdf"

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            # Normalize comparison (e.g. 68 JED 29 == 68-JED-29)
            clean_main = re.sub(r'[\s\-]+', '', main_pdf_name.lower())
            clean_file = re.sub(r'[\s\-]+', '', filename.lower())

            if clean_file == clean_main:
                continue  # skip the main PDF

            if "map" in filename.lower():
                appendix_files.append(filename)

    return sorted(appendix_files)  # optionally sort for order

def secure_pdf_file(request, token):
    try:
        decoded = signing.loads(token, salt=SIGNING_SALT)
        parts = decoded.split(":")
    except (signing.BadSignature, ValueError):
        return HttpResponseForbidden("Invalid or expired token")

    if parts[0] == "report":
        report_id = parts[1]
        report = get_object_or_404(Report, pk=report_id)
        file_path = get_report_file_path(report.Library_Reference)

    elif parts[0] == "appendix_file":
        library_reference = parts[1]
        filename = parts[2]
        file_path = os.path.join(settings.MEDIA_ROOT, "TECHNICAL_REPORTS", library_reference, filename)

    else:
        return HttpResponseForbidden("Unknown file type")

    if not os.path.exists(file_path):
        return HttpResponseBadRequest("File not found")

    return FileResponse(open(file_path, 'rb'), content_type='application/pdf')


def secure_pdf_download(request, token):
    try:
        decoded = signing.loads(token, salt=SIGNING_SALT)
        parts = decoded.split(":")
    except (signing.BadSignature, ValueError):
        return HttpResponseForbidden("Invalid or expired token")

    if parts[0] == "report":
        report_id = parts[1]
        report = get_object_or_404(Report, pk=report_id)
        file_path = get_report_file_path(report.Library_Reference)
        filename = f"{report.Library_Reference}.pdf"

    elif parts[0] == "appendix_file":
        library_reference = parts[1]
        filename = parts[2]
        file_path = os.path.join(settings.MEDIA_ROOT, "TECHNICAL_REPORTS", library_reference, filename)

    else:
        return HttpResponseForbidden("Unknown file type")

    if not os.path.exists(file_path):
        return HttpResponseBadRequest("File not found")

    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



#  for the list of the Reports 

def report_admin_list(request):
    lang = translation.get_language()
    is_arabic = lang.startswith('ar')

    title_field = "Title_ar" if is_arabic else "Title"
    report_type_field = "Arabic_Value" if is_arabic else "English_Value"

    reports = Report.objects.select_related('company', 'Type_of_report_ID').all()

    query = request.GET.get("q")
    company_id = request.GET.get("company")
    author = request.GET.get("author")
    report_id = request.GET.get("report_id")
    title = request.GET.get("title")
    report_type = request.GET.get("report_type")
    year = request.GET.get("year")

    # Note: add table alias before column names in extra where clause
    # Report table alias in queries is usually "BIB_tech_report"
    report_table = Report._meta.db_table
    type_report_table = Type_Report._meta.db_table

    if query:
        reports = icontains_ntext(reports, f"{report_table}.{title_field}", query)
    if company_id:
        reports = reports.filter(company_id=company_id)
    if author:
        reports = icontains_ntext(reports, f"{report_table}.Authors_Name", author)
    if report_id:
        reports = icontains_ntext(reports, f"{report_table}.Library_Reference", report_id)
    if title:
        reports = icontains_ntext(reports, f"{report_table}.{title_field}", title)
    if report_type:
        # Because Type_of_report_ID is a FK, join is automatic via select_related,
        # but for extra where we must join manually
        # We'll add the related table for where clause filtering
        reports = reports.extra(
            tables=[type_report_table],
            where=[
                f"{report_table}.Type_of_report_ID = {type_report_table}.id",
                f"CAST({type_report_table}.{report_type_field} AS NVARCHAR(MAX)) LIKE %s"
            ],
            params=[f"%{report_type}%"]
        )
    if year and year.isdigit():
        reports = reports.filter(Date_Issue=int(year))

    # Attach related documents (by report type) to each report
    for report in reports:
        if report.Type_of_report_ID is None:
            report.related_documents = []
            continue  # Skip if no type is assigned

        report_type_value = getattr(report.Type_of_report_ID, report_type_field)
        related_filter = {
            f"Type_of_report_ID__{report_type_field}": report_type_value
        }
        report.related_documents = Report.objects.filter(
            **related_filter
        ).exclude(Library_Reference=report.Library_Reference)[:5]

    paginator = Paginator(reports, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    query_params = "".join(
        [f"&{key}={value}" for key, value in request.GET.items() if key != "page"]
    )

    companies = Company.objects.all()

    return render(request, 'admin_reports/list.html', {
        "reports": page_obj,
        "companies": companies,
        "query_params": query_params,
        "count": reports.count(),
        "is_arabic": is_arabic,
    })




def report_create(request):
    return _handle_report_form(request)

def report_update(request, Library_Reference):
    report = get_object_or_404(Report, pk=Library_Reference)
    return _handle_report_form(request, instance=report)

def _handle_report_form(request, instance=None):
    action = _("Edit") if instance else _("Add")

    # ✅ Correct: create formset class WITHOUT 'prefix'
    # AppendixFormSet = inlineformset_factory(
    #     Report,
    #     # Appendix_table,
    #     # form=AppendixForm,
    #     extra=1 if instance is None else 0,
    #     can_delete=True
    # )

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=instance)
        # formset = AppendixFormSet(request.POST, request.FILES, instance=instance, prefix='form')  # ✅ Correct: use prefix here only

        if form.is_valid() :
            report = form.save()
            # appendices = formset.save(commit=False)

            # for index, appendix in enumerate( start=1):
            #     if not appendix.Appendix_Id:
            #         appendix.Appendix_Id = f"{report.Library_Reference}_{str(index).zfill(3)}"
            #     appendix.Library_Reference = report
            #     appendix.save()

            # for obj in formset.deleted_objects:
            #     obj.delete()

            return redirect('report_admin_list')
        else:
            print(form.errors)
            # print(formset.errors)

    else:
        form = ReportForm(instance=instance)
        # formset = AppendixFormSet(instance=instance, prefix='form')  # ✅ Correct usage here

    return render(request, 'admin_reports/form.html', {
        'form': form,
        # 'formset': formset,
        'action': action,
        'type_choices': Type_Report.objects.all()
    })



# for delete the report
def report_delete(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        report.delete()
        return redirect('report_admin_list')
    return render(request, 'admin_reports/confirm_delete.html', {'report': report})




#  for add appendix to the report 

