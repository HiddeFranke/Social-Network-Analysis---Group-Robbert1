# """Streamlit page: Upload & Overview.

# This page allows the user to upload a `.mtx` file, validates it and
# computes basic statistics.  It also displays a baseline network plot
# with no particular sizing or colouring.  Once the graph is loaded,
# subsequent pages can access it via `st.session_state`.
# """

# import streamlit as st
# import pandas as pd
# from dss.ui.state import init_state, set_state, get_state
# from dss.utils.io_mtx import load_mtx
# from dss.graph.build_graph import build_graph
# from dss.graph.stats import basic_statistics
# from dss.utils.validation import validate_graph
# from dss.utils.plotting import plot_network
# from dss.graph.layouts import compute_layout
# from dss.ui.components import display_network


# def page() -> None:
#     st.set_page_config(page_title="Upload & Overview", layout="wide")
#     st.title("Upload & Overview")

#     with st.expander("Quick User Guide", expanded=False):
#         st.markdown(
#             """
#                 ### Welcome
                
#                 This dashboard allows you to analyze network structures using advanced graph-based methods.  
#                 Everything starts by uploading a network file.
                
#                 ---
                
#                 ### What to upload
                
#                 Upload a **Matrix Market (.mtx)** file that represents a network adjacency matrix.
                
#                 - Each row and column corresponds to a node  
#                 - Non-zero values indicate connections between nodes  
                
#                 ---
                
#                 ### What happens next
                
#                 After uploading the file:
                
#                 - The network is automatically loaded and validated  
#                 - All analysis pages in the navigation menu become available  
#                 - Centrality, roles, communities, robustness, and optimization analyses can be performed  
                
#                 ---
                
#                 ### No file uploaded yet
                
#                 If no file is uploaded, the analysis pages remain inactive.  
#                 Once a valid `.mtx` file is provided, you can immediately continue with the next steps.
                
#                 ---
                
#                 ### Tip
                
#                 If you are unsure about the file format or interpretation of results, consult the **User Manual** in the navigation menu for detailed explanations and examples.
#             """
#         )

#     # Initialise session state
#     init_state()
#     # File uploader
#     # uploaded_file = st.file_uploader("Upload a Matrix Market (.mtx) file", type=["mtx"])
#     uploaded_file = st.file_uploader(
#         "Upload a Matrix Market (.mtx) file",
#         type=["mtx"],
#         help="""
#     What is a .mtx file?
#     Upload a Matrix Market (.mtx) file representing a network adjacency matrix.
    
#     Rows and columns correspond to nodes; non-zero entries indicate connections.
    
#     After upload, the graph will be loaded and all analysis pages become available.
#     """
#     )


#     if uploaded_file is not None:
#         try:
#             # Load adjacency matrix
#             adjacency = load_mtx(uploaded_file)
#             # st.write(adjacency)
#             # Build graph (assume undirected by default)
#             G = build_graph(adjacency, directed=False)
#             # Validate graph
#             stats = validate_graph(G)
#             # Store in session state
#             set_state("graph", G)
#             set_state("adjacency", adjacency)
#             # Show summary metrics
#             basic = basic_statistics(G)
#             st.subheader("Network Summary")
#             cols = st.columns(4)
#             cols[0].metric("Nodes", basic["N"])
#             cols[1].metric("Edges", basic["E"])
#             cols[2].metric("Density", f"{basic['density']:.3f}")
#             cols[3].metric("Components", basic["components"])
#             # Symmetry and self-loop warnings
#             if not stats["symmetric"]:
#                 st.warning("Adjacency matrix is not symmetric.  Edges may be directed.")
#             if stats["self_loops"]:
#                 st.warning("Graph contains self loops.  They have been removed.")
#             if not stats["connected"]:
#                 st.info("Graph is not connected.  Analyses will operate on the entire graph but some metrics (e.g. Kemeny) will use the largest component.")
#             # Plot the graph
#             st.subheader("Network Graph")
            
#             col_left, col_right = st.columns([3, 2], gap="large")
#             with col_left:
#                 display_network(G, title="Base network")
                
