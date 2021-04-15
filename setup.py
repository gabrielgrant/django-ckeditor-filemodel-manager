from setuptools import setup

setup(
    name='django-ckeditor-filemodel-manager',
    version='0.1.3dev',
    packages=['ckeditor_filemodel_manager',],
    include_package_data=True,
    author='Gabriel Grant',
    author_email='g@briel.ca',
    license='LGPL',
    long_description=open('README').read(),
    url='http://github.org/gabrielgrant/django-ckeditor-filemodel-manager/',
    install_requires=[
        'pillow',
        'django-ckeditor>=0.9.4',
    ],
    dependency_links = [
        'http://github.com/gabrielgrant/django-ckeditor/tarball/master#egg=django-ckeditor-0.9.4',
    ]
)

