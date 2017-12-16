from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic.list import ListView
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView


from .models import Course, Module, Content
from .forms import ModuleFormSet


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


class OwnerCourseEditMixin(LoginRequiredMixin, OwnerCourseMixin, OwnerEditMixin):
    # the fields of the model to build the ModelForm of the CreateView and UpdateView
    fields = ('subject', 'title', 'slug', 'overview')
    success_url = reverse_lazy('course:manage_course_list')
    template_name = 'courses/manage/course/form.html'


class CourseCreateView(PermissionRequiredMixin, OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(PermissionRequiredMixin, OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(PermissionRequiredMixin, OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('course:manage_course_list')
    permission_required = 'courses.delete_course'


class CourseModuleUpdateView(View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    # Before being assigned to get or post or other methods, the dispatch method is called
    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super(CourseModuleUpdateView, self).dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return render(request, self.template_name, {'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('course:manage_course_list')
        return render(request, self.template_name, {'course': self.course, 'formset': formset})


class ContentCreateUpdateView(View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ('text', 'video', 'image', 'file'):
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        # To dynamically build forms
        Form = modelform_factory(model, exclude=('owner', 'order', 'created', 'updated'))
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        # if id is None, then it is a new object, otherwise it is an existing object
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        self.model = self.get_model(model_name)

        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)

        return super(ContentCreateUpdateView, self).dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)

        return render(request, self.template_name, {'form': form,
                                                    'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()

            if not id:
                # new object
                Content.objects.create(module=self.module, item=obj)

            return redirect('course:module_content_list', self.module.id)

        return render(request, self.template_name, {'form': form,
                                                    'object': self.obj})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('course:module_content_list', module.id)


class ModuleContentListView(View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)

        return render(request, self.template_name, {'module': module})