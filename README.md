# Depuratori Acque Dashboard

The `depuratori-acque-dashboard` project is an interactive web application designed for the national monitoring, analysis, and visualization of water treatment plant (depurator) data. Built with Streamlit, this dashboard allows users to upload raw data, which is then processed to display key metrics, geographical distributions, and efficiency insights through intuitive charts and interactive maps. The "ML" in the dashboard title suggests a potential for integrating machine learning-driven insights or predictions regarding depurator performance.

## Key Features

*   **Interactive Data Visualization**: Explore depurator data through dynamic and interactive charts powered by Plotly and geographic maps using Folium.
*   **Geographical Monitoring**: Visualize the distribution of water treatment plants across different "area_riferimento" (reference areas) with geocoded locations displayed on an interactive map.
*   **Data Processing & Efficiency Analysis**: Automatically processes uploaded CSV data, maps treatment types, and calculates efficiency metrics for comprehensive performance evaluation.
*   **User-Friendly Interface**: An intuitive Streamlit interface allows for easy data upload and exploration without technical expertise.

## Tech Stack

The project leverages a robust set of Python libraries for data processing, analysis, and web application development:

*   **Streamlit**: For building the interactive web dashboard.
*   **Pandas & NumPy**: For efficient data manipulation and analysis.
*   **Plotly & Matplotlib & Seaborn**: For creating rich, interactive data visualizations.
*   **Folium & Streamlit-Folium**: For rendering geographical maps and integrating them into the Streamlit app.
*   **Geopy**: For geocoding location data to display on maps.
*   **Scikit-learn**: Indicates potential machine learning capabilities for advanced analysis or predictive modeling.

## Getting Started

Follow these steps to set up and run the `depuratori-acque-dashboard` application locally.

### Prerequisites

*   Python 3.8+

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/depuratori-acque-dashboard.git
    cd depuratori-acque-dashboard
    ```
    (Note: Replace `your-username` with the actual GitHub username if this project is public.)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

2.  Your default web browser should automatically open a new tab displaying the dashboard (usually at `http://localhost:8501`).

3.  Within the application, you will be prompted to upload a CSV file containing your depurator data. Ensure the CSV includes the following columns: `id`, `area_riferimento`, `tipo_trattamento`, `anno`, and `valore_osservato`.