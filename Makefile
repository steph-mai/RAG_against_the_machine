PYTHON = uv run python
ARGS ?= index

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: help install run debug clean lint lint-strict test


install:
	@uv sync

run:
	@$(PYTHON) -m src $(ARGS)

debug:
	@$(PYTHON) -m pdb -m src $(ARGS)

clean:
	@echo "Removing temporary files and caches..."
	@rm -rf .mypy_cache .pytest_cache .uv_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -delete
	@echo "Cleaning complete."

fclean: clean
	@echo "Removing generated data (processed index and outputs)..."
	@rm -rf data/chroma data/processed data/output
	@echo "Full cleaning complete."

lint:
	@echo "--- Running Flake8 ---"
	@uv run flake8 src/ --exclude .venv,vllm-0.10.1,moulinette
	@echo "--- Running MyPy ---"
	@uv run mypy src/ $(MYPY_FLAGS)

lint-strict:
	@echo "--- Running Flake8 ---"
	@uv run flake8 src/ --exclude .venv,vllm-0.10.1,moulinette
	@echo "--- Running MyPy ---"
	@uv run mypy src/ --strict
