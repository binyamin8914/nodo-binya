#!/usr/bin/env python

import os
import sys
import django

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NODO.settings')
django.setup()

from clientes.models import Client, Domain

# Validar si ya existe el tenant 'public'
if Client.objects.filter(schema_name='public').exists():
    print("❌ El tenant 'public' ya existe.")
else:
    client = Client(schema_name='public', name='NODO')
    client.save()
    print("✅ Tenant 'public' creado correctamente.")

    if Domain.objects.filter(domain='nodo.com').exists():
        print("❌ El dominio 'nodo.com' ya está en uso.")
    else:
        domain = Domain(
            domain='nodo.com',
            tenant=client,
            is_primary=True
        )
        domain.save()
        print("✅ Dominio 'nodo.com' asociado al tenant 'public'.")
