"""Help / Tutorial page.

A single, scrollable English guide to the whole application: what RePrint
is, a quick start, a walkthrough of every page, the input file format, the
bundled datasets, a parameter reference, and troubleshooting.

Anything that can be derived from the app's own configuration (bundled
files, example datasets, defaults) is read from it, so this page cannot
drift away from what the other pages actually offer.
"""

from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from pages.nav import navbar, license_footer, REPO_URL
from utils.utils import (FILES, DEFAULT_SIGNATURES, DEFAULT_LINKAGE_METHOD,
                         linkage_methods, example_set_options,
                         LEGIBLE_SIGNATURE_LIMIT, PAPER_GOLD_STANDARD_GROUPS)
from utils.community import DEFAULT_K

PAPER_TITLE = "Toward identification of common DNA repair process in mutational signatures"
PAPER_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC12873990/"

# ============================================================================
# STYLING CONFIGURATION (same palette as the other pages)
# ============================================================================
COLORS = {
    "primary_blue": "#2563EB",
    "primary_dark": "#1e40af",
    "bg_light": "#F8FAFC",
    "bg_lighter": "#F0F5FB",
    "white": "#FFFFFF",
    "navy": "#1E293B",
    "teal": "#14B8A6",
    "red": "#E11D48",
    "text_primary": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
}

CARD_STYLE = {
    "backgroundColor": COLORS["white"],
    "border": f"1px solid {COLORS['border']}",
    "boxShadow": COLORS["shadow"],
    "marginBottom": "2rem",
    "padding": "2rem",
    "borderRadius": "0.75rem",
    # Anchor targets sit below the sticky-looking header when jumped to;
    # a little scroll margin keeps the section title visible.
    "scrollMarginTop": "1.5rem",
}

INFO_CARD_STYLE = {
    "backgroundColor": "#F0F9FF",
    "border": "1px solid #BFDBFE",
    "borderRadius": "0.5rem",
    "padding": "1rem 1.25rem",
    "marginTop": "1rem",
}

PRE_STYLE = {
    "whiteSpace": "pre",
    "tabSize": 12,
    "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
    "fontSize": "0.85rem",
    "backgroundColor": COLORS["bg_light"],
    "padding": "0.75rem 1rem",
    "borderRadius": "0.375rem",
    "border": f"1px solid {COLORS['border']}",
    "overflowX": "auto",
    "margin": "0.5rem 0 0 0",
}

TEXT = {"fontSize": "0.95rem", "color": COLORS["text_primary"], "lineHeight": 1.6}

# The pages this guide describes, in navbar order. Keep in sync with
# pages/nav.py and the routes in app.py.
PAGES = [
    {
        "anchor": "help-start-page",
        "icon": "tabler:home-2",
        "name": "Start page",
        "path": "/",
        "summary": "Clustered similarity heatmaps of the original signatures and of their RePrints, side by side.",
    },
    {
        "anchor": "help-reprints-charts",
        "icon": "tabler:chart-bar",
        "name": "RePrints charts",
        "path": "/page1",
        "summary": "Per-signature bar plots: the 96-context mutation profile next to its RePrint footprint.",
    },
    {
        "anchor": "help-merge-signatures",
        "icon": "tabler:git-merge",
        "name": "Merge signatures",
        "path": "/page3",
        "summary": "Place your own (query) signatures on a dendrogram of a reference catalogue such as COSMIC.",
    },
    {
        "anchor": "help-community-detection",
        "icon": "tabler:affiliate",
        "name": "Community Detection",
        "path": "/community",
        "summary": "Group signatures with a mutual k-nearest-neighbour graph and the Louvain algorithm.",
    },
]

TOC = [
    ("help-what-is-reprint", "What is RePrint?"),
    ("help-quick-start", "Quick start"),
    ("help-pages", "The four pages"),
    ("help-file-format", "Input file format"),
    ("help-datasets", "Bundled datasets"),
    ("help-parameters", "Parameter reference"),
    ("help-reading-plots", "Reading the plots"),
    ("help-exporting", "Exporting results"),
    ("help-troubleshooting", "Troubleshooting"),
    ("help-citation", "Citation and source code"),
]


# ============================================================================
# Small layout helpers
# ============================================================================

