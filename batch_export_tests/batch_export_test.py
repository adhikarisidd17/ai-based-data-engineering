from google.cloud.bigquery_storage import BigQueryReadClient
from google.cloud.bigquery_storage import types


def test_batch_export():
    create_read_session()


def create_read_session():
    big_query_read_client = BigQueryReadClient()
    session_request = types.stream.ReadSession()
    session_request.table = "projects/{}/datasets/{}/tables/{}".format('ab73-np-rawlay-dev-3324', 'icasoi', 'store_orderable_item')
    session_request.data_format = types.DataFormat.ARROW

    parent = "projects/{}".format('ab73-np-rawlay-dev-3324')
    session = big_query_read_client.create_read_session(
        parent=parent,
        read_session=session_request,
        max_stream_count=1,
    )

    reader = big_query_read_client.read_rows(session.streams[0].name)
    df = reader.to_dataframe()
    if len(df.index) < 1:
        assert False
    else:
        assert True
