import base64
import numpy as np
import io
import re
import pandas as pd

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    file_content = decoded.decode('utf-8')

    if format == 'TSV Format' or format == 'Mutated CSV Format' or format == 'Mutated TSV Format':
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=0, sep=sep)
    if format == 'CSV Format':
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=[0, 1], sep=sep)

    if 'csv' in filename:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=[0, 1], sep=',')
    elif 'txt' in filename:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=0, sep='\t')
    elif 'xls' in filename:
        return pd.read_excel(io.BytesIO(decoded))

    if format == 'Unknown Format':
        raise ValueError('Unknown Format')

def parse_signatures(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    if 'txt' in filename:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=0, sep='\t')
    if 'csv' in filename:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')), index_col=[0, 1], sep=',')


def load_signatures(filename, organ=False):
    if organ:
        file_path = f'data/signatures_organ/latest/{filename}'
        delimiter = ','
    else:
        delimiter = '\t' if '.txt' in filename else ','
        file_path = f'data/signatures/{filename}'

    df = pd.read_csv(file_path, delimiter=delimiter, header=0)
    if 'Type' in df.columns[0] or 'Unnamed: 0' in df.columns[0]:
        df = df.drop(df.columns[0], axis=1)

    names_signatures = df.columns.tolist()

    COSMIC = df.values

    return COSMIC, names_signatures

def load_names(filename):
    file_path = f"../data/signatures_organ/latest/{filename}_Signature.csv"
    signatures = np.genfromtxt(file_path, delimiter=',', max_rows=1, dtype='str')[1:]

    pattern = r'([^_]+)$'
    return [re.search(pattern, item).group() for item in signatures if re.search(pattern, item)]