def section_title(text, icon, anchor):
    """Section heading with an anchor id so the table of contents can jump to it."""
    return html.Div(
        id=anchor,
        style={"display": "flex", "alignItems": "center", "gap": "0.75rem", "marginBottom": "1rem",
               "scrollMarginTop": "1.5rem"},
        children=[
            DashIconify(icon=icon, width=24, height=24, color=COLORS["primary_blue"]),
            html.H2(text, style={"margin": 0, "fontSize": "1.4rem"}),
        ],
    )


def sub_title(text):
    return html.H6(text, style={"fontWeight": "600", "marginTop": "1.25rem", "marginBottom": "0.5rem",
                                "fontSize": "1rem"})


def p(*children):
    return html.P(list(children), style={**TEXT, "marginBottom": "0.75rem"})


def li(*children):
    return html.Li(list(children), style={**TEXT, "marginBottom": "0.5rem"})


def ul(items):
    return html.Ul([li(*i) if isinstance(i, (list, tuple)) else li(i) for i in items],
                   style={"paddingLeft": "1.5rem", "marginBottom": "0.75rem"})


def ol(items):
    return html.Ol([li(*i) if isinstance(i, (list, tuple)) else li(i) for i in items],
                   style={"paddingLeft": "1.5rem", "marginBottom": "0.75rem"})


def button_name(label):
    """Inline rendering of a button the user will see in the UI."""
    return html.Code(label, style={
        "backgroundColor": COLORS["bg_lighter"],
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "0.25rem",
        "padding": "0.05rem 0.4rem",
        "fontSize": "0.85em",
        "color": COLORS["primary_dark"],
        "fontFamily": "inherit",
        "fontWeight": 600,
    })


def code(text):
    return html.Code(text, style={"fontSize": "0.85em"})


def page_link(name, path):
    return dcc.Link(name, href=path, style={"fontWeight": 600})


def table(header, rows, first_col_width=None):
    """Plain HTML table styled like the rest of the app."""
    th_style = {"textAlign": "left", "padding": "0.5rem 0.75rem", "borderBottom": f"2px solid {COLORS['border']}",
                "fontSize": "0.85rem", "color": COLORS["text_secondary"], "textTransform": "uppercase",
                "letterSpacing": "0.03em", "whiteSpace": "nowrap"}
    td_style = {"padding": "0.6rem 0.75rem", "borderBottom": f"1px solid {COLORS['border']}",
                "fontSize": "0.92rem", "color": COLORS["text_primary"], "verticalAlign": "top",
                "lineHeight": 1.5}
    body = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            style = dict(td_style)
            if i == 0:
                style["fontWeight"] = 600
                if first_col_width:
                    style["width"] = first_col_width
            cells.append(html.Td(cell, style=style))
        body.append(html.Tr(cells))
    return html.Div(
        style={"overflowX": "auto", "marginTop": "0.75rem"},
        children=html.Table(
            [html.Thead(html.Tr([html.Th(h, style=th_style) for h in header])), html.Tbody(body)],
            style={"width": "100%", "borderCollapse": "collapse"},
        ),
    )


def card(*children, style=None):
    return dmc.Card(children=list(children), style={**CARD_STYLE, **(style or {})})


# ============================================================================
# Derived content (kept in sync with the app's configuration)
# ============================================================================

EXAMPLE_SETS = example_set_options()

_cosmic_files = [f for f in FILES if f.startswith('COSMIC')]
_other_files = [f for f in FILES if not f.startswith('COSMIC')]
_cosmic_versions = sorted({f.split('_')[1] for f in _cosmic_files},
                          key=lambda v: [int(x) for x in v.lstrip('v').split('.')])
_cosmic_builds = sorted({f.rsplit('_', 1)[1].replace('.txt', '') for f in _cosmic_files})

_gold_rows = [
    (g['name'], g['pathway'], ", ".join(g['members'])) for g in PAPER_GOLD_STANDARD_GROUPS
]


# ============================================================================
# Sections
# ============================================================================

