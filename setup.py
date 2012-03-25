#!/usr/bin/env python
"""
django-linked-choice-field
==========================

A ModelChoiceField that can span a relation between two models.

:copyright: (c) 2012 by the Linovia, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    # 'nose==1.1.2',
]

install_requires = [
    'django>=1.3.1',
]

setup(
    name='django-linked-choice-field',
    version='0.1.0',
    author='Xavier Ordoquy',
    author_email='xordoquy@linovia.com',
    url='http://github.com/linovia/django-linked-choice-field',
    description='A ModelChoiceField that restricts its content \
according to a foreign key contraint.',
    long_description=__doc__,
    license='BSD',
    packages=find_packages(exclude=['demo']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
