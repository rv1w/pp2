import os
#To delete a file, you must import the OS module, and run its os.remove() function:

os.remove("demofile.txt")


'''Example
Check if file exists, then delete it:'''

if os.path.exists("demofile.txt"):
  os.remove("demofile.txt")
else:
  print("The file does not exist")


#To delete an entire folder, use the os.rmdir() method:

os.rmdir("myfolder")