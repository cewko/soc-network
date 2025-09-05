from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from actions.utils import create_action
from .forms import ImageCreateForm
from .models import Image
from .services import ImageViewService, ImageRankingService, ImagePaginationService


class ImageCreateView(LoginRequiredMixin, CreateView):
    model = Image
    form_class = ImageCreateForm
    template_name = 'images/image/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            kwargs['data'] = self.request.GET
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        create_action(self.request.user, "bookmarked image", self.object)
        messages.success(self.request, "Image added successfully")
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'images'
        return context


class ImageDetailView(DetailView):
    model = Image
    template_name = 'images/image/detail.html'
    context_object_name = 'image'
    slug_field = 'slug'
    pk_url_kwarg = 'id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'images'
        
        view_service = ImageViewService()
        context['total_views'] = view_service.record_view(self.object)
        
        return context


class ImageListView(LoginRequiredMixin, ListView):
    model = Image
    template_name = 'images/image/list.html'
    context_object_name = 'images'

    def get_queryset(self):
        return Image.objects.select_related('user').recent()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page = self.request.GET.get("page", 1)
        images_page, is_last_page = ImagePaginationService.paginate_images(
            self.get_queryset(), page, per_page=8
        )

        context['images'] = images_page
        context['is_last_page'] = is_last_page
        context['section'] = 'images'
        return context



class ImageRankingView(LoginRequiredMixin, ListView):
    template_name = 'images/image/ranking.html'
    context_object_name = 'most_viewed'
    
    def get_queryset(self):
        ranking_service = ImageRankingService()
        return ranking_service.get_most_viewed_images()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'images'
        return context


@require_POST
@login_required
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")
    
    if not image_id or action not in ['like', 'unlike']:
        return JsonResponse({"status": "error", "message": "Invalid request"})

    try:
        image = Image.objects.get(id=image_id)
        
        if action == "like":
            if not image.is_liked_by(request.user):
                image.users_like.add(request.user)
                create_action(request.user, "liked", image)
        else:
            if image.is_liked_by(request.user):
                image.users_like.remove(request.user)
        
        return JsonResponse({"status": "ok"})
    except Image.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Image not found"})


image_create = ImageCreateView.as_view()
image_detail = ImageDetailView.as_view()
image_list = ImageListView.as_view()
image_ranking = ImageRankingView.as_view()