
from django.forms import ModelForm
from django.utils.functional import update_wrapper
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import RedirectView, DetailView, ListView
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse

class ConfigurationError(Exception):
	pass

class ModelManager(object):
	def __init__(self, model, fieldname, manager_site):
		self.model = model
		self.opts = model._meta
		self.fieldname = fieldname
		self.field = model._meta.get_field(fieldname)
		self.manager_site = manager_site
		self.create_views()
		
	def get_image_url(self, image_instance):
		return getattr(image_instance, self.image_fieldname).url
		
	def get_image_model(self):
		if hasattr(self, 'image_set_fieldname'):
			return getattr(self.model, self.image_set_fieldname).related.model
		elif hasattr(self, 'image_queryset'):
			return self.image_queryset.model
		elif hasattr(self, 'image_model'):
			return self.image_model
		else:
			raise ConfigurationError('no image model appears to be specified')
	
	def get_image_queryset(self, content_instance):
		if hasattr(self, 'image_set_fieldname'):
			return getattr(content_instance, self.image_set_fieldname).all()
		elif hasattr(self, 'image_queryset'):
			return self.image_queryset
		elif hasattr(self, 'image_model'):
			return self.image_model.objects.all()
		else:
			raise ConfigurationError('no image model appears to be specified')
	
	def add_image_to_set(self, content_instance, image_instance):
		""" this method ensures that an object appears in the queryset
		    returned from get_image_queryset()
		    
		    if a custom queryset is specified, this method must also be overriden
		"""
		if hasattr(self, 'image_set_fieldname'):
			return getattr(content_instance, self.image_set_fieldname).add(image_instance)
		elif hasattr(self, 'image_queryset'):
			raise RuntimeError("if a custom queryset is specified, add_image_to_set must be overridden")
	
	def get_urls(self):

		def wrap(view):
			def wrapper(*args, **kwargs):
				return self.manager_site.manager_view(view)(*args, **kwargs)
			return update_wrapper(wrapper, view)
	
		info = (self.model._meta.app_label,
			self.model._meta.module_name,
			self.fieldname
		)
		
		urlpatterns = patterns('',
			url(r'^(?P<object_pk>.+)/%s/images/add/$'%self.fieldname,
				wrap(self.image_add_view),
				name='%s_%s_%s_image_new' % info),
			url(r'^(?P<object_pk>.+)/%s/images/(?P<pk>.+)/edit/$'%self.fieldname,
				wrap(self.image_edit_view),
				name='%s_%s_%s_image_edit' % info),
			url(r'^(?P<object_pk>.+)/%s/images/(?P<pk>.+)/delete/$'%self.fieldname,
				wrap(self.image_delete_view),
				name='%s_%s_%s_image_delete' % info),
			url(r'^(?P<object_pk>.+)/%s/images/(?P<pk>.+)/url/$'%self.fieldname,
				wrap(self.image_url_view),
				name='%s_%s_%s_image_redirect' % info),
			#url(r'^(?P<object_pk>.+)/%s/images/(?P<pk>.+)/$'%self.fieldname,
			#	wrap(self.image_detail_view),
			#	name='%s_%s_%s_image_detail' % info),
			url(r'^(?P<object_pk>.+)/%s/images/$'%self.fieldname,
				wrap(self.image_list_view),
				name='%s_%s_%s_image_list' % info),
		)
		print urlpatterns[-1]
		return urlpatterns

	def urls(self):
		return self.get_urls()
	urls = property(urls)
	
	def create_views(self):
		
		class ImageForm(ModelForm):
			class Meta:
				model = self.get_image_model()
				if hasattr(self, 'image_set_fieldname'):
					exclude = (
						getattr(self.model, self.image_set_fieldname).related.field.name,
					)
					print exclude
						
		info = (self.model._meta.app_label,
			self.model._meta.module_name,
			self.fieldname
		)
		success_view_name = 'ckeditor_filemodel_manager:%s_%s_%s_image_list' % info
		#print reverse(success_view_name, kwargs={'object_pk': 1})
		 
		class ManagerViewMixin(object):
			success_url = '%d/%s/images/(?P<pk>.+)/'# % self.object.pk
			def get_success_url(self):
				object_pk = self.kwargs['object_pk']
				#TODO this should use the current_app kwarg
				return reverse(success_view_name,
					kwargs={'object_pk': object_pk}
				)
			def get_content_object(inner_self):
				if not hasattr(inner_self, 'content_object'):
					pk = inner_self.kwargs['object_pk']
					inner_self.content_object = get_object_or_404(self.model, pk=pk)
				return inner_self.content_object
				
			def get_queryset(inner_self):
				return self.get_image_queryset(inner_self.get_content_object())
			
			def get_context_data(inner_self, **kwargs):
				#TODO #FIXME ATCHUNG!! Super ugly hack ahead...
				# this is to avoid an infinite loop from calling
				# super(...).get_context()
				# we want to go further up the class hierarchy for this function 
				bases = type(inner_self).__bases__
				base = [b for b in bases if ManagerViewMixin not in b.mro()][0]
				print base
				context = base.get_context_data(inner_self, **kwargs)
				if 'object_list' in context:
					context['url_list'] = [self.get_image_url(o) for o in context['object_list']]
				return context
		
		class ImageCreateView(ManagerViewMixin, CreateView):
			template_name = 'ckeditor_filemodel_manager/image_add.html'
			form_class = ImageForm
			def form_valid(inner_self, form):
				image_instance = form.instance
				content_instance = inner_self.get_content_object()
				self.add_image_to_set(content_instance, image_instance)
				return super(ImageCreateView, inner_self).form_valid(form) 
		
		class ImageUpdateView(ManagerViewMixin, UpdateView):
			template_name = 'ckeditor_filemodel_manager/image_edit.html'
			form_class = ImageForm
		
		class ImageDeleteView(DeleteView):
			template_name = 'ckeditor_filemodel_manager/image_delete.html'
		
		class ImageDetailView(ManagerViewMixin, DetailView):
			template_name = 'ckeditor_filemodel_manager/image_detail.html'
		
		class ImageListView(ManagerViewMixin, ListView):
			template_name = 'ckeditor_filemodel_manager/image_list.html'
		
		add_decorator = user_passes_test(self.user_can_add)
		edit_decorator = user_passes_test(self.user_can_edit)
		delete_decorator = user_passes_test(self.user_can_delete)
		view_decorator = user_passes_test(self.user_can_view)
		
		self.image_add_view = add_decorator(ImageCreateView.as_view())
		self.image_edit_view = edit_decorator(ImageUpdateView.as_view())
		self.image_delete_view = delete_decorator(ImageDeleteView.as_view())
		self.image_detail_view = view_decorator(ImageDetailView.as_view())
		self.image_list_view = view_decorator(ImageListView.as_view())
		
		class ImageRedirectView(RedirectView):
			permanent=False
			def get_redirect_url(inner_self, **kwargs):
				object = get_object_or_404(self.model, pk=kwargs['object_pk'])
				queryset = self.get_image_queryset(object)
				image_object = get_object_or_404(queryset, pk=kwargs['pk'])
				return self.get_image_url(image_object)
		
		self.image_url_view = ImageRedirectView.as_view()
	
	# permission related properties
	
	public_can_view = True
	public_can_browse = False
	public_can_edit = False
	all_users_can_edit = False
	public_can_delete = False
	all_users_can_delete = False
	public_can_add = False
	all_users_can_add = False
	
	def user_can_view(self, user):
		return self.public_can_view or user.is_authenticated()
	def user_can_browse(self, user):
		return self.public_can_view or user.is_authenticated()
	def user_can_edit(self, user):
		perm = '%s.change_%s'%(self.model._meta.app_label, self.model._meta.module_name)
		return self.public_can_edit or self.all_users_can_edit or user.has_perm(perm)
	def user_can_delete(self, user):
		perm = '%s.delete_%s'%(self.model._meta.app_label, self.model._meta.module_name)
		return self.public_can_delete or self.all_users_can_edit or user.has_perm(perm)
	def user_can_add(self, user):
		perm = '%s.add_%s'%(self.model._meta.app_label, self.model._meta.module_name)
		return self.public_can_add or self.all_users_can_edit or user.has_perm(perm)
	
	
	
	
