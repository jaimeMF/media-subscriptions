import shlex
import sys

from media_subscriptions import build_argparser, APP_NAME

parser = build_argparser()

commands = []

commands.append(['--exclusive', '--arguments', '({} --list-subs)'.format(APP_NAME)])

for a in parser._get_optional_actions():
    command = []
    for flag in a.option_strings:
        if flag.startswith('--'):
            command.extend(['--long-option', flag[2:]])
        elif flag.startswith('-'):
            command.extend(['--short-option', flag[1:]])
    if a.help:
        command.extend(['--description', a.help])
    commands.append(command)

commands = (' '.join(map(shlex.quote, c)) for c in commands)

res = '\n'.join('complete --command {} {}'.format(APP_NAME, c) for c in commands)
with open(sys.argv[1], 'wt') as f:
    f.write(res)
