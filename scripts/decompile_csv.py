import csv
import sys

from src.config import CSV_DATA, DATA_PATH

"""
I was provided with a huge CSV containing all data from all PAM recording locations; this splits them up by location
"""

def read_csv(file_path):
    locations = ["North Control Grassland", "Hedgerow North"]
    csv_files = {}

    with open(file_path, newline="", encoding="UTF-8") as compiled:
        reader = csv.reader(compiled)

        info_line = ",".join(next(reader))

        for instance in reader:
            if instance[5] not in locations:
                continue

            if instance[5] not in csv_files:
                csv_files[instance[5]] = [instance]
            else:
                csv_files[instance[5]].append(instance)

    return csv_files, info_line

def create_csv(csv_files):
    #Parse data into yyyyMMdd_hhmmss
    pass



if __name__ == "__main__":
    filename = sys.argv[1]
    filepath = CSV_DATA + filename

    csv_files, info_line = read_csv(filepath)

    print(info_line)
    for file in csv_files:
        for bird in csv_files[file]:
            print (bird)