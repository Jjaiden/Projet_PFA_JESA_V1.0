# JESA DMAT - Digital Maturity Assessment Tool

**JESA Digital Maturity Assessment Tool** is a comprehensive web application designed to assess, analyze, and visualize the digital maturity of industrial organizations. Developed as an internship project for JESA in partnership with ENSAM Casablanca, this tool implements the Industry 5.0 digital transformation framework.

---

## Table of Contents

- Overview
- Purpose
- Key Features
- Technology Stack
- Project Architecture
- Installation and Setup
- Usage Guide
- Assessment Workflow
- Export Options
- Configuration
- Development
- Contributors

---

## Overview

JESA DMAT is a full-stack digital maturity assessment platform that guides organizations through their digital transformation journey. The tool follows a structured approach:

1. Assess — Collect maturity data via Excel-based questionnaires
2. Identify — Reveal transformation gaps against strategic targets
3. Prioritize — Focus on high-value initiatives using TPI (Transformation Priority Index)
4. Transform — Turn priorities into actionable roadmaps

The tool enables industrial organizations to evaluate their current digital maturity across multiple dimensions, set strategic targets, identify gaps, prioritize transformation initiatives based on impact and feasibility, generate comprehensive reports and roadmaps, and track progress over time through historical assessments.

---

## Purpose

The primary purpose of JESA DMAT is to provide a structured, data-driven approach to digital transformation assessment for industrial organizations. By leveraging a comprehensive reference framework, the tool helps organizations understand their current digital maturity level, identify areas requiring attention, and develop a prioritized action plan for transformation.

The tool is designed to be used by digital transformation engineers, consultants, and decision-makers in industrial settings who need to assess and plan digital transformation initiatives across their organizations.

---

## Key Features

### Assessment Management
- Upload Excel-based assessment questionnaires
- Multi-step assessment workflow with validation
- Session persistence and state management
- Historical assessment storage and retrieval

### Interactive Dashboard
- Digital Maturity Index (DMI) gauge visualization
- Pillar performance bar charts
- Dimension radar charts comparing current and target scores
- Sub-dimension heatmaps for detailed analysis
- Gap analysis with visual indicators
- Diagnostic insights derived from assessment data

### Decision Analysis
- Site-specific decision parameter collection
- Multi-criteria scoring including Business Impact, Strategic Importance, ROI, Cost, and Difficulty
- Transformation Priority Index calculation
- Priority ranking and visualization

### Transformation Roadmap
- Prioritized action items with TPI scores
- Phase-based implementation planning
- Action details with objectives and expected benefits
- Strategic synthesis

### Export Capabilities
- PDF Score Summary for quick stakeholder overview
- PDF Full Report for comprehensive documentation
- Excel Workbook for further analysis
- JSON data export for integration with other systems
- ZIP bundle containing all generated reports

---

## Technology Stack

### Frontend
- **Streamlit** (1.40+) – Web application framework
- **Plotly** (5.24+) – Interactive visualizations
- **Kaleido** (1.0+) – Static image export for charts
- **HTML/CSS** – Custom styling and theming

### Backend
- **Python** (3.9+) – Core application logic
- **Pandas** (2.2+) – Data manipulation
- **OpenPyXL** (3.1+) – Excel file processing
- **NumPy** (1.24+) – Numerical computations
- **ReportLab** (4.0+) – PDF generation
- **Matplotlib** (3.7+) – Chart generation for PDFs

### Testing
- **Pytest** (8.0+) – Unit and integration testing

---

## Project Architecture

The project is organized into the following main directories:

- **assets** – Static resources including logos, stylesheets, and templates
- **charts** – Visualization components for charts and graphs
- **components** – Reusable UI components
- **config** – Application constants and settings
- **data** – Data loading, models, and runtime storage
- **engines** – Business logic for assessment scoring and decision analysis
- **exports** – Report generation in various formats
- **outputs** – Generated assessment outputs organized by assessment ID
- **pages** – Streamlit multi-page application
- **streamlit** – Streamlit configuration
- **tests** – Unit and integration test suite
- **utils** – Utility modules for various functionality

This modular architecture separates concerns and makes the codebase maintainable and extensible.

---

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip (Python package manager)

### Step 1: Clone the Repository

