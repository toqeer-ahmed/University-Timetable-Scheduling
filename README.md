# University Timetable Scheduling System (AI-Based)

This project solves the NP-Hard university timetabling problem using a **Genetic Algorithm (GA)**. It schedules academic events (lectures and labs) into specific time slots and rooms without any conflicts while adhering to strict hard and soft constraints.

## Features
- **Genetic Algorithm**: Automatically resolves complex constraints (room capacity, overlapping schedules, lab requirements).
- **Web Interface**: A premium, glassmorphism-styled web dashboard built with Flask and Vanilla HTML/CSS/JS.
- **Reporting**: Generates an Excel workbook with isolated timetable sheets for every student group, along with a heatmap visualization of room utilization.

## Project Structure
- `data/`: Contains the raw JSON-like dataset (`formatted_data.py`).
- `static/` & `templates/`: Contains the frontend assets (HTML, CSS, JS) for the web application.
- `app.py`: Flask backend server to run the web interface.
- `main.py`: CLI entry point to run the genetic algorithm and generate `.xlsx` and `.png` outputs.
- `scheduler.py`: The core Genetic Algorithm implementation.
- `constraints.py`: Contains the fitness evaluation and penalty logic for hard/soft constraints.
- `data_loader.py`: Cleans, validates, and normalizes the raw data.
- `Project_Report.md`: The complete academic report including complexity analysis and algorithm design.

## Installation

Ensure you have Python 3.8+ installed.

1. **Install Dependencies**
   Run the following command to install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

### Option 1: Web Interface (Recommended)
Launch the beautiful full-stack web application:
```bash
python app.py
```
Then, open your web browser and navigate to `http://127.0.0.1:5000`. 
*(Note: Generating a schedule may take 10-30 seconds depending on the selected number of generations).*

### Option 2: Command Line (CLI)
To run the algorithm directly in your terminal and export the timetable to an Excel file:
```bash
python main.py
```
This will output a `University_Timetable_[timestamp].xlsx` and a `Room_Utilization_Heatmap.png` in the project directory.

## Academic Submission
This project is structured for academic evaluation for **CS378: Design and Analysis of Algorithms**. Please refer to `Project_Report.md` for a complete breakdown of Time Complexity ($\mathcal{O}(G \times P \times (N + E \log C + \log P))$) and Space Complexity.
