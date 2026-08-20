# JESA DMAT — Digital Maturity Assessment Tool

**JESA Digital Maturity Assessment Tool (JESA DMAT)** is a web-based platform designed to assess, analyze, and visualize the digital maturity of industrial organizations.

Developed as an internship project for **JESA Group** in partnership with **ENSAM Casablanca**, the platform provides a structured and data-driven approach to digital transformation assessment in industrial environments.

JESA DMAT implements an **Industry 5.0-oriented digital maturity assessment framework** and guides users from assessment data collection through maturity analysis, transformation prioritization, roadmap generation, and reporting.

---

## Live Application

The application is deployed using **Streamlit Community Cloud**.

**JESA DMAT:**  
https://jesa-dmat-pfa.streamlit.app/

The deployed application provides the complete assessment workflow directly through a web interface.

---

## Overview

JESA DMAT follows a structured digital transformation workflow:

**Assess → Identify → Prioritize → Transform**

1. **Assess** — Collect digital maturity data through an Excel-based questionnaire.
2. **Identify** — Analyze the current maturity level and reveal gaps against strategic targets.
3. **Prioritize** — Rank transformation opportunities using the Transformation Priority Index (TPI).
4. **Transform** — Convert priorities into actionable transformation roadmaps and reports.

The platform allows industrial organizations to evaluate their digital maturity across multiple dimensions, identify areas requiring improvement, prioritize transformation initiatives, and develop structured action plans.

---

## Purpose

The primary objective of JESA DMAT is to provide a structured and practical tool for evaluating digital maturity within industrial organizations.

The platform helps users:

- Assess the current digital maturity of an industrial site.
- Visualize maturity across different pillars and dimensions.
- Compare current maturity against target maturity levels.
- Identify digital transformation gaps.
- Prioritize transformation opportunities.
- Evaluate initiatives using site-specific decision criteria.
- Calculate the Transformation Priority Index (TPI).
- Generate a transformation roadmap.
- Generate professional reports and analytical exports.
- Maintain a history of previous assessments.

The tool is intended for use by:

- Digital transformation engineers.
- Industrial engineers.
- Consultants.
- Plant and site managers.
- Digital transformation teams.
- Decision-makers involved in Industry 4.0 and Industry 5.0 initiatives.

---

## Key Features

### Assessment Management

- Create a new digital maturity assessment.
- Define assessment identity and site information.
- Download the official Excel assessment template.
- Upload completed assessment workbooks.
- Validate assessment data before processing.
- Process and score assessment results.
- Maintain assessment session state.
- Store and retrieve historical assessments.

### Interactive Dashboard

The dashboard provides a visual representation of the assessment results, including:

- Digital Maturity Index (DMI).
- Overall maturity level.
- Current versus target maturity.
- Overall transformation gap.
- Pillar performance.
- Dimension maturity profile.
- Radar charts.
- Sub-dimension heatmaps.
- Transformation gaps.
- Diagnostic insights.
- Attention areas.

### Decision Analysis

The Decision Analysis module supports transformation prioritization through site-specific decision criteria.

The platform evaluates:

- Business Impact.
- Strategic Importance.
- Expected ROI.
- Implementation Cost.
- Implementation Difficulty.

Each criterion is evaluated on a **1–5 scale**.

The collected decision parameters are used to calculate the **Transformation Priority Index (TPI)** and establish transformation priorities.

### Transformation Roadmap

The Roadmap module transforms prioritized opportunities into an actionable implementation plan.

It provides:

- Ranked transformation actions.
- TPI scores.
- Priority levels.
- Implementation phases.
- Action descriptions.
- Objectives.
- Expected benefits.
- Implementation information.
- Strategic synthesis.

### History

The History module allows users to:

- View previous assessments.
- Review historical assessment information.
- Restore previous assessments.
- Continue working with stored assessment results.
- Start a new assessment.

### Export Capabilities

JESA DMAT provides several export formats:

- **PDF Score Summary**
- **PDF Full Report**
- **Excel Workbook**
- **JSON**
- **ZIP Bundle**

The Score Summary is designed for concise stakeholder communication, while the Full Report provides comprehensive assessment documentation.

---

## Technology Stack

### Frontend

- **Streamlit** — Web application framework
- **Plotly** — Interactive data visualization
- **Kaleido** — Static chart export
- **HTML/CSS** — Custom interface styling and theming

### Backend

- **Python** — Core application logic
- **Pandas** — Data processing
- **OpenPyXL** — Excel processing
- **NumPy** — Numerical computation
- **ReportLab** — PDF generation
- **Matplotlib** — PDF chart generation

### Testing

- **Pytest** — Unit and integration testing

---

## Project Architecture

