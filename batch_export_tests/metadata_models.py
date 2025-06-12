from collections import Counter
from pydantic import BaseModel, Field, ValidationInfo, field_validator
from enum import Enum
from typing import List, Optional
from typing import Union

class BackupBucket(BaseModel):
    needed: bool
    data_viewer_group: Optional[str] = None

    @field_validator('data_viewer_group')
    def data_viewer_group_when_bucket_needed(cls, v, info: ValidationInfo):
        if v and not info.data.get('needed'):
            raise ValueError("The data_viewer_group should not be specified when the Ops bucket is not needed.")
        return v

class Env(str, Enum):
    dev = 'dev'
    tcm = 'tcm'
    ver = 'ver'
    prd = 'prd'

class FileFormat(str, Enum):
    csv = 'csv'
    json = 'json'
    parquet = 'parquet'

class FileCompression(str, Enum):
    gzip = 'gzip'

class FileProcessingDate(str, Enum):
    prev_hour = 'prev_hour'
    prev_day = 'prev_day'
    prev_week = 'prev_week'
    prev_month = 'prev_month'
    prev_quarter = 'prev_quarter'
    prev_year = 'prev_year'
    two_hours_back = '2_hours_back'
    two_days_back = '2_days_back'
    two_weeks_back = '2_weeks_back'
    two_months_back = '2_months_back'
    two_years_back = '2_years_back'

class Trigger(str, Enum):
    schedule = 'schedule'
    event = 'event'     

class Deployment(BaseModel):
    schedule: Optional[str] = None
    cloud_scheduler: Optional[List[Env]] = None
    cloud_run: List[Env]

class Operations(BaseModel):
    backup_bucket: BackupBucket

class OwnBucket(BaseModel):
    needed: bool
    service_account: str | None = Field(default=None, validate_default=True)
    name: str | None = Field(default=None, validate_default=True)

    @field_validator('service_account')
    def service_account_defined_when_bucket_needed(cls, v, info: ValidationInfo):
        if v and not info.data.get('needed'):
            raise ValueError("The service_account should not be specified when sink.own_bucket.needed=False.")
        elif not v and info.data.get('needed'):
            raise ValueError("When sink.own_bucket.needed=True a value for service_account should be specified too.")
        return v
    
    @field_validator('name')
    def bucket_name(cls, v, info: ValidationInfo):
        if v and not any(e.value in v for e in Env):
            raise ValueError("The bucket name should contain the environment name.")
        
        if v and not info.data.get('needed'):
            raise ValueError("The bucket name should not be specified when sink.own_bucket.needed=False.")
        return v

class SourceFilesExports(BaseModel):
    project_id: str
    dataset: str
    table: str
    requested_streams: Optional[int] = None
    column_list: Optional[List[str]] = None
    row_filter: Optional[str] = None
    is_view: Optional[bool] = None
    sorting: Optional[str] = None

class SourceKafka(BaseModel):
    dataset: str
    table: str
    requested_streams: Optional[int] = None
    column_list: Optional[List[str]] = None
    row_filter: Optional[str] = None

class FileSink(BaseModel):
    file_name: str
    file_format: FileFormat
    file_compression: Optional[FileCompression] = None
    file_max_size: Optional[int] = None
    file_signature: Optional[str] = None
    file_iclude_header: Optional[bool] = None
    file_delimiter: Optional[str] = None
    file_processing_date: Optional[FileProcessingDate] = None
    file_split_columns: Optional[str] = None
    file_encoding: Optional[str] = None
    own_bucket: Optional[OwnBucket] = None
    file_split_rows: Optional[int] = None

    @field_validator('file_delimiter')
    def file_delimiter_only_in_csv(cls, v, info: ValidationInfo):
        if v and info.data.get('file_format') != FileFormat.csv:
            raise ValueError("file_delimiter is only supported for csv file format.")
        return v

    @field_validator('file_iclude_header')
    def file_include_header_only_in_csv(cls, v, info: ValidationInfo):
        if v and info.data.get('file_format') != FileFormat.csv:
            raise ValueError("file_iclude_header is only supported for csv file format.")
        return v
    
    @field_validator('file_compression')
    def gz_extension_for_gzip_compression(cls, v, info: ValidationInfo):
        if v == FileCompression.gzip and not info.data.get('file_name').endswith(".gz"):
            raise ValueError("For gzip compression the file_name should have a .gz extension.")
        return v

class FileExportsMetadata(BaseModel):

    def __hash__(self) -> int:
        """Object identity is the hash of the id field"""
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        """Two rows are equal if they have common id"""
        return isinstance(other, FileExportsMetadata) and self.id == other.id
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Integration:{self.integration},id:{self.id}"

    integration: str
    id: int
    trigger: Trigger
    source: SourceFilesExports
    sink: FileSink
    deployment: Deployment
    operations: Optional[Operations] = None

    @field_validator('deployment')
    def deployment_requirements_based_on_trigger(cls, v, info: ValidationInfo):
        if not v.schedule:
            if info.data.get('trigger') == Trigger.schedule:
                raise ValueError("Schedule should be defined in order to run a batch export of trigger type 'schedule'")
        else:
            if info.data.get('trigger') == Trigger.event:
                raise ValueError("Scheduler and schedule are not needed when running a batch export of trigger type 'event'")
        return v
    
class FileExportsMetadataList(BaseModel):
    rows: List[FileExportsMetadata]

    @field_validator("rows")
    def check_unique_integrations(cls, rows):
        # The ids should be unique
        if len(set(rows)) != len(rows):
            duplicates = [
                name for name, count in Counter(rows).items() if count > 1
            ]
            raise Exception(f"Integrations with duplicate 'id' fields found: {duplicates}")
        
        integrations = []
        # Duplicate integrations for the same env are not allowed
        for i in rows:
            for env in i.deployment.cloud_run:
                integrations.append((i.integration, env))
        duplicates = [k for k, v in Counter(integrations).items() if v > 1]
        if duplicates:
            raise Exception(f"Duplicate integrations found: {duplicates}")
        
class KafkaSink(BaseModel):
    topic: str
    business_object: Union[int, str]
    ica_integration_id: Union[int, str]
    ica_message_version: str
        
class KafkaMetadata(BaseModel):

    def __hash__(self) -> int:
        """Object identity is the hash of the id field"""
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        """Two rows are equal if they have common id"""
        return isinstance(other, KafkaMetadata) and self.id == other.id
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Integration:{self.integration},id:{self.id}"

    integration: str
    id: int
    trigger: Trigger
    source: SourceKafka
    sink: KafkaSink
    deployment: Deployment

class KafkaMetadataList(BaseModel):
    rows: List[KafkaMetadata]

    @field_validator("rows")
    def check_unique_integrations(cls, rows):
        # The ids should be unique
        if len(set(rows)) != len(rows):
            duplicates = [
                name for name, count in Counter(rows).items() if count > 1
            ]
            raise Exception(f"Integrations with duplicate 'id' fields found: {duplicates}")
        
        integrations = []
        # Duplicate integrations for the same env are not allowed
        for i in rows:
            for env in i.deployment.cloud_run:
                integrations.append((i.integration, env))
        duplicates = [k for k, v in Counter(integrations).items() if v > 1]
        if duplicates:
            raise Exception(f"Duplicate integrations found: {duplicates}")
