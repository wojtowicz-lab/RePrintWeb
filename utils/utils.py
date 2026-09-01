import numpy as np
import pandas as pd

FILES = [
    'COSMIC_v3.6_SBS_GRCh38.txt',
    'COSMIC_v3.5_SBS_GRCh38.txt',
    'COSMIC_v3.4_SBS_GRCh38.txt',
    'COSMIC_v3.3.1_SBS_GRCh38.txt',
    'COSMIC_v3.2_SBS_GRCh38.txt',
    'COSMIC_v3.1_SBS_GRCh38.txt',
    'COSMIC_v3_SBS_GRCh38.txt',
    'COSMIC_v2_SBS_GRCh38.txt',
    'COSMIC_v1_SBS_GRCh38.txt',

    'COSMIC_v3.6_SBS_GRCh37.txt',
    'COSMIC_v3.5_SBS_GRCh37.txt',
    'COSMIC_v3.4_SBS_GRCh37.txt',
    'COSMIC_v3.3.1_SBS_GRCh37.txt',
    'COSMIC_v3.2_SBS_GRCh37.txt',
    'COSMIC_v3.1_SBS_GRCh37.txt',
    'COSMIC_v3_SBS_GRCh37.txt',
    'COSMIC_v2_SBS_GRCh37.txt',
    'COSMIC_v1_SBS_GRCh37.txt',
    'transcribed.txt',
    'untranscribed.txt'
]

DEFAULT_SIGNATURES = 'COSMIC_v3.4_SBS_GRCh38.txt'


linkage_methods = ['single', 'complete', 'average', 'ward']

DEFAULT_LINKAGE_METHOD = 'complete'

def normalize(data):
    return (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))

