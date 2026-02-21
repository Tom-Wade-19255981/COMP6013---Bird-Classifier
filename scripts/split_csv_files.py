import csv
import sys

from pathlib import Path

from src.config import CSV_DATA, FULL_CSV, SPLIT_CSV

""""
Reads compiled data from given CSV file and produces CSVs based on the wav recording files.
"""


def get_file_name(date, time):
        #wav name is formatted as yyyyMMdd_hhmmss
        day, month, year = date.split("/")
        hour, minute = time.split(":")

        if int(minute)<20:
             formatted_minute = "00"
        elif int(minute)<40:
             formatted_minute = "20"
        else:
             formatted_minute = "40"

        return str(year+month+day+"_"+hour+formatted_minute+"00")

def read_csv(file_path):
    csv_files = {}
    bird_count = {}
    #CSV files encoded with UTF-8 with Byte Order Mark
    with open(file_path, newline='', encoding="utf-8-sig") as compiled_csv:
        bird_reader = csv.reader(compiled_csv)

        #Extract csv header
        info_line = ",".join(next(bird_reader))

        for i,bird in enumerate(bird_reader):
            date, time = bird[0].split(" ")
            csv_file = get_file_name(date, time)

            #(Scientific name, common name)
            species = (bird[3],bird[4])

            if species in bird_count:
                bird_count[species] += 1
            else:
                bird_count[species] = 1

            if csv_file in csv_files:
                 csv_files[csv_file].append(bird)
            else:
                 csv_files[csv_file] = [bird]

    return csv_files, info_line, bird_count

def merge_sort(to_sort):
    if len(to_sort) <= 1:
         return to_sort
    
    mid = len(to_sort)//2

    left = merge_sort(to_sort[:mid])
    right = merge_sort(to_sort[mid:])

    return merge(left, right)

def merge(left, right):
    result = []
    i, j = 0, 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    #One of the lists are empty, the other contains one item. Add final item
    result.extend(left[i:])
    result.extend(right[j:])

    return result

def construct_csv(info_line, csv_files):
    out_path = Path(SPLIT_CSV)
    out_path.mkdir(parents=True, exist_ok=True)


    for file, birds in csv_files.items():
        file_path = out_path / f"{file}.csv"

        # print("Writing: ")
        # print([file_path])
        # print([info_line])
        # print(birds)

        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(info_line.split(","))
            writer.writerows(birds)


def count_calls():
    pass


if __name__ == "__main__":
    filename = sys.argv[1]
    file_path = FULL_CSV+filename
    print ("file: ", file_path)
    csv_files, info_line, bird_count = read_csv(file_path)

    print (len(csv_files))
    input()

    filenames = merge_sort(list(csv_files.keys()))

    # for file in filenames:
    #      print(file)

    #https://stackoverflow.com/a/1915631
    sorted_birds = [(k, bird_count[k]) for k in sorted(bird_count, key=bird_count.get, reverse=True)]

    for bird in sorted_birds:
        print (bird)
    
    construct_csv(info_line, csv_files)

    # for file in csv_files:
    #     print(file, ": ", csv_files[file])
        # print(file, ": ")
        # csv_files[file] = merge_sort(csv_files[file])   
        # for bird in csv_files[file]:
        #     print (bird)


        #  print (file[0],":" )
        #  i=0
        #  while i<25 and i < len(csv_files[file]):
        #       print(csv_files[file][i])
        #       i += 1
    





