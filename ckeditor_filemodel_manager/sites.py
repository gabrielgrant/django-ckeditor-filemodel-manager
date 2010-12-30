
from django.utils.functional import update_wrapper
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django import forms  # for monkey patching
from django.core.urlresolvers import reverse


from ckeditor_filemodel_manager.options import ModelManager

CKEDITOR_PRESENT = 'ckeditor' in getattr(settings, 'INSTALLED_APPS', [])
if CKEDITOR_PRESENT:
	import ckeditor.widgets

class AlreadyRegistered(Exception):
	pass

class ManagerSite(object):
	"""
	A ManagerSite object encapsulates an instance of the CKEditor
	imagemodel manager, ready to be hooked into your URLconf. Models
	are registered with the ManagerSite using the register() method,
	and the get_urls() method can then be used to access Django view
	functions that present the manager interface for the collection
	of registered models.
	"""
	
	def __init__(self, name=None, app_name='ckeditor_filemodel_manager'):
		self._registry = {}  # model_class -> fieldname -> manager_class instance
		self.root_path = None
		if name is None:
			self.name = 'ckeditor_filemodel_manager'
		else:
			self.name = name
		self.app_name = app_name

	def register(self, model, fieldname, manager_class=None, **options):
		"""
		Registers the given manager class.

		If a manager class isn't given, it will use ImageManager (the
		default manager options). If keyword arguments are given 
		they'll be applied as options to the manager class.

		If a field is already registered, this will raise AlreadyRegistered.
		"""
		if not manager_class:
			manager_class = ModelManager
			
		if model in self._registry and fieldname in self._registry[model]:
			raise AlreadyRegistered(
				'The field %s on model %s is already registered' % (
					fieldname, model.__name__
				)
			)
		
		# If we got **options then dynamically construct a subclass of
		# manager_class with those **options.
		if options:
			# For reasons I don't quite understand, without a __module__
			# the created class appears to "live" in the wrong place,
			# which causes issues later on.
			options['__module__'] = __name__
			manager_class = type(
				"%s_%sManager" % (model.__name__, fieldname),
				(manager_class,), options
			)

		# Instantiate the manager class to save in the registry
		reg_dict = self._registry.setdefault(model, {})
		manager_instance = manager_class(model, fieldname, self)
		reg_dict[fieldname] = manager_instance
		
		# set the formfield, if requested, by wrapping the formfield() method
		if (
			CKEDITOR_PRESENT and
			getattr(manager_instance, 'use_ckeditor_formfield', False)
		):
			print "doin' the nasty"
			self.set_ckeditor_formfield(manager_instance)
		
	def set_ckeditor_formfield(self, manager):
		"""
		Sets the model field of the given manager to use a CKEditor
		with the appropriate filebrowser and imagebrowser url options
		
		Note: this only works properly for instances that have already
		been saved to the db, because an id is needed to attach image
		instances to. For unsaved instances, an error page will be displayed,
		informing the user that the text must be saved before files can be
		linked.
		
		Done with an ugly monkey-patch of forms.forms.BoundField.as_widget
		
		"""
		model = manager.model
		fieldname = manager.fieldname
		field = model._meta.get_field(fieldname)
		
		# files haven't been implemented yet, so there must be an image url for now
		#filebrowser_url = ''
		imagebrowser_url = ''
		
		old_as_widget = forms.forms.BoundField.as_widget
		def new_as_widget(self, widget=None, attrs=None, only_initial=False):
			"""
			Wraps BoundField.as_widget to update the CKEditor widget if the form is tied to an instance
			"""
			if not widget:
				widget = self.field.widget
			instance = getattr(self.form, 'instance', False)
			cond1 = isinstance(widget, ckeditor.widgets.CKEditor)
			cond2 = instance
			cond3 = type(instance) is model
			if cond1 and cond2 and cond3:
				info = (model._meta.app_label, model._meta.module_name, fieldname)
				url_pattern_name = 'ckeditor_filemodel_manager:%s_%s_%s_image_list'%info
				imagebrowser_url = reverse(url_pattern_name, kwargs={'object_pk':instance.pk})
				config = widget.get_ckeditor_config_dict()
				new_config = {
					#'filebrowserBrowseUrl':filebrowser_url,
					'filebrowserImageBrowseUrl': imagebrowser_url
				}
				new_config.update(config)
				widget.ckeditor_config = new_config
			return old_as_widget(self, widget, attrs, only_initial)
		
		forms.forms.BoundField.as_widget = new_as_widget
		"""
		class FileManagedCKEditor(ckeditor.widgets.CKEditor):
			def __init__(self, *args, **kwargs):
				self.ckeditor_config = kwargs.pop('ckeditor_config', 'default')
				super(FileManagedCKEditor, self).__init__(*args, **kwargs)
			def get_ckeditor_config(self):
				new_config = {
					'filebrowserBrowseUrl':filebrowser_url,
					'filebrowserImageBrowseUrl': imagebrowser_url
				}
				if hasattr(self.ckeditor_config, 'items'):
					old_config = self.ckeditor_config
				else:
					old_config = settings.CKEDITOR_CONFIGS[self.ckeditor_config]
				new_config.update(old_config)
				self.ckeditor_config = new_config
				return super(FileManagedCKEditor, self).get_ckeditor_config()

		class FileManagedAdminCKEditor(admin_widgets.AdminTextareaWidget, FileManagedCKEditor):
			pass
		
		old_formfield = field.formfield
		def new_formfield(self, **kwargs):
			defaults = { 'widget': FileManagedCKEditor(object_id=self.XX) }
			defaults.update(kwargs)

			if defaults['widget'] == admin_widgets.AdminTextareaWidget:
				defaults['widget'] = FileManagedAdminAdminCKEditor

			return old_formfield(**defaults)
		# bind the new method, as per Alex Martelli's comment:
		# http://stackoverflow.com/questions/1015307/python-bind-an-unbound-method/1015405#1015405

		field.formfield = new_formfield.__get__(field, type(Field))

		# alternate way of accomplishing practically the same thing
		# field.formfield = lambda **kwargs: new_formfield(field, **kwargs)
		"""
			
	def get_urls(self):
		from django.conf.urls.defaults import patterns, url, include

		def wrap(view, cacheable=False):
			def wrapper(*args, **kwargs):
				return self.admin_view(view, cacheable)(*args, **kwargs)
			return update_wrapper(wrapper, view)
		
		# Manager-site-wide views.
		urlpatterns = []

		# Add in each model's common and manager views.
		for model, reg_dict in self._registry.iteritems():
			info = model._meta.app_label, model._meta.module_name
			def fieldlist_view(*args, **kwargs):
				return self.modelfieldlist_view(model=model, *args, **kwargs)
			urlpatterns += patterns('',
				url(r'^%s/%s/$' % (info), wrap(fieldlist_view),
					name='%s_%s_fieldlist' % info
				),
			)
				
			for fieldname_dict, manager in reg_dict.iteritems():
				urlpatterns += patterns('',
					url(r'^%s/%s/' % info, include(manager.urls))
				)
		return urlpatterns
	
	def urls(self):
		""" return a (urlpatterns, app_name, name) tuple for namespaced urls """
		return self.get_urls(), self.app_name, self.name
	urls = property(urls)
	

	def has_permission(self, request):
		"""
		Returns True if the given HttpRequest has permission to view
		*at least one* page in the admin site.
		"""
		#return request.user.is_active and request.user.is_staff
		return True

	def check_dependencies(self):
		"""
		Check that all things needed to run the manager have been correctly installed.

		The default implementation checks that the admin app and the
		auth context processor are installed.
		"""
		from django.contrib.admin.models import LogEntry
		from django.contrib.contenttypes.models import ContentType
		
		# check for admin site
		if not ContentType._meta.installed:
			raise ImproperlyConfigured("Put 'django.contrib.admin' in "
				"your INSTALLED_APPS setting in order to use the manager application.")
		if not ('django.contrib.auth.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS or
			'django.core.context_processors.auth' in settings.TEMPLATE_CONTEXT_PROCESSORS):
			raise ImproperlyConfigured("Put 'django.contrib.auth.context_processors.auth' "
				"in your TEMPLATE_CONTEXT_PROCESSORS setting in order to use the manager application.")



	def manager_view(self, view, cacheable=False):
		"""
		Decorator to create an admin view attached to this ``ManagerSite``.
		This wraps the view and provides permission checking by calling
		``self.has_permission``.

		You'll want to use this from within ``ManagerSite.get_urls()``:

			class MyManagerSite(AdminSite):

				def get_urls(self):
					from django.conf.urls.defaults import patterns, url

					urls = super(MyManagerSite, self).get_urls()
					urls += patterns('',
						url(r'^my_view/$', self.manager_view(some_view))
					)
					return urls

		"""
		def inner(request, *args, **kwargs):
			if not self.has_permission(request):
				return self.login(request)
			return view(request, *args, **kwargs)
		# We add csrf_protect here so this function can be used as a utility
		# function for any view, without having to repeat 'csrf_protect'.
		if not getattr(view, 'csrf_exempt', False):
			inner = csrf_protect(inner)
		return update_wrapper(inner, view)


		
# This global object represents the default manager site, for the common case.
# You can instantiate ManagerSite in your own code to create a custom manager site.
site = ManagerSite()
