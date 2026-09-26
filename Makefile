SHELL := /bin/bash

.PHONY: clean
clean:
	@echo Cleaning up builds and caches...
	@rm -rf {.mypy_cache,.ruff_cache}
	$(MAKE) -C python clean