```
git clone <repository-url>
cd Projet_PFA_JESA_V1.0
```

### Step 2: Create a Virtual Environment

**Windows**
```
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**
```
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```
pip install -r requirements.txt
```

### Step 4: Verify Installation

```
pip list
```

Ensure all required packages are present:
- streamlit >= 1.40
- pandas >= 2.2
- plotly >= 5.24
- openpyxl >= 3.1
- reportlab >= 4.0
- pytest >= 8.0 (optional, for testing)

---

## Usage Guide

### Starting the Application

**Option 1: Streamlit Frontend (Recommended)**

```
streamlit run app.py
```

The application will open in your browser at http://localhost:8501.

**Option 2: Backend CLI**

```
python app.py --assessment-file path/to/assessment.xlsx [OPTIONS]
```

CLI Options:

| Option | Description |
|--------|-------------|
| --assessment-file PATH | Path to the Assessment.xlsx file (required) |
| --assessment-id TEXT | Custom assessment identifier |
| --output-dir PATH | Output directory (default: ./outputs) |
| --formats [json|excel|pdf] | Export formats (default: json) |
| --no-gap | Skip gap analysis |
| --no-tpi | Skip TPI calculation |
| --no-recommendations | Skip recommendations |
| --no-roadmap | Skip roadmap generation |
| --verbose | Enable verbose logging |

### Step-by-Step Workflow

**1. Home Page**

The landing page provides an overview of the digital transformation journey, quick access to start a new assessment, institutional branding, and engineering team credit.

**2. New Assessment**

Step 1: Assessment Identity
- Assessment Name or Reference
- Company or Business Unit
- Industrial Site or Plant
- Assessor Name and Role
- Assessment Date
- Contact Email (optional)

Step 2: Assessment Data
- Download the official Excel template
- Complete the questionnaire
- Upload the completed workbook

Step 3: Review and Launch
- Review all assessment details
- Start the assessment processing

**3. Dashboard**

The dashboard provides comprehensive visualization of assessment results:

Executive Snapshot
- Digital Maturity Index (DMI) score
- Maturity Level
- Overall Gap (current versus target)
- Attention Areas count

Overall Maturity Position
- Gauge chart showing DMI
- Current and Target scores
- Remaining gap

Pillar Performance
- Horizontal bar chart showing performance by pillar

Maturity Profile
- Radar charts comparing current versus target maturity across dimensions

Sub-Dimension Heatmap
- Detailed score matrix by dimension and sub-dimension

Transformation Gaps
- List of dimensions with the largest gaps
- Visual progress bars showing gap severity

Diagnostic Insights
- Key observations derived from the assessment

**4. Decision Analysis**

Purpose: Prioritize transformation actions based on site-specific criteria.

Decision Criteria:
- Business Impact (1-5)
- Strategic Importance (1-5)
- Expected ROI (1-5)
- Implementation Cost (1-5)
- Implementation Difficulty (1-5)

Process:
1. Review transformation opportunities (dimensions with positive gaps)
2. Complete all criteria for each dimension
3. Click the button to run TPI calculation

**5. Transformation Roadmap**

Summary KPIs:
- DMI score
- Maturity Level
- Number of transformation actions
- Top priority level

Prioritization Overview:
- Ranked list of actions with TPI scores
- Priority badges (Critical, High, Medium, etc.)
- Visual TPI progress bars

Action Details:
- Expandable sections for each action
- Description, objective, expected benefit
- Implementation notes

Export Section:
- Select export formats (PDF Score Summary, PDF Full Report, Excel)
- Generate and download files

**6. History**

- View all historical assessments in a table
- Select and restore previous assessments
- Start new assessments

**7. Export**

- Select from available export formats
- Generate individual files or complete ZIP bundle
- Download generated files

---

## Assessment Workflow

The typical assessment workflow follows these steps:

1. Start — User begins a new assessment
2. Download Template — User downloads the official Excel template
3. Complete Assessment — User fills out the questionnaire
4. Upload — User uploads the completed workbook
5. Validation and Processing — System validates and processes the data
6. If invalid, error message is shown and user returns to upload step
7. View Dashboard — User reviews the assessment results
8. Decision Analysis — User enters decision criteria
9. TPI Calculation — System calculates Transformation Priority Index
10. View Roadmap — User reviews the prioritized action plan
11. Generate Reports — User selects and generates export files
12. Export or Share — User downloads or shares the assessment outputs

