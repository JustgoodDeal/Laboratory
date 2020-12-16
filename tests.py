import os

def test_outcome_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path) as file:
        data = file.readline()
        lines_count = 0
        while data:
            data = data.split(';')
            if not len(data) == 11:
                return
            data = file.readline()
            lines_count += 1
        return lines_count == 100



