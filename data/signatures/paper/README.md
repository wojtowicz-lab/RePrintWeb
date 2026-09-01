# Paper signature sets (RePrint)

Signature matrices analysed in
**"Toward identification of common DNA repair process in mutational signatures"**
(<https://pmc.ncbi.nlm.nih.gov/articles/PMC12873990/>).

All files here were produced from the paper's single combined matrix
`reprintPapier.txt` (96 mutation types x 102 signatures) by
`data/split_paper_signatures.py`. Columns are copied verbatim as text, so the
values are byte-identical to that source. Every file is tab-separated with a
leading `Type` column, i.e. the format the app's uploader expects, and every
signature column sums to 1.

| File | Signatures | Source |
| --- | --- | --- |
| `RePrint_COSMIC_v3.4_SBS_GRCh37.txt` | 67 | COSMIC v3.4 (GRCh37) |
| `RePrint_Kucab2019_mutagens.txt` | 28 | Kucab et al. 2019, environmental mutagen exposures |
| `RePrint_Zou2021_repair_KO.txt` | 7 | Zou et al. 2021, CRISPR-Cas9 DNA-repair gene knockouts |
| `RePrint_gold_standard_clusters.txt` | 39 | Cross-source subset: the paper's Table 1 reference clusters |

Concatenating the first three files on `Type` reproduces `reprintPapier.txt`
exactly (verified), so "the full paper set" needs no separate file - the app
builds it by merging them.

## How each set relates to the bundled reference data

- **COSMIC** - identical to `data/signatures/COSMIC_v3.4_SBS_GRCh37.txt` minus the
  19 signatures flagged as possible sequencing artefacts (SBS27, SBS43,
  SBS45-SBS60, SBS95): 86 - 19 = 67.
- **Kucab2019** - a 28-profile subset of the 54 profiles in
  `data/signatures/Kucab2019-sub_signature.txt`, renormalised so each column sums
  to 1. The untreated `Control` column and the duplicate
  `Temozolomide (200 uM).1` are not part of it.
- **Zou2021** - EXO1, MSH6, OGG1, PMS1, PMS2, RNF168, UNG knockouts. This is a
  wider panel than the three knockouts (EXO1, FANCC, MSH6) in
  `data/signatures/Zou2018-signatures.SBS-96.tsv`; FANCC is not in the paper's set.

## Gold-standard clusters (Table 1)

`RePrint_gold_standard_clusters.txt` keeps signatures in cluster order, so
related signatures sit next to each other on the heatmap:

| Cluster | Repair pathway | Members |
| --- | --- | --- |
| PAHs | NER | SBS4 + 8 PAH exposures (BaP, BPDE, DBP, DBPDE, DBADE, DBAC, DBA, 5-Methylchrysene) |
| NitroPAHs | NER | 3-NBA, 1,8-DNP, 6-Nitrochrysene (+/- S9) |
| ROS | BER | SBS18, SBS36, SBS38 |
| HRD | HR | SBS3, EXO1_KO, RNF168_KO |
| TMZ | MMR | SBS11, Temozolomide |
| Platinum | NER | SBS31, SBS35, Cisplatin, Carboplatin |
| AAs | NER | SBS22a, SBS22b, AAI |
| MMRd | MMR | SBS6, SBS14, SBS15, SBS20, SBS21, SBS26, SBS44, MSH6_KO, PMS1_KO, PMS2_KO |
| DrugsBAbroad | NER | adds SBS24 to Platinum + AAs |

## Regenerating

```
python3 data/split_paper_signatures.py     # run from the repo root
```
