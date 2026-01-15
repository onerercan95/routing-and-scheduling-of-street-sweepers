## Requirements

- Python 3.x
- pip

## Installation & Setup

### 1. Update package lists

```bash
sudo apt update
```

### 2. Install Python 3

```bash
sudo apt install python3 -y
```

Verify:

```bash
python3 --version
```

### 3. Install pip for Python 3

```bash
sudo apt install python3-pip -y
```

Verify:

```bash
pip3 --version
```

### 4. Upgrade pip (recommended)

```bash
pip3 install --upgrade pip
```

### 5. Install required packages

Make sure `req.txt` is in the project directory:

```bash
pip3 install -r req.txt
```

If you get permission errors:

```bash
pip3 install --user -r req.txt
```

## Running the Program

```bash
python3 -m run
```

## Author

Öner ERCAN

## Zenodo

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18261970.svg)](https://doi.org/10.5281/zenodo.18261970)
