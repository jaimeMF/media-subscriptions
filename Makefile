PYTHON ?= python3

RST_OPTIONS = --strict

.PHONY: all clean dist sdist wheel

HTML_DOCS = media-subscriptions.html README.html
MANPAGES = media-subscriptions.1
DOCS = $(MANPAGES) $(HTML_DOCS)
DISTFILES = $(DOCS)

all: $(DOCS)

dist: sdist wheel

sdist: $(DISTFILES)
	$(PYTHON) setup.py sdist

wheel: $(DISTFILES)
	$(PYTHON) setup.py bdist_wheel

clean:
	rm -rf $(DOCS) build dist ./*.egg-info

.SUFFIXES: .rst .html .1

.rst.1:
	rst2man.py $(RST_OPTIONS) $< $@

.rst.html:
	rst2html.py $(RST_OPTIONS) $< | sed 's:\.rst:\.html:g' > $@
