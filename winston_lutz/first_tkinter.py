import tkinter as tk

window = tk.Tk()

frame_a = tk.Frame(master=window, borderwidth=1, relief=tk.RAISED)
frame_b = tk.Frame(master=window)

label_a = tk.Label(master=frame_a, text="I'm in frame a")
label_a.pack()

tk.Label(master=frame_b, text="I'm in frame b").pack()

frame_a.pack()
frame_b.pack()

# print(name[0])

window.mainloop()
