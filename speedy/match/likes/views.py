from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views import generic
from rules.contrib.views import PermissionRequiredMixin

from speedy.net.profiles.views import UserMixin
from .models import EntityLike


class LikeListDefaultRedirectView(UserMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('likes:list_to', kwargs={'username': self.user.slug})


class LikeListViewBase(UserMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'likes.view_likes'
    template_name = 'likes/like_list.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        cd = super().get_context_data(**kwargs)
        cd.update({
            'display': self.display,
        })
        return cd


class LikeListToView(LikeListViewBase):
    display = 'to'

    def get_queryset(self):
        return EntityLike.objects.filter(from_user=self.user)


class LikeListFromView(LikeListViewBase):
    display = 'from'

    def get_queryset(self):
        return EntityLike.objects.filter(to_entity=self.user)


class LikeListMutualView(LikeListViewBase):
    display = 'to'

    def get_queryset(self):
        who_likes_me = EntityLike.objects.filter(to_entity=self.user).values_list('from_user_id', flat=True)
        return EntityLike.objects.filter(from_user=self.user,
                                         to_entity_id__in=who_likes_me)


class LikeView(UserMixin, PermissionRequiredMixin, generic.View):
    permission_required = 'likes.like'
    raise_exception = True

    def get(self, request, *args, **kwargs):
        return redirect(self.user)

    def post(self, request, *args, **kwargs):
        EntityLike.objects.create(from_user=self.request.user, to_entity=self.user)
        # messages.success(request, _('You like this user.'))
        return redirect(self.user)


class UnlikeView(UserMixin, PermissionRequiredMixin, generic.View):
    permission_required = 'likes.unlike'
    raise_exception = True

    def get(self, request, *args, **kwargs):
        return redirect(self.user)

    def post(self, request, *args, **kwargs):
        EntityLike.objects.filter(from_user=self.request.user, to_entity=self.user).delete()
        # messages.success(request, _('You don\'t like this user.'))
        return redirect(self.user)