hero = dmc.Card(
    style={
        **CARD_STYLE,
        "background": f"linear-gradient(135deg, {COLORS['primary_blue']} 0%, {COLORS['primary_dark']} 100%)",
        "color": "white",
        "border": "none",
    },
    children=[
        dmc.Group(
            gap="md",
            align="center",
            children=[
                DashIconify(icon="tabler:help-circle", width=40, height=40, color="white"),
                html.Div([
                    html.H1("Help & Tutorial", style={"color": "white", "margin": 0, "fontSize": "2rem"}),
                    dmc.Text(
                        "How to use RePrint to compare mutational signatures and their DNA repair footprints.",
                        size="md", style={"color": "rgba(255,255,255,0.9)", "marginTop": "0.25rem"},
                    ),
                ]),
            ],
        ),
        html.Div(
            style={"display": "flex", "flexWrap": "wrap", "gap": "0.5rem", "marginTop": "1.5rem"},
            children=[
                html.A(
                    label,
                    href=f"#{anchor}",
                    style={
                        "color": "white",
                        "backgroundColor": "rgba(255,255,255,0.15)",
                        "border": "1px solid rgba(255,255,255,0.35)",
                        "borderRadius": "999px",
                        "padding": "0.3rem 0.85rem",
                        "fontSize": "0.85rem",
                        "fontWeight": 600,
                        "textDecoration": "none",
                    },
                )
                for anchor, label in TOC
            ],
        ),
    ],
)


what_is_reprint = card(
    section_title("What is RePrint?", "tabler:dna-2", "help-what-is-reprint"),
    p("A ", html.Strong("mutational signature"), " is a probability distribution over the 96 single-base "
      "substitution (SBS) types: the six substitutions C>A, C>G, C>T, T>A, T>C, T>G, each seen in its 16 "
      "possible trinucleotide contexts (the bases immediately 5' and 3' of the mutated base). "
      "Signature catalogues such as COSMIC describe each signature as one such 96-element vector."),
    p("A signature mixes two things: ", html.Em("which contexts get damaged"), " and ",
      html.Em("which substitution the damage ends up as"), " after DNA repair has acted on it. "
      "RePrint (", html.Strong("Repair Print"), ") isolates the second part. For every context it "
      "divides the probability of one substitution by the total probability of all three substitutions "
      "of the same reference base in the same context:"),
    html.Pre(
        "RePrint( L[X>Y]R ) = p( L[X>Y]R ) / ( p( L[X>A]R ) + p( L[X>C]R ) + p( L[X>G]R ) + p( L[X>T]R ) )\n"
        "                                   (the term with Z = X does not exist and is skipped)",
        style=PRE_STYLE,
    ),
    p("The result is the conditional probability of the outcome Y given that base X in context L_R was "
      "mutated at all. Context preference, which is largely a property of the damaging agent, cancels out. "
      "What remains reflects how the lesion was processed, so signatures that share a DNA repair pathway "
      "tend to have similar RePrints even when their original 96-context profiles look different. "
      "This is the observation the RePrint paper builds on, and every page of this app shows the two "
      "representations next to each other so you can see where they agree and where they diverge."),
    html.Div(
        style=INFO_CARD_STYLE,
        children=[
            dmc.Group(gap="xs", align="flex-start", wrap="nowrap", children=[
                DashIconify(icon="tabler:info-circle", width=18, color="#0369A1", style={"flexShrink": 0, "marginTop": "0.2rem"}),
                html.Div([
                    p(html.Strong("Epsilon. "),
                      "Before the ratio is taken, a small pseudo-count ε (default 1e-4) is added to every "
                      "probability. It keeps contexts with zero counts from producing undefined ratios and "
                      "dampens noise in rare contexts. You can change it under ",
                      button_name("Advanced Options"), " on every page."),
                ]),
            ]),
        ],
    ),
)


quick_start = card(
    section_title("Quick start", "tabler:rocket", "help-quick-start"),
    p("The fastest way to see what the app does, in about a minute:"),
    ol([
        ["Open the ", page_link("Start page", "/"), ". It loads the bundled ", code(DEFAULT_SIGNATURES),
         " reference catalogue with all of its signatures selected."],
        ["Under the upload box, pick ", html.Strong(EXAMPLE_SETS[0]['label']), " in the ",
         html.Em("Load a published dataset"), " selector and click ", button_name("Load dataset"),
         ". This is the set of reference clusters from the paper, so the heatmaps have a known answer to compare against."],
        ["Click ", button_name("Reload Heatmaps"), ". Two clustered heatmaps appear: ",
         html.Strong("Signature Similarity"), " (distances between the original signatures) and ",
         html.Strong("RePrint Similarity"), " (distances between their RePrints)."],
        ["Open ", button_name("Advanced Options"), " and switch on ",
         html.Em("Annotate the paper's gold-standard groups"),
         ". The strip above each heatmap is now coloured by the expected repair-pathway group. "
         "Compare how well the dendrogram of each heatmap recovers those groups."],
        ["Click ", button_name("Download Reprints"), " to get the RePrint matrix as CSV, or use the camera "
         "icon in the top-right corner of any plot to save it as PNG."],
    ]),
    p("To analyse your own data, drop a file into the upload box instead of loading a dataset. "
      "The required layout is described under ", html.A("Input file format", href="#help-file-format"), "."),
)


