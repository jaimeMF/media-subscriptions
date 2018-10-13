import argparse
import concurrent.futures
import configparser
import datetime
import itertools
import json
import logging
import os
import shlex
import sqlite3
import threading
import unittest.mock

import youtube_dl
import youtube_dl.utils
import youtube_dl.extractor as ydl_ies
import xdg.BaseDirectory
import colorama
from colorama import Fore


APP_NAME = 'media-subscriptions'


class YoutubeDLError(Exception):
    def __init__(self, code):
        super().__init__('youtube-dl exited with code {}'.format(code))
        self.code = code


class SubscriptionDownloader(youtube_dl.YoutubeDL):
    def __init__(self, config):
        self.config = config
        logging.basicConfig(level=logging.DEBUG, format=Fore.GREEN + '[{threadName:^20}]' + Fore.RESET + ' {message}', style='{')
        self.logger = logging.getLogger(APP_NAME)
        self.db_filename = os.path.join(xdg.BaseDirectory.xdg_data_home, APP_NAME, 'media-subscriptions.db')
        self.localdata = threading.local()
        self.lasts_filename = os.path.join(os.path.dirname(self.db_filename), 'last.json')
        super().__init__({'logger': self.logger}, auto_init=False)

        self.add_info_extractor(ydl_ies.YoutubeUserIE())
        self.add_info_extractor(ydl_ies.YoutubeChannelIE())

    @property
    def db(self):
        if not hasattr(self.localdata, 'db'):
            db = self.localdata.db = sqlite3.connect(self.db_filename)
            if not db.execute('SELECT * FROM sqlite_master WHERE name="downloaded"').fetchall():
                with db:
                    db.execute('CREATE TABLE downloaded (subscription text, url text, date timestamp)')
                if os.path.exists(self.lasts_filename):
                    print('Migrating the json info to the sqlite database')
                    with open(self.lasts_filename, 'rt') as f:
                        info = json.load(f)
                    with db:
                        for name, url in info.items():
                            self.register_download(name, url)
                    os.rename(self.lasts_filename, self.lasts_filename + '.backup')
        else:
            db = self.localdata.db
        return db

    def process_ie_result(self, ie_result, download=True, extra_info={}):
        result_type = ie_result.get('_type', 'video')
        if result_type == 'playlist':
            return ie_result
        elif result_type == 'url':
            return super().process_ie_result(ie_result, download, extra_info)

    def extract_entries(self, name, config):
        threading.current_thread().name = name
        all_entries = self.extract_info(config['url'])['entries']
        last_download = self.db.execute('SELECT * FROM downloaded WHERE subscription=? LIMIT 1', (name,)).fetchone()
        if last_download is None:
            print('Last download from subscription "{}" not found, downloading only the most recent video'.format(name))
            entries = [next(all_entries)]
        else:
            entries = list(itertools.takewhile(lambda x: not self.is_downloaded(name, x['url']), all_entries))[::-1]
        return entries

    def download_subscriptions(self, names):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def fn(name):
                cfg = self.config[name]
                return name, cfg, self.extract_entries(name, cfg)
            futures = [executor.submit(fn, name) for name in names]
            for future in concurrent.futures.as_completed(futures):
                name, config, entries = future.result()
                print('Downloading {} videos from "{}"'.format(len(entries), name))
                for entry in entries:
                    self.download_entry(name, entry, config)

    def run_youtube_dl(self, args):
        # this is the only way to use the youtube-dl config file, if you
        # directly pass the args to youtube_dl.main it doesn't read it
        with unittest.mock.patch('sys.argv', ['youtube-dl'] + args):
            try:
                youtube_dl.main()
            except SystemExit as err:
                if err.code != 0:
                    raise YoutubeDLError(err.code)

    def download_entry(self, name, entry, config):
        args = []
        args.extend(['--output', os.path.join(config['download-folder'], name, youtube_dl.utils.DEFAULT_OUTTMPL)])
        extra_args = shlex.split(config['extra-args'])
        args.extend(extra_args)
        args.extend(['--', entry['url']])
        self.run_youtube_dl(args)
        self.register_download(name, entry['url'])

    def is_downloaded(self, name, url):
        res = self.db.execute('SELECT * FROM downloaded WHERE subscription=? AND url=?', (name, url))
        return res.fetchone() is not None

    def register_download(self, name, url):
        with self.db as db:
            db.execute('INSERT INTO downloaded VALUES (?, ?, ?)', (name, url, datetime.datetime.now()))

    def compact_db(self):
        print('Compacting database')
        with self.db as db:
            db.execute('VACUUM')

    def clean_db(self, names):
        N = 10
        deleted_entries = False
        with self.db as db:
            for name in names:
                if db.execute('SELECT count(*) from downloaded WHERE subscription=?', (name,)).fetchone()[0] > N:
                    to_delete = db.execute('SELECT url FROM downloaded WHERE subscription=? ORDER BY date', (name,)).fetchall()[:-N]
                    print('Deleting {} entries from "{}"'.format(len(to_delete), name))
                    db.executemany('DELETE FROM downloaded WHERE subscription=? AND url=?', [(name, url) for (url,) in to_delete])
                    deleted_entries = True

        if deleted_entries:
            self.compact_db()

    def delete(self, names):
        if names:
            with self.db as db:
                for name in names:
                    print('Deleting "{}"'.format(name))
                    db.execute('DELETE FROM downloaded WHERE subscription=?', (name,))
            self.compact_db()


def build_config():
    defaults = {
        'download-folder': os.path.expanduser('~/Movies/subscriptions'),
        'extra-args': '',
    }
    return configparser.ConfigParser(defaults=defaults)


def build_argparser():
    parser = argparse.ArgumentParser(APP_NAME)
    parser.add_argument('subscriptions', metavar='SUBSCRIPTION', nargs='*', help='Specify a subscription to download')
    parser.add_argument('--list-subs', help='Print the subscriptions', action='store_true')
    rm_group = parser.add_mutually_exclusive_group()
    rm_group.add_argument('--clean-db', help='Delete old entries from the downloads database', action='store_true')
    rm_group.add_argument('--delete', help='Delete subscription from the database', action='store_true')
    return parser


def main():
    colorama.init()

    parser = build_argparser()
    args = parser.parse_args()
    config_filename = os.path.join(xdg.BaseDirectory.load_first_config(APP_NAME), 'config')

    config = build_config()
    config.read(config_filename)
    dl = SubscriptionDownloader(config)
    subscriptions = (name for name in config if name != 'DEFAULT')

    if args.list_subs:
        for name in subscriptions:
            print(name)
        return

    if args.subscriptions:
        subscriptions = args.subscriptions

    if args.clean_db:
        dl.clean_db(subscriptions)
        return

    if args.delete:
        dl.delete(args.subscriptions)
        return

    dl.download_subscriptions(subscriptions)

if __name__ == '__main__':
    main()
