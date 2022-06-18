from concurrent.futures import ThreadPoolExecutor, wait
from multiprocessing import Lock


class ThreadPoolSingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ThreadPoolSingelton(metaclass=ThreadPoolSingletonMeta):
    """
    We'll use this property to prove that our Singleton really works.
    """

    def __init__(self, max_workers=10) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._process_list = []
        self._process_list_mutex = Lock()
        self._process_files_list = []
        self._process_files_list_mutex = Lock()

    def wait(self):
        wait(self._process_list)
        return

    def add_job(self, process, *args, **kwargs):
        with self._process_list_mutex:
            future = self._executor.submit(process, *args, **kwargs)
            self._process_list.append(future)

    def add_job_name(self, job_name):
        with self._process_files_list_mutex:
            self._process_files_list.append(job_name)
            print(self._process_files_list, len(self._process_files_list))

    def job_finished(self, job_name):
        with self._process_files_list_mutex:
            self._process_files_list.remove(job_name)
