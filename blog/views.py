from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from django.contrib import messages
from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
# Create your views here.

def truncate_text_exclude_images(contenido, word_limit):
    soup = BeautifulSoup(contenido, 'html.parser')

    for img in soup.find_all('img'):
        img.decompose()

    text = soup.get_text()
    words = text.split()
    truncated_text = ' '.join(words[:word_limit])

    return truncated_text



def blog(request):
    query = request.GET.get('q', '')  # Obtén el término de búsqueda del query string
    posts = Post.objects.filter(is_active=True,publico=True).order_by('-fecha')
    
    if query:
        # Filtra los posts por título o contenido
        posts = posts.filter(Q(titulo__icontains=query) | Q(contenido__icontains=query))
    
    
    for post in posts:
        post.contenido_preview = truncate_text_exclude_images(post.contenido, 15)

    return render(request, 'blog.html', {'posts': posts, 'query': query})


def post(request, slug):
    post = get_object_or_404(Post.objects, slug=slug)
    return render(request, 'post.html', {'post': post})

@login_required
def post_preview(request,slug):
    post = get_object_or_404(Post.objects, slug=slug)
    
    post.contenido_preview = truncate_text_exclude_images(post.contenido, 15)

    return render(request, 'post_prev.html', {'post': post})

