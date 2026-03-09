def load_word_list(filepath: str) -> list:
    with open(filepath, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    return words

def load_command_list(filepath: str) -> list:
    with open(filepath, 'r', encoding='utf-8') as f:
        items = []
        for line in f:
            s = line.strip()
            if not s:
                continue
            # remove trailing commas and surrounding quotes
            s = s.rstrip(',')
            if s.startswith('"') and s.endswith('"'):
                s = s[1:-1]
            items.append(s)
    return items

class RecordConfig:
    wordsfile: str = "words/3000words.txt"
    record_dir: str = "records"
    number_list = [str(i) for i in range(10)]
    alphabet_list_lower = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    alphabet_list_upper = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    body_parts = ["board", "palm", "thigh", "pocket", "in-air"]
    speeds = ["medium", "fast", "slow"]
    # 默认采集内容改为手势（从 command.txt 加载）
    contents = ["gesture"]
    word_list = load_word_list(wordsfile)
    word_count: int = 100  # select words randomly from word_list
    # Redefined semantics:
    # - number_times: cycles of 0..9 per block (total items per block = 10 * number_times)
    # - alphabet_times: cycles of A..Z then a..z per block (total items per block = 52 * alphabet_times)
    # - word_times: number of words per block (total items per block = word_times)
    # - password_times: number of random numeric passwords per block (length = password_length)
    number_times: int = 2
    alphabet_times: int = 1
    word_times: int = 10
    password_times: int = 10
    password_length: int = 6
    # gesture list loaded from command.txt in the same folder
    try:
        gesture_list = load_command_list("command.txt")
    except Exception:
        gesture_list = []


