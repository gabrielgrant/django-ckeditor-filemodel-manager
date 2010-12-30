import os.path

from django.template import TemplateDoesNotExist
from django.conf import settings
from django.test import TestCase
from django.core.files import File

from view_tests.models import NewsStory, NewsImage
import ckeditor_filemodel_manager as manager

test_data = os.path.dirname(__file__) + '/data/'
test_image = test_data + 'image.jpg'

class InstanceTest(TestCase):
	urls = 'view_tests.urls'
	def setUp(self):
		self.site = manager.ManagerSite()
		self.site.register(
			NewsStory, 'body', image_model=NewsImage, image_fieldname='image'
		)
		self.story = NewsStory(headline="Gabriel wins!")
		self.story.save()
		self.image = NewsImage(story=self.story, image=File(open(test_image)))
		self.image.save()
	def test_image_redirect(self):
		settings.DEBUG = True
		url = '/manager/view_tests/newsstory/%d/body/images/%d/url/'%(self.story.pk, self.image.pk)
		
		try:
			response = self.client.get(url)
		except TemplateDoesNotExist, e:
			print e
			print e.args
			raise
		show_debug(response)
		self.assertEqual(response.status_code, 302)
	
	def test_image_new_view(self):
		url = '/manager/view_tests/newsstory/%d/body/images/new/'%self.story.pk
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		
		def test_image_edit_view(self):
			url = '/manager/view_tests/newsstory/%d/body/images/%d/edit/'%(self.story.pk, self.image.pk)
			response = self.client.get(url)
			print '\n\n\n', response.items(), '\n\n\n'
			self.assertEqual(response.status_code, 200)
		
		def test_image_delete_view(self):
			url = '/manager/view_tests/newsstory/%d/body/images/%d/delete/'%(self.story.pk, self.image.pk)
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)
		
		def test_image_detail_view(self):
			url = '/manager/view_tests/newsstory/%d/body/images/%d/'%(self.story.pk, self.image.pk)
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)
		
		def test_image_list_view(self):
			url = '/manager/view_tests/newsstory/%d/body/images/'%self.story.pk
			response = self.client.get(url)
			self.assertEqual(response.status_code, 200)


def show_debug(response):
	if response.status_code == 404:
		# get better debug output
		for pattern in response.context['urlpatterns']:
			print ' '.join(pat.regex.pattern for pat in pattern)
				
		for k in [
		'root_urlconf',
		'request_path',
		'reason',
		'request',
		'settings']:
			print '\n\n' + k + ':', response.context[k], '\n\n'
	
