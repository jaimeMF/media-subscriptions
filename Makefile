PYTHON ?= python3

RST_OPTIONS = --strict

.PHONY: all clean dist sdist wheel

HTML_DOCS = media-subscriptions.html README.html
MANPAGES = media-subscriptions.1
DOCS = $(MANPAGES) $(HTML_DOCS)
DISTFILES = $(DOCS) media-subscriptions.fish

all: $(DISTFILES)

dist: sdist wheel

sdist: $(DISTFILES)
	$(PYTHON) setup.py sdist

wheel: $(DISTFILES)
	$(PYTHON) setup.py bdist_wheel

clean:
	rm -rf $(DISTFILES) build dist ./*.egg-info

.SUFFIXES: .rst .html .1

.rst.1:
	rst2man.py $(RST_OPTIONS) $< $@

.rst.html:
	rst2html.py $(RST_OPTIONS) $< | sed 's:\.rst:\.html:g' > $@

VENV = VENV_BUILD/bin/activate
VENV_ACTIVATE = source $(VENV)

$(VENV):
	virtualenv -p $(PYTHON) $$(dirname $$(dirname $@))
	$(VENV_ACTIVATE); pip install -e .

media-subscriptions.fish: devscripts/fish_completion.py media_subscriptions.py $(VENV)
	$(VENV_ACTIVATE); python devscripts/fish_completion.py $@
