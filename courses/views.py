from django.core.urlresolvers import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView


from .models import Course

# This class can be used for any views, given the model contains the 'owner' attribute
class OwnerMixin(object):
    # This method will be used by Django's Views
    def get_query(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerCourseMixin(OwnerMixin):
    model = Course


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'


class OwnerEditMixin(object):
    # This method will be used by the Django's `ModelForm` mixin
    # UpdateView.form_valid/CreateView.form_valid() is executed when the submitted form is valid
    # Default behaviour:- instance is saved(for modelforms) and redirects to success_url
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    # the fields of the model to build the ModelForm of the CreateView and UpdateView
    fields = ('subject', 'title', 'slug', 'overview')
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    pass


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    pass


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