The project follows a modular architecture separating the user interface, data management, assessment engines, decision engines, visualization, and export layers.

```text
Projet_PFA_JESA_V1.0/
│
├── app.py
├── requirements.txt
├── README.md
│
├── assets/
│   ├── logos/
│   ├── styles/
│   └── templates/
│
├── charts/
│   ├── radar_chart.py
│   ├── bar_chart.py
│   ├── gauge_chart.py
│   └── ...
│
├── components/
│   └── ...
│
├── config/
│   ├── settings.py
│   └── ...
│
├── data/
│   ├── loader.py
│   ├── models.py
│   ├── knowledge_base/
│   └── ...
│
├── engines/
│   ├── assessment/
│   └── decision/
│
├── exports/
│   ├── report.py
│   ├── pdf.py
│   └── ...
│
├── pages/
│   ├── 1_Home.py
│   ├── 2_New_Assessment.py
│   ├── 3_Dashboard.py
│   ├── 4_Decision_analysis.py
│   ├── 5_Roadmap.py
│   ├── 6_History.py
│   └── 6_Export.py
│
├── tests/
│   └── ...
│
└── utils/
    └── ...
```

---

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip

### Clone the Repository

```bash
git clone https://github.com/Jjaiden/Projet_PFA_JESA_V1.0.git
cd Projet_PFA_JESA_V1.0
```

### Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

## Usage Guide

### 1. Home

The Home page provides:

- An overview of JESA DMAT.
- Access to the assessment workflow.
- Institutional branding.
- Information about the digital transformation assessment process.
- Engineering team information.

### 2. New Assessment

The New Assessment workflow consists of three main steps.

#### Step 1 — Assessment Identity

The user provides:

- Assessment name or reference.
- Company or business unit.
- Industrial site or plant.
- Assessor name.
- Assessor role.
- Assessment date.
- Contact email.

#### Step 2 — Assessment Data

The user:

1. Downloads the official Excel template.
2. Completes the questionnaire.
3. Uploads the completed workbook.
4. Submits the assessment for validation.

#### Step 3 — Review and Launch

The user reviews the assessment information and launches the assessment processing.

The system validates the workbook before calculating the maturity results.

---

## Assessment Workflow

The complete assessment process follows this sequence:

```text
Start
  ↓
Create Assessment
  ↓
Download Excel Template
  ↓
Complete Questionnaire
  ↓
Upload Assessment
  ↓
Validate Data
  ↓
Calculate Maturity
  ↓
Dashboard
  ↓
Identify Transformation Gaps
  ↓
Decision Analysis
  ↓
TPI Calculation
  ↓
Transformation Roadmap
  ↓
Generate Reports
  ↓
Export / Share Results
```

---

## Dashboard

The Dashboard provides a comprehensive view of assessment results.

### Executive Snapshot

Displays:

- Digital Maturity Index (DMI).
- Maturity level.
- Overall gap.
- Number of attention areas.

### Overall Maturity Position

Provides:

- Current maturity score.
- Target maturity score.
- Remaining transformation gap.
- Maturity gauge.

### Pillar Performance

Displays maturity performance across the main pillars of the assessment framework.

### Maturity Profile

Provides radar visualizations comparing:

- Current maturity.
- Target maturity.

### Sub-Dimension Analysis

Provides detailed maturity information at the sub-dimension level through visual matrices and heatmaps.

### Transformation Gaps

Highlights dimensions where the current maturity is below the desired target.

### Diagnostic Insights

Provides automatically derived observations based on the assessment results.

---

## Decision Analysis

The Decision Analysis module transforms assessment gaps into prioritized transformation opportunities.

For each relevant dimension, users provide values from **1 to 5** for:

| Criterion | Description |
|---|---|
| Business Impact | Expected impact on business performance |
| Strategic Importance | Importance to the organization's strategy |
| Expected ROI | Expected return on investment |
| Implementation Cost | Estimated implementation cost |
| Implementation Difficulty | Expected implementation complexity |

The system uses these criteria to calculate the **Transformation Priority Index (TPI)**.

The resulting analysis provides a ranked view of transformation opportunities.

---

## Transformation Roadmap

The Roadmap module converts the prioritized transformation opportunities into an implementation plan.

It provides:

### Summary KPIs

- DMI score.
- Maturity level.
- Number of transformation actions.
- Highest priority level.

### Prioritization Overview

- Ranked transformation actions.
- TPI scores.
- Priority levels.
- Visual priority indicators.

### Action Details

Each transformation action may include:

- Description.
- Objective.
- Expected benefits.
- Implementation information.
- Recommended actions.

### Implementation Phases

Transformation initiatives are organized into implementation phases to support progressive digital transformation planning.