pages_overview = card(
    section_title("The four pages", "tabler:layout-grid", "help-pages"),
    p("Each page takes the same kind of input (a table of signatures) and shows the original signatures "
      "and their RePrints side by side, but answers a different question."),
    dmc.Grid(
        gutter="md",
        children=[
            dmc.GridCol(
                span={"base": 12, "sm": 6},
                children=dmc.Paper(
                    p="md", radius="md",
                    style={"backgroundColor": COLORS["bg_lighter"], "border": f"1px solid {COLORS['border']}", "height": "100%"},
                    children=[
                        dmc.Group(gap="xs", align="center", children=[
                            DashIconify(icon=pg["icon"], width=20, color=COLORS["primary_blue"]),
                            dcc.Link(pg["name"], href=pg["path"], style={"fontWeight": 700, "fontSize": "1rem"}),
                            dmc.Badge(pg["path"], size="xs", variant="light", color="gray",
                                      style={"background": "none", "color": COLORS["text_secondary"], "boxShadow": "none"}),
                        ]),
                        dmc.Text(pg["summary"], size="sm", style={"marginTop": "0.5rem", "color": COLORS["text_primary"]}),
                        html.A("Read more", href=f"#{pg['anchor']}", style={"fontSize": "0.85rem", "display": "inline-block", "marginTop": "0.5rem"}),
                    ],
                ),
            )
            for pg in PAGES
        ],
    ),

    # ---- Start page --------------------------------------------------------
    html.Div(id="help-start-page", style={"scrollMarginTop": "1.5rem"}),
    sub_title("Start page — clustered similarity heatmaps"),
    p("Computes a pairwise distance matrix between the selected signatures, clusters it hierarchically "
      "and draws the matrix as a heatmap with the dendrogram on top. The same is done for the RePrints "
      "of those signatures, so the two heatmaps can be compared directly."),
    ul([
        [html.Strong("Data source. "), "Either a bundled reference catalogue (", html.Em("Change Reference File"),
         "), one of the published example sets (", html.Em("Load a published dataset"), "), or files you upload. "
         "Uploading or loading a dataset replaces the reference dropdown; ", button_name("Clear Uploaded Signatures"),
         " brings it back."],
        [html.Strong("Select Signatures. "), "Deselect signatures to focus the heatmap. Above ",
         str(LEGIBLE_SIGNATURE_LIMIT), " signatures the labels become hard to read and a warning is shown."],
        [html.Strong("Reload Heatmaps. "), "Recomputes both figures. Changing any parameter, the signature "
         "selection or the data source clears the plots until you click it again, so what you see always "
         "matches the current settings."],
        [html.Strong("Advanced Options. "), "Distance metric, clustering (linkage) method, epsilon, the "
         "dendrogram cut threshold that defines the coloured cluster strip, and the gold-standard annotation switch."],
        [html.Strong("Hide Heatmap Visualization. "), "Replaces each heatmap with a standalone dendrogram, "
         "which is easier to read for large sets."],
        [html.Strong("Downloads. "), button_name("Download Reprints"), " (RePrint matrix, CSV) and ",
         button_name("Download Signatures"), " (the selected original signatures, CSV)."],
    ]),

    # ---- RePrints charts ----------------------------------------------------
    html.Div(id="help-reprints-charts", style={"scrollMarginTop": "1.5rem"}),
    sub_title("RePrints charts — one signature at a time"),
    p("Shows, for every selected signature, the familiar 96-bar mutation profile on the left and its "
      "RePrint footprint on the right. Use it to look at what the transformation does to a specific signature."),
    ul([
        [html.Strong("Original. "), "Bars are the signature's probabilities, grouped by the six substitution "
         "types in the usual COSMIC colours, one bar per trinucleotide context."],
        [html.Strong("RePrint. "), "Three panels, one per possible outcome of a mutated C (top) and of a "
         "mutated T (bottom). Within each context the three outcome probabilities sum to one, so the plot "
         "reads as \"given that this base was hit in this context, what did it become?\"."],
        [html.Strong("Pagination. "), "Five signatures are shown per page; use ", button_name("Previous"),
         " and ", button_name("Next"), " below the plots."],
        [html.Strong("Generate Plots. "), "Redraws after you change the reference file, upload a file or "
         "edit epsilon. This page accepts a single uploaded file."],
    ]),

    # ---- Merge signatures --------------------------------------------------
    html.Div(id="help-merge-signatures", style={"scrollMarginTop": "1.5rem"}),
    sub_title("Merge signatures — reference base vs. query signatures"),
    p("Answers \"which known signature is my signature closest to?\". The reference catalogue is "
      "clustered into a dendrogram; each uploaded query signature is then matched to its nearest "
      "reference signature and written next to that leaf as ", code("query → reference"),
      ". A second dendrogram does the same in RePrint space, so you can check whether the nearest "
      "neighbour is the same in both representations."),
    ul([
        [html.Strong("Reference Signatures. "), "Pick the catalogue and, optionally, narrow the signatures "
         "that go into the dendrogram."],
        [html.Strong("Query Signatures. "), "Upload one file. Its columns are added to the selector with "
         "the reference signatures; the upload is matched on the ", code("Type"), " column, so only the 96 "
         "mutation types present in both tables are used."],
        [html.Strong("Advanced Options. "), "Distance metric, linkage method and epsilon. Click ",
         button_name("Generate plots"), " after any change."],
    ]),

    # ---- Community Detection -----------------------------------------------
    html.Div(id="help-community-detection", style={"scrollMarginTop": "1.5rem"}),
    sub_title("Community Detection — graph-based grouping"),
    p("An alternative to cutting a dendrogram. Every signature is connected to its k most similar "
      "neighbours; with ", html.Em("Mutual neighbours only"), " an edge is kept only when both signatures "
      "chose each other. The Louvain algorithm then partitions this graph into communities by maximising "
      "modularity. Because the neighbourhood criterion is local, a tightly packed family and a looser one "
      "can both survive at the same k, which a single global distance cutoff cannot do."),
    ul([
        [html.Strong("Default data. "), "The page opens with the ", html.Em(EXAMPLE_SETS[-1]['label']),
         " example already loaded: COSMIC v2 plus three DNA-repair knockouts, small enough to read at a "
         "glance. Upload your own files or pick a reference catalogue to replace it."],
        [html.Strong("Detect Communities. "), "Runs Louvain on the signature graph and on the RePrint graph. "
         "Nodes are coloured by community; the members of each community are listed under the plot together "
         "with the modularity score."],
        [html.Strong("Advanced Options. "), "Distance metric, epsilon, Louvain resolution, k, the mutual "
         "switch and a random seed for reproducible runs."],
        [html.Strong("Download Community Assignments. "), "A CSV with one row per signature and the "
         "community it landed in for the signatures and for the RePrints."],
    ]),
)


