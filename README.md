<h1 align="center">Depuratori Acque Dashboard</h1>
<h3 align="center">Water Treatment Plant Monitoring Dashboard</h3>

<p align="center">
  <em>Interactive data visualization and geographical monitoring with ML insights</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white" alt="Plotly" />
  <img src="https://img.shields.io/badge/Folium-77B829?style=flat-square" alt="Folium" />
</p>

<p align="center">
  :gb: <a href="#english">English</a> | :it: <a href="#italiano">Italiano</a>
</p>

---

<a name="english"></a>
## :gb: English

### Overview

An interactive web application for national monitoring, analysis, and visualization of water treatment plant data. Upload raw data to display key metrics, geographical distributions, and efficiency insights through charts and interactive maps.

### Features

- **Interactive Visualization** - Dynamic charts powered by Plotly
- **Geographical Monitoring** - Treatment plants on interactive Folium maps
- **Efficiency Analysis** - Automatic metrics calculation and performance evaluation
- **User-Friendly Interface** - Easy data upload via Streamlit

### Tech Stack

| Category | Technologies |
|----------|--------------|
| Dashboard | Streamlit |
| Data | Pandas, NumPy |
| Visualization | Plotly, Matplotlib, Seaborn |
| Maps | Folium, Geopy |
| ML | Scikit-learn |

### Quick Start

```bash
git clone https://github.com/fracabu/depuratori-acque-dashboard.git
cd depuratori-acque-dashboard

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Access at `http://localhost:8501`

---

<a name="italiano"></a>
## :it: Italiano

### Panoramica

Un'applicazione web interattiva per il monitoraggio nazionale, analisi e visualizzazione dei dati dei depuratori. Carica i dati grezzi per visualizzare metriche chiave, distribuzioni geografiche e insights sull'efficienza tramite grafici e mappe interattive.

### Funzionalita

- **Visualizzazione Interattiva** - Grafici dinamici con Plotly
- **Monitoraggio Geografico** - Impianti su mappe interattive Folium
- **Analisi Efficienza** - Calcolo automatico metriche e valutazione performance
- **Interfaccia User-Friendly** - Upload dati semplice via Streamlit

### Stack Tecnologico

| Categoria | Tecnologie |
|-----------|------------|
| Dashboard | Streamlit |
| Dati | Pandas, NumPy |
| Visualizzazione | Plotly, Matplotlib, Seaborn |
| Mappe | Folium, Geopy |
| ML | Scikit-learn |

### Avvio Rapido

```bash
git clone https://github.com/fracabu/depuratori-acque-dashboard.git
cd depuratori-acque-dashboard

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Accedi su `http://localhost:8501`

---

## CSV Format

Required columns: `id`, `area_riferimento`, `tipo_trattamento`, `anno`, `valore_osservato`

## Requirements

- Python 3.8+

## License

MIT

---

<p align="center">
  <a href="https://github.com/fracabu">
    <img src="https://img.shields.io/badge/Made_by-fracabu-8B5CF6?style=flat-square" alt="Made by fracabu" />
  </a>
</p>
