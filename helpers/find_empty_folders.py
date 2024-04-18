# For each directory in this folder, write the folder name if it contains no files
import os

os.chdir("./29595")
for folder in os.listdir():
    if os.path.isdir(folder):
        if not os.listdir(folder):
            print(folder)
