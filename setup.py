#!/usr/bin/env python
from setuptools import setup

from whistle import VERSION

setup(
    name='django-whistle',
    version=VERSION,
    description='Advanced notifications for Django',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author='Pragmatic Mates',
    author_email='info@pragmaticmates.com',
    maintainer='Pragmatic Mates',
    maintainer_email='info@pragmaticmates.com',
    url='https://github.com/PragmaticMates/django-whistle',
    packages=[
        'whistle',
        'whistle.migrations'
    ],
    include_package_data=True,
    install_requires=('django', 'django_rq', 'django-crispy-forms', 'django-pragmatic>=4.1.0'),
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 5 - Production/Stable'
    ],
    license='BSD License',
    keywords="django notifications events push email iOS Android APN FireBase GCM",
)
