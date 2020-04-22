### ListDataSources
Request
```json
{}
```

Response
```json
{
  "dataSources": [
    {
      "id": "ds_id_test_grpc",
      "name": "Test Datasource (grpc)"
    }
  ]
}
```

### dataSourceUniques
Request
```json
{
  "dataSourceId": "ds_id_test_grpc",
  "projectColumns": [
    {
      "name": "date",
      "type": 2
    },
    {
      "name": "trans",
      "type": 0
    },
    {
      "name": "symbol",
      "type": 0
    },
    {
      "name": "qty",
      "type": 1
    },
    {
      "name": "price",
      "type": 1
    },
    {
      "name": "currency",
      "type": 0
    }
  ]
}
```

Response
```json
{
  "records": [
    {
      "strings": [
        {
          "value": {
            "value": "BUY"
          }
        },
        {
          "value": {
            "value": "RHAT"
          }
        },
        {
          "value": {
            "value": "USD"
          }
        }
      ],
      "numbers": [
        {
          "value": {
            "value": 100
          }
        },
        {
          "value": {
            "value": 35
          }
        }
      ],
      "times": [
        {
          "value": {
            "value": "1136073600"
          }
        }
      ]
    },
    // ...
  ]
}
```

# sampleDataSourceMeta
Request
```json
{
  "dataSourceId": "ds_id_test_grpc"
}
```

Response
```json
{
    "columnConfigs": [
    {
      "timeColumnConfig": {
        "name": "date",
        "displayLabel": "date",
        "dateFormat": ""
      },
      "columnConfig": "timeColumnConfig"
    },
    {
      "stringColumnConfig": {
        "name": "trans",
        "displayLabel": "trans",
        "modifier": "None",
        "ontology": null
      },
      "columnConfig": "stringColumnConfig"
    },
    {
      "stringColumnConfig": {
        "name": "symbol",
        "displayLabel": "symbol",
        "modifier": "None",
        "ontology": null
      },
      "columnConfig": "stringColumnConfig"
    },
    {
      "numberColumnConfig": {
        "name": "qty",
        "displayLabel": "qty"
      },
      "columnConfig": "numberColumnConfig"
    },
    {
      "numberColumnConfig": {
        "name": "price",
        "displayLabel": "price"
      },
      "columnConfig": "numberColumnConfig"
    },
    {
      "stringColumnConfig": {
        "name": "currency",
        "displayLabel": "currency",
        "modifier": "None",
        "ontology": null
      },
      "columnConfig": "stringColumnConfig"
    }
  ],
  "dataSourceId": "ds_id_test_grpc",
  "dataSourceName": "Test Datasource (grpc)",
  "dataLoadMapping": {
    "keyColumns": [
      "trans",
      "symbol",
      "currency"
    ],
    "valueModifiers": [],
    "timeColumns": [
      "date"
    ],
    "valueLabelColumn": [],
    "timeTuples": [
      {
        "timeColumn": "date",
        "valueColumn": "qty"
      },
      {
        "timeColumn": "date",
        "valueColumn": "price"
      }
    ],
    "frequency": null
  },
  "sampleData": [
      // ...
  ],
  "columnSamples": {
      // ...
  }
}
```
