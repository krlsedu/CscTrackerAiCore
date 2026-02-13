import json
import logging
import os
import clickhouse_connect
from datetime import datetime

class ClickHouseDb:
    def __init__(self, host="localhost", port=8123, username='admin', password='admin'):
        self.logger = logging.getLogger()
        self.host = os.getenv("CLICKHOUSE_HOST", host)
        self.port = int(os.getenv("CLICKHOUSE_PORT", port))
        self.username = os.getenv("CLICKHOUSE_USER", username)
        self.password = os.getenv("CLICKHOUSE_PASSWORD", password)
        self.database = os.getenv("CLICKHOUSE_DB", "default")

        self.init_db()

    def get_ch_client(self):
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database
        )

    def init_db(self):
        try:
            _client = self.get_ch_client()
            _client.command("""
            CREATE TABLE IF NOT EXISTS ai_events (
                timestamp DateTime,
                event_id String CODEC(ZSTD(9)),
                tokens_input UInt32 DEFAULT 0,
                tokens_image UInt32 DEFAULT 0,
                tokens_output UInt32 DEFAULT 0,
                payload String CODEC(ZSTD(9)),
                result String CODEC(ZSTD(9)),
                model String CODEC(ZSTD(9)),
                task String CODEC(ZSTD(9)) 
            ) ENGINE = MergeTree()
            ORDER BY timestamp
            """)
            _client.close()
        except Exception as e:
            logging.error(f"Falha ao inicializar banco: {e}")

    def log_event_telemetry(self, event_id, tokens, payload, result, model_name, task):
        try:
            _client = self.get_ch_client()
            if not payload: payload = {}
            row = [
                datetime.now(),
                str(event_id),
                tokens.get('input', 0),
                tokens.get('image', 0),
                tokens.get('output', 0),
                json.dumps(payload, separators=(',', ':')),
                result,
                model_name,
                task
            ]
            _client.insert('ai_events', [row], column_names=[
                'timestamp', 'event_id', 'tokens_input', 'tokens_image',
                'tokens_output', 'payload', 'result', 'model', 'task'
            ])
            _client.close()
        except Exception as e:
            logging.error(f"Observabilidade falhou: {e}")

