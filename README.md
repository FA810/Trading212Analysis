# Trading 212 Analytics Dashboard

A modern, local financial analytics application built with Streamlit, Plotly, and PostgreSQL to process, analyze, and visualize Trading 212 account transaction logs.

## Screenshots

### Main Dashboard & Customization
<table width="100%">
  <tr>
    <td width="50%">
      <p align="center"><b>Portfolio Overview & Asset Allocation</b></p>
      <img src="screenshots/01dashboard.PNG" alt="Main Dashboard" width="100%">
    </td>
    <td width="50%">
      <p align="center"><b>Theme Management & Customization</b></p>
      <img src="screenshots/05othertheme.PNG" alt="Alternative UI Theme" width="100%">
    </td>
  </tr>
</table>

### Core Analytics Views
<table width="100%">
  <tr>
    <td width="33%">
      <p align="center"><b>Transaction Log Grid</b></p>
      <img src="screenshots/02transactionslog.PNG" alt="Transaction Log" width="100%">
    </td>
    <td width="33%">
      <p align="center"><b>Single Ticker Timeline</b></p>
      <img src="screenshots/03history.PNG" alt="Historical Asset Performance" width="100%">
    </td>
    <td width="33%">
      <p align="center"><b>Trading Frequency Analysis</b></p>
      <img src="screenshots/04mostactive.PNG" alt="Most Active Stocks" width="100%">
    </td>
  </tr>
</table>

## Features

- **Centralized Database Storage:** Fully dynamic relational infrastructure powered by PostgreSQL.
- **Dynamic KPI Metrics Engine:** Accurate rolling tracking of Net Invested Capital, Total Cash Interest, Capital Gains, and Dividends.
- **Smart Asset Allocation:** Interactive, responsive Plotly charts featuring dynamic grouping thresholds (e.g., automated "Others" cluster generation for minor holdings).
- **Custom Multi-Theme System:** Injectable CSS configuration layer with pre-built theme setups (*Premium Gold*, *Teal Emerald*, *Cyberpunk Neon*, *Minimal Avio Blue*).
- **Frontend Serialization Safety:** Clean grid layouts with automated field parsing to safely view and filter complete transaction history datasets chronologically.

## Tech Stack

- **Backend / DB Processing:** Python, PostgreSQL, `psycopg2`, `pandas`
- **Frontend / Visualization:** Streamlit, Plotly Express, Plotly Graph Objects
- **Environment & Lifecycle Management:** Docker Compose, `python-dotenv`