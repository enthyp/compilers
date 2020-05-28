ROOT_DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
TEST_DIR := $(ROOT_DIR)/tests

.PHONY: all
all: test

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	pytest -s --log-cli-level=1 $(TEST_DIR)

.PHONY: tar_tc
tar_tc:
	tar --exclude=tc/__pycache__ --exclude=tc/optimization/__pycache__ --exclude=examples/out --exclude=examples/optimizations/out --exclude=tc.egg-info --exclude=tc/parsetab.py -czvf jakub_lanecki_5.tar.gz tc/*