file_format = card(
    section_title("Input file format", "tabler:file-spreadsheet", "help-file-format"),
    p("All upload boxes expect the same layout: a text table with one row per mutation type and one column "
      "per signature."),
    ul([
        [html.Strong("Separator. "), "Tab-separated for ", code(".txt"), " and ", code(".tsv"),
         "; comma-separated for ", code(".csv"), "."],
        [html.Strong("Type column. "), "The first column must be named ", code("Type"),
         " and hold the mutation types in the ", code("L[X>Y]R"), " notation, e.g. ", code("A[C>A]A"),
         ". A CSV whose first column has no header (as some organ-specific signature exports do) is accepted "
         "and treated as ", code("Type"), "."],
        [html.Strong("Rows. "), "The 96 SBS types. Order does not matter; rows are aligned by name."],
        [html.Strong("Signature columns. "), "Any header (", code("SBS1"), ", ", code("MySample"), ", ",
         code("Cisplatin (12.5 uM)"), " ...). Values are probabilities or frequencies; each column is "
         "normally scaled to sum to 1, but RePrint itself is a ratio within each context and does not "
         "depend on that scale."],
        [html.Strong("Several files at once. "), "On the Start page and the Community Detection page you can "
         "select multiple files. They are merged on ", code("Type"), " (outer join, missing values filled "
         "with 0). If two files contain a column with the same name, the second one is prefixed with its "
         "file name, e.g. ", code("Zou2018-signatures.SBS-96_SBS1"), "."],
    ]),
    p(html.Strong("Example (tab-separated):")),
    html.Pre(
        "Type\tSBS1\tSBS2\tSBS3\n"
        "A[C>A]A\t0.000876\t0.000001\t0.020920\n"
        "A[C>A]C\t0.002220\t0.000146\t0.016343\n"
        "A[C>A]G\t0.000180\t0.000053\t0.001808\n"
        "...\t...\t...\t...\n"
        "T[T>G]T\t0.000375\t0.000038\t0.002468",
        style=PRE_STYLE,
    ),
    p("Any of the bundled files in the ", code("data/signatures/"), " folder of the repository is a valid "
      "template."),
)


