#!/usr/bin/env python

import os
import sys
import django

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NODO.settings')
django.setup()

from clientes.models import Client, Domain

if len(sys.argv) != 3:
    print("Uso: python create_tenant.py <NombreEmpresa> <dominio>")
    sys.exit(1)

name = sys.argv[1]
domain_name = sys.argv[2]
schema = domain_name.split('.')[0]

if Client.objects.filter(schema_name=schema).exists():
    print(f"❌ El esquema '{schema}' ya existe.")
    sys.exit(1)

if Domain.objects.filter(domain=domain_name).exists():
    print(f"❌ El dominio '{domain_name}' ya está en uso.")
    sys.exit(1)

client = Client(schema_name=schema, name=name)
client.save()
print(f"✅ Tenant '{name}' con esquema '{schema}' creado.")

domain = Domain(
    domain=domain_name,
    tenant=client,
    is_primary=True
)
domain.save()
print(f"✅ Dominio '{domain_name}' asociado al tenant '{name}'.")
