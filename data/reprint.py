import numpy as np
import pandas as pd

name = 'transcribed.normalized.txt'
data = pd.read_csv(f'signatures/{name}', sep='\t')


# Extracting mutation categories and their probabilities
mutation_types = data['Type'].values
signatures = data.columns[1:]

# Initialize a dictionary to store the RePrint probabilities for each signature
reprint_probabilities = {signature: {} for signature in signatures}

# Iterate over each signature
for signature in signatures:
    # Extract the probabilities for the current signature
    signature_probs = data[signature].values

    # Iterate over each mutation type
    for idx, mutation in enumerate(mutation_types):
        # Split the mutation type to extract NL, X, Y, NR
        flanking_bases, mutation_info = mutation.split('[')

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
print(reprint_df.to_csv(f'cosmic_reprints/{name}.reprint', sep='\t'))
