import signal
import logging
from threading import Thread
from banal import ensure_list
from abc import ABC, abstractmethod

from servicelayer import settings
from servicelayer.jobs import Stage
from servicelayer.cache import get_redis
from servicelayer.util import unpack_int

log = logging.getLogger(__name__)


class Worker(ABC):
    """Workers of all microservices, unite!"""

    def __init__(self, conn=None, stages=None, num_threads=settings.WORKER_THREADS):
        self.conn = conn or get_redis()
        self.stages = stages
        self.num_threads = num_threads
        self._exit_code = 0

    def _handle_signal(self, signal, frame):
        log.warning("Shutting down worker (signal %s)", signal)
        self._exit_code = 100 + signal

    def handle_safe(self, task):
        try:
            self.handle(task)
        except SystemExit as exc:
            self._exit_code = exc.code
            self.retry(task)
        except KeyboardInterrupt:
            self._exit_code = 23
            self.retry(task)
        except Exception:
            if 0 == self._exit_code:
                self._exit_code = 23
            self.retry(task)
            log.exception("Error in task handling")
        finally:
            task.done()
            self.after_task(task)

    def init_internal(self):
        self._exit_code = 0
        self.boot()

    def retry(self, task):
        retries = unpack_int(task.context.get("retries"))
        if retries < settings.WORKER_RETRY:
            log.warning("Queue failed task for re-try...")
            task.context["retries"] = retries + 1
            task.stage.queue(task.payload, task.context)

    def process(self, interval=2):
        while True:
            if self._exit_code > 0:
                return self._exit_code
            self.periodic()
            stages = self.get_stages()
            task = Stage.get_task(self.conn, stages, timeout=interval)
            if task is None:
                continue
            self.handle_safe(task)

    def sync(self):
        """Process only the tasks already in the job queue, but do not
        go into an infinte loop waiting for new ones."""
        self.init_internal()
        while True:
            if self._exit_code > 0:
                return self._exit_code
            stages = self.get_stages()
            task = Stage.get_task(self.conn, stages, timeout=None)
            if task is None:
                return 0
            self.handle_safe(task)

    def run(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        self.init_internal()
        if not self.num_threads:
            return self.process()
        log.info("Worker has %d threads.", self.num_threads)
        threads = []
        for _ in range(self.num_threads):
            thread = Thread(target=self.process)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return self._exit_code

    def get_stages(self):
        """Easily allow the user to make the active stages dynamic."""
        return self.stages

    def boot(self):
        """Optional hook for the boot-up of the worker."""
        pass

    def periodic(self):
        """Optional hook for running a periodic task checker."""
        pass

    def after_task(self, task):
        """Optional hook excuted after handling a task"""
        pass

    def dispatch_pipeline(self, task, payload):
        """Some queues use a continuation passing style pipeline argument
        to specify the next steps for a processing chain."""
        pipeline = ensure_list(task.context.get("pipeline"))
        if len(pipeline) == 0:
            return
        next_stage = pipeline.pop(0)
        stage = task.job.get_stage(next_stage)
        context = dict(task.context)
        context["pipeline"] = pipeline
        stage.queue(payload, context)

    @abstractmethod
    def handle(self, task):
        raise NotImplementedError
