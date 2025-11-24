# Installation

## Prerequisites

- **Python 3.13** or higher
- **pip** (Python package installer)
- **Git** (optional, for cloning)
- **Docker** (optional, for containerized deployment)

## Local Setup

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone https://github.com/yourusername/pairwise.git
    cd pairwise
    ```

2.  **Create a virtual environment**:
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Alternatively, if you are developing:*
    ```bash
    pip install -e ".[dev]"
    ```

## Docker Setup

If you prefer using Docker, you don't need to install Python locally.

1.  **Build the image**:
    ```bash
    docker build -t pairwise .
    ```
