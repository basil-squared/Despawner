def add_char_after_first_string(line, char_to_add):
    """
    Adds a character after the first "string" (word) in a given line.
    Assumes "string" refers to the first sequence of non-whitespace characters.
    """
    parts = line.split(maxsplit=1)  # Split into at most two parts: first word and the rest
    if len(parts) > 0:
        first_word = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""
        new_line = first_word + char_to_add + remainder
        return new_line
    else:
        return line

try:
    input_file = open("thelist.txt", 'r')
    all_raw = input_file.readlines()
    input_file.close()

    print(f"Read {len(all_raw)} lines from thelist.txt")

    file_lines = []
    for line in all_raw:
        file_lines.append(line.strip())

    output_lines = []
    for line in file_lines:
        new_line = add_char_after_first_string(line, ',')
        print(new_line)
        output_lines.append(new_line + '\n')

    output_file = open("thelist.csv", "w")
    output_file.writelines(output_lines)
    output_file.close()
except Exception as e:
    print(f"Error: {e}")







