media-subscriptions
===================

``media-subscriptions`` is command line program for downloading the most recent videos from a YouTube user.
You just add two lines to ``~/.config/media-subscriptions/config``:

.. code:: ini

    [youtube]
    url = https://www.youtube.com/user/youtube

and when you run ``media-subscriptions`` the new videos will be downloaded (with `youtube-dl <https://github.com/rg3/youtube-dl>`_) to ``~/Movies/subscriptions/youtube``.

For more information read the `manual <media-subscriptions.rst>`_.

Install
-------

From the source code directory run:

.. code:: sh

    $ pip install -e .
