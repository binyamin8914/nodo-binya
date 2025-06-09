from django_tenants.utils import schema_context

with schema_context('empresax'):
    from django.contrib.auth.models import User
    from administracion.models import Empresa, usuario_base, Match
    from desafios.models import Desafio, PostulacionDesafio
    from iniciativas.models import Iniciativa, PostulacionIniciativa

    # Cambia este correo por el de tu ejecutivo real
    ejecutivo_email = "ejecutivo1.prueba@gmail.com"
    ejecutivo_user = User.objects.get(email=ejecutivo_email)

    empresa = Empresa.objects.create(
        nombre="Empresa X",
        cantPersonas=100,
        año=2024,
        actividad="Tecnología",
        pais="Chile",
        ciudad="Santiago",
        isActive=True
    )

    contacto = usuario_base.objects.create(
        nombre="Carlos Contacto",
        correo="contacto@empresa.com",
        contraseña="contactopass@123",
        rol="contacto",
        cargo="Gerente de Innovación",
        telefono="123456789",
        empresa=empresa,
        es_activo=True
    )

    postulacion = PostulacionDesafio.objects.create(
        empresa=empresa,
        contacto=contacto,
        descripcionInicial="desc",
        desafioFrase="frase",
        presupuesto="10000",
        pregunta="pregunta",
        origen="web"
    )

    desafio = Desafio.objects.create(
        postulacion=postulacion,
        ejecutivo=ejecutivo_user,
        empresa=empresa,
        contacto=contacto,
        nombreDesafio="Desafío de Prueba",
        impactoProblema="Impacto alto",
        efectoOperacion="Afecta operaciones críticas",
        descripcionDesafio="Descripción extensa del desafío",
        costoOportunidad=10000,
        intentosPreviosSolucion="Ninguno",
        ventasMesUsd=10000,
        margenBruto=2000,
        ebitda=1500,
        cantidadClientes=5,
        isPrincipal=True,
        show=True,
        isActive=True
    )
    postulacion_iniciativa = PostulacionIniciativa.objects.create(
        empresa=empresa,
        contacto=contacto,
        titulo="Postulación de Prueba",
        descripcion="Descripción de la postulación",
        pregunta="¿Por qué quieres participar?",
        origen="web",
        latam="Sí",
        video="",
        diferenciacion="Algo diferente",
        traccion="Tracción demostrada",
        piloto="Piloto exitoso"
    )

    iniciativa = Iniciativa.objects.create(
        titulo="Iniciativa de Prueba",
        descripcion="Descripción de la iniciativa",
        preevaluacion="Preevaluación",
        recomendacion="Recomendación",
        madurez="Alta",
        presentacion="",
        comite="Comité de Innovación",
        postulacion=postulacion_iniciativa,  # Ahora sí, no es None
        empresa=empresa,
        contacto=contacto,
        ejecutivo=ejecutivo_user,
        desafio=desafio,
        isActive=True
    )

    match = Match.objects.create(
        estado="Activo",
        brl="BRL1",
        trl="TRL1",
        ejecutivo=ejecutivo_user,
        desafio=desafio,
        iniciativa=iniciativa,
        isActive=True
    )

    print("¡Datos de prueba creados en el tenant empresax!")