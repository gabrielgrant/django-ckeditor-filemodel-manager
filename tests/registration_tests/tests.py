from django.test import TestCase

from registration_tests.models import NewsStory, NewsImage
import ckeditor_filemodel_manager as manager

class RegisterTest(TestCase):
	urls = 'registration_tests.urls'
	def setUp(self):
		self.site = manager.ManagerSite()
		
	def test_basic_registration(self):
		self.site.register(
			NewsStory, 'body', image_set_fieldname='images', image_fieldname='image'
		)
		self.assertTrue(
			isinstance(self.site._registry[NewsStory]['body'], manager.ModelManager)
		)
	def test_image_model_registration(self):
		self.site.register(
			NewsStory, 'body', image_model=NewsImage, image_fieldname='image'
		)
		self.assertTrue(
			isinstance(self.site._registry[NewsStory]['body'], manager.ModelManager)
		)
	def test_registration_with_model_manager(self):
		class NewsStoryManager(manager.ModelManager):
			image_model = NewsImage
			image_fieldname = 'image'

		self.site.register(NewsStory, 'body', NewsStoryManager)
		self.assertTrue(
			isinstance(self.site._registry[NewsStory]['body'], NewsStoryManager)
		)
	def test_prevent_double_registration(self):
		self.site.register(
			NewsStory, 'body', image_model=NewsImage, image_fieldname='image'
		)
		self.assertRaises(manager.sites.AlreadyRegistered, self.site.register,
			NewsStory, 'body', image_model=NewsImage, image_fieldname='image'
		)
		


