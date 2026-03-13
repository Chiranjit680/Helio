import logging
import requests
import traceback
from datetime import datetime
import queue
import threading


class MonitoringLogHandler(logging.Handler):

    def __init__(
        self,
        monitoring_url: str = "http://localhost:8004/api/logs",
        service_name: str = "unknown_service",
        timeout: int = 2
    ):
        super().__init__()
        self.monitoring_url = monitoring_url
        self.service_name = service_name.strip().lower().replace(" ", "_")
        self.timeout = timeout
        self.session = requests.Session()
        self.log_queue = queue.Queue(maxsize=1000)

        # 🔥 START BACKGROUND WORKER
        self.worker = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.worker.start()

    def emit(self, record: logging.LogRecord):
        print("EMIT CALLED:", record.getMessage())

        payload = {
            "service_name": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "traceback": ''.join(traceback.format_exception(*record.exc_info))
            if record.exc_info else None
        }

        try:
            self.log_queue.put_nowait(payload)
        except queue.Full:
            print("Queue full, dropping log")

    def _process_queue(self):
        print("Background worker started")

        while True:
            try:
                payload = self.log_queue.get(timeout=1)
                self._send(payload)
            except queue.Empty:
                continue

    def _send(self, payload):
        try:
            print("Sending log to monitoring service:", payload["message"])
            response = self.session.post(
                self.monitoring_url,
                json=payload,
                timeout=self.timeout
            )
            print("Response:", response.status_code)
        except Exception as e:
            print("HTTP ERROR:", e)
def setup_monitoring_logger(
    service_name: str,
    monitoring_url: str = "http://localhost:8004/api/logs",
    log_level: int = logging.INFO
) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)
    handler = MonitoringLogHandler(
        monitoring_url=monitoring_url,
        service_name=service_name
    )
    logger.addHandler(handler)
    return logger