#To open a file for reading it is enough to specify the name of the file:
f=open("example1.txt")
print()

'''To open the file, use the built-in open() function.

The open() function returns a file object, which has a read() method for reading the content of the file:'''
f=open("example1.txt")
print(f.read())

print()

#now thats how to read the file from another location

x=open(r"C:\Users\kazir\pp2new\practice6\difloc.txt")
print(x.read())
print()

'''It is a good practice to always close the file when you are done with it.

If you are not using the with statement, you must write a close statement in order to close the file:'''

f = open("example1.txt")
print(f.readline())
f.close()
#readline usually only prints one line per time

print()


#read only some parts of the files
with open("example1.txt") as f:
  print(f.read(5))