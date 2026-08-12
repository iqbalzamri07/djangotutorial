from django.shortcuts import get_object_or_404, render

from .models import Post


def blog(request):
    posts = Post.objects.filter(published=True)
    category = request.GET.get("category")

    if category:
        posts = posts.filter(category=category)

    featured = posts.filter(featured=True).first() or posts.first()
    others = posts.exclude(pk=featured.pk) if featured else posts.none()
    categories = (
        Post.objects.filter(published=True)
        .values_list("category", flat=True)
        .distinct()
    )

    return render(
        request,
        "blogs/blog.html",
        {
            "featured": featured,
            "posts": others,
            "categories": categories,
            "active_category": category or "",
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, published=True)
    related = (
        Post.objects.filter(published=True, category=post.category)
        .exclude(pk=post.pk)[:3]
    )

    return render(
        request,
        "blogs/post_detail.html",
        {
            "post": post,
            "related": related,
        },
    )
