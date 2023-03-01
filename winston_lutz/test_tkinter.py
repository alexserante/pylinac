from tkinter import *


def sel():
    print("You selected the option " + str(var.get()))



root = Tk()
var = StringVar()
R1 = Radiobutton(root, text="Option 1", variable=var, value=1)
R1.pack(anchor=W)

R2 = Radiobutton(root, text="Option 2", variable=var, value=2)
R2.pack(anchor=W)

R3 = Radiobutton(root, text="Option 3", variable=var, value=3)
R3.pack(anchor=W)

btn = Button(root, text="click here", command=sel)
btn.pack(anchor=W)

label = Label(root)
label.pack()
root.mainloop()
