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
    x_normalized = normalize(x)
    y_normalized = normalize(y)
    return np.sqrt(np.nanmean((x_normalized - y_normalized) ** 2))

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


# Bundled example signature files (data/signatures/) offered as a one-click
# "Load Example" demo of merging multiple datasets for clustering.
EXAMPLE_SIGNATURE_FILES = [
    'COSMIC_v3.4_SBS_GRCh37.txt',
    'Kucab2019-sub_signature.txt',
    'Zou2018-signatures.SBS-96.tsv',
]


def load_example_merged_signatures(base_dir='data/signatures'):
    """Read and merge the bundled example signature files from disk, the
    same way merge_uploaded_signatures merges user-uploaded files."""
    named_dfs = []
    for filename in EXAMPLE_SIGNATURE_FILES:
        sep = ',' if filename.endswith('.csv') else '\t'
        df = pd.read_csv(f'{base_dir}/{filename}', sep=sep)
        named_dfs.append((filename, df))

    return _merge_signature_dataframes(named_dfs)
