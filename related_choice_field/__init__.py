"""
related_choice_field
===========================

A ModelChoiceField that can span a relation between two models.

:copyright: (c) 2012 by the Linovia, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('django-related-choice-field').version
except Exception as e:
    VERSION = 'unknown'