def calculate_rmse(x, y):
    """Root mean square error between two signature vectors.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return np.sqrt(np.nanmean((x - y) ** 2))

def calculate_cosine(x, y):
    return 1-np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))

def calculate_kl_divergence(x, y):
    """
    Calculate KL divergence between two signature vectors.
    Normalizes vectors to probabilities before computation.
    """
    # Normalize to probabilities
    x_prob = x / np.sum(x) if np.sum(x) > 0 else x
    y_prob = y / np.sum(y) if np.sum(y) > 0 else y
    
    return kl_divergence(x_prob, y_prob)

def calculate_js_divergence(x, y):
    """
    Calculate Jensen-Shannon divergence between two signature vectors.
    Normalizes vectors to probabilities before computation.
    """
    # Normalize to probabilities
    x_prob = x / np.sum(x) if np.sum(x) > 0 else x
    y_prob = y / np.sum(y) if np.sum(y) > 0 else y
    
    return js_divergence(x_prob, y_prob)



def kl_divergence(p, q):
    """
    Computes the Kullback–Leibler divergence D_KL(P || Q).
    Assumes that p and q are probability vectors (summing to 1).
    """
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    
    # Small offset to avoid division by zero
    eps = 1e-12
    p = np.clip(p, eps, 1)
    q = np.clip(q, eps, 1)
    
    return np.sum(p * np.log(p / q))

def js_divergence(p, q):
    """
    Computes the Jensen–Shannon divergence (a symmetric version of KL).
    """
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    m = 0.5 * (p + q)
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def reprint(data, epsilon=10e-4):
    # Extracting mutation categories and their probabilities
    mutation_types = data.index
    signatures = data.columns

    # Initialize a dictionary to store the RePrint probabilities for each signature
    reprint_probabilities = {signature: {} for signature in signatures}

    # Iterate over each signature
    for signature in signatures:
        # Extract the probabilities for the current signature
        signature_probs = data[signature].values + epsilon

        # Iterate over each mutation type
        for idx, mutation in enumerate(mutation_types):
            # Split the mutation type to extract NL, X, Y, NR
            NL = mutation[0]
            NR = mutation[6]
            X, Y = mutation[2], mutation[4]

            # Compute the denominator: sum of probabilities for Z != X
            denominator = np.sum([signature_probs[j] for j in range(len(mutation_types))
                                  if mutation_types[j].startswith(f"{NL}[{X}>") and mutation_types[j].endswith(f"]{NR}")
                                  and mutation_types[j][4] != X])

            # Compute the RePrint probability for the current mutation
            reprint_prob = signature_probs[idx] / denominator if denominator != 0 else 0

            # Store the RePrint probability
            reprint_probabilities[signature][mutation] = reprint_prob

    # Convert the reprint_probabilities dictionary to a DataFrame for better readability
    reprint_df = pd.DataFrame(reprint_probabilities)
    return reprint_df

import base64
import io


def parse_signatures(contents, filename):
    content_type, content_string = contents.split(',')

    try:
        decoded = base64.b64decode(content_string)
        decoded_str = decoded.decode('utf-8')
        buffer = io.StringIO(decoded_str)

        # Choose parser based on extension
        if filename.endswith('.txt') or filename.endswith('.tsv'):
            df = pd.read_csv(buffer, sep='\t')
        elif filename.endswith('.csv'):
            df = pd.read_csv(buffer, sep=',', index_col=None)
        else:
            raise ValueError(f"Unsupported file format for file: {filename}")

        # Ensure we have a 'Type' column.
        # Some CSV files (e.g. organ signatures like Biliary_Signature.csv)
        # store mutation types in the first column without a proper header,
        # which pandas may name '' or 'Unnamed: 0'. In that case, treat it as 'Type'.
        if 'Type' not in df.columns:
            first_col = df.columns[0]
            if (isinstance(first_col, str)
                    and (first_col.strip() == '' or first_col.startswith('Unnamed:'))
               ):
                df = df.rename(columns={first_col: 'Type'})
            else:
                raise ValueError("Uploaded file must include a 'Type' column.")

        # Log basic information for debugging
        print(f"Parsed file: {filename}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Shape: {df.shape}")
        print("First few rows:")
        print(df.head())

        return df

    except Exception as e:
        print(f"Error parsing file {filename}: {str(e)}")
        raise ValueError(f"Error while parsing file {filename}: {str(e)}")


def _merge_signature_dataframes(named_dfs):
    """
    named_dfs: list of (filename, df) tuples, each df having a 'Type' column.

    Merges them into a single DataFrame aligned on 'Type' (outer join,
    missing values filled with 0). Column name collisions across files are
    disambiguated by prefixing the column with its source filename.

    Returns a DataFrame with 'Type' as a regular column (index reset).
    """
    dfs = []
    seen_columns = set()

    for filename, df in named_dfs:
        df = df.set_index('Type')
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        rename_map = {col: f"{base_name}_{col}" for col in df.columns if col in seen_columns}
        if rename_map:
            df = df.rename(columns=rename_map)
        seen_columns.update(df.columns)
        dfs.append(df)

    merged = pd.concat(dfs, axis=1, join='outer').fillna(0)
    merged.index.name = 'Type'
    return merged.reset_index()


def merge_uploaded_signatures(contents_list, filenames_list):
    """
    Parse one or more uploaded signature files and merge them into a single
    DataFrame indexed by mutation 'Type'. Files are aligned on 'Type' (outer
    join, missing values filled with 0). Column name collisions across files
    are disambiguated by prefixing the column with its source filename.

    Returns (merged_df, errors), where merged_df has 'Type' as a regular
    column (index reset) ready for to_dict('records'), and errors is a list
    of (filename, message) tuples for files that failed to parse. merged_df
    is None if every file failed.
    """
    named_dfs = []
    errors = []

    for content, filename in zip(contents_list, filenames_list):
        try:
            df = parse_signatures(content, filename)
        except Exception as e:
            errors.append((filename, str(e)))
            continue
        named_dfs.append((filename, df))

    if not named_dfs:
        return None, errors

    return _merge_signature_dataframes(named_dfs), errors


# ============================================================================
# Bundled example signature sets
# ============================================================================

PAPER_SIGNATURE_DIR = 'data/signatures/paper'
DEFAULT_SIGNATURE_DIR = 'data/signatures'

# Above this many signatures the heatmap's labels stop being legible; the UI
# warns rather than silently truncating the user's selection.
LEGIBLE_SIGNATURE_LIMIT = 60

EXAMPLE_SIGNATURE_SETS = {
    'paper_gold_standard': {
        'label': 'Paper - gold-standard clusters (39)',
        'blurb': "The paper's Table 1 reference clusters: COSMIC, mutagen exposures and "
                 "repair-gene knockouts that share a DNA repair pathway (MMRd, HRD, PAHs, "
                 "NitroPAHs, ROS, TMZ, Platinum, AAs).",
        'dir': PAPER_SIGNATURE_DIR,
        'files': ['RePrint_gold_standard_clusters.txt'],
    },
    'paper_mutagens_ko': {
        'label': 'Paper - mutagens + knockouts (35)',
        'blurb': '28 Kucab2019 environmental mutagen exposures merged with 7 Zou2021 '
                 'DNA-repair gene knockouts. No COSMIC signatures, so damage source and '
                 'repair deficiency can be compared directly.',
        'dir': PAPER_SIGNATURE_DIR,
        'files': [
            'RePrint_Kucab2019_mutagens.txt',
            'RePrint_Zou2021_repair_KO.txt',
        ],
    },
    'paper_cosmic': {
        'label': 'Paper - COSMIC v3.4 curated (67)',
        'blurb': 'COSMIC v3.4 (GRCh37) as used in the paper: the full catalogue minus the '
                 '19 signatures flagged as possible sequencing artefacts.',
        'dir': PAPER_SIGNATURE_DIR,
        'files': ['RePrint_COSMIC_v3.4_SBS_GRCh37.txt'],
    },
    'paper_full': {
        'label': 'Paper - full set (102)',
        'blurb': 'Everything the paper analysed: 67 curated COSMIC signatures, 28 mutagen '
                 'exposures and 7 repair-gene knockouts. Large - expect small labels; use '
                 'the signature selector to narrow it down.',
        'dir': PAPER_SIGNATURE_DIR,
        'files': [
            'RePrint_COSMIC_v3.4_SBS_GRCh37.txt',
            'RePrint_Kucab2019_mutagens.txt',
            'RePrint_Zou2021_repair_KO.txt',
        ],
    },
    # --- Other bundled sets -------------------------------------------------
    # COSMIC v2's 30 signatures plus the three Zou2018 knockouts. Small and
    # sparse enough that DNA-repair families stay separable: the mismatch-repair
    # signatures (6, 14, 15, 20, 21, 26) group with the MSH6 knockout, and
    # signatures 3 and 8 group with FANCC.
    'cosmic_v2_zou': {
        'label': 'COSMIC v2 + Zou2018 knockouts (33)',
        'blurb': '30 COSMIC v2 signatures and 3 DNA-repair gene knockouts '
                 '(EXO1, FANCC, MSH6).',
        'dir': DEFAULT_SIGNATURE_DIR,
        'files': [
            'COSMIC_v2_SBS_GRCh37.txt',
            'Zou2018-signatures.SBS-96.tsv',
        ],
    },
}

DEFAULT_EXAMPLE_SET = 'paper_gold_standard'


# ============================================================================
# The published COSMIC+Enviro+KO figure
# ============================================================================

PAPER_GOLD_STANDARD_GROUPS = [
    {
        'name': 'PAHs',
        'pathway': 'NER',
        'color': '#36648B',  # SteelBlue4
        'members': [
            'SBS4',
            'BaP (2 uM) + S9',
            'BPDE (0.125 uM)',
            'DBP (0.0313 uM) + S9',
            'DBPDE (0.000625 uM)',
            'DBADE (0.109 uM)',
            'DBAC (5 uM) + S9',
            'DBA (75 uM) + S9',
            '5-Methylchrysene (1.6 uM) + S9',
        ],
    },
    {
        'name': 'Nitro-PAHs',
        'pathway': 'NER',
        'color': '#63B8FF',  # SteelBlue1
        'members': [
            '3-NBA (0.1 uM)',
            '1,8-DNP (8 uM)',
            '6-Nitrochrysene (50 uM) + S9',
            '6-Nitrochrysene (50 uM)',
        ],
    },
    {
        'name': 'Platinum',
        'pathway': 'NER',
        'color': '#A2CD5A',  # DarkOliveGreen3
        'members': [
            'SBS31',
            'SBS35',
            'Cisplatin (12.5 uM)',
            'Carboplatin (5 uM)',
        ],
    },
    {
        'name': 'Aristolochic acids',
        'pathway': 'NER',
        'color': '#CAFF70',  # DarkOliveGreen1
        'members': [
            'SBS22a',
            'SBS22b',
            'AAI (1.25 uM)',
        ],
    },
    {
        'name': 'ROS',
        'pathway': 'BER',
        'color': '#CAE1FF',  # LightSteelBlue1
        'members': [
            'SBS18',
            'SBS36',
            'SBS38',
        ],
    },
    {
        'name': 'HRD',
        'pathway': 'HR',
        'color': '#EE9572',  # Salmon2
        'members': [
            'SBS3',
            'EXO1_KO',
            'RNF168_KO',
        ],
    },
    {
        'name': 'MMRd',
        'pathway': 'MMR',
        'color': '#FF0000',  # red
        'members': [
            'SBS6',
            'SBS14',
            'SBS15',
            'SBS20',
            'SBS21',
            'SBS26',
            'SBS44',
            'MSH6_KO',
            'PMS1_KO',
            'PMS2_KO',
        ],
    },
    {
        'name': 'Alkylating agents',
        'pathway': 'MMR',
        'color': '#FFAEB9',  # LightPink1
        'members': [
            'SBS11',
            'Temozolomide (200 uM)',
            'MNU (350 uM)',
        ],
    },
]

PAPER_FIGURE_PRESET = {
    'example_set': 'paper_full',      # the 102 signatures the figure is built on
    'distance_metric': 'rmse',        # the figure's other panel pair uses 'cosine'
    'clustering_method': 'complete',
    'epsilon': 1e-4,
}


def gold_standard_group_of(signature):
    """Group name a signature is annotated with in the published figure, or
    None for the columns the figure leaves blank."""
    for group in PAPER_GOLD_STANDARD_GROUPS:
        if signature in group['members']:
            return group['name']
    return None


def _example_set_dir(example_set):
    return EXAMPLE_SIGNATURE_SETS[example_set].get('dir', DEFAULT_SIGNATURE_DIR)


def example_set_signature_count(example_set, base_dir=None):
    """Number of signature columns a set contributes, read from file headers."""
    spec = EXAMPLE_SIGNATURE_SETS[example_set]
    directory = base_dir or _example_set_dir(example_set)

    total = 0
    for filename in spec['files']:
        sep = ',' if filename.endswith('.csv') else '\t'
        header = pd.read_csv(f'{directory}/{filename}', sep=sep, nrows=0)
        total += len(header.columns) - 1  # minus the 'Type' column
    return total


def example_set_options():
    """[{label, value, blurb, count}] for the example-dataset picker, in
    declaration order (smallest/most useful set first)."""
    options = []
    for key, spec in EXAMPLE_SIGNATURE_SETS.items():
        options.append({
            'label': spec['label'],
            'value': key,
            'blurb': spec['blurb'],
            'count': example_set_signature_count(key),
        })
    return options


def load_example_merged_signatures(base_dir=None, example_set=DEFAULT_EXAMPLE_SET):
    """Read and merge one bundled example set from disk, the same way
    merge_uploaded_signatures merges user-uploaded files. Returns
    (merged_df, filenames)."""
    if example_set not in EXAMPLE_SIGNATURE_SETS:
        example_set = DEFAULT_EXAMPLE_SET

    spec = EXAMPLE_SIGNATURE_SETS[example_set]
    filenames = spec['files']
    directory = base_dir or _example_set_dir(example_set)

    named_dfs = []
    for filename in filenames:
        sep = ',' if filename.endswith('.csv') else '\t'
        df = pd.read_csv(f'{directory}/{filename}', sep=sep)
        named_dfs.append((filename, df))

    return _merge_signature_dataframes(named_dfs), filenames
