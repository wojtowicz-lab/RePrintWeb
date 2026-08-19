import glob
import itertools
import os
import re

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community import modularity

from utils.figpanel import CONTEXTS

ORGAN_DIR = 'data/signatures_organ/version_1'

_COLUMN_PATTERN = re.compile(r'^(?P<sig_id>.+?)\s*\(RefSig\s+(?P<refsig>.+?)\)\s*$')


def list_available_organs(organ_dir=ORGAN_DIR):
    return sorted(
        os.path.basename(p).replace('_Signature_1.csv', '')
        for p in glob.glob(os.path.join(organ_dir, '*_Signature_1.csv'))
    )


def load_organ_signatures(organ_dir=ORGAN_DIR):
    """
    Load every {Organ}_Signature_1.csv in organ_dir (Degasperi et al. 2022,
    organ-specific substitution signatures). Each column is one organ-
    specific signature named "<id> (RefSig <label>)"; there's no Type
    column, but the 96 rows are in the same context order figpanel.CONTEXTS
    uses - verified against COSMIC reference signatures (e.g. "Breast_C
    (RefSig 13)" is 0.97 cosine-similar to COSMIC SBS13 under this order,
    vs ~0.02 under the Type-column order COSMIC files use).

    Returns (df, meta): df is indexed by mutation Type with one column per
    organ signature (node id "<Organ>:<sig_id>"), meta maps node id to
    {'organ', 'refsig', 'label'}. Files that don't parse into a clean
    96-row table (a couple of the bundled exports are genuinely empty) are
    skipped.
    """
    frames = []
    meta = {}
    for path in sorted(glob.glob(os.path.join(organ_dir, '*_Signature_1.csv'))):
        organ = os.path.basename(path).replace('_Signature_1.csv', '')
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if len(df) != len(CONTEXTS) or df.shape[1] == 0:
            continue

        df = df.copy()
        df.index = CONTEXTS
        renamed = {}
        for col in df.columns:
            m = _COLUMN_PATTERN.match(col)
            sig_id = m.group('sig_id').strip() if m else col
            refsig = m.group('refsig').strip() if m else 'Unknown'
            # sig_id is already organ-prefixed (e.g. "Breast_A"), so it's
            # unique across the whole pooled dataset without extra decoration.
            node_id = sig_id if sig_id not in meta else f"{organ}:{sig_id}"
            renamed[col] = node_id
            meta[node_id] = {'organ': organ, 'refsig': refsig, 'label': sig_id}
        frames.append(df.rename(columns=renamed))

    combined = pd.concat(frames, axis=1)
    combined.index.name = 'Type'
    return combined, meta


