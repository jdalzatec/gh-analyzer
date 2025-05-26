# GitHub Repository Analyzer

A tool to analyze GitHub repositories and extract useful information.

## Project Structure

```
app/
├── main.py           # Main application entry point
├── consumers/        # Consumer modules
│   └── manager.py    # ConsumerManager implementation
├── fetchers/         # Data fetching modules
│   └── github.py     # GitHub API fetcher
├── models/           # Data models
│   └── repo.py       # Repository data models
└── processors/       # Data processing modules
    └── repo_data.py  # Repository data processors
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd gh-analyzer

# Install dependencies
pip install -r requirements.txt


## Usage

```bash
# Run from the project root with Python path set
python main.py
```