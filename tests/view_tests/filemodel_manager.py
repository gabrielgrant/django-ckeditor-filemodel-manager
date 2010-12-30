import ckeditor_filemodel_manager as manager

from view_tests.models import NewsStory, NewsImage

class NewsStoryManager(manager.ModelManager):
	image_queryset = NewsImage.objects.filter(public=True)
	image_fieldname = 'image'

class NewsStoryManager(manager.ModelManager):
	def get_image_queryset(self, story_instance):
		return story_instance.images.all()
	image_fieldname = 'image'

class NewsStoryManager(manager.ModelManager):
	image_set_fieldname = 'images'
	image_fieldname = 'image'

manager.site.register(NewsStory, 'body', NewsStoryManager, use_ckeditor_formfield=True)
#)
