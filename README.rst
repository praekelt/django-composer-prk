Django Composer
=============
**Build Pages by composing listings and individual content**

.. image:: https://travis-ci.org/praekelt/django-composer-prk.svg?branch=develop
    :target: https://travis-ci.org/praekelt/django-composer-prk

.. image:: https://coveralls.io/repos/github/praekelt/django-composer-prk/badge.svg?branch=develop
    :target: https://coveralls.io/github/praekelt/django-composer-prk?branch=develop

.. contents:: Contents
    :depth: 5

Installation
------------

#. Install or add ``django-composer-prk`` to your pip requirements.

#. Add ``composer`` to your ``INSTALLED_APPS`` setting.

#. Temporary: Add ``django-nested-admin==3.0.12`` to your pip requirements.

#. Temporary: Add ``nested_admin`` to your ``INSTALLED_APPS``

#. Add ``composer.middleware.ComposerFallbackMiddleware`` to your middleware setting. This will **REPLACE** the flatpages 404 middleware, so remove that if needed.

#. Add ``composer.context_processors.slots`` to your context processors setting.

#. Add the following to your urls.py: ::

   url(r"^nested_admin/", include("nested_admin.urls")),
   url(r"^contentblocks/", include("contentblocks.urls", namespace="contentblocks")),

Content types
-------------

Slot:

* url: The url where the slot should appear. This follows the same rules as flatpages: start and end with a slash. the url ``/`` has special meaning, which will be detailed in the usage section.

* slot_name: In your project, the slot names are defined in ``templates/base.html``. This field provides options that are automatically generated from the composer slots found in that base template.

Row:

* Each row is nested within a slot (ordered)

* The row can have extra CSS classes

Column:

* Each column is nested within a row (ordered)

* width: A row is 12 columns wide, so columns can be fitted next to each other. 

* title: rendered at the top of a column. Can be blank.

* class_name: Extra CSS classes that can be added to the column wrapping div.

Tile:

* Each tile is nested within a column. (ordered)

* The tile target is a generic foreign key, so it can reference any content type.

* The view name can be any filesystem view. Either a target or view must be specified.

* style: The template to use for the listing or object.

* class_name: The extra classes to add to the tile

Usage
-----

The base template usually defines some composer slots. Typically this would be a header slot, content slot and footer slot. This can be extended easily by adding slots to the ``templates/base.html`` template. Example of adding a sidebar slot: ::

    {% if composer_slots %}{% load composer_tags %}{% endif %}

    {% if composer_slots.sidebar %}
        <div id="sidebar">
            {% composer sidebar %}
        </div>
    {% endif %}

On any url on the site, if an appropriate slot exists that matches the url and slot name, that slot will be rendered on the page. The current matching logic works as follows:

#. If there is a slot with an url matching the exact current url and a slot name matching the slot on the page, it will be rendered.

#. If there is a slot with the url ``/`` and a slot name matching the slot on the page, it will be rendered. 

The content slot is special:

#. Current content overrides the ``content`` slot: Any object that fills the ``content`` block will be rendered in the content block. This includes any modelbase object that will normally be rendered at that url.

#. A slot with a slot name of ``content`` and an url of ``/`` will serve as the content for the home page of the site. However, it will **NOT** be rendered on any other page, allowing a fallback to flatpages and the normal 404 page.
