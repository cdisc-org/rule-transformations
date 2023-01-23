# Tools to transform CORE rule structures

## Implement alternative transformers

In order to create a transformer provider for a different type of storage, implement the `Transformer` interface. Some provider implementations are already provided:

- `CosmosdbTransformer` for ms cosmosdb storage
- `FileTransformer` for simple json filesystem storage

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