---

## Export Options

### PDF Score Summary
- Format: 2-page PDF
- Content: Executive summary, DMI, maturity level, key metrics
- Usage: Quick overview for stakeholders

### PDF Full Report
- Format: Comprehensive PDF
- Content: Complete assessment details, all charts, gaps, insights, recommendations, roadmap
- Usage: Detailed analysis and documentation

### Excel Workbook
- Format: Multi-sheet Excel
- Content: All assessment data, scores, gaps, recommendations
- Usage: Further analysis and data manipulation

### JSON Export
- Format: JSON data dump
- Content: Complete structured data
- Usage: API integration or custom analysis

### ZIP Bundle
- Format: ZIP archive
- Content: All generated report files
- Usage: Complete package delivery

---

## Configuration

### Backend Configuration

The backend configuration is centralized in config/settings.py. Key settings include:

| Setting | Description | Default |
|---------|-------------|---------|
| REFERENTIEL_FILE | Path to reference framework | data/knowledge_base/REFERENTIEL_*.xlsx |
| RECOMMENDATIONS_FILE | Path to recommendations knowledge base | data/knowledge_base/BASE_*.xlsx |
| OUTPUT_DIR | Output directory for generated files | ./outputs |
| SCORE_DECIMAL_PRECISION | Score decimal precision | 3 |
| DMI_DECIMAL_PRECISION | DMI decimal precision | 1 |
| TPI_DECIMAL_PRECISION | TPI decimal precision | 3 |
| STRICT_WEIGHT_VALIDATION | Enforce weight validation | True |
| ALLOW_MISSING_SCORE_ON_APPLICABLE | Allow missing scores | False |

### Frontend Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| APP_NAME | Application name | JESA DMAT |
| APP_VERSION | Application version | 1.0.0 |
| PAGE_TITLE | Browser page title | JESA DMAT |
| LAYOUT | Streamlit layout | wide |
| PDF_PAGE_SIZE | PDF page size | A4 |
| PDF_ORIENTATION | PDF orientation | portrait |

### Environment Variables

```
JDMAF_REFERENTIEL_FILE=path/to/referentiel.xlsx
JDMAF_RECOMMENDATIONS_FILE=path/to/recommendations.xlsx
JDMAF_ASSESSMENT_FILE=path/to/assessment.xlsx
JDMAF_OUTPUT_DIR=path/to/outputs
JDMAF_LOG_LEVEL=DEBUG

STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

---

## Development

### Running Tests

```
# Run all tests
pytest

# Run frontend tests
pytest tests/tests_frontend/

# Run chart tests
pytest tests/tests_charts/

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Style

The project follows PEP 8 guidelines with the following conventions:

- Type hints are required for all functions
- Google-style docstrings for all modules and functions
- Imports are grouped into standard library, third-party, and local
- Maximum line length is 100 characters

---

## Contributors

This project was developed as an internship project at JESA in partnership with ENSAM Casablanca.

**Engineering Team**
- IGOURZAL Fatima Ezzahrae — Digital Transformation Engineer
- EL BALJOURI Boutayna — Digital Transformation Engineer

**Affiliation**
- JESA Group — Industry Partner
- ENSAM Casablanca — Academic Partner
- ELECTRICAL ENGENERING - MSEI(Management of Intelligent Electrical System) — Engineering Program

---

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use of this software is strictly prohibited.

---

## Contact

For any questions, feedback, or support regarding the JESA DMAT tool, please reach out to the engineering team:

**Engineering Team**
- IGOURZAL Fatima Ezzahrae
  - Email: fatimaezzahraeigourzal91@gmail.com
  - Phone: +212 6 49 28 66 72

- EL BALJOURI Boutayna
  - Email: boutaynael917@gmail.com
  - Phone: +212 6 06 16 44 48

**Institutional Contacts**
- JESA Group: https://www.jesagroup.com/
- ENSAM Casablanca: https://ensam-casa.ma/

---

## Acknowledgments

- JESA Management for supporting this project
- ENSAM Casablanca for academic guidance


---

*Last Updated: August 2026*
*Version: 1.0.0*