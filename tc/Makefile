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
	tar --exclude=tc/__pycache__ --exclude=tests/__pycache__ --exclude=tc/optimization/__pycache__ --exclude=tests/out --exclude=tc.egg-info --exclude=tc/parsetab.py -czvf jakub_lanecki_6.tar.gz tc/* tests/* examples/*

.PHONY: zip_tc
zip_tc:
	zip -r jakub_lanecki_tc.zip tc examples tests Makefile requirements.txt setup.py -x "tests/.pytest_cache/*" "tests/__pycache__/*"  "tests/out/*" "tc/__pycache__/*" "tc/optimization/__pycache__/*" tc/parsetab.py
