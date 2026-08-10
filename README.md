*This project has been created as part of the 42 curriculum by stmaire.*

<div align="center">
<br>
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQPzuYKu7n0cWUYa5Kbg0_LrlEQAIURWeo9A&s" alt="42 Logo" width="400" />
  <br>
</div>

# RAG Against The Machine
![Language](https://img.shields.io/badge/Language-python-blue)
![Static Badge](https://img.shields.io/badge/AI-green)
![Static Badge](https://img.shields.io/badge/parsing-green)
![Static Badge](https://img.shields.io/badge/LLM-green)
![Static Badge](https://img.shields.io/badge/Algorithms_&_IA-pink)
![Static Badge](https://img.shields.io/badge/Object_oriented_programming-pink)
![Static Badge](https://img.shields.io/badge/DB_and_Data-pink)

## 🔵 Description

### ✳️ Goal
The objective of this project is to build a Retrieval-Augmented Generation system that answers questions about a codebase. The system is designed to ingest the provided vLLM repository, retrieve the most relevant snippets for a given question, generate a grounded answer using the Qwen/Qwen3-0.6B model, and measure the retrieval quality using the recall@k metric.

### ✳️ Overview
Language models only know what they were trained on, and retraining them to add knowledge is slow and costly. Instead of putting knowledge directly into the model, this system allows it to pull information from an external source at answer time.

The RAG pipeline functions through four main stages:
 - Indexing: The data is organised so it can be searched.
 - Retrieving: A question is matched against the index to pull the most relevant snippets.
 - Augmenting: Those snippets are filtered and placed into the model's context window.
 - Generating: The context is read to produce the answer.

## 🔵 Instructions

### ✳️ Prerequisites
*   Python 3.10 or later.
*   The `uv` project and package manager.
*   Ollama installed and running locally with the `Qwen/Qwen3-0.6B` model pulled.
*   Sufficient free disk space for the deep-learning stack and model weights.

### ✳️ Installation
To install the project dependencies using `uv`, run the following command at the root of the repository:
```bash
make install
```

**1. Execution via Makefile**

You can run the CLI commands using the Makefile. By default, running `make run` triggers the `index` command.

To execute other commands, you can override the ARGS variable. For example:


```bash
make run ARGS="search --query 'How to configure the OpenAI server?' --k 5"
```

Note: You can use any of the commands and options listed in the Manual Execution section below by passing them to the ARGS variable.


**2. Manual Execution via uv**

Alternatively, you can interact directly with the Command-Line Interface (CLI) built with Python Fire. Every command is invoked through the Python module:

```bash
uv run python -m src <command> [options]
```

**Available CLI Commands:**

*Note: The file and directory paths in the command examples below are provided for illustration purposes and can be modified according to the location of your data.*


**index**: Ingest the raw data and build the processed index. Options include --max_chunk_size (defaults to 2000) and --with_embeddings for vector indexing (bonus).

```bash
uv run python -m src index --max_chunk_size 2000
```

**search**: Return the top-k sources for a single query. Requires --query and --k. Can be run with --hybrid to combine lexical and semantic search (bonus).
```bash
uv run python -m src search --query "How to configure the OpenAI server?" --k 5
```

**search_dataset**: Run search over a whole dataset and write a JSON file. Requires --dataset_path, --k, and --save_directory. Can be run with --hybrid.

```bash
uv run python -m src search_dataset \
  --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json \
  --k 10 \
  --save_directory data/output/search_results
```

**answer**: Answer a single query using the retrieved context. Requires --query and --k. Can be run with --hybrid.

```bash
uv run python -m src answer --query "What hardware platforms does vLLM support?" --k 5
```

**answer_dataset**: Generate answers for a dataset, producing a JSON file. Requires --student_search_results_path and --save_directory.

```bash
uv run python -m src answer_dataset \
  --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  --save_directory data/output/search_results_and_answer
```

**evaluate**: Report your own recall@k against a ground-truth dataset, for your own testing. Requires --student_search_results_path and --dataset_path.

```bash
uv run python -m src evaluate \
  --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json
```

**3. Code Quality & Linting**

In accordance with the 42 curriculum standards, the project adheres to strict coding rules using flake8 and mypy for PEP 8 compliance and type safety.

```bash
# Standard linting
make lint

# Strict type checking
make lint-strict
```

**4. Debugging**

Run with Python debugger (pdb):

```bash
make debug
```

**6. Cleanup**

Remove cache and temporary files:

```bash
make clean
```

To perform a full cleanup that also removes the generated index, the vector database, and the output files:

```bash
make fclean
```

## 🔵 System architecture
### ✳️ RAG Pipeline components



### ✳️ Interactions between components


## 🔵 Chunking strategy


## 🔵 Retrieval method


## 🔵 Performance analysis



## 🔵 Design decisions

## 🔵 Challenges faced




## 🔵 Example usage


## 🔵 Resources

### ✳️ References


### ✳️ AI Usage