#         except Exception as e:
#             st.error(f"Failed to load network: {e}")
#     else:
#         st.info("Please upload a `.mtx` file to begin the analysis.")


# if __name__ == "__main__":
#     page()



"""Streamlit page: Upload & Overview.

This page allows the user to upload a `.mtx` file, validates it and
computes basic statistics.  It also displays a baseline network plot
with no particular sizing or colouring.  Once the graph is loaded,
subsequent pages can access it via `st.session_state`.

Note on "remembering" uploads:
- Streamlit cannot prefill `st.file_uploader` with a previously uploaded file.
- We can still remember the uploaded network by storing the parsed adjacency
  (and graph) in session state, plus showing the stored filename above the uploader.
"""

from __future__ import annotations

import io
import hashlib
from typing import Optional

import streamlit as st
import pandas as pd  # kept because it was in your original file (may be used elsewhere)

from scipy import sparse
import numpy as np

from dss.ui.state import init_state, set_state, get_state
from dss.utils.io_mtx import load_mtx
from dss.graph.build_graph import build_graph
from dss.graph.stats import basic_statistics
from dss.utils.validation import validate_graph
from dss.utils.plotting import plot_network  # kept because it was in your original file (may be used elsewhere)
from dss.graph.layouts import compute_layout  # kept because it was in your original file (may be used elsewhere)
from dss.ui.components import display_network


def _sha256(data: bytes) -> str:
    """Compute a stable hash for change detection."""
    return hashlib.sha256(data).hexdigest()


def _serialize_adjacency(adjacency) -> bytes:
    """Serialize adjacency so it can be restored later in the same session."""
    buf = io.BytesIO()
    if sparse.issparse(adjacency):
        sparse.save_npz(buf, adjacency)
    else:
        np.save(buf, np.asarray(adjacency))
    return buf.getvalue()


def _deserialize_adjacency(data: bytes):
    """Deserialize adjacency bytes back to a matrix (sparse npz first, then numpy)."""
    buf = io.BytesIO(data)
    try:
        buf.seek(0)
        return sparse.load_npz(buf)
    except Exception:
        buf.seek(0)
        return np.load(buf, allow_pickle=False)


def _clear_loaded_network_state() -> None:
    """Clear the stored upload and all derived analysis results."""
    # Stored upload metadata and payload
    set_state("mtx_name", None)
    set_state("mtx_sha256", None)
    set_state("adjacency_bytes", None)

    # Live objects
    set_state("graph", None)
    set_state("adjacency", None)

    # Derived results that depend on the graph
    set_state("centrality_table", None)
    set_state("centrality_result", None)
    set_state("role_result", None)
    set_state("community_results", {})
    set_state("kemeny_result", None)
    set_state("arrest_result", None)

    # Reset uploader widget (so UI truly clears)
    st.session_state["mtx_uploader"] = None


