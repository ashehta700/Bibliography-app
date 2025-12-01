from django.db import models



def report_upload_to(instance, filename):
    return f"pdfs/{instance.Library_Reference}/{filename}"

class Report(models.Model):
    Library_Reference = models.CharField(max_length=50  ,primary_key=True)
    Date_Issue = models.IntegerField()
    Type_of_report_ID = models.ForeignKey('Type_Report', on_delete=models.SET_NULL, null=True, db_column='Type_of_report_ID')
    Title = models.CharField(max_length=255)
    Title_ar = models.CharField(max_length=255)
    Authors_Name = models.CharField(max_length=255)
    Abstract = models.TextField(blank=True)
    Abstract_ar = models.TextField(blank=True)
    Keywords = models.TextField(blank=True)
    Reference = models.TextField(blank=True)
    publishability = models.TextField(blank=True)
    Reference = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to=report_upload_to)
    # Publisher_ID = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, db_column='Publisher_ID')
    read_count = models.PositiveIntegerField(default=0)  # New field to track views
    def __str__(self):
        return f"{self.Library_Reference} - {self.Title}"
    
    class Meta:
        managed = False
        db_table = 'BIB_tech_report'



class Company(models.Model):
    id = models.CharField(primary_key=True, max_length=50)  # example: 'T001'
    English_Value = models.CharField(max_length=255, unique=True)
    Arabic_Value = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.English_Value  
    
    class Meta:
        managed = False
        db_table = 'Lex_Organization'
    
    
    
class Type_Report(models.Model):  
    id = models.CharField(primary_key=True, max_length=10)  # example: 'T001'
    English_Value = models.CharField(max_length=255, unique=True)
    Arabic_Value = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.English_Value  
    
    
    class Meta:
        managed = False
        db_table = 'Lex_tech_reports'
        
        
        
# def appendix_upload_to(instance, filename):
#     if instance.Library_Reference:
#         return f"pdfs/{instance.Library_Reference.Library_Reference}/appendices/{filename}"
#     return f"pdfs/unknown_report/appendices/{filename}"




# class Appendix_table(models.Model):  
#     Appendix_Id = models.CharField(max_length=255, primary_key=True)
#     Library_Reference = models.ForeignKey('Report', on_delete=models.SET_NULL, null=True, db_column='Library_Reference')
#     Type_of_report_ID = models.ForeignKey('Type_Report', on_delete=models.SET_NULL, null=True, db_column='[Type_Id]')
#     Name_of_appendix = models.CharField(max_length=500)
#     Notes = models.CharField(max_length=255, blank=True)
#     pdf_file = models.FileField(upload_to=appendix_upload_to)

#     def __str__(self):
#         return self.Name_of_appendix  # Fix this to a valid field name
    
#     # def save(self, *args, **kwargs):
#     #     if not self.Appendix_Id:
#     #         self.Appendix_Id = f"{self.Library_Reference.Library_Reference}_APP_{uuid.uuid4().hex[:6]}"
#     #     super().save(*args, **kwargs)
    
#     class Meta:
#         managed = False
#         db_table = 'Appendex_info'
