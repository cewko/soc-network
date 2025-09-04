from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator

from actions.models import Action
from actions.utils import create_action
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Contact, Profile

User = get_user_model()


class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'account/dashboard.html'
    context_object_name = 'actions'
    paginate_by = 10

    def get_queryset(self):
        following_ids = self.request.user.following.values_list('id', flat=True)
        queryset = Action.objects.exclude(user=self.request.user)
        
        if following_ids:
            queryset = queryset.filter(user_id__in=following_ids)
        
        return queryset.select_related('user', 'user__profile').prefetch_related('target')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'dashboard'
        context['total_images'] = self.request.user.images_created.count()
        return context


@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'account/user/list.html'
    context_object_name = 'users'
    paginate_by = 12

    def get_queryset(self):
        return User.objects.filter(is_active=True).select_related('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'people'
        return context


@method_decorator(login_required, name='dispatch')
class UserDetailView(DetailView):
    model = User
    template_name = 'account/user/detail.html'
    context_object_name = 'user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        return User.objects.filter(is_active=True).select_related('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'people'
        context['user_images'] = self.object.images_created.all()[:12]
        return context


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                create_action(user, 'has created an account')
                messages.success(request, 'Account created successfully!')
                return redirect('account:register_done', user_id=user.id)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'account/register.html', {'form': form})


def register_done_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'account/register_done.html', {'new_user': user})


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile,
            data=request.POST,
            files=request.FILES
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully')
                return redirect('account:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    return render(request, 'account/edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'section': 'profile'
    })


@require_POST
@login_required
def user_follow_view(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')

    if not user_id or action not in ['follow', 'unfollow']:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    try:
        user_to_follow = User.objects.get(id=user_id, is_active=True)
        
        if user_to_follow == request.user:
            return JsonResponse({'status': 'error', 'message': 'Cannot follow yourself'})

        with transaction.atomic():
            if action == 'follow':
                contact, created = Contact.objects.get_or_create(
                    user_from=request.user,
                    user_to=user_to_follow
                )
                if created:
                    create_action(request.user, 'started following', user_to_follow)
            else:
                Contact.objects.filter(
                    user_from=request.user,
                    user_to=user_to_follow
                ).delete()

        return JsonResponse({'status': 'ok'})
        
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An error occurred'})


dashboard = DashboardView.as_view()
user_list = UserListView.as_view()
user_detail = UserDetailView.as_view()
register = register_view
register_done = register_done_view
edit = edit_profile_view
user_follow = user_follow_view
