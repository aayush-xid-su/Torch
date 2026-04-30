# Phone Number Intelligence Toolkit

## 📌 Overview

This project is a **phone number intelligence and validation toolkit** that allows you to:

* Generate phone numbers from a given prefix
* Validate numbers using international standards
* Fetch associated metadata and names using external APIs

It is useful for:

* Data analysis & research
* Cybersecurity/OSINT learning
* Telecom pattern analysis

---

## 🚀 Features

* 🔢 Bulk phone number generation
* ✅ Number validation using `phonenumbers`
* 🔍 Truecaller-based name lookup
* 🌐 AbstractAPI phone data lookup
* 📁 JSON & CSV export support

---
```
Step 1                    Step 2                    Step 3 / Step 4
──────────                ──────────                ────────────────
number_generator.py  ──▶  validation.py  ──────────▶  truecaller_lookup.py
                                                                
  │                         │                       (owner names via Truecaller)
  │                         │                       
  ▼                         ▼                       ▶  abstractapi_lookup.py
numbergen.txt          validnumber.txt              
                                                     (carrier/line/location
(100,000 numbers)      (valid numbers only,          via AbstractAPI)
                        with carrier & location)
```
## 🏗️ Workflow

### Step 1: Generate Numbers

Generate all possible phone numbers from a given prefix.

```bash
python3 number_generator.py
```

**Input:**

```
Enter prefix: 9876543210
```

**Output:**

```
numbergen.txt
```

---

### Step 2: Validate Numbers

Filter valid phone numbers using Google's `phonenumbers` library.

```bash
pip install phonenumbers
python3 validation.py
```

**Output:**

```
validnumber.txt
```

---

### Step 3: Enrichment (Choose One or Both)**

---

#### 🔹 Step 3a: Truecaller Lookup

Fetch names and details using Truecaller.

```bash
pip install truecallerpy
```

**Setup:**

```bash
truecallerpy login
truecallerpy -i -r
```

**Run:**

```bash
python3 truecaller_lookup.py <INSTALLATION_ID>
```

**Output:**

```
truecaller_results.json
truecaller_results.csv
```

---

#### 🔹 Step 3b: AbstractAPI Lookup

Fetch phone metadata using AbstractAPI.

```bash
python3 abstractapi_lookup.py YOUR_API_KEY --limit 50
```

**Output:**

```
abstractapi_results.json
abstractapi_results.csv
```

---

## 📂 Project Structure

```
.
├── number_generator.py       # Generates phone numbers
├── validation.py             # Validates numbers
├── truecaller_lookup.py      # Truecaller integration
├── abstractapi_lookup.py     # AbstractAPI integration
├── numbergen.txt             # Generated numbers
├── validnumber.txt           # Valid numbers
├── *.json / *.csv            # Output results
```

---

## ⚙️ Requirements

* Python 3.x
* pip

### Install Dependencies

```bash
pip install phonenumbers truecallerpy requests
```

---

## 📊 Output Formats

* `.txt` → Raw numbers
* `.json` → Structured API data
* `.csv` → Spreadsheet-friendly format

---

## ⚠️ Disclaimer

This tool is intended **strictly for educational and research purposes**.

* Do NOT use for spamming, scraping, or harassment
* Respect privacy and applicable laws
* API usage must comply with respective service terms

---

## 🛠️ Future Improvements

* Add GUI dashboard
* Multi-threaded processing
* Proxy support
* Database integration
* Real-time lookup system

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Submit a pull request

---

## 👨‍💻 Author

Developed for learning and experimentation in phone number intelligence and OSINT.

---

## ⭐ Support

If you found this useful:

* Star the repository ⭐
* Share with others 📢
* Contribute improvements 🚀

---