datasets = card(
    section_title("Bundled datasets", "tabler:database", "help-datasets"),
    sub_title("Reference catalogues (Change Reference File)"),
    p("COSMIC SBS catalogues ", html.Strong(", ".join(_cosmic_versions)), " for the ",
      html.Strong(" and ".join(_cosmic_builds)), " genome builds, plus:"),
    ul([[code(f), " — ", {
        'transcribed.txt': "SBS signatures restricted to the transcribed strand.",
        'untranscribed.txt': "SBS signatures restricted to the untranscribed strand.",
    }.get(f, "additional bundled signature table.")] for f in _other_files]),
    p("The default is ", code(DEFAULT_SIGNATURES), "."),

    sub_title("Published example sets (Load a published dataset)"),
    p("Signature matrices from the RePrint paper, stored in ", code("data/signatures/paper/"),
      " and merged on ", code("Type"), " exactly like uploaded files would be:"),
    table(
        ["Dataset", "Signatures", "Contents"],
        [(s['label'], str(s['count']), s['blurb']) for s in EXAMPLE_SETS],
        first_col_width="18rem",
    ),

    sub_title("Gold-standard groups"),
    p("The paper's reference clusters: signatures that are known to share a DNA repair pathway. On the "
      "Start page, the ", html.Em("Annotate the paper's gold-standard groups"), " switch colours the strip "
      "above the heatmap by these groups so you can judge a clustering against them."),
    table(["Group", "Pathway", "Members"], _gold_rows, first_col_width="10rem"),
)


