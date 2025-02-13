import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import traceback

# load config
CONFIG_FILENAME = "config.json"
RESPONSES_FILENAME = "questionnaire_responses.json"

# load json config file
def load_config():
    if os.path.isfile(CONFIG_FILENAME):
        try:
            with open(CONFIG_FILENAME, "r") as f:
                return json.load(f)
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("error", f"failed to load config: {e}")
            return None
    else:
        messagebox.showerror("error", f"configuration file '{CONFIG_FILENAME}' not found. create one in settings.")
        return None

# participant sorting
def participant_sort_key(pn):
    match = re.match(r'^([a-zA-Z]+)(\d+)$', pn)
    if match:
        group_letters = match.group(1).lower()
        number_part = int(match.group(2))
        return (group_letters, number_part)
    else:
        return ("zzz", float('inf'))

# scrolled frame helper
class ScrolledFrame(ttk.Frame):
    # helper frame with scrollbar
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def get_frame(self):
        return self.inner_frame

# main app
class QuestionnaireApp(tk.Tk):
    # init main app window
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        app_settings = self.config_data.get("app_settings", {})
        self.title(app_settings.get("window_title"))
        self.geometry(app_settings.get("window_size"))
        self.participant_regex = app_settings.get("participant_regex", r'^[a-zA-Z]+\d+$')
        self.responses = self.load_responses()
        self.current_index = 0
        self.create_widgets()
        if not self.responses:
            self.new_response()
        else:
            self.load_response_to_gui()

    # load responses from json file
    def load_responses(self):
        if os.path.isfile(RESPONSES_FILENAME):
            try:
                with open(RESPONSES_FILENAME, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    # save responses to json file
    def save_responses(self):
        with open(RESPONSES_FILENAME, "w") as f:
            json.dump(self.responses, f, indent=2)

    # ui setup
    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5, fill="x")
        self.participant_combobox = ttk.Combobox(top_frame, state="readonly", width=5)
        self.participant_combobox.pack(side=tk.LEFT, padx=5)
        self.participant_combobox.bind("<<ComboboxSelected>>", self.on_participant_select)
        self.visualize_button = ttk.Button(top_frame, text="Visualize", command=self.open_visualization_options)
        self.visualize_button.pack(side=tk.RIGHT, padx=5)
        self.update_participant_combobox()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.participant_frame = ttk.Frame(self.notebook)
        self.ratings_tab = ttk.Frame(self.notebook)
        self.open_questions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.participant_frame, text="Participant")
        self.notebook.add(self.ratings_tab, text="Ratings")
        self.notebook.add(self.open_questions_tab, text="Open Questions")
        self.create_participant_widgets()
        self.create_ratings_widgets()
        self.create_open_questions_widgets()
        self.create_navigation_buttons()

    # create participant widget
    def create_participant_widgets(self):
        ttk.Label(self.participant_frame, text="Participant ID (e.g. 'a1'):").pack(pady=5)
        self.participant_entry = ttk.Entry(self.participant_frame)
        self.participant_entry.pack(pady=5)

    # create ratings widgets
    def create_ratings_widgets(self):
        self.rating_vars = []
        rating_settings = self.config_data.get("rating_settings", {})
        questions = rating_settings.get("questions", [])
        default_range = rating_settings.get("default_rating_range", [1, 5])
        start_val, end_val = default_range
        rating_values = [str(x) for x in range(start_val, end_val + 1)]
        self.ratings_scrolled = ScrolledFrame(self.ratings_tab)
        self.ratings_scrolled.pack(fill="both", expand=True)
        container = self.ratings_scrolled.get_frame()
        for i, q_obj in enumerate(questions, start=1):
            statement = q_obj.get("statement", f"Question {i}")
            ttk.Label(container, text=f"Rating {i}: {statement}").pack(pady=5)
            var = tk.StringVar()
            ttk.Combobox(container, textvariable=var, values=rating_values, state="readonly").pack(pady=5)
            is_neg = q_obj.get("is_negative", False)
            self.rating_vars.append((var, is_neg))

    # create open question widgets
    def create_open_questions_widgets(self):
        self.open_entries = []
        open_questions = self.config_data.get("open_questions_settings", {}).get("questions", [])
        self.open_scrolled = ScrolledFrame(self.open_questions_tab)
        self.open_scrolled.pack(fill="both", expand=True)
        container = self.open_scrolled.get_frame()
        for i, question in enumerate(open_questions, start=1):
            ttk.Label(container, text=f"Open Question {i}: {question}").pack(pady=5)
            text_widget = tk.Text(container, width=60, height=5, wrap="word")
            text_widget.pack(pady=5)
            self.open_entries.append(text_widget)

    # create nav buttons
    def create_navigation_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        self.button_previous = ttk.Button(button_frame, text="Previous", command=self.previous_response)
        self.button_next = ttk.Button(button_frame, text="Next", command=self.next_response)
        self.button_new = ttk.Button(button_frame, text="New", command=self.new_response)
        self.button_save = ttk.Button(button_frame, text="Save", command=self.save_current_response)
        self.button_delete = ttk.Button(button_frame, text="Delete", command=self.delete_current_response)
        self.button_export = ttk.Button(button_frame, text="Export", command=self.export_responses)
        self.button_previous.grid(row=0, column=0, padx=5, pady=5)
        self.button_next.grid(row=0, column=1, padx=5, pady=5)
        self.button_new.grid(row=0, column=2, padx=5, pady=5)
        self.button_save.grid(row=1, column=0, padx=5, pady=5)
        self.button_delete.grid(row=1, column=1, padx=5, pady=5)
        self.button_export.grid(row=1, column=2, padx=5, pady=5)

    # participant logic: update combobox
    def update_participant_combobox(self):
        participant_nums = [resp["participant_number"] for resp in self.responses]
        sorted_nums = sorted(participant_nums, key=participant_sort_key)
        self.participant_combobox['values'] = sorted_nums
        if sorted_nums:
            current_pn = self.responses[self.current_index]["participant_number"]
            self.participant_combobox.set(current_pn)
        else:
            self.participant_combobox.set('')

    # participant logic: load selected participant
    def on_participant_select(self, event):
        selected = self.participant_combobox.get()
        for idx, resp in enumerate(self.responses):
            if resp["participant_number"] == selected:
                self.current_index = idx
                self.load_response_to_gui()
                break

    # crud: load response into gui
    def load_response_to_gui(self):
        resp = self.responses[self.current_index]
        self.participant_entry.delete(0, tk.END)
        self.participant_entry.insert(0, resp.get("participant_number", ""))
        rating_data = resp.get("ratings", {})
        for i, (var, is_neg) in enumerate(self.rating_vars, start=1):
            raw_val = rating_data.get(f"rating_{i}", "")
            var.set(str(raw_val))
        open_data = resp.get("open_answers", {})
        for i, txt in enumerate(self.open_entries, start=1):
            val = open_data.get(f"open_{i}", "")
            txt.delete("1.0", tk.END)
            txt.insert(tk.END, val)
        self.participant_combobox.set(resp["participant_number"])

    # crud: new response
    def new_response(self):
        rating_settings = self.config_data.get("rating_settings", {})
        questions = rating_settings.get("questions", [])
        num_qs = len(questions)
        open_qs = self.config_data.get("open_questions_settings", {}).get("questions", [])
        num_open = len(open_qs)
        blank_ratings = {f"rating_{i}": "" for i in range(1, num_qs + 1)}
        blank_opens = {f"open_{i}": "" for i in range(1, num_open + 1)}
        new_resp = {
            "participant_number": "",
            "ratings": blank_ratings,
            "open_answers": blank_opens
        }
        self.current_index = len(self.responses)
        self.responses.append(new_resp)
        self.load_response_to_gui()
        self.update_participant_combobox()

    # crud: save current response
    def save_current_response(self):
        participant_number = self.participant_entry.get().strip()
        if not re.match(self.participant_regex, participant_number):
            messagebox.showerror("error", "invalid participant id (e.g. 'a1, a2, b1').")
            return
        rating_settings = self.config_data["rating_settings"]
        force_ratings = rating_settings.get("force_ratings", False)
        rating_dict = {}
        for i, (var, is_neg) in enumerate(self.rating_vars, start=1):
            val_str = var.get().strip()
            if force_ratings and not val_str:
                messagebox.showerror("error", "please answer all rating questions.")
                return
            if val_str.isdigit():
                rating_dict[f"rating_{i}"] = int(val_str)
            else:
                rating_dict[f"rating_{i}"] = val_str
        open_answers = {}
        open_qs = self.config_data.get("open_questions_settings", {}).get("questions", [])
        for i, txt in enumerate(self.open_entries, start=1):
            ans = txt.get("1.0", tk.END).strip()
            if force_ratings and not ans:
                messagebox.showerror("error", "please fill all open questions.")
                return
            open_answers[f"open_{i}"] = ans
        self.responses[self.current_index] = {
            "participant_number": participant_number,
            "ratings": rating_dict,
            "open_answers": open_answers
        }
        self.save_responses()
        messagebox.showinfo("success", "response saved.")
        self.update_participant_combobox()

    # crud: delete response
    def delete_current_response(self):
        if messagebox.askyesno("delete", "are you sure you want to delete this response?"):
            del self.responses[self.current_index]
            self.save_responses()
            if self.responses:
                self.current_index = min(self.current_index, len(self.responses) - 1)
                self.load_response_to_gui()
            else:
                self.new_response()
            self.update_participant_combobox()

    # crud: previous response
    def previous_response(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_response_to_gui()

    # crud: next response
    def next_response(self):
        if self.current_index < len(self.responses) - 1:
            self.current_index += 1
            self.load_response_to_gui()

    # export responses
    def export_responses(self):
        if not self.responses:
            messagebox.showinfo("no data", "no responses to export.")
            return
        file_path = filedialog.asksaveasfilename(
            title="export responses",
            defaultextension=".csv",
            filetypes=[("csv files", "*.csv"), ("text files", "*.txt"), ("all files", "*.*")]
        )
        if not file_path:
            return
        num_ratings = len(self.config_data.get("rating_settings", {}).get("questions", []))
        num_open = len(self.config_data.get("open_questions_settings", {}).get("questions", []))
        if file_path.lower().endswith(".csv"):
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    header = ["Participant Number"]
                    for i in range(1, num_ratings + 1):
                        header.append(f"Rating {i}")
                    for i in range(1, num_open + 1):
                        header.append(f"Open Answer {i}")
                    writer.writerow(header)
                    for resp in self.responses:
                        row = [resp.get("participant_number", "")]
                        ratings = resp.get("ratings", {})
                        for i in range(1, num_ratings + 1):
                            row.append(ratings.get(f"rating_{i}", ""))
                        open_answers = resp.get("open_answers", {})
                        for i in range(1, num_open + 1):
                            row.append(open_answers.get(f"open_{i}", ""))
                        writer.writerow(row)
                messagebox.showinfo("success", f"responses exported as csv to {file_path}")
            except Exception as e:
                messagebox.showerror("export error", f"error exporting csv: {e}")
        else:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for resp in self.responses:
                        f.write(f"Participant: {resp.get('participant_number', '')}\n")
                        f.write("Ratings:\n")
                        for key, value in resp.get("ratings", {}).items():
                            f.write(f"  {key}: {value}\n")
                        f.write("Open Answers:\n")
                        for key, value in resp.get("open_answers", {}).items():
                            f.write(f"  {key}: {value}\n")
                        f.write("-" * 40 + "\n")
                messagebox.showinfo("success", f"responses exported to {file_path}")
            except Exception as e:
                messagebox.showerror("export error", f"error exporting: {e}")

    # visualization
    def open_visualization_options(self):
        if not self.responses:
            messagebox.showinfo("no data", "no responses to visualize.")
            return
        vis_window = tk.Toplevel(self)
        vis_window.title("visualizations")
        vis_window.geometry("1200x1000")
        notebook = ttk.Notebook(vis_window)
        notebook.pack(fill="both", expand=True)
        self.figures = {}
        # box plot
        df = pd.DataFrame(self.responses)
        df["Group"] = df["participant_number"].str[0]
        rating_columns = [col for col in df.iloc[0]["ratings"].keys()]
        for col in rating_columns:
            df[col] = df["ratings"].apply(lambda x: x.get(col, np.nan))
        rating_settings = self.config_data.get("rating_settings", {})
        questions = rating_settings.get("questions", [])
        start_val, end_val = rating_settings.get("default_rating_range", [1, 5])
        for i, q_obj in enumerate(questions, start=1):
            col_name = f"rating_{i}"
            if q_obj.get("is_negative", False):
                df[col_name] = df[col_name].apply(lambda val: (end_val + 1) - val if pd.notnull(val) else val)
        grouped_data = {}
        for group in df["Group"].unique():
            group_rows = df[df["Group"] == group]
            grouped_data[group] = group_rows[rating_columns].mean(axis=1)
        fig_box, ax_box = plt.subplots(figsize=(10, 6))
        ax_box.boxplot(
            grouped_data.values(),
            widths=0.7,
            labels=grouped_data.keys(),
            flierprops=dict(marker='o', color='red', markersize=6),
            medianprops={'color': 'orange', 'linewidth': 2},
            boxprops={'color': 'black', 'linewidth': 1.5},
            whiskerprops={'color': 'black', 'linewidth': 1.5},
            capprops={'color': 'black', 'linewidth': 1.5}
        )
        ax_box.set_title("box plot - group ratings with outliers")
        ax_box.set_xlabel("groups")
        ax_box.set_ylabel("ratings")
        ax_box.grid(True, linestyle='--', alpha=0.7)
        self.figures["Box Plot"] = fig_box
        frame_box = ttk.Frame(notebook)
        notebook.add(frame_box, text="Box Plot")
        canvas_box = FigureCanvasTkAgg(fig_box, master=frame_box)
        canvas_box.draw()
        canvas_box.get_tk_widget().pack(fill="both", expand=True)
        # heatmap
        colormap = self.config_data.get("visualization_settings", {}).get("plot_defaults", {}).get("heatmap_colormap", "viridis")
        sorted_participants = sorted(
            [resp["participant_number"] for resp in self.responses],
            key=participant_sort_key
        )
        participant_dict = {}
        for resp in self.responses:
            pn = resp["participant_number"]
            rating_dict = resp.get("ratings", {})
            adjusted_scores = []
            for i, q_obj in enumerate(questions, start=1):
                raw_val = rating_dict.get(f"rating_{i}", "")
                if isinstance(raw_val, int):
                    val = raw_val
                elif isinstance(raw_val, str) and raw_val.isdigit():
                    val = int(raw_val)
                else:
                    val = np.nan
                if not np.isnan(val) and q_obj.get("is_negative", False):
                    val = (end_val + 1) - val
                adjusted_scores.append(val)
            participant_dict[pn] = adjusted_scores
        data = np.array([participant_dict[pn] for pn in sorted_participants], dtype=float)
        data_heat = data.T
        fig_heatmap, ax_heatmap = plt.subplots(figsize=(8, 5))
        im = ax_heatmap.imshow(
            data_heat,
            cmap=colormap,
            aspect="auto",
            vmin=start_val,
            vmax=end_val
        )
        ax_heatmap.set_title("individual rating heatmap")
        ax_heatmap.set_xlabel("participants")
        ax_heatmap.set_ylabel("statement index")
        ax_heatmap.set_xticks(np.arange(len(sorted_participants)))
        ax_heatmap.set_xticklabels(sorted_participants, rotation=45, ha="right", fontsize=6)
        ax_heatmap.set_yticks(np.arange(len(questions)))
        ax_heatmap.set_yticklabels([f"{i}" for i in range(1, len(questions) + 1)])
        cbar = fig_heatmap.colorbar(im, ax=ax_heatmap)
        cbar.ax.set_ylabel(f"score range ({start_val}-{end_val})", rotation=-90, va="bottom")
        fig_heatmap.tight_layout()
        self.figures["Heatmap"] = fig_heatmap
        frame_heat = ttk.Frame(notebook)
        notebook.add(frame_heat, text="Heatmap")
        canvas_heat = FigureCanvasTkAgg(fig_heatmap, master=frame_heat)
        canvas_heat.draw()
        canvas_heat.get_tk_widget().pack(fill="both", expand=True)
        # custom plot tab
        frame_custom = ttk.Frame(notebook)
        notebook.add(frame_custom, text="Custom Plot")
        ttk.Label(
            frame_custom,
            text=(
                "'responses' is provided by the app. Each response is a dict with keys:\n"
                "• 'participant_number'\n"
                "• 'ratings' (which is itself a dict)."
            )
        ).pack(pady=5)
        custom_code_text = tk.Text(frame_custom, wrap="word", height=15)
        custom_code_text.pack(padx=5, pady=5, fill="both", expand=True)
        sample_code = '''\
import matplotlib.pyplot as plt
import numpy as np

participants = []
average_ratings = []

for resp in responses:
    participant = resp.get("participant_number", "Unknown")
    ratings = resp.get("ratings", {})
    valid_ratings = []
    for key, val in ratings.items():
        try:
            valid_ratings.append(float(val))
        except Exception:
            continue
    if valid_ratings:
        avg_rating = np.mean(valid_ratings)
    else:
        avg_rating = 0
    participants.append(participant)
    average_ratings.append(avg_rating)

fig, ax = plt.subplots(figsize=(8, 6))
ax.bar(participants, average_ratings, color='skyblue')
ax.set_title("average ratings per participant")
ax.set_xlabel("participant")
ax.set_ylabel("average rating")
plt.xticks(rotation=45)
'''
        custom_code_text.insert("1.0", sample_code)
        ttk.Button(frame_custom, text="Run Custom Code",
                   command=lambda: self.run_custom_code(custom_code_text, notebook)
                  ).pack(pady=5)
        ttk.Button(vis_window, text="Save Plot", command=lambda: self.save_plot(notebook)).pack(pady=5)

    # save plot
    def save_plot(self, notebook):
        current_tab = notebook.select()
        tab_text = notebook.tab(current_tab, "text")
        fig = self.figures.get(tab_text)
        if not fig:
            messagebox.showerror("error", "no plot available to save.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("png image", "*.png"), ("pdf file", "*.pdf"), ("all files", "*.*")],
            title="save plot"
        )
        if file_path:
            fig.savefig(file_path)
            messagebox.showinfo("success", f"plot saved to {file_path}")

    # custom code exec
    def run_custom_code(self, text_widget, notebook):
        code = text_widget.get("1.0", tk.END)
        try:
            compiled_code = compile(code, '<string>', 'exec')
        except Exception:
            messagebox.showerror("syntax error", f"syntax error in custom code:\n{traceback.format_exc()}")
            return
        rating_settings = self.config_data.get("rating_settings", {})
        open_questions_settings = self.config_data.get("open_questions_settings", {})
        keyword_settings = self.config_data.get("keyword_settings", {})
        visualization_settings = self.config_data.get("visualization_settings", {})
        try:
            df = pd.DataFrame(self.responses)
            if not df.empty and "ratings" in df.columns:
                rating_columns = list(df.iloc[0]["ratings"].keys())
                for col in rating_columns:
                    df[col] = df["ratings"].apply(lambda x: x.get(col, np.nan))
        except Exception:
            df = None
        local_ns = {
            'plt': plt,
            'np': np,
            'pd': pd,
            'responses': self.responses,
            'config': self.config_data,
            'rating_settings': rating_settings,
            'open_questions_settings': open_questions_settings,
            'keyword_settings': keyword_settings,
            'visualization_settings': visualization_settings,
            'df': df
        }
        try:
            exec(compiled_code, local_ns)
            if 'fig' in local_ns and isinstance(local_ns['fig'], plt.Figure):
                fig = local_ns['fig']
            else:
                messagebox.showerror("no figure", "custom code did not produce a valid matplotlib figure (expected variable 'fig').")
                return
            frame_new = ttk.Frame(notebook)
            tab_name = f"Custom Plot {len(notebook.tabs())}"
            notebook.add(frame_new, text=tab_name)
            canvas_new = FigureCanvasTkAgg(fig, master=frame_new)
            canvas_new.draw()
            canvas_new.get_tk_widget().pack(fill="both", expand=True)
            self.figures[tab_name] = fig
            notebook.select(frame_new)
        except Exception:
            messagebox.showerror("error executing code", f"error executing custom code:\n{traceback.format_exc()}")

if __name__ == "__main__":
    app = QuestionnaireApp()
    app.mainloop()