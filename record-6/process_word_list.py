import os

WORD_DIR = "words"
OUTPUT_FILE = os.path.join(WORD_DIR, "3000words.txt")
INPUT_FILE = os.path.join(WORD_DIR, "10k.txt")

if __name__ == "__main__":
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        words = f.readlines()
    
    filtered_words = []
    for word in words:
        word = word.strip()
        if len(word) > 1 and ' ' not in word:
            filtered_words.append(word)
            if len(filtered_words) == 3000:
                break
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for word in filtered_words:
            f.write(word + '\n')