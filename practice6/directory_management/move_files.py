import os
# rename file (same as move in Python)
os.rename("old.txt", "new.txt")

#Move a file to another folder
import shutil

# move file to another folder
shutil.move("file.txt", "target_folder/file.txt")

#Copy a file
import shutil

shutil.copy("file.txt", "backup/file.txt")

#Move multiple files with a pattern
import glob
import shutil

for f in glob.glob("*.txt"):
    shutil.move(f, "text_files/" + f)
    