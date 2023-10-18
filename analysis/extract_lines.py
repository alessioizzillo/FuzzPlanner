import sys, os

def extract_lines_with_word(file_path, word):
    extracted_lines = []
    
    with open(file_path, 'r') as file:
        for line in file:
            fields = line.strip().split(',')
            
            if len(fields) >= 4 and word in fields[3]:
                extracted_lines.append(line)
    
    return extracted_lines

def save_lines_to_file(lines):
    directory = "extracted_logs/"
    pattern = "run_"
    if os.path.isdir(directory):
        subdirs = [int(subdir[len(pattern):]) for subdir in os.listdir(directory) if subdir.startswith(pattern) and os.path.isdir(os.path.join(directory, subdir))]
        run = f"{pattern}{max(subdirs)+1}" if subdirs else f"{pattern}0"
    else:
        run = f"{pattern}0"

    if not os.path.exists("extracted_logs/"):
        os.makedirs("extracted_logs/")

    outfile = "extracted_logs/%s.log"%(run)

    with open(outfile, 'w') as file:
        file.writelines(lines)

    print("Extraction complete. Extracted lines saved to", outfile)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python extract_lines.py <file_path> <word>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    word = sys.argv[2]
    
    extracted_lines = extract_lines_with_word(file_path, word)
    save_lines_to_file(extracted_lines)
    
