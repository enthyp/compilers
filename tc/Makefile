ROOT_DIR := $(dir $(abspath $(firstword $(MAKEFILE_LIST))))
TEST_DIR := $(ROOT_DIR)/tests
TEST_SET := $(if $(SET),$(TEST_DIR)/test_$(SET).py,$(TEST_DIR))

.PHONY: all
all: test

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	pytest -s --log-cli-level=1 $(TEST_SET)

.PHONY: tar_tc
tar_tc:
	tar --exclude=tc/__pycache__ --exclude=tc/optimization/__pycache__ --exclude=examples/out --exclude=examples/optimizations/out --exclude=tc.egg-info --exclude=tc/parsetab.py -czvf jakub_lanecki_5.tar.gz tc/*

