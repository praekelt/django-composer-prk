Django Composer
=============
**Build Pages by composing listings and individual content**

.. image:: https://travis-ci.org/praekelt/django-composer-prk.svg?branch=develop
    :target: https://travis-ci.org/praekelt/django-composer-prk

.. image:: https://coveralls.io/repos/github/praekelt/django-composer-prk/badge.svg?branch=develop
    :target: https://coveralls.io/github/praekelt/django-composer-prk?branch=develop

.. contents:: Contents
    :depth: 5

Quick start
-----------

``django-composer-prk`` is intended to be a standalone library, not a project, but it can indeed be run with::

    - virtualenv ve
    - ./ve/bin/pip install -r composer/tests/requirements/19.txt
    - ./ve/bin/python manage.py migrate --run-syncdb --settings=composer.tests.settings.19
    - ./ve/bin/python manage.py runserver 0.0.0.0:8000 --settings=composer.tests.settings.19


Installation
------------

#. Install the contents of ``composer/tests/requirements/19.txt`` to your Python environment.

#. Add ``composer`` to the ``INSTALLED_APPS`` setting.

#. Add ``composer.middleware.ComposerFallbackMiddleware`` to the middleware setting. This will **REPLACE** the flatpages 404 middleware, so remove that if needed.

#. Add ``composer.context_processors.slots`` to the context processors setting.

#. Add the following to your urls.py::

   url(r"^nested_admin/", include("nested_admin.urls"))

Content types
-------------

Slot:

* url: The URL or URL pattern where the slot should appear. This may be a regular expression.

* slot_name: In your project, the slot names are defined in ``templates/base.html``. This field provides options that are automatically generated from the composer slots found in that base template.

Row:

* Each row is nested within a slot (ordered).

* The row can have extra CSS classes.

Column:

* Each column is nested within a row (ordered).

* width: A row is 12 columns wide, so columns can be fitted next to each other.

* title: rendered at the top of a column. Can be blank.

* class_name: Extra CSS classes that can be added to the column wrapping div.

Tile:

* Each tile is nested within a column (ordered).

* The tile target is a generic foreign key, so it can reference any content type.

* The view name can be any filesystem view. Either a target or view must be specified. View name takes precendence if both are set.

* style: The style is used to look up a suitable template for rendering the target. An example is ``templates/myapp/inclusion_tags/mymodel_tile.html``.

* class_name: The extra classes to add to the tile.

Usage
-----

The base template usually defines some composer slots. Typically this would be a header slot, content slot and footer slot. This can be extended easily by adding slots to the ``templates/base.html`` template. Example of adding a sidebar slot: ::

    {% if composer_slots %}{% load composer_tags %}{% endif %}

    {% if composer_slots.sidebar %}
        <div id="sidebar">
            {% composer sidebar %}
        </div>
    {% endif %}

On any URL on the site, if an appropriate slot exists that matches the URL and slot name, that slot will be rendered on the page. The current matching logic works as follows:

#. Find the slot with the best possible match for the current URL. Slot URL's are treated as regular expressions so one slot can match many URL's.

The content slot is special:

#. If the template being rendered fills the content block then it trumps any slot that may try to fill the content block.

Target rendering
----------------

``django-composer-prk`` tries to render in order:

* ``templates/{{ app_label }}/inclusion_tags/{{ model_name }}_{{ tile_style }}.html``

* ``templates/{{ app_label }}/inclusion_tags/{{ tile_style }}.html``

* The view returned by ``get_absolute_url`` if it exists. It will extract HTML within any ``<div id="content">`` tag.

