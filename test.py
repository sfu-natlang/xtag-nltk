from Tkinter import *    

def returnPressed(event):
    print repr(event.widget)

master = Tk()
master.bind("<Return>", returnPressed)
myStringVar = StringVar(value="Foo")
myEntry = Entry(master, textvariable=myStringVar)
myEntry.grid()
master.mainloop()