from time import perf_counter

class Log:
    def __init__(self, filepath):
        self.filepath = filepath
        self.body_part: str = ""
        self.content: str = ""
        self.speed: str = ""
        self.start = perf_counter()
        self.end = perf_counter()
        # new optional fields
        self.trial_index: int | None = None
        self.stimulus: str = ""
        self.log_cache = []

    def save_log_cache(
        self,
        body_part: str,
        content: str,
        speed: str,
        trial_index: int | None = None,
        stimulus: str = "",
        *,
        qualified: bool | None = None,
        min_valid_duration_s: float | None = None,
    ):
        self.record_end()
        duration_s = self.end - self.start
        if qualified is None:
            if min_valid_duration_s is None:
                qualified = True
            else:
                qualified = duration_s >= min_valid_duration_s

        log = {}
        log['body_part'] = body_part
        # record category ("number"/"alphabet"/"word")
        log['category'] = content
        # record concrete content, e.g., "1", "A", "apple"
        log['content'] = stimulus
        log['speed'] = speed
        log['trial_index'] = trial_index
        log['start'] = self.start
        log['end'] = self.end
        log['duration_s'] = duration_s
        log['qualified'] = qualified
        self.log_cache.append(log)
        return log

    def record_start(self):
        self.start = perf_counter()
    
    def record_end(self):
        self.end = perf_counter()

    def save_log_start(self):
        self.record_start()
        log = {"start": self.start}
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(str(log) + '\n')
    
    def pop_log_cache(self):
        if self.log_cache:
            return self.log_cache.pop()
        return None

    def save_log(self):
        with open(self.filepath, 'a', encoding='utf-8') as f:
            for log in self.log_cache:
                f.write(str(log) + '\n')
        self.log_cache.clear()
