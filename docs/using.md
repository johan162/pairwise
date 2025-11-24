# Using the System

## 1. Preparing Your Data
Create a CSV file containing the items you want to rank. The file **must** have at least two columns: `id` and `description`.

**Example `tasks.csv`**:
```csv
id,description
REQ-1,User Login System
REQ-2,Payment Gateway Integration
REQ-3,Admin Dashboard
...
```

## 2. Creating a Project
1.  On the home page, fill in the **Project Name** and **Description**.
2.  Upload your CSV file.
3.  Click **Create Project**.

## 3. Voting Process
The system will present two items side-by-side.
1.  **Select the winner**: Click on the card of the item that is "higher" in the current dimension (e.g., has more Business Value).
2.  **Progress**: Watch the progress bar and "Certainty" metric (Kendall Tau) increase.
3.  **Switch Dimensions**: Use the link at the top to switch between ranking **Business Value** and **Technical Complexity**.

## 4. Viewing Results
Click **Results** in the navigation bar at any time.
- **Scatter Plot**: Visualizes items with Complexity on the X-axis and Value on the Y-axis.
    - *High Value, Low Complexity*: Quick Wins (Top Left)
    - *High Value, High Complexity*: Strategic Initiatives (Top Right)
- **Table**: Detailed list of scores and ranks.

## 5. Saving and Resuming
The system saves the state to `data/current_state.json` after every vote.
- If you restart the server, the application will automatically detect the previous session and allow you to resume.
- To start fresh, click **Close Project** (this will clear the current session).
