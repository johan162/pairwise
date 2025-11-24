# Running the Application

## Running Locally

Once you have installed the dependencies, you can start the Flask application directly.

1.  **Activate your virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the application**:
    ```bash
    python run.py
    ```

3.  **Access the interface**:
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Running with Docker

1.  **Run the container**:
    ```bash
    docker run -p 5000:5000 -v $(pwd)/data:/app/data pairwise
    ```
    *Note: The `-v` flag mounts your local `data` directory to the container, ensuring that your project state and uploaded CSVs are persisted.*

2.  **Access the interface**:
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)
