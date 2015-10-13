media-subscriptions
===================

.. |date| date::

:subtitle: Download subscriptions from YouTube
:author: Jaime Marquínez Ferrándiz
:date: |date|
:version: 0.0
:copyright: Public Domain
:manual section: 1
:manual group: multimedia

Synopsis
--------

.. code::

    media-subscriptions

Description
-----------

``media-subscriptions`` is a program that downloads the most recent videos from a YouTube user.
Its purpose is to allow subscribing to a user content without having to use a YouTube account.
For downloading the videos it uses ``youtube-dl`` (https://github.com/rg3/youtube-dl), you can use the same options and configuration files.

Adding subscriptions
--------------------

The subscriptions are saved in ``~/.config/media-subscriptions/config``, it is a INI file (https://en.wikipedia.org/wiki/INI_file) where each subscription has its own section::

    [<identifier>]
    url = https://www.youtube.com/user/<user>

The *identifier* must be unique and is used as the folder for downloading the videos.

For example::

    [youtube]
    url = https://www.youtube.com/user/youtube

After adding this to the configuration file, you can run ``media-subscriptions`` and the new videos will be downloaded to ``~/Movies/subscriptions/youtube``.

In addition to ``url``, others keys are supported:

``extra-args``

    A string containing additional arguments used when calling ``youtube-dl``, see its manual for all the available options.
