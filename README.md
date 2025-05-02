# Codestellation

## Relevant artifacts
- **MetaGPT** fork: [link](https://github.com/jbcallv/MetaGPT)
- **Annotated Benchmark** [link](https://docs.google.com/spreadsheets/d/1-W4i4gqte2xnymOzFlpLCcfcrabHlaETNj8ARoT_nAI/edit?usp=sharing)

## Overview

CodeStellation is a novel multi-agent Large Language Model (LLM) framework designed for automatically generating comprehensive documentation for large-scale source code projects. Unlike existing code summarization approaches that focus primarily on method-level documentation, CodeStellation effectively handles higher-order code components such as classes and files by using collaborative LLM agents to tackle the complexities of larger code structures.

This project is built on our [forked version of MetaGPT](https://github.com/jbcallv/MetaGPT), which has been modified to support local LLM deployment.

## Key Features

- **Multi-Agent Architecture**: Employs specialized agents that collaborate to generate high-quality code summaries
- **Higher-Order Component Support**: Effectively summarizes classes and entire files, not just methods
- **Structural Awareness**: Maintains contextual understanding of project dependencies and relationships
- **Semantic Search Integration**: Stores generated summaries in vector databases for efficient retrieval
- **Language Support**: Currently works with Java and Python projects

## How It Works

CodeStellation uses a sequential pipeline architecture with five specialized agents:

1. **Project Splitter Agent**: Identifies and collects relevant code files within the target project
2. **Dependency Graph Builder Agent**: Constructs a representation of project dependencies and determines optimal processing order
3. **Chunk Summarizer Agent**: Processes individual files using a sliding window approach to accommodate LLM context limitations
4. **Chunk Summary Combiner Agent**: Consolidates lower-level summaries while preserving critical details
5. **File Level Summarizer Agent**: Produces comprehensive summaries for each code file by integrating dependency summaries, method definitions, and combined chunk summaries

## Getting Started

### Prerequisites

- Python 3.11
- MetaGPT framework locally cloned [(our forked version with modifications)](https://github.com/jbcallv/MetaGPT)
- Local LLM support or API access
- Pinecone account (for vector database storage)

### Installation

```bash
# Clone the repository
git clone https://github.com/jbcallv/codestallation.git
cd codestallation

# Install dependencies
pip install -r deps/requirements.txt
pip install -e <path to metagpt>
```

### Configuration

1. Download an open-source LLM or create an API key.
2. In `model_configuration.py` you can view examples of how to configure the model.
3. Adjust `main.py` to select model of your choice.
4. Create an .env file with these keys:
```
ANTHROPIC_API_KEY
PINECONE_API_KEY
```

### Usage

```bash
# Analyze a local project
python main.py <path to project> --pinecone-index=<pinecone namespace> --file-extensions={java | py}
```

## Evaluation Results
CodeStellation has been evaluated on diverse, large-scale open-source Java and Python projects including Apache Ant and Pandas. Our evaluation taxonomy classifies summaries as:

- **Very Good (4)**: Captures all key functionality, API usage patterns, and exceptional conditions
- **Good (3)**: Captures the core purpose and most key implementation aspects, including some API usage patterns or exceptional conditions, but lacks full coverage or depth
- **Adequate (2)**: Captures core purpose, misses significant implementation aspects
- **Poor (1)**: Misrepresents functionality or contains major factual errors


## Contributions

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use CodeStellation in your research, please cite our paper:

```
TBD
```
