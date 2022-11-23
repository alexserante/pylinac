import tkinter as tk


def fahrenheit_to_celsius():
    """Convert the value for Fahrenheit to Celsius and insert the
    result into lbl_result.
    """
    fahrenheit = ent_temperature.get()
    celsius = (5 / 9) * (float(fahrenheit) - 32)
    lbl_result["text"] = f"{round(celsius, 2)} \N{DEGREE CELSIUS}"
    pass


window = tk.Tk()
window.title("Temperature converter")
window.resizable(width=False, height=False)

frm_entry = tk.Frame(master=window)
ent_temperature = tk.Entry(master=frm_entry, width=5)
lbl_temp = tk.Label(master=frm_entry, text="\N{DEGREE FAHRENHEIT}")
btn_convert = tk.Button(master=frm_entry, text="\N{RIGHTWARDS BLACK ARROW}",
                        command=fahrenheit_to_celsius)
lbl_result = tk.Label(master=frm_entry, text="\N{DEGREE CELSIUS}")


frm_entry.grid(row=0, column=0, padx=50)
ent_temperature.grid(row=0, column=0, sticky="e")
lbl_temp.grid(row=0, column=1, sticky="w")
btn_convert.grid(row=0, column=2, padx=10, pady=20)
lbl_result.grid(row=0, column=3, padx=10, sticky="w")

window.mainloop()
