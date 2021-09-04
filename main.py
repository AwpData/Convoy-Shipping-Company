import re

import pandas as pd

print("Input file name")
file_name = str(input()).split(".")
my_df = None
if file_name[1] == "xlsx":
    try:
        my_df = pd.read_excel("{}.xlsx".format(file_name[0]), sheet_name='Vehicles', dtype=str)
    except FileNotFoundError:
        print("Error! File Not Found")
    else:
        my_df.to_csv("{}.csv".format(file_name[0]), index=None, header=True)
        print("{} line{} added to {}.csv".format(my_df["vehicle_id"].count(),
                                                 " was" if my_df["vehicle_id"].count() == 1 else "s were",
                                                 file_name[0]))

else:
    my_df = pd.read_csv("{}.csv".format(file_name[0]))

cells_corrected = 0
for column in my_df:
    for text in my_df[column]:
        old_text = text
        cell_corrected = False
        for letter in text:
            if re.match(r"[a-zA-Z._\s]+", letter) is not None:
                text = text.replace(letter, "")
                cell_corrected = True
        if cell_corrected is True:
            cells_corrected += 1
        my_df[column] = my_df[column].replace([old_text], text)
my_df.to_csv("{}.csv".format(file_name[0] + "[CHECKED]"), index=None, header=True)
print("{} cell{} corrected in {}.csv".format(cells_corrected, " was" if cells_corrected == 1 else "s were",
                                             file_name[0] + "[CHECKED]"))
