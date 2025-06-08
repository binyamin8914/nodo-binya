from django.db import models
from django.utils.text import slugify
# Create your models here.
class Post(models.Model):
    autor = models.CharField(max_length=200,blank=False)
    titulo = models.CharField(max_length=200, blank=False)
    portada= models.ImageField(upload_to='django-summernote/portadas/', default='django-summernote/portadas/default.png', blank=True)
    contenido = models.TextField(blank=False)
    publico = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=200,blank=True,help_text="Este sera el nombre del enlace para ver el post <br>  *Dejalo vacio si quieres que sea el nombre del post")
    tags = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Agrega tags separados por comas "
    )
    fecha = models.DateTimeField(auto_now=True)

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def save(self, *args, **kwargs):
        slug = self.slug
        base_slug = self.slug
        if not self.slug:  # Si el slug está vacío, generamos uno a partir del título
            base_slug = slugify(self.titulo)
            slug = base_slug
        num = 1
        while Post.objects.filter(slug=slug).exists():#si el slug existe se crea con un numero al final
            slug = f"{base_slug}-{num}"
            num += 1
        self.slug = slug
        super().save(*args, **kwargs)