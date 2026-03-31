import os

#1. Creating directories
os.mkdir("my_folder")

os.makedirs("parent/child/grandchild")

#check if the directory exists
if os.path.exists("my_folder"):
    print("Folder exists")

#List files and folders
files = os.listdir("my_folder")
print(files)

#Get current working directory
cwd = os.getcwd()
print("Current folder:", cwd)

#Loop through all files in a folder

for item in os.listdir("."):
    if os.path.isfile(item):
        print("File:", item)
    else:
        print("Folder:", item)

#Walk through all subdirectories
for root, dirs, files in os.walk("parent_folder"):
    print("Current path:", root)
    print("Folders:", dirs)
    print("Files:", files)


    