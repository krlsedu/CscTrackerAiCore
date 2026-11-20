import atexit
import json
import logging
import os
import queue
import threading
import time
import weakref
from datetime import datetime

import clickhouse_connect


def _parse_bool_env(env_name: str, default: bool) -> bool:
    raw = os.getenv(env_name)
    if raw is None:
        return default
    val = raw.strip().lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _parse_int_env(env_name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        parsed = int(raw.strip())
        return parsed if parsed >= minimum else default
    except ValueError:
        return default


def _parse_float_env(env_name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        parsed = float(raw.strip())
        return parsed if parsed >= minimum else default
    except ValueError:
        return default


def _atexit_close(db_ref):
    db = db_ref()
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


class ClickHouseDb:
    AI_EVENTS_COLUMNS = [
        "timestamp",
        "event_id",
        "tokens_input",
        "tokens_image",
        "tokens_output",
        "tokens_reasoning",
        "payload",
        "result",
        "model",
        "task",
        "time_spent",
        "service_tier",
    ]

    def __init__(self, host=None, port=None, username=None, password=None):
        self.logger = logging.getLogger()
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = port or int(os.getenv("CLICKHOUSE_PORT", 8123))
        self.username = username or os.getenv("CLICKHOUSE_USER", "admin")
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", "admin")
        self.database = os.getenv("CLICKHOUSE_DB", "default")

        self.connect_timeout = _parse_float_env(
            "CLICKHOUSE_CONNECT_TIMEOUT", 5.0, minimum=0.1
        )
        self.send_receive_timeout = _parse_float_env(
            "CLICKHOUSE_SEND_RECEIVE_TIMEOUT", 30.0, minimum=0.1
        )

        self.async_telemetry = _parse_bool_env("CLICKHOUSE_ASYNC_TELEMETRY", True)
        self.queue_maxsize = _parse_int_env(
            "CLICKHOUSE_QUEUE_MAXSIZE", 10000, minimum=1
        )
        self.queue_max_mb = _parse_float_env(
            "CLICKHOUSE_QUEUE_MAX_MB", 500.0, minimum=0.0001
        )
        self._queue_max_bytes = max(1, int(self.queue_max_mb * 1024 * 1024))
        self.batch_size = _parse_int_env("CLICKHOUSE_BATCH_SIZE", 20, minimum=1)
        self.flush_interval_seconds = _parse_float_env(
            "CLICKHOUSE_FLUSH_INTERVAL_SECONDS", 5.0, minimum=0.01
        )

        self._lock = threading.Lock()
        self._client = None

        self._queue_lock = threading.Lock()
        self._queue_bytes = 0
        self._queue = queue.Queue(maxsize=self.queue_maxsize)
        self._flush_lock = threading.Lock()
        self._flush_event = threading.Event()
        self._flush_done_event = threading.Event()
        self._stop_event = threading.Event()
        self._closed = False
        self._worker_thread = None

        self.init_db()

        if self.async_telemetry:
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="ClickHouseTelemetryWorker",
                daemon=True,
            )
            self._worker_thread.start()

        self._atexit_handler = lambda ref=weakref.ref(self): _atexit_close(ref)
        atexit.register(self._atexit_handler)

    def get_ch_client(self):
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
            connect_timeout=self.connect_timeout,
            send_receive_timeout=self.send_receive_timeout,
        )

    def _get_persistent_client(self):
        """Retorna o cliente persistente (deve ser chamado sob self._lock)."""
        if self._client is None:
            self._client = self.get_ch_client()
        return self._client

    def _reset_client(self):
        """Fecha e descarta o cliente persistente (deve ser chamado sob self._lock)."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def init_db(self):
        with self._lock:
            try:
                _client = self._get_persistent_client()
                _client.command("""
                CREATE TABLE IF NOT EXISTS ai_events (
                    timestamp DateTime,
                    event_id String CODEC(ZSTD(9)),
                    tokens_input UInt32 DEFAULT 0,
                    tokens_image UInt32 DEFAULT 0,
                    tokens_output UInt32 DEFAULT 0,
                    tokens_reasoning UInt32 DEFAULT 0,
                    payload String CODEC(ZSTD(9)),
                    result String CODEC(ZSTD(9)),
                    model String CODEC(ZSTD(9)),
                    task String CODEC(ZSTD(9)),
                    time_spent Float,
                    service_tier String DEFAULT 'standard' CODEC(ZSTD(9))
                ) ENGINE = MergeTree()
                ORDER BY timestamp
                """)
            except Exception as e:
                logging.error(f"Falha ao inicializar banco: {e}")
                self._reset_client()
                return

            migrations = (
                (
                    "time_spent",
                    """
                    alter table ai_events
                        add column if not exists time_spent Float;
                    """,
                ),
                (
                    "tokens_reasoning",
                    """
                    alter table ai_events
                        add column if not exists tokens_reasoning UInt32 DEFAULT 0;
                    """,
                ),
                (
                    "service_tier",
                    """
                    alter table ai_events
                        add column if not exists service_tier String default 'standard' CODEC(ZSTD(9));
                    """,
                ),
            )

            for column_name, ddl in migrations:
                try:
                    _client.command(ddl)
                except Exception as e:
                    logging.error(f"Falha ao adicionar coluna {column_name}: {e}")

    def _build_telemetry_row(
        self,
        event_id,
        tokens,
        payload,
        result,
        model_name,
        task,
        time_spent,
        service_tier,
    ):
        if not payload:
            payload = {}
        payload_json = json.dumps(payload, separators=(",", ":"))
        row = [
            datetime.now(),
            str(event_id),
            tokens.get("input", 0),
            tokens.get("image", 0),
            tokens.get("output", 0),
            tokens.get("reasoning", 0),
            payload_json,
            result,
            model_name,
            task,
            time_spent,
            service_tier,
        ]
        result_str = "" if result is None else str(result)
        approx_bytes = len(payload_json.encode("utf-8", errors="ignore")) + len(
            result_str.encode("utf-8", errors="ignore")
        )
        return row, approx_bytes

    def _insert_batch_with_retry(self, batch):
        if not batch:
            return True
        with self._lock:
            try:
                client = self._get_persistent_client()
                client.insert(
                    "ai_events",
                    batch,
                    column_names=self.AI_EVENTS_COLUMNS,
                )
                return True
            except Exception as first_err:
                logging.warning(
                    f"Falha ao gravar batch de telemetria ({len(batch)} evento(s)), tentando reconectar: {first_err}"
                )
                self._reset_client()
                try:
                    client = self._get_persistent_client()
                    client.insert(
                        "ai_events",
                        batch,
                        column_names=self.AI_EVENTS_COLUMNS,
                    )
                    return True
                except Exception as second_err:
                    logging.error(
                        f"Observabilidade falhou após retry ({len(batch)} evento(s) descartados): {second_err}"
                    )
                    self._reset_client()
                    return False

    def _worker_loop(self):
        batch = []
        batch_start_time = None
        poll_step = min(0.05, self.flush_interval_seconds)

        while True:
            if batch:
                elapsed = time.monotonic() - batch_start_time
                remaining = max(0.0, self.flush_interval_seconds - elapsed)
                wait_timeout = min(remaining, poll_step)
            else:
                wait_timeout = poll_step

            try:
                row, row_bytes = self._queue.get(timeout=wait_timeout)
                with self._queue_lock:
                    self._queue_bytes = max(0, self._queue_bytes - row_bytes)
                batch.append(row)
                if batch_start_time is None:
                    batch_start_time = time.monotonic()
            except queue.Empty:
                pass

            should_flush = False
            if batch:
                if len(batch) >= self.batch_size:
                    should_flush = True
                elif (
                    time.monotonic() - batch_start_time >= self.flush_interval_seconds
                ):
                    should_flush = True
                elif (
                    (self._flush_event.is_set() or self._stop_event.is_set())
                    and self._queue.empty()
                ):
                    should_flush = True

            if should_flush:
                self._insert_batch_with_retry(batch)
                batch = []
                batch_start_time = None

            if self._flush_event.is_set() and not batch and self._queue.empty():
                self._flush_event.clear()
                self._flush_done_event.set()

            if self._stop_event.is_set() and not batch and self._queue.empty():
                break

    def log_event_telemetry(
        self,
        event_id,
        tokens,
        payload,
        result,
        model_name,
        task,
        time_spent,
        service_tier,
    ):
        try:
            row, approx_bytes = self._build_telemetry_row(
                event_id,
                tokens,
                payload,
                result,
                model_name,
                task,
                time_spent,
                service_tier,
            )

            if not self.async_telemetry:
                self._insert_batch_with_retry([row])
                return

            with self._queue_lock:
                if self._closed:
                    logging.warning(
                        "Telemetria descartada: ClickHouseDb já está encerrado."
                    )
                    return

                if (
                    self._queue.qsize() >= self.queue_maxsize
                    or self._queue_bytes + approx_bytes > self._queue_max_bytes
                ):
                    logging.warning(
                        f"Fila de telemetria cheia (eventos={self._queue.qsize()}/{self.queue_maxsize}, "
                        f"bytes={self._queue_bytes + approx_bytes}/{self._queue_max_bytes}). "
                        f"Evento '{event_id}' descartado."
                    )
                    return

                try:
                    self._queue.put_nowait((row, approx_bytes))
                    self._queue_bytes += approx_bytes
                except queue.Full:
                    logging.warning(
                        f"Fila de telemetria atingiu o limite ({self.queue_maxsize}). "
                        f"Evento '{event_id}' descartado."
                    )
        except Exception as e:
            logging.error(f"Observabilidade falhou: {e}")

    def flush(self, timeout: float = 5.0) -> bool:
        """Drena eventos pendentes na fila assíncrona até o limite de timeout."""
        if (
            not self.async_telemetry
            or self._worker_thread is None
            or not self._worker_thread.is_alive()
        ):
            return True
        with self._flush_lock:
            self._flush_done_event.clear()
            self._flush_event.set()
            return self._flush_done_event.wait(timeout=timeout)

    def close(self, timeout: float = 5.0):
        """Realiza flush gracioso da fila e fecha a conexão persistente do ClickHouse."""
        with self._queue_lock:
            if self._closed:
                return
            self._closed = True

        if self.async_telemetry and self._worker_thread is not None:
            self._flush_event.set()
            self._stop_event.set()
            if self._worker_thread.is_alive():
                self._worker_thread.join(timeout=timeout)

        with self._lock:
            self._reset_client()
