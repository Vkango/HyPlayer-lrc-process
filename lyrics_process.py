"""
处理HyPlayer保存的歌词文件
"""
import os
import re
def process_lrc_line(line):
    match = re.match(r'\[\d{2}:\d{2}.\d{2}\](.*)', line)
    if match:
        timestamp = match.group(0)[0:10]
        content = match.group(1).strip()
        original_translation = content.split(' 「')
        if len(original_translation) == 2:
            original = original_translation[0].strip()
            translation = original_translation[1].split('」')[0].strip()
            return [0,original,translation,timestamp]
    return [1,line]
def process_lrc_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()
    processed_lines = []
    for line in content:
        processed_line = process_lrc_line(line)
        if processed_line[0]==0:
            processed_lines.append(processed_line[3]+processed_line[1]+"\n")
        else:
            processed_lines.append(line)
    for line in content:
        processed_line = process_lrc_line(line)
        if processed_line[0]==0:
            processed_lines.append(processed_line[3]+processed_line[2]+"\n")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(processed_lines)
def traverse_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.lrc'):
                file_path = os.path.join(root, file)
                print(f'Processing {file_path}')
                process_lrc_file(file_path)

directory_path = 'C:\\Users\\Lenovo\\Music\\HyPlayer'
traverse_directory(directory_path)