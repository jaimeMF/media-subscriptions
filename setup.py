# coding: utf-8

from setuptools import setup

setup(
    name='media-subscriptions',
    version='0.0',
    description='',  # TODO
    long_description='',  # TODO
    author='Jaime Marquínez Ferrándiz',
    author_email='jaime.marquinez.ferrandiz@gmail.com',
    url='',  # TODO
    py_modules=['media_subscriptions'],
    entry_points={
        'console_scripts': [
            'media-subscriptions = media_subscriptions:main',
        ],
    },
    data_files=[
        ('share/man/man1', ['media-subscriptions.1']),
    ],
    install_requires=[
        'youtube_dl',
        'pyxdg',
    ],
    classifiers=[
        'Topic :: Multimedia :: Video',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: Public Domain',
        'Programming Language :: Python :: 3',
    ],
)