---

## History

The History module provides access to previous assessments.

Users can:

- View assessment history.
- Review assessment information.
- Restore previous assessments.
- Continue analysis from historical results.
- Start new assessments.

---

## Export Options

### PDF Score Summary

A concise **two-page PDF** designed for quick stakeholder communication.

Includes:

- Executive summary.
- DMI score.
- Maturity level.
- Key metrics.
- Main assessment results.

### PDF Full Report

A comprehensive report containing detailed assessment information, visualizations, gaps, insights, recommendations, and roadmap information.

### Excel Workbook

Provides structured assessment and analytical data for further processing.

### JSON

Provides structured machine-readable assessment data suitable for:

- Integration.
- Data processing.
- Custom analysis.
- Future API integration.

### ZIP Bundle

Packages the generated reports and export files into a single downloadable archive.

---

## Configuration

The backend configuration is centralized in:

```text
config/settings.py
```

Important configuration elements include:

| Setting | Description |
|---|---|
| `REFERENTIEL_FILE` | Reference digital maturity framework |
| `RECOMMENDATIONS_FILE` | Recommendations knowledge base |
| `OUTPUT_DIR` | Generated output directory |
| `SCORE_DECIMAL_PRECISION` | Score precision |
| `DMI_DECIMAL_PRECISION` | DMI precision |
| `TPI_DECIMAL_PRECISION` | TPI precision |
| `STRICT_WEIGHT_VALIDATION` | Weight validation |
| `ALLOW_MISSING_SCORE_ON_APPLICABLE` | Missing-score handling |

---

## Environment Variables

The application can use environment variables for configuration, including:

```text
JDMAF_REFERENTIEL_FILE
JDMAF_RECOMMENDATIONS_FILE
JDMAF_ASSESSMENT_FILE
JDMAF_OUTPUT_DIR
JDMAF_LOG_LEVEL
```

For local Streamlit execution, the application can also use:

```text
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

---

## Development

### Run Tests

Run the complete test suite:

```bash
pytest
```

Run frontend tests:

```bash
pytest tests/tests_frontend/
```

Run chart tests:

```bash
pytest tests/tests_charts/
```

Run tests with coverage:

```bash
pytest --cov=. --cov-report=html
```

### Code Style

The project follows standard Python development practices, including:

- Type hints.
- Structured module organization.
- Google-style docstrings.
- Separation between frontend and backend logic.
- Modular business engines.
- Reusable visualization components.

---

## Deployment

JESA DMAT is deployed using **Streamlit Community Cloud**.

The production application is connected to the GitHub repository and automatically reflects committed changes after deployment processing.

**Production application:**

https://jesa-dmat-pfa.streamlit.app/

Streamlit Community Cloud supports deployment directly from GitHub repositories and automatically processes subsequent code changes. 

---

## Version

**Current release: 1.0.0**

**Status: Stable Deployment Version**

The `v1.0.0-deployed` Git tag marks the verified deployment state of the application.

This version represents the stable baseline following deployment and end-to-end functional testing.

---

## Contributors

This project was developed as an internship project at **JESA Group** in partnership with **ENSAM Casablanca**.

### Engineering Team

**IGOURZAL Fatima Ezzahrae**  
Digital Transformation Engineer

**EL BALJOURI Boutayna**  
Digital Transformation Engineer

### Academic / Industrial Affiliation

**JESA Group** — Industry Partner

**ENSAM Casablanca** — Academic Partner

**Electrical Engineering — MSEI**  
Management of Intelligent Electrical Systems

---

## Contact

For questions, feedback, collaboration, or information regarding JESA DMAT, please contact the engineering team.

### Engineering Team

**IGOURZAL Fatima Ezzahrae**   
Email: **fatimaezzahraeigourzal91@gmail.com**  
Phone: **+212 6 49 28 66 72**

**EL BALJOURI Boutayna**   
Email: **boutaynael917@gmail.com**  
Phone: **+212 6 06 16 44 48**

### Institutional Contacts

**JESA Group**  
https://www.jesagroup.com/

**ENSAM Casablanca**  
https://ensam-casa.ma/

---

## Acknowledgments

The development of JESA DMAT was made possible through the support and guidance of:

- JESA Management.
- JESA Digital Transformation teams.
- ENSAM Casablanca.
- Academic and industrial supervisors.
- All contributors involved in the development and validation of the platform.

---

## License

This project was developed as an internship project and is considered **proprietary and confidential**.

Unauthorized copying, redistribution, modification, or commercial use of this software is prohibited without appropriate authorization.

---

*Last Updated: August 2026*  
*Version: 1.0.0*  
*JESA DMAT — Digital Maturity Assessment Tool*