parameters = card(
    section_title("Parameter reference", "tabler:adjustments", "help-parameters"),
    p("All of these live under ", button_name("Advanced Options"), " on the respective page. "
      "After changing one, click the page's red action button to recompute."),

    sub_title("Distance metric (all pages)"),
    table(
        ["Metric", "What it measures", "Notes"],
        [
            ("RMSE", "Root mean square error between the two 96-element vectors.",
             "Default, and the metric reported in the paper. Lower is more similar."),
            ("Cosine", "1 minus the cosine of the angle between the two vectors.",
             "Insensitive to overall scale; 0 means identical direction."),
            ("JS Divergence", "Jensen-Shannon divergence between the two vectors treated as distributions.",
             "Symmetric, bounded version of Kullback-Leibler divergence. Vectors are re-normalised to sum to 1 first."),
            ("Euclidean", "Heatmap shows RMSE; the dendrogram clusters the rows of the RMSE matrix by their Euclidean distance.",
             "Start page only. Groups signatures that have a similar distance profile to all other signatures, which is how "
             "plotly's default dendrogram treats a distance matrix."),
        ],
        first_col_width="9rem",
    ),

    sub_title("Clustering method (Start page, Merge signatures)"),
    p("The linkage rule used by hierarchical clustering to decide which clusters merge next. Start page offers ",
      ", ".join(linkage_methods), "; Merge signatures offers single, complete, average, weighted, centroid and median. "
      "Default: ", html.Strong(DEFAULT_LINKAGE_METHOD), "."),
    ul([
        [html.Strong("single: "), "distance between the closest pair of members. Tends to chain."],
        [html.Strong("complete: "), "distance between the farthest pair. Compact, evenly sized clusters."],
        [html.Strong("average: "), "mean distance between all pairs (UPGMA)."],
        [html.Strong("ward: "), "minimises within-cluster variance. Assumes Euclidean-like distances."],
        [html.Strong("weighted / centroid / median: "), "variants that weight sub-clusters equally or merge by "
         "centroid position."],
    ]),

    sub_title("Other parameters"),
    table(
        ["Parameter", "Page", "Effect"],
        [
            ("Epsilon (pseudo-count)", "all",
             "Added to every probability before RePrint is computed. Default 1e-4; allowed range 1e-10 to 1e-2. "
             "Larger values flatten RePrints of sparse signatures towards 1/3 per outcome."),
            ("Cluster granularity", "Start page",
             "Fraction of the dendrogram's tallest branch at which it is cut to colour the cluster strip. "
             "Default 0.7. Lower values split large clusters; higher values merge them. It changes the colouring only, "
             "not the dendrogram itself."),
            ("Annotate gold-standard groups", "Start page",
             "Colours the strip by the paper's reference groups instead of by the dendrogram cut. Only the "
             f"{sum(len(g['members']) for g in PAPER_GOLD_STANDARD_GROUPS)} annotated signatures are coloured."),
            ("Hide Heatmap Visualization", "Start page",
             "Shows a plain dendrogram instead of the heatmap."),
            ("Resolution", "Community Detection",
             "Louvain resolution parameter, 0.3 to 3.0, default 1.0. Above 1 favours more, smaller communities; "
             "below 1 fewer, larger ones."),
            ("Neighbours per signature (k)", "Community Detection",
             f"How many nearest neighbours each signature links to, 2 to 10, default {DEFAULT_K}. Raise it if many "
             "signatures end up isolated; lower it if everything collapses into one community."),
            ("Mutual neighbours only", "Community Detection",
             "Keep an edge only if both signatures rank each other in their top k. On by default and recommended; "
             "switching it off yields a denser graph."),
            ("Random seed", "Community Detection",
             "Fixes the randomness in Louvain and in the graph layout so a run can be reproduced. Default 42."),
        ],
        first_col_width="15rem",
    ),
)


reading_plots = card(
    section_title("Reading the plots", "tabler:chart-dots", "help-reading-plots"),
    sub_title("Similarity heatmaps (Start page)"),
    ul([
        ["Each cell is the distance between the signature in its row and the one in its column. ",
         html.Strong("Lighter is more similar"), " (smaller distance), darker is more different. The colour bar "
         "is labelled with the chosen metric."],
        ["Rows and columns are reordered by the dendrogram drawn above the matrix, so related signatures "
         "sit next to each other and similar groups show up as light blocks along the diagonal."],
        ["The thin coloured strip between the dendrogram and the matrix marks the clusters obtained by cutting "
         "the dendrogram at the ", html.Em("Cluster granularity"), " threshold, or the gold-standard groups "
         "when that switch is on."],
        ["The signature heatmap uses a green-blue palette and the RePrint heatmap an orange-red palette, "
         "the same as the paper's figures, so the two are easy to tell apart when placed side by side."],
        ["Hover a cell to read the exact pair of signatures and their distance. Drag to zoom into a region; "
         "double-click to reset."],
    ]),
    sub_title("Dendrograms (Merge signatures)"),
    ul([
        ["Leaves on the right are the reference signatures. The height at which two branches join is their "
         "distance under the chosen metric and linkage."],
        ["A label of the form ", code("MyQuery → SBS3"), " means the uploaded signature ", code("MyQuery"),
         " is closest to ", code("SBS3"), ". If the two dendrograms disagree, the query resembles one signature "
         "in its raw profile but another in how its lesions were repaired."],
    ]),
    sub_title("Community graphs (Community Detection)"),
    ul([
        ["Each node is a signature, coloured by the community it was assigned to. Edges are the (mutual) "
         "nearest-neighbour links the algorithm worked with; thicker edges are stronger similarities."],
        ["Communities are laid out as separate clusters so their membership is readable; distances on the "
         "canvas are not meaningful beyond that."],
        ["The modularity printed in the subtitle is the quality of the partition (higher means communities "
         "are denser inside than between). Signatures that had no mutual neighbour at the chosen k appear "
         "as isolated nodes."],
    ]),
)


