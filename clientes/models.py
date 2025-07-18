from django.db import models

# Create your models here.
from django_tenants.models import TenantMixin, DomainMixin 

 

class Client(TenantMixin): 
    name = models.CharField(max_length=100) 
    paid_until = models.DateField(null=True, blank=True) 
    on_trial = models.BooleanField(default=True) 
    created_on = models.DateField(auto_now_add=True) 
    auto_create_schema = True 

    def __str__(self): 
        return self.name 

class Domain(DomainMixin): 
    pass 