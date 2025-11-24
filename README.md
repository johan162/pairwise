# Pairwise Ranking System

A Python application for ranking requirements based on Business Value and Technical Complexity using Active Bayesian Ranking. 
This system minimizes the number of manual comparisons needed to achieve a statistically significant ranking by using uncertainty sampling.
The resulting ranking is not perfect as such a ordering would requies O(nlgn)) comparisons

## Features

- **Active Bayesian Ranking**: Uses uncertainty sampling to minimize the number of comparisons needed.
- **Two Dimensions**: Rank tasks separately by Complexity and Value.
- **Visual Results**: Scatter plot and sorted tables.
- **Persistence**: Auto-saves progress.
- **Modern UI**: Dark themed web interface.

## Development Environment Setup

To set up the development environment locally:

1.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

2.  **Install dependencies**:
    Install the package in editable mode along with development and documentation dependencies:
    ```bash
    pip install -e ".[dev,docs]"
    ```

3.  **Run the application**:
    ```bash
    python run.py
    ```
    Access the application at `http://127.0.0.1:5000`.

4.  **Run Tests**:
    ```bash
    pytest
    ```

5.  **Build Documentation**:
    ```bash
    mkdocs serve
    ```

## Container Deployment (Podman)

The application is containerized and can be run using Podman (or Docker).

### Build the Container

To build the container image using Podman:

```bash
podman build -t pairwise .
```

### Run the Container

To run the container, you need to map port 5000 and mount the `data` directory to ensure persistence.

```bash
podman run -d \
  --name pairwise-app \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data:Z \
  pairwise
```

*Note: The `:Z` flag is often required on SELinux-enabled systems (like Fedora/RHEL) to allow the container to write to the mounted volume.*

Access the application at `http://127.0.0.1:5000`.

## Usage

1.  Create a CSV file with your tasks (see `data/example_tasks.csv` for format).
2.  Start a new project via the web interface and upload the CSV.
3.  Vote on pairs for "Technical Complexity".
4.  Switch dimension to "Business Value" and vote.
5.  View results to see the ranking matrix.