def page() -> None:
    st.set_page_config(page_title="Upload & Overview", layout="wide")
    st.title("Upload & Overview")

    with st.expander("Quick User Guide", expanded=False):
        st.markdown(
            """
                ### Welcome

                This dashboard allows you to analyze network structures using advanced graph-based methods.  
                Everything starts by uploading a network file.

                ---

                ### What to upload

                Upload a **Matrix Market (.mtx)** file that represents a network adjacency matrix.

                - Each row and column corresponds to a node  
                - Non-zero values indicate connections between nodes  

                ---

                ### What happens next

                After uploading the file:

                - The network is automatically loaded and validated  
                - All analysis pages in the navigation menu become available  
                - Centrality, roles, communities, robustness, and optimization analyses can be performed  

                ---

                ### No file uploaded yet

                If no file is uploaded, the analysis pages remain inactive.  
                Once a valid `.mtx` file is provided, you can immediately continue with the next steps.

                ---

                ### Tip

                If you are unsure about the file format or interpretation of results, consult the **User Manual** in the navigation menu for detailed explanations and examples.
            """
        )

    # Initialise session state
    init_state()

    # Ensure these keys exist even if state.py hasn't been updated yet.
    # This keeps backward compatibility with your current state.py defaults.
    if "mtx_name" not in st.session_state:
        st.session_state["mtx_name"] = None
    if "mtx_sha256" not in st.session_state:
        st.session_state["mtx_sha256"] = None
    if "adjacency_bytes" not in st.session_state:
        st.session_state["adjacency_bytes"] = None

    # If a network is already stored in session state, show it above the uploader.
    stored_name = get_state("mtx_name")
    stored_adj_bytes = get_state("adjacency_bytes")

    if stored_name and stored_adj_bytes:
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.success(f"Stored network file: {stored_name}")
        with header_cols[1]:
            if st.button("Clear stored file"):
                _clear_loaded_network_state()
                st.rerun()

    # File uploader (cannot be prefilled by Streamlit)
    uploaded_file = st.file_uploader(
        "Upload a Matrix Market (.mtx) file",
        type=["mtx"],
        key="mtx_uploader",
        help="""
    What is a .mtx file?
    Upload a Matrix Market (.mtx) file representing a network adjacency matrix.

    Rows and columns correspond to nodes; non-zero entries indicate connections.

    After upload, the graph will be loaded and all analysis pages become available.
    """,
    )

    # Decide which adjacency/graph to use:
    # - If user uploads a file now, that replaces the stored one.
    # - Else if we have stored adjacency bytes, restore from that.
    adjacency = None
    G = None

    if uploaded_file is not None:
        try:
            # Read bytes once so we can detect changes and store the "remembered" version
            file_bytes = uploaded_file.getvalue()
            file_hash = _sha256(file_bytes)
            file_name = uploaded_file.name

            # Load adjacency matrix from bytes
            adjacency = load_mtx(io.BytesIO(file_bytes))

            # Build graph (assume undirected by default)
            G = build_graph(adjacency, directed=False)

            # Persist in session state so it is available when you navigate away and back
            set_state("mtx_name", file_name)
            set_state("mtx_sha256", file_hash)
            set_state("adjacency_bytes", _serialize_adjacency(adjacency))

            # Store live objects too (fast path for other pages)
            set_state("graph", G)
            set_state("adjacency", adjacency)

            # Reset derived results because the input graph changed
            set_state("centrality_table", None)
            set_state("centrality_result", None)
            set_state("role_result", None)
            set_state("community_results", {})
            set_state("kemeny_result", None)
            set_state("arrest_result", None)

        except Exception as e:
            st.error(f"Failed to load network: {e}")
            return

    elif stored_adj_bytes:
        # No new upload this run, but we have a stored adjacency to restore
        try:
            adjacency = _deserialize_adjacency(stored_adj_bytes)
            G = build_graph(adjacency, directed=False)

            # Keep live objects available (in case other pages expect them)
            set_state("graph", G)
            set_state("adjacency", adjacency)

        except Exception as e:
            st.error(f"Failed to restore stored network: {e}")
            _clear_loaded_network_state()
            return

    # If we still have no graph, show the original info message
    if G is None:
        st.info("Please upload a `.mtx` file to begin the analysis.")
        return

    # From here on: identical behavior to your original page (stats, warnings, plot)
    try:
        # Validate graph
        stats = validate_graph(G)

        # Show summary metrics
        basic = basic_statistics(G)
        st.subheader("Network Summary")
        cols = st.columns(4)
        cols[0].metric("Nodes", basic["N"])
        cols[1].metric("Edges", basic["E"])
        cols[2].metric("Density", f"{basic['density']:.3f}")
        cols[3].metric("Components", basic["components"])

        # Symmetry and self-loop warnings
        if not stats["symmetric"]:
            st.warning("Adjacency matrix is not symmetric.  Edges may be directed.")
        if stats["self_loops"]:
            st.warning("Graph contains self loops.  They have been removed.")
        if not stats["connected"]:
            st.info(
                "Graph is not connected.  Analyses will operate on the entire graph but some metrics "
                "(e.g. Kemeny) will use the largest component."
            )

        # Plot the graph
        st.subheader("Network Graph")
        col_left, col_right = st.columns([3, 2], gap="large")
        with col_left:
            display_network(G, title="Base network")

    except Exception as e:
        st.error(f"Failed to load network: {e}")


if __name__ == "__main__":
    page()







