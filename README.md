# DSS Social Network Analysis Dashboard

A Streamlit-based Decision Support System (DSS) for analysing clandestine or organisational networks.
Upload a network in Matrix Market (`.mtx`) format and explore node importance, structural roles, communities, robustness, connectivity via the Kemeny constant, and an arrest optimisation workflow.

## Live demo (recommended)

The dashboard is hosted online and can be accessed here:
https://social-network-analysis-group-robbert1.streamlit.app/

For most users, this is the recommended way to explore the project, since it requires no local setup.  
If you prefer to run the app locally (for development or experimentation), follow the **Quick start** section below for installation, configuration, and execution instructions.

## Quick start

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure login credentials

This app uses Streamlit secrets.

Create a local file at `.streamlit/secrets.toml`:

```toml
[auth]
username = "Robbert"
password = "Group1"
```

### 4) Run the dashboard

```bash
streamlit run src/app.py
```

Open the URL printed in the terminal (default: http://localhost:8501).

## Input data format

The dashboard expects a Matrix Market file (`.mtx`) representing an adjacency matrix.

- The file must contain a square matrix.
- Node identifiers are the row or column indices `0..N-1`.
- The graph is inferred as:
  - **Undirected** if the adjacency matrix is symmetric.
  - **Directed** otherwise.
- Self-loops are removed during loading.
- Edge weights in the matrix are currently treated as “edge exists” (non-zero) rather than used as weights in the analytics.

Example files are provided in `example_graphs/`.

## What the dashboard computes

### Upload & Overview

- Validates the uploaded file and constructs a NetworkX graph.
- Reports basic statistics: number of nodes, number of edges, density, connected components.
- Shows an initial network visualisation.

### Centrality Analysis

Computes the following centrality measures:

- degree (raw degree)
- Katz
- eigenvector
- betweenness
- closeness
- PageRank

You can:

- Combine measures via **weighted sum** or **Borda count** aggregation.
- Highlight top or bottom nodes and manually select nodes to inspect.
- Download centrality tables as CSV.

### Role Identification

Provides multiple approaches to role discovery:

- Cooper and Barahona (k-hop or random-walk signatures, cosine or correlation distance)
- RoleSim
- RoleSim*
- RolX (feature-based role extraction)

The page supports clustering, role summaries, and a role-based “leader ranking” view.
Some methods can be computationally heavy on large graphs.

### Communities & Robustness

Community detection options:

- Spectral clustering
- Girvan-Newman
- Louvain (available for undirected graphs)

Robustness evaluation:

- Perturbation test that removes a fraction of edges across multiple runs
- Stability measured with Adjusted Rand Index (ARI)

### Kemeny Analysis

- Computes the baseline Kemeny constant (random-walk connectivity measure).
- Shows an edge sensitivity view (impact on Kemeny if an edge is removed).
- Lets you interactively remove edges and control the order of removals.
- Optional setting to recompute on the largest component if the graph becomes disconnected.

### Arrest Optimisation

Assigns nodes to two departments to maximise “effective arrests” and minimise risky cross-department edges.

- Formulated as a balanced cut optimisation solved via PuLP (CBC). If the solver cannot find an optimal solution, the app falls back to a heuristic assignment.
- Community structure and centrality can be weighted via parameters `alpha` and `beta`.
- A `gamma` parameter influences the recommended arrest order by penalising risky edges.
- Includes a simulation of sequential arrests and CSV export of the recommended order.

## Repository structure

```
.
├─ src/
│  ├─ app.py                      # Streamlit entry point (includes login and navigation)
│  └─ dss/
│     ├─ analytics/               # Centrality, roles, communities, robustness, Kemeny, arrest optimisation
│     ├─ graph/                   # Loading, layout, and graph statistics helpers
│     ├─ pages/                   # Streamlit pages (imported by app.py)
│     ├─ ui/                      # Session state, login helpers, UI components
│     ├─ utils/                   # Plotting, IO, validation, and vendored graphrole utilities
│     ├─ config.py                # Default parameters used across the app
│     └─ types.py                 # Dataclasses for typed results passed between modules
├─ example_graphs/                # Sample .mtx files for quick testing
├─ requirements.txt
└─ .streamlit/config.toml         # Streamlit theme settings
```

## Development
The code uses Python 3.11, installs dependencies, and starts Streamlit.

### Code organisation

- Application entry point: `src/app.py`.
- Page implementations: `src/dss/pages/`.
- Algorithms and analysis: `src/dss/analytics/`.

## Troubleshooting

- **Login error: “Missing Streamlit secrets”**
  Ensure `.streamlit/secrets.toml` exists and contains `[auth] username` and `password`.

- **Kemeny is undefined after removals**
  The Markov chain may become disconnected. Enable “Recompute on largest component” on the Kemeny page.

- **Slow computation on large graphs**
  RoleSim, RoleSim*, and robustness tests can be expensive. Start with smaller graphs or reduce the number of perturbation runs.

- **Arrest optimisation solver issues**
  If PuLP cannot find an optimal solution, the dashboard falls back to a heuristic assignment automatically.

## Third-party code

This repository includes vendored code under `src/dss/utils/graphrole/` (MIT License). See `src/dss/utils/graphrole/LICENSE.txt`.

## Use of Generative AI

This project was developed with limited support from Generative AI tools (for example, large language models) to assist with productivity tasks such as brainstorming, drafting documentation text, and improving code readability through refactoring suggestions. All algorithmic choices, mathematical definitions, experimental design, and final implementation decisions were made by the authors. Any AI-generated suggestions were reviewed, validated, and, where necessary, rewritten by the authors to ensure correctness, reproducibility, and alignment with course requirements. No confidential or personally identifiable data was provided to AI tools.
