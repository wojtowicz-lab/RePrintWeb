## 🧬 RePrint – Mutational Signature Analysis Dashboard

**RePrint** is an interactive web application built with **Dash + Plotly**, enabling you to:
- Browse and compare mutational signatures (e.g. from the **COSMIC** database),
- Upload your own datasets (`.tsv`, `.csv`, `.xls`) and compare them against reference signatures,
- Automatically generate visualizations (bar plots, heatmaps, dendrograms),
- Integrate with tools for mutation analysis and tumor type identification.

---

### 🚀 Features

- ✅ Load predefined COSMIC signature files (`.txt`)
- ✅ Upload your own mutation signature data
- ✅ Merge uploaded data with reference datasets
- ✅ Generate real-time plots (bar plots, heatmaps, dendrograms)
- ✅ Supports `.csv`, `.tsv`, `.xls`, and `.xlsx` formats
- ✅ One-click session clearing
- ✅ `.env` environment variable support (for Django, Redis, etc.)

---

### 🛠 Installation

#### 1. Clone the repository
```bash
git clone git@github.com:marcin119a/RePrint.git
cd reprint
```

#### 2. Set up a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### 3. Run the app locally
```bash
python app.py
```

Open in your browser:  
📍 `http://localhost:8050`

---

### 📁 Project Structure

```
reprint/
├── app.py                     # Main application entry point
├── utils/
│   ├── figpanel.py            # Plot generation logic
│   ├── utils.py               # Data parsing and RePrint logic
│   └── uploader.py            # Upload handlers
├── data/
│   └── signatures/            # COSMIC .txt files
├── pages/
│   └── page3.py               # Main dashboard for signature comparison
├── assets/                    # CSS styles, favicon, etc.
├── .env                       # Environment variables
└── README.md                  # This file
```

---

### 📤 Input File Format

#### 📌 Requirements:
- `.csv`, `.tsv`, or `.xls` file with a `Type` column (e.g. `A[C>A]A`)
- Remaining columns = mutational signatures (`Signature_1`, `SBS1`, `MySampleX`, ...)

#### 📌 Example:
```tsv
Type	SBS1	SBS2
A[C>A]A	0.01	0.02
A[C>A]C	0.03	0.04
```


---

### 🧪 How It Works ?

1. Select a COSMIC reference file from the dropdown.
2. Upload your signature data using drag-and-drop.
3. Click **Generate Plots** to visualize the comparison.
4. Click **Clear Session** to reset uploaded data.

---
