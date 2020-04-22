from . import _domain as domain

def validate_data_loader(csv_data_loader, df=None):
    '''
    Validates a csv_data_loader object.
    Optionally checks against a passed in data frame

    :param csv_data_loader:
    :param df:
    :returns: Boolean
    :raises Exception:
    '''

    loader_config = csv_data_loader.get('loaderConfig')
    if not loader_config:
        raise Exception('Empty loader config')

    # Check mapping
    mapping = loader_config.get('mapping')
    if not mapping.get('timeColumns'):
        raise Exception('Loader config requires non-empty time columns.')

    # Check time tuples nonempty
    if not mapping.get('timeTuples'):
        raise Exception('Time tuples empty. No column loaded.')

    columnByName = domain.get_columns_by_name(loader_config['sourceSettings']['columnConfigs'])

    # Collectors for referenced cols
    requiredFields = set()

    # Check all columns are correct types and all are defined
    for field in mapping['keyColumns']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'key column {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not domain.is_string_data_type(fieldType):
            raise Exception(f'key column {field} must be a string, got {fieldType}.')

    # Check all value label are correct types and all are defined
    for field in mapping['valueLabelColumn']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'value label {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not domain.is_string_data_type(fieldType):
            raise Exception(f'value label {field} must be a string, got {fieldType}.')

    # Check all time columns label are correct types and all are defined
    for field in mapping['timeColumns']:
        requiredFields.add(field)
        if not columnByName.get(field):
            raise Exception(f'time column {field} not found.')

        fieldType = columnByName[field]['dataType']
        if not domain.is_time_data_type(fieldType):
            raise Exception(f'time column {field} must be a time, got {fieldType}.')

    # Check all time tuples
    for timeTuple in mapping['timeTuples']:
        requiredFields.add(timeTuple['timeColumn'])
        requiredFields.add(timeTuple['valueColumn'])

        if not columnByName.get(timeTuple['timeColumn']):
            raise Exception(f'time column in tuple {str(timeTuple)} not found.')

        timeType = columnByName[timeTuple['timeColumn']]['dataType']
        if not domain.is_time_data_type(timeType):
            raise Exception(f'time column in tuple {str(timeTuple)} must be a time, got {timeType}.')

        if not columnByName.get(timeTuple['valueColumn']):
            raise Exception(f'value column in tuple {str(timeTuple)} not found.')

        valueType = columnByName.get(timeTuple['valueColumn'])['dataType']
        if not domain.is_number_data_type(valueType):
            raise Exception(f'value column in tuple {str(timeTuple)} must be a number, got {valueType}.')

    # Check data frame fields and types
    if not df is None:
        dfColumnsByName = domain.get_columns_by_name(domain.get_column_configs(df))
        for keyField in filter(lambda x: not domain.is_static_data_type(columnByName[x]['dataType']), requiredFields):
            requiredType = columnByName[keyField]['dataType']
            if not dfColumnsByName.get(keyField):
                raise Exception(f'data frame missing required field: {keyField} of type: {requiredType}')

            if dfColumnsByName[keyField]['dataType'] != requiredType:
                raise Exception(
                    f'data frame field {keyField} must be of type {requiredType}. Got {dfColumnsByName[keyField]["dataType"]}')

    return True
