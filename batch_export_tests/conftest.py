import pytest
import yaml
import glob

def read_yaml_file(filename):
    with open(filename, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
            return None

@pytest.fixture
def file_exports_metadata():
    files = glob.glob("terraform/metadata/file_exports/*.yml")
    all_metadata = []
    for yaml_data in [read_yaml_file(f) for f in files]:
        for integration in yaml_data["files_batch"]:
            all_metadata.append(integration)
    return all_metadata

@pytest.fixture
def kafka_metadata():
    files = glob.glob("terraform/metadata/kafka_exports/*.yml")
    all_metadata = []
    for yaml_data in [read_yaml_file(f) for f in files]:
        for integration in yaml_data["kafka_batch"]:
            all_metadata.append(integration)
    return all_metadata