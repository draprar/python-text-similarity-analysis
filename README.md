# 🧠 AI Document Diff Tool

AI Document Diff Tool is an advanced document comparison engine for **DOCX, XLSX, and TXT** files.  
It generates **interactive HTML reports** enhanced with **AI semantic heuristics** for meaningful change detection.

## ✨ Features

- **Smart Diff Engine** — detects added, deleted, and modified content in text, tables, and images.  
- **AI Heuristics** — uses spaCy to detect semantic context, entities, and similarity scores.  
- **Interactive Reports** — HTML reports with filters, collapsible sections, and dark/light mode.  
- **JSON Export** — structured data for further integration or automation.  

## 🛠️ Technologies

- **Python 3.11+**
- **spaCy (pl_core_news_md)** — for Polish language semantic analysis  
- **difflib** — for fine-grained text comparison  
- **openpyxl**, **python-docx**, **pandas** — document parsing  
- **Custom AI Heuristics** — lightweight scoring and entity detection  

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/draprar/python-text-similarity-analysis.git
   cd python-text-similarity-analysis
   ```
   
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download pl_core_news_md
   ```

3. Run the tool:
   ```bash
   python main.py old.docx new.docx
   ```
   
4. The output report will be saved as:
   ```bash
   raport.html
   raport.json
   ```
   
## ▶️ Usage

### Compare two documents
   ```bash
   python main.py file_old.docx file_new.docx
   ```

Then open `raport.html` in your browser to explore:

- Collapsible unchanged sections  
- Highlighted semantic differences  
- AI analysis summaries per paragraph or table  

---

## 📊 Example Report Features

- Toggle between change types *(added, deleted, changed, unchanged)*  
- Filter by block type *(paragraph, table, image)*  
- AI labels such as `osoba`, `data`, `liczba`, `organizacja`  
- Semantic similarity scores *(0–10)*  
- Light/Dark mode toggle  

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Credits

**Developer**: Walery ([@draprar](https://github.com/draprar/))  