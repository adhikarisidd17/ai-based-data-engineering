from batch_export_tests.metadata_models import FileExportsMetadata, FileExportsMetadataList, KafkaMetadata, KafkaMetadataList

def test_file_exports_metadata_collection(file_exports_metadata):
    FileExportsMetadataList(rows=file_exports_metadata)

def test_file_exports_metadata(file_exports_metadata):
    for integration in file_exports_metadata:
        print(integration)
        FileExportsMetadata(**integration)

def test_kafka_metadata_collection(kafka_metadata):
    KafkaMetadataList(rows=kafka_metadata)

def test_kafka_metadata(kafka_metadata):
    for integration in kafka_metadata:
        print(integration)
        KafkaMetadata(**integration)