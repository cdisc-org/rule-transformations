# Tools to transform CORE rule structures

## Implement alternative transformers

In order to create a transformer provider for a different type of storage, implement the `Transformer` interface. Some provider implementations are already provided:

- `CosmosdbTransformer` for ms cosmosdb storage
- `JSONTransformer` for simple json filesystem storage
- `YAMLTransformer` for simple yaml filesystem storage

## Create transformers

### CosmosdbTransformer

```python
from transformer.transformer_cosmosdb import CosmosdbTransformer
prod_transformer = CosmosdbTransformer(
    getenv("PROD_COSMOS_URL"),
    getenv("PROD_COSMOS_KEY"),
    getenv("PROD_COSMOS_DATABASE"),
    getenv("PROD_COSMOS_CONTAINER"),
)
```

### JSON File Transformer

```python
from transformer.transformer_json import JSONTransformer
json_transformer = JSONTransformer(f"{getenv('WORKING_DIR')}/rules")
```

### YAML File Transformer

```python
from transformer.transformer_yaml import YAMLTransformer
yaml_transformer = YAMLTransformer(f"{getenv('WORKING_DIR')}/rules")
```

## Export Rules

```python
prod_transformer.export_json(f"{getenv('WORKING_DIR')}/rules")
```

## Delete and replace rules from one transformer location to another

```python
from transformer.transformer import Transformer
Transformer.replace_rules(
    from_transformer=prod_transformer, to_transformer=dev_transformer
)
```

## Run Transformations

There are sets of transformations available and you can implement your own set of transformations. Some sets provided:

- `transformations_misc`
- `transformations_crog`

Run CROG Schema Transformations:

```python
from transformer.transformations_crog import (
    all_transformations,
)
dev_transformer.transform_rules(all_transformations())
```



---

## Data Transformer - Tool to convert CORE Sharepoint Test Data XLSX to CSV
The data transformer is a standalone tool for converting CDISC CORE unit test data from Excel format into CSV files suitable for use with the rules engine.

### Install dependencies
create and activate a virtual environemnt

```bash
pip install -r data_transformer/requirements.txt
```

### Directory structure

The tool expects a standard directory (e.g. `SDTMIG/`) organized as follows:

```
SDTMIG/
  CG0001/
    negative/
      01/
        data/
        results/
    positive/
      01/
        data/
```

Any directory that does not contain a `negative/` or `positive/` subdirectory (e.g. `SEND Rules Team Documents/`) is automatically skipped.

### Output structure

Running the tool creates a `<standard>_csv/` directory alongside the original, leaving the source untouched:

```
SDTMIG/        <- original, untouched
SDTMIG_csv/
  CG0001/
    negative/
      01/
        data/
          dm.csv          <- one per dataset sheet, header + data rows
          variables.csv   <- variable metadata for all datasets
          tables.csv      <- dataset labels
          .env            <- standard, version, CT packages, xml paths
          define.xml      <- copied from source if present
        result/           <- copied from source, logged in errors if results are in excel and not JSON
```

### Output files

| File | Description |
|---|---|
| `<tab_name>.csv` | One per dataset sheet. Single header row (variable names) followed by data rows. |
| `variables.csv` | One row per variable across all datasets: `dataset, variable, label, type, length` |
| `tables.csv` | Dataset filenames and labels from the Datasets tab: `Filename, Label` |
| `.env` | Key-value pairs from the Library tab plus paths to any XML files |
| `define.xml` | Copied as-is if present in the source data directory |

The `.env` file format:
```
PRODUCT=sdtmig
VERSION=3-4
SUBSTANDARD=sdtm
CT=sdtmct-2014-09-26,sdtmct-2015-03-27
DEFINE_XML=define.xml
```

### Usage

From the `rule-transformations` directory:

```bash
# Convert a full standard directory
python data_transformer/csv_data_converter.py "C:\path\to\unitTesting\SDTMIG"

# Convert a single Excel file
python data_transformer/csv_data_converter.py --file "C:\path\to\test.xlsx"
```

### Error reporting

If any Excel files fail to convert, a `conversion_errors.log` is written to the root of the output directory (e.g. `SDTMIG_csv/conversion_errors.log`). Each line identifies the file and the reason:

```
/path/to/CG0002/negative/01/data/unit-test.xlsx: failed to open Excel file — File is not a zip file
/path/to/CG0003/negative/01/data/unit-test.xlsx: missing Datasets tab
```

If all files convert successfully the log file is not created.