def _add_combination_edges(G, df, meta, min_similarity=0.89, min_contribution=0.65):
    """
    Second half of the Degasperi et al. Fig 2k/3 rule: for a same-organ pair
    (A, C), fit the convex combination w*A + (1-w)*C (w in [0,1], the w that
    best reconstructs each candidate target B - a closed-form 1D least-
    squares fit, since signatures are probability vectors so a 2-term
    mixture is the natural model) against every other-organ signature B. If
    the reconstruction clears min_similarity cosine similarity to B *and*
    one of A/C supplies at least min_contribution of the mix, add a directed
    edge from that dominant signature to B (kind='combination', with the
    mix weight stored as `contribution`) - this is what gives the paper's
    network its extra density beyond plain pairwise similarity, since a
    signature can be a genuine mixture that doesn't closely match any single
    other signature on its own.
    """
    organs = {}
    for node in df.columns:
        organs.setdefault(meta[node]['organ'], []).append(node)

    values = {node: df[node].to_numpy(dtype=float) for node in df.columns}
    all_nodes = df.columns.tolist()

    for organ, members in organs.items():
        if len(members) < 2:
            continue
        others = [n for n in all_nodes if meta[n]['organ'] != organ]
        if not others:
            continue
        other_matrix = np.stack([values[n] for n in others])
        other_norms = np.linalg.norm(other_matrix, axis=1)
        other_norms[other_norms == 0] = 1e-12

        for i, j in itertools.combinations(members, 2):
            A, C = values[i], values[j]
            d = A - C
            denom = np.dot(d, d)
            if denom < 1e-12:
                continue

            w = (other_matrix - C) @ d / denom
            w = np.clip(w, 0.0, 1.0)
            recon = C[None, :] + w[:, None] * d[None, :]
            recon_norms = np.linalg.norm(recon, axis=1)
            recon_norms[recon_norms == 0] = 1e-12
            cos_sim = (recon * other_matrix).sum(axis=1) / (recon_norms * other_norms)

            for idx in np.where(cos_sim >= min_similarity)[0]:
                wi = float(w[idx])
                if wi >= min_contribution:
                    dominant, contribution = i, wi
                elif (1 - wi) >= min_contribution:
                    dominant, contribution = j, 1 - wi
                else:
                    continue

                target = others[idx]
                sim = float(cos_sim[idx])
                if G.has_edge(dominant, target):
                    edata = G[dominant][target]
                    if sim > edata.get('weight', 0):
                        edata['weight'] = sim
                    edata['kind'] = 'both' if edata.get('kind') in ('direct', 'both') else 'combination'
                    edata['contribution'] = contribution
                else:
                    G.add_edge(dominant, target, weight=sim, kind='combination', contribution=contribution)

    return G


def build_organ_similarity_graph(min_similarity=0.89, organs=None, min_contribution=0.65, include_combinations=True):
    """
    Undirected graph over organ-specific signatures pooled across organs.
    Edges come from the two rules in Degasperi et al. Fig 2k/3: a direct
    edge between two different-organ signatures at >= min_similarity cosine
    similarity (kind='direct'), and - when include_combinations is True - a
    combination edge from _add_combination_edges (kind='combination'). The
    combination rule is what makes the paper's network one dense, mostly-
    connected graph rather than many small disconnected pieces: it captures
    signatures that are a genuine mix of two others, which plain pairwise
    similarity misses.
    """
    df, meta = load_organ_signatures()

    if organs is not None:
        organs = set(organs)
        keep = [c for c in df.columns if meta[c]['organ'] in organs]
        df = df[keep]
        meta = {k: v for k, v in meta.items() if k in keep}

    node_ids = df.columns.tolist()
    values = df.to_numpy(dtype=float).T  # n_nodes x 96

    norms = np.linalg.norm(values, axis=1)
    norms[norms == 0] = 1e-12
    normalized = values / norms[:, None]
    sim_matrix = normalized @ normalized.T

    G = nx.Graph()
    G.add_nodes_from(node_ids)
    n = len(node_ids)
    for i in range(n):
        for j in range(i + 1, n):
            if meta[node_ids[i]]['organ'] == meta[node_ids[j]]['organ']:
                continue
            sim = sim_matrix[i, j]
            if sim >= min_similarity:
                G.add_edge(node_ids[i], node_ids[j], weight=float(sim), kind='direct')

    if include_combinations:
        _add_combination_edges(G, df, meta, min_similarity=min_similarity, min_contribution=min_contribution)

    return G, meta


def group_by_refsig(G, meta):
    """
    Group nodes by their RefSig label - already known from the source data,
    not discovered by an algorithm. Sorted largest-first so the layout/
    coloring machinery (built for Louvain output) can treat it the same way.
    Also reports modularity of this known grouping against the observed
    similarity graph, as a sanity check of how well "closest reference
    signature" explains the cross-organ similarity structure.
    """
    groups = {}
    for node in G.nodes():
        groups.setdefault(meta[node]['refsig'], set()).add(node)

    ordered = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    communities = [members for _, members in ordered]
    labels = [f"RefSig {name}" for name, _ in ordered]

    mod_score = None
    if G.number_of_edges() > 0 and len(communities) > 1:
        mod_score = modularity(G, communities, weight='weight')

    return communities, labels, mod_score
