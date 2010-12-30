
# from http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/

from django.conf import settings
from django.core.management import call_command

def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    settings.configure(
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.admin',
            'django.contrib.sessions',
            'login',
            'ckeditor_filemodel_manager',
            'registration_tests',
            'view_tests',
        ),
        # Django replaces this, but it still wants it. *shrugs*
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        MEDIA_ROOT = '/tmp/ckeditor_filemodel_manager_test_media/',
        MEDIA_PATH = '/media/',
        ROOT_URLCONF = 'ckeditor_filemodel_manager.urls',
        DEBUG = True,
		TEMPLATE_DEBUG = True,
		#TEMPLATE_CONTEXT_PROCESSORS = (
		#	"django.core.context_processors.auth",
		#	"django.core.context_processors.debug",
		#	"django.core.context_processors.i18n",
		#	"django.core.context_processors.media",
		#	"django.core.context_processors.request",
		#),
    )
    
    # Fire off the tests
    call_command('test', 'registration_tests', 'view_tests')
    #call_command('test', 'registration_tests')
    

if __name__ == '__main__':
    main()

