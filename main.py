import json
import math
import re
import sqlite3

import pandas as pd
from lxml import etree

print("Input file name")
file_name = str(input()).split(".")  # First get the file name
my_df = None

if file_name[1] == "xlsx":  # If file is xlsx, we need to first convert it to csv
    my_df = pd.read_excel("{}.xlsx".format(file_name[0]), sheet_name='Vehicles', dtype=str)
    my_df.to_csv("{}.csv".format(file_name[0]), index=None, header=True)
    print("{} line{} added to {}.csv".format(my_df["vehicle_id"].count(),
                                             " was" if my_df["vehicle_id"].count() == 1 else "s were",
                                             file_name[0]))

elif file_name[1] == "csv":  # Else, we can already read the CSV
    my_df = pd.read_csv("{}.csv".format(file_name[0]))

if file_name[1] != "s3db" and file_name[0].find(
        "[CHECKED]") < 0:  # If the csv file has not been checked yet, it is prone to having letters
    cells_corrected = 0
    for column in my_df:
        for text in my_df[column]:
            old_text = text
            cell_corrected = False
            for letter in text:
                if re.match(r"[a-zA-Z._\s]", letter) is not None:  # If this letter matches the regex pattern
                    text = text.replace(letter, "")  # Replace the letter in the text with nothing
                    cell_corrected = True
            if cell_corrected is True:
                cells_corrected += 1
            my_df[column] = my_df[column].replace([old_text], text)
    corrected_file = my_df.to_csv("{}.csv".format(file_name[0] + "[CHECKED]"), index=None, header=True)
    print("{} cell{} corrected in {}.csv".format(cells_corrected, " was" if cells_corrected == 1 else "s were",
                                                 file_name[0] + "[CHECKED]"))

non_checked_name = file_name[0][0:file_name[0].find("[CHECKED]")] if file_name[0].find("[CHECKED]") > 0 else file_name[
    0]  # First, get rid of the "checked" in the file_name

conn = sqlite3.connect("{}.s3db".format(non_checked_name))  # Connect to the database file
cursor = conn.cursor()
if file_name[1] != "s3db":  # Finally, we can start the conversion to the database IF NOT ALREADY
    with conn:  # Create the table
        cursor.execute("""CREATE TABLE IF NOT EXISTS convoy (
                        vehicle_id INTEGER PRIMARY KEY,
                        engine_capacity INTEGER NOT NULL,
                        fuel_consumption INTEGER NOT NULL,
                        maximum_load INTEGER NOT NULL,
                        score INTEGER NOT NULL);""")

    # Remove the headers since the database already has properly named columns
    file_no_headers = my_df.to_csv("{}.csv".format(non_checked_name + "[NO HEADER]"), index=None, header=False)
    with conn:  # This will Insert each line into the database into their respective columns
        for line in open("{}[NO HEADER].csv".format(non_checked_name), "r"):
            properties = line.split(",")
            conn.execute("INSERT OR IGNORE INTO convoy VALUES (?, ?, ?, ?, 0)",
                         (int(properties[0]), int(properties[1]), int(properties[2]), int(properties[3].strip("\n"))))

    # Get the number of rows
    rows = len(conn.execute("SELECT * FROM convoy").fetchall())
    print("{} record{} inserted into {}.s3db".format(rows, " was" if rows == 1 else "s were", non_checked_name))

with conn:  # Get the values in each row in the database
    data = conn.execute("SELECT * FROM convoy").fetchall()
    for line in data:
        total_gas = line[1]
        fuel_consumption = line[2]
        total_fills = math.floor((450 / ((total_gas / fuel_consumption) * 100)))
        score = 0
        score += 2 if line[3] >= 20 else 0  # Scoring for weight
        score += 1 if total_fills == 1 else 2 if total_fills == 0 else 0  # Scoring for pit stops
        score += 2 if 4.5 * fuel_consumption <= 230 else 1  # Scoring for fuel burned
        conn.execute("UPDATE convoy SET score = ? WHERE vehicle_id = ?", (score, line[0]))  # Update score in database
    data = conn.execute("SELECT * FROM convoy").fetchall()  # Update data again
conn.close()

# Export everything to json file (If their score is > 3)
with open("{}.json".format(non_checked_name), "w") as json_file:
    dict_ = dict()
    dict_["convoy"] = []
    for line in data:
        if line[4] > 3:
            dict_["convoy"].append(
                {"vehicle_id": line[0],
                 "engine_capacity": line[1],
                 "fuel_consumption": line[2],
                 "maximum_load": line[3]})

    json.dump(dict_, json_file)
    print("{} vehicle{} saved into {}.json".format(len(dict_["convoy"]),
                                                   " was" if len(dict_["convoy"]) == 1 else "s were", non_checked_name))

# Now write it to an xml file (ONLY if their score <= 3)
root = "<convoy> "
counter = 0
for line in data:
    if line[4] <= 3:
        root += "<vehicle>"
        root += "<vehicle_id>{}</vehicle_id>".format(line[0])
        root += "<engine_capacity>{}</engine_capacity>".format(line[1])
        root += "<fuel_consumption>{}</fuel_consumption>".format(line[2])
        root += "<maximum_load>{}</maximum_load>".format(line[3])
        root += "</vehicle>"
        counter += 1
root += "</convoy>"

root = etree.fromstring(root)
element_tree = etree.ElementTree(root)
element_tree.write("{}.xml".format(non_checked_name))

print("{} vehicle{} saved into {}.xml".format(counter, " was" if counter == 1 else "s were", non_checked_name))
