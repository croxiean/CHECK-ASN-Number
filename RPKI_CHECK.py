import asyncio
import aiohttp
import tkinter as tk
from tkinter import ttk
import pyperclip
from datetime import datetime
import os

#
file_name = "asn.txt"  
file_path = os.path.abspath(file_name)  
asn_file = open(file_name, "a+", encoding="utf-8")  

async def check_rpki_single(ip_address, resource="3333"):
    """Tek bir IP adresinin RPKI durumunu asenkron olarak kontrol eder."""
    url = f"https://stat.ripe.net/data/rpki-validation/data.json?resource={resource}&prefix={ip_address}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data['data']['validating_roas']:
                    asn_list = [roa['origin'] for roa in data['data']['validating_roas']]
                    return ip_address, asn_list
                else:
                    return ip_address, ["No ROAs found"]
            else:
                return ip_address, ["Error fetching data"]

async def check_rpki_multiple(ip_addresses, resource="3333"):
    tasks = [check_rpki_single(ip, resource) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    return dict(results)

def load_ip_list():
    ip_addresses = text_input.get("1.0", tk.END).splitlines()
    rpki_results = asyncio.run(check_rpki_multiple(ip_addresses))
    listbox.delete(0, tk.END)
    for ip, asn_list in rpki_results.items():
        asn_display = ", ".join(asn_list)
        listbox.insert(tk.END, f"{ip} - {asn_display}")

def filter_results():
    ip_addresses = text_input.get("1.0", tk.END).splitlines()
    rpki_results = asyncio.run(check_rpki_multiple(ip_addresses))
    listbox.delete(0, tk.END)
    
    asn_file.seek(0)
    existing_asns = [line.strip() for line in asn_file.readlines()]
    
    for ip, asn_list in rpki_results.items():
        # Sadece dosyada kayıtlı olmayan ASN'leri gösterir
        if not any(asn in existing_asns for asn in asn_list):
            asn_display = ", ".join(asn_list)
            listbox.insert(tk.END, f"{ip} - {asn_display}")

def clear_all():
    text_input.delete("1.0", tk.END)
    listbox.delete(0, tk.END)
    asn_input.delete(0, tk.END)
    last_asn_label.config(text="En son eklenen ASN: ")
    alert_label.config(text="")
    overwrite_button.grid_remove()

def copy_results():
    results_text = "\n".join(listbox.get(0, tk.END)) 
    pyperclip.copy(results_text)

def check_asn_in_file(asn_number):
    asn_file.seek(0)  
    for line in asn_file:
        if asn_number == line.strip():
            return True
    return False

def overwrite_asn(asn_number):
    # Tüm içeriği okuyup ASN numarasını güncelleriz
    asn_file.seek(0)
    lines = asn_file.readlines()
    
    with open(file_name, "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() == asn_number:
                f.write(asn_number + "\n")  # Üzerine yazılır
            else:
                f.write(line)

    last_asn_label.config(text=f"En son eklenen ASN: {asn_number}")
    alert_label.config(text="")
    overwrite_button.grid_remove()

def save_asn():
    asn_number = asn_input.get()
    if asn_number:
        if check_asn_in_file(asn_number):
            alert_label.config(text="BU RPKI ASN LISTENDE MEVCUT! Uzerine yazmak ister misiniz?")
            overwrite_button.grid(row=9, column=0, columnspan=2)
        else:
            asn_file.write(asn_number + "\n")
            asn_file.flush()  # Hemen dosyaya yazılsın
            last_asn_label.config(text=f"En son eklenen ASN: {asn_number}")
            alert_label.config(text="")
            asn_input.delete(0, tk.END)

def open_asn_file():
    os.startfile(file_name)

def update_file_info():
    last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
    file_info_label.config(text=f"Son Değişiklik: {last_modified_time}")

# GUI setup
root = tk.Tk()
root.title("RPKI Checker")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

text_input = tk.Text(frame, width=50, height=10)
text_input.grid(row=0, column=0, columnspan=2)

listbox = tk.Listbox(frame, width=50, height=10)
listbox.grid(row=1, column=0, columnspan=2, pady=10)

asn_input = ttk.Entry(frame, width=50)
asn_input.grid(row=2, column=0, columnspan=2, pady=10)

open_file_button = ttk.Button(frame, text="Open ASN File", command=open_asn_file)
open_file_button.grid(row=3, column=0)

save_asn_button = ttk.Button(frame, text="Save ASN", command=save_asn)
save_asn_button.grid(row=3, column=1)

load_button = ttk.Button(frame, text="Check RPKI", command=load_ip_list)
load_button.grid(row=4, column=0)

clear_button = ttk.Button(frame, text="Clear", command=clear_all)
clear_button.grid(row=4, column=1)

check_data_button = ttk.Button(frame, text="Check Data", command=filter_results)
check_data_button.grid(row=5, column=0, columnspan=2)

copy_button = ttk.Button(frame, text="Copy Results", command=copy_results)
copy_button.grid(row=6, column=0, columnspan=2)

last_asn_label = ttk.Label(frame, text="En son eklenen ASN: ")
last_asn_label.grid(row=7, column=0, columnspan=2)

alert_label = ttk.Label(frame, text="", foreground="red")
alert_label.grid(row=8, column=0, columnspan=2)

overwrite_button = ttk.Button(frame, text="Evet, uzerine yaz", command=lambda: overwrite_asn(asn_input.get()))
overwrite_button.grid(row=9, column=0, columnspan=2)
overwrite_button.grid_remove()

file_info_label = ttk.Label(frame, text=f"Dosya Yolu: {file_path}", foreground="black")
file_info_label.grid(row=10, column=0, columnspan=2, pady=10)

update_file_info()  # Dosya bilgilerini günceller

root.mainloop()

asn_file.close()

