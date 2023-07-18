import time
import threading
from queue import Queue
import tkinter as tk
from tkinter import ttk, filedialog
import json
import csv
import tkinter.messagebox as msgbox
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import folium
from PIL import Image, ImageTk
import gettext

# Configuración de gettext
_ = gettext.translation('loSIEM', localedir='locales', languages=['en', 'es'])
_.install()

class Event:
    def __init__(self, timestamp, source, event_type, description):
        self.timestamp = timestamp
        self.source = source
        self.event_type = event_type
        self.description = description

class loSIEM:
    def __init__(self):
        self.events_queue = Queue()
        self.detected_events = []
        self.database_conn = sqlite3.connect("events.db")
        self.create_events_table()

    def create_events_table(self):
        cursor = self.database_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                          timestamp REAL,
                          source TEXT,
                          event_type TEXT,
                          description TEXT)''')
        self.database_conn.commit()

    def log_event(self, event):
        self.events_queue.put(event)
        self.insert_event_into_database(event)

    def insert_event_into_database(self, event):
        cursor = self.database_conn.cursor()
        cursor.execute("INSERT INTO events VALUES (?, ?, ?, ?)",
                       (event.timestamp, event.source, event.event_type, event.description))
        self.database_conn.commit()

    def load_events_from_database(self, filename):
        self.database_conn = sqlite3.connect(filename)

    def load_events_from_system_logs(self):
        # Implementar la carga de eventos desde registros del sistema (como archivos de log).
        # Aquí, se podría simular la carga de eventos con datos reales.
        pass

    def load_events_from_csv(self, filename):
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp = float(row['timestamp'])
                source = row['source']
                event_type = row['event_type']
                description = row['description']
                event = Event(timestamp, source, event_type, description)
                self.detected_events.append(event)

    def export_events_to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'source', 'event_type', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for event in self.detected_events:
                writer.writerow({'timestamp': event.timestamp,
                                 'source': event.source,
                                 'event_type': event.event_type,
                                 'description': event.description})

    def analyze_events(self):
        while True:
            if not self.events_queue.empty():
                event = self.events_queue.get()
                if "ataque" in event.description.lower():
                    self.detected_events.append(event)
            time.sleep(1)

    def get_event_count_by_type(self):
        event_count = {}
        for event in self.detected_events:
            event_type = event.event_type
            event_count[event_type] = event_count.get(event_type, 0) + 1
        return event_count

    def get_event_count_by_hour(self):
        event_count_by_hour = {}
        for event in self.detected_events:
            timestamp = event.timestamp
            hour = time.strftime("%H", time.localtime(timestamp))
            event_count_by_hour[hour] = event_count_by_hour.get(hour, 0) + 1
        return event_count_by_hour

    def search_online_events(self, keyword):
        # Implementar la búsqueda en línea de eventos relacionados con la keyword.
        # Aquí, se podría simular la búsqueda en línea con datos reales.
        pass

class App:
    def __init__(self, root, siem):
        self.root = root
        self.root.title(_("loSIEM - Creada por Christian de López"))
        self.siem = siem

        self.style = ttk.Style()
        self.style.theme_use("clam")  # Puedes cambiar el tema aquí si lo deseas (opciones: 'clam', 'default', 'alt', 'vista', 'xpnative')

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=_("Archivo"), menu=self.file_menu)
        self.file_menu.add_command(label=_("Cargar Registros del Sistema"), command=self.load_system_logs)
        self.file_menu.add_command(label=_("Cargar desde Base de Datos"), command=self.load_events_from_database)
        self.file_menu.add_command(label=_("Cargar desde Archivo CSV"), command=self.load_events_from_csv)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=_("Exportar Eventos a CSV"), command=self.export_to_csv)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=_("Salir"), command=self.root.quit)

        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill=tk.BOTH, expand=True)

        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab3 = ttk.Frame(self.tab_control)
        self.tab4 = ttk.Frame(self.tab_control)
        self.tab5 = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab1, text=_("Eventos en tiempo real"))
        self.tab_control.add(self.tab2, text=_("Búsqueda en línea"))
        self.tab_control.add(self.tab3, text=_("Tendencias de Eventos"))
        self.tab_control.add(self.tab4, text=_("Mapa de Eventos"))
        self.tab_control.add(self.tab5, text=_("Cargar desde Base de Datos"))

        self.event_list = ttk.Treeview(self.tab1, columns=("Timestamp", "Fuente", "Tipo de Evento", "Descripción"), show="headings")
        self.event_list.heading("Timestamp", text=_("Timestamp"))
        self.event_list.heading("Fuente", text=_("Fuente"))
        self.event_list.heading("Tipo de Evento", text=_("Tipo de Evento"))
        self.event_list.heading("Descripción", text=_("Descripción"))
        self.event_list.column("Timestamp", width=150)
        self.event_list.column("Fuente", width=150)
        self.event_list.column("Tipo de Evento", width=150)
        self.event_list.column("Descripción", width=400)
        self.event_list.pack(padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(self.tab1, orient=tk.VERTICAL, command=self.event_list.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.event_list.config(yscrollcommand=self.scrollbar.set)

        self.event_info_label = ttk.Label(self.tab1, text=_("Información del Evento:"), font=("Helvetica", 12, "bold"))
        self.event_info_label.pack(padx=10, pady=2)

        self.event_info_text = tk.Text(self.tab1, width=100, height=5, wrap=tk.WORD, font=("Helvetica", 11))
        self.event_info_text.pack(padx=10, pady=2)

        self.refresh_button_img = Image.open("refresh.png").resize((20, 20))
        self.refresh_icon = ImageTk.PhotoImage(self.refresh_button_img)
        self.refresh_button = ttk.Button(self.tab1, image=self.refresh_icon, command=self.update_event_list)
        self.refresh_button.pack(padx=10, pady=5)

        self.export_csv_img = Image.open("export.png").resize((20, 20))
        self.export_icon = ImageTk.PhotoImage(self.export_csv_img)
        self.export_csv_button = ttk.Button(self.tab1, image=self.export_icon, command=self.export_to_csv)
        self.export_csv_button.pack(padx=10, pady=5)

        self.delete_img = Image.open("delete.png").resize((20, 20))
        self.delete_icon = ImageTk.PhotoImage(self.delete_img)
        self.delete_button = ttk.Button(self.tab1, image=self.delete_icon, command=self.delete_event)
        self.delete_button.pack(padx=10, pady=5)

        self.search_img = Image.open("search.png").resize((20, 20))
        self.search_icon = ImageTk.PhotoImage(self.search_img)
        self.search_source_button = ttk.Button(self.tab1, image=self.search_icon, command=self.search_online_by_source)
        self.search_source_button.pack(padx=10, pady=5)

        self.filter_label = ttk.Label(self.tab1, text=_("Filtrar por Fuente/Tipo/Descripción:"), font=("Helvetica", 11, "bold"))
        self.filter_label.pack(padx=10, pady=2)

        self.filter_entry = ttk.Entry(self.tab1, width=40, font=("Helvetica", 11))
        self.filter_entry.pack(padx=10, pady=2)

        self.filter_button_img = Image.open("filter.png").resize((20, 20))
        self.filter_icon = ImageTk.PhotoImage(self.filter_button_img)
        self.filter_button = ttk.Button(self.tab1, image=self.filter_icon, command=self.filter_events)
        self.filter_button.pack(padx=10, pady=5)

        self.from_date_label = ttk.Label(self.tab1, text=_("Desde (yyyy-mm-dd):"), font=("Helvetica", 11, "bold"))
        self.from_date_label.pack(padx=10, pady=2)

        self.from_date_entry = ttk.Entry(self.tab1, width=15, font=("Helvetica", 11))
        self.from_date_entry.pack(padx=10, pady=2)

        self.to_date_label = ttk.Label(self.tab1, text=_("Hasta (yyyy-mm-dd):"), font=("Helvetica", 11, "bold"))
        self.to_date_label.pack(padx=10, pady=2)

        self.to_date_entry = ttk.Entry(self.tab1, width=15, font=("Helvetica", 11))
        self.to_date_entry.pack(padx=10, pady=2)

        self.filter_by_date_img = Image.open("filter_date.png").resize((20, 20))
        self.filter_date_icon = ImageTk.PhotoImage(self.filter_by_date_img)
        self.filter_by_date_button = ttk.Button(self.tab1, image=self.filter_date_icon, command=self.filter_events_by_date)
        self.filter_by_date_button.pack(padx=10, pady=5)

        self.total_events_label = ttk.Label(self.tab1, text=_("Total de Eventos: 0"), font=("Helvetica", 11))
        self.total_events_label.pack(padx=10, pady=2)

        self.update_event_list()
        self.analyze_events_thread = threading.Thread(target=self.siem.analyze_events)
        self.analyze_events_thread.daemon = True
        self.analyze_events_thread.start()

    def update_event_list(self):
        self.event_list.delete(*self.event_list.get_children())
        for event in self.siem.detected_events:
            timestamp = time.ctime(event.timestamp)
            self.event_list.insert("", "end", values=(timestamp, event.source, event.event_type, event.description))
        self.total_events_label.config(text=_("Total de Eventos: {0}").format(len(self.siem.detected_events)))

    def delete_event(self):
        selected_item = self.event_list.selection()
        if selected_item:
            item_id = self.event_list.item(selected_item, 'values')
            timestamp = time.mktime(time.strptime(item_id[0], "%c"))
            self.siem.detected_events = [event for event in self.siem.detected_events if event.timestamp != timestamp]
            self.update_event_list()

    def show_full_event_info(self):
        selected_item = self.event_list.selection()
        if selected_item:
            item_id = self.event_list.item(selected_item, 'values')
            timestamp = time.mktime(time.strptime(item_id[0], "%c"))
            selected_event = next((event for event in self.siem.detected_events if event.timestamp == timestamp), None)
            if selected_event:
                event_info = _("Timestamp: {0}\nFuente: {1}\nTipo de Evento: {2}\nDescripción: {3}").format(
                    item_id[0], item_id[1], item_id[2], item_id[3])
                self.event_info_text.delete(1.0, tk.END)
                self.event_info_text.insert(tk.END, event_info)

    def search_online_by_source(self):
        selected_item = self.event_list.selection()
        if selected_item:
            item_id = self.event_list.item(selected_item, 'values')
            keyword = item_id[1]
            if keyword:
                self.siem.search_online_events(keyword)
                self.update_event_list()

    def filter_events(self):
        keyword = self.filter_entry.get().lower()
        filtered_events = [event for event in self.siem.detected_events
                           if keyword in event.source.lower() or
                           keyword in event.event_type.lower() or
                           keyword in event.description.lower()]
        self.siem.detected_events = filtered_events
        self.update_event_list()

    def filter_events_by_date(self):
        from_date_str = self.from_date_entry.get()
        to_date_str = self.to_date_entry.get()
        try:
            from_date = time.mktime(time.strptime(from_date_str, "%Y-%m-%d"))
            to_date = time.mktime(time.strptime(to_date_str, "%Y-%m-%d"))
            filtered_events = [event for event in self.siem.detected_events
                               if from_date <= event.timestamp <= to_date]
            self.siem.detected_events = filtered_events
            self.update_event_list()
        except ValueError:
            msgbox.showerror(_("Error"), _("Formato de fecha inválido. Use yyyy-mm-dd."))

    def load_system_logs(self):
        # Implementar la carga de eventos desde registros del sistema (como archivos de log).
        # Aquí, se podría abrir un cuadro de diálogo para que el usuario seleccione el archivo de log.
        pass

    def load_events_from_database(self):
        file_path = filedialog.askopenfilename(filetypes=[(_("Database Files"), "*.db")])
        if file_path:
            self.siem.load_events_from_database(file_path)
            self.update_event_list()

    def load_events_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[(_("CSV Files"), "*.csv")])
        if file_path:
            self.siem.load_events_from_csv(file_path)
            self.update_event_list()

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[(_("CSV Files"), "*.csv")])
        if file_path:
            self.siem.export_events_to_csv(file_path)

    # ... (Código previo)

def main():
    root = tk.Tk()
    root.geometry("900x600")
    siem = loSIEM()
    app = App(root, siem)
    root.mainloop()

if __name__ == "__main__":
    main()