exporting = card(
    section_title("Exporting results", "tabler:download", "help-exporting"),
    table(
        ["What", "Where", "Format"],
        [
            ("RePrint matrix", "Start page, RePrints charts → " + "Download Reprints",
             "CSV, 96 rows, one column per selected signature named reprint_<signature>. Uses the current epsilon."),
            ("Original signatures", "Start page, RePrints charts → Download Signatures",
             "CSV with the selected signature columns, as loaded (after merging, if several files were uploaded)."),
            ("Community assignments", "Community Detection → Download Community Assignments",
             "CSV with columns Signature, Community_Signatures, Community_RePrint."),
            ("Any figure as an image", "Camera icon in the toolbar that appears at the top-right of every plot",
             "PNG at 2× resolution. The toolbar also offers zoom, pan and reset."),
        ],
        first_col_width="13rem",
    ),
)


troubleshooting = card(
    section_title("Troubleshooting", "tabler:lifebuoy", "help-troubleshooting"),
    table(
        ["Symptom", "Cause and fix"],
        [
            ("The plot only says \"Click Reload Heatmaps\" (or \"Generate plots\", \"Detect Communities\")",
             "This is intentional. Whenever you change a parameter, the signature selection or the data, the "
             "previous result is cleared so it can never be mistaken for the current settings. Click the red "
             "button to recompute."),
            ("Upload fails with \"Uploaded file must include a 'Type' column\"",
             "The first column header must be exactly Type (or empty for CSV). Check that the separator matches "
             "the extension: tabs for .txt/.tsv, commas for .csv. Excel files are not accepted; export to CSV first."),
            ("A signature I uploaded is missing from the selector",
             "If two of the uploaded files share a column name, the later one is renamed with its file name as a "
             "prefix. Look for <file>_<signature> in the list."),
            ("Heatmap labels are unreadable",
             f"More than {LEGIBLE_SIGNATURE_LIMIT} signatures are selected. Deselect some in Select Signatures, "
             "load a smaller dataset, or switch on Hide Heatmap Visualization to get a plain dendrogram. The "
             "heatmap can also be scrolled horizontally and zoomed."),
            ("The dendrogram on Merge signatures is empty",
             "The query file must share its mutation types with the reference; the two tables are joined on "
             "Type and only common rows are kept. Check the L[X>Y]R notation and that all 96 types are present."),
            ("Everything ends up in one community / every signature is isolated",
             "Lower k (or raise the resolution) to split things up; raise k or switch off Mutual neighbours only "
             "to connect isolated signatures."),
            ("My uploaded data disappeared",
             "Uploads live in the browser's session storage. They survive page changes within the app but not a "
             "closed tab or a hard refresh. Use Clear Uploaded Signatures to remove them deliberately."),
            ("The reference file dropdown vanished",
             "It is hidden while uploaded or example data is active. Click Clear Uploaded Signatures to return "
             "to the bundled catalogues."),
        ],
        first_col_width="18rem",
    ),
)


citation = card(
    section_title("Citation and source code", "tabler:book", "help-citation"),
    p("If you use RePrint in your work, please cite the paper that introduced the method:"),
    html.Blockquote(
        [
            html.Em(PAPER_TITLE), html.Br(),
            html.A(PAPER_URL, href=PAPER_URL, target="_blank", rel="noopener noreferrer"),
        ],
        style={
            "borderLeft": f"4px solid {COLORS['primary_blue']}",
            "margin": "0 0 1rem 0",
            "padding": "0.5rem 1rem",
            "backgroundColor": COLORS["bg_lighter"],
            "borderRadius": "0 0.375rem 0.375rem 0",
            **TEXT,
        },
    ),
    p("The application is open source. Bug reports, feature requests and pull requests are welcome at ",
      html.A(REPO_URL, href=REPO_URL, target="_blank", rel="noopener noreferrer"), "."),
    p("Reference signatures are taken from the COSMIC Mutational Signatures catalogue; the mutagen exposure "
      "signatures come from Kucab et al. 2019 and the DNA-repair knockout signatures from Zou et al. 2018 and 2021."),
)


# ============================================================================
# PAGE LAYOUT
# ============================================================================
page_help_layout = html.Div([
    navbar,
    dmc.Container(
        size="xl",
        style={"backgroundColor": COLORS["bg_light"], "minHeight": "100vh", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            hero,
            what_is_reprint,
            quick_start,
            pages_overview,
            file_format,
            datasets,
            parameters,
            reading_plots,
            exporting,
            troubleshooting,
            citation,
        ],
    ),
    license_footer,
])
