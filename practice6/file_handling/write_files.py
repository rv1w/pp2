'''To write to an existing file, you must add a parameter to the open() function:

"a" - Append - will append to the end of the file

"w" - Write - will overwrite any existing content'''

with open("example2.txt", "a") as f:
  f.write("Now the file has more content!")

#open and read the file after the appending:
with open("example2.txt") as f:
  print(f.read())


#Note: the "w" method will overwrite the entire file.

'''"x" - Create - will create a file, returns an error if the file exists

"a" - Append - will create a file if the specified file does not exists

"w" - Write - will create a file if the specified file does not exists'''
