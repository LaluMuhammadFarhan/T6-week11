import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import queue

API_BASE = "https://api.pahrul.my.id/api/posts"
TIMEOUT = 15


class APIError(Exception):
    def __init__(self, message, status_code=0, errors=None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or {}


class PostFormDialog(tk.Toplevel):
    def __init__(self, parent, title, post_data=None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.result = None
        self.post_data = post_data
        self.transient(parent)
        self.grab_set()

        self.geometry("500x480")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = ["title", "body", "author", "slug", "status"]
        self.entries = {}

        row = 0
        for field in fields:
            ttk.Label(frame, text=field.capitalize(), font=("", 10, "bold")).grid(
                row=row, column=0, sticky=tk.W, pady=(10, 2)
            )
            if field == "body":
                txt = tk.Text(frame, height=5, width=50, wrap=tk.WORD)
                txt.grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
                self.entries[field] = txt
                row += 2
            elif field == "status":
                combo = ttk.Combobox(
                    frame, values=["published", "draft"], state="readonly", width=47
                )
                combo.grid(row=row + 1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
                combo.set("draft")
                self.entries[field] = combo
                row += 2
            else:
                entry = ttk.Entry(frame, width=50)
                entry.grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
                self.entries[field] = entry
                row += 2

        if post_data:
            for field in fields:
                val = post_data.get(field, "")
                if field == "body":
                    self.entries[field].insert(1.0, val)
                elif field == "status":
                    self.entries[field].set(val if val in ["published", "draft"] else "draft")
                else:
                    self.entries[field].insert(0, val)

        self.error_label = ttk.Label(frame, text="", foreground="red", wraplength=450)
        self.error_label.grid(row=row, column=0, columnspan=2, pady=(5, 0))
        row += 1

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(15, 0))

        ttk.Button(btn_frame, text="Simpan", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Batal", command=self.destroy).pack(side=tk.LEFT, padx=5)

        frame.columnconfigure(1, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window()

    def _save(self):
        data = {}
        for field, widget in self.entries.items():
            if field == "body":
                val = widget.get(1.0, tk.END).strip()
            else:
                val = widget.get().strip()
            if field == "body" and not val:
                self.error_label.config(text="Body tidak boleh kosong")
                return
            if field != "body" and not val:
                self.error_label.config(text=f"{field.capitalize()} tidak boleh kosong")
                return
            data[field] = val

        self.result = data
        self.destroy()


class PostManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Post Manager")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        self.selected_post_id = None
        self.posts = []
        self.api_queue = queue.Queue()

        self._setup_ui()
        self.root.after(100, self._process_queue)
        self.load_posts()

    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Button(toolbar, text="Refresh", command=self.load_posts).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Tambah Post", command=self.add_post).pack(side=tk.LEFT, padx=2)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Frame(paned)
        paned.add(left, weight=2)

        columns = ("id", "title", "author", "status")
        self.tree = ttk.Treeview(
            left, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("author", text="Author")
        self.tree.heading("status", text="Status")
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=300)
        self.tree.column("author", width=180)
        self.tree.column("status", width=100, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(paned, width=400)
        paned.add(right, weight=1)

        detail_frame = ttk.LabelFrame(right, text="Detail Post", padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.detail_text = tk.Text(
            detail_frame, wrap=tk.WORD, state=tk.DISABLED,
            font=("Helvetica", 10), padx=8, pady=8
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(detail_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_edit = ttk.Button(
            btn_frame, text="Edit", command=self.edit_post, state=tk.DISABLED
        )
        self.btn_edit.pack(side=tk.LEFT, padx=2)

        self.btn_delete = ttk.Button(
            btn_frame, text="Hapus", command=self.delete_post, state=tk.DISABLED
        )
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        self.status_bar = ttk.Label(
            self.root, text="Siap", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.loading = ttk.Progressbar(
            self.root, mode="indeterminate", style="Loading.Horizontal.TProgressbar"
        )

    def _process_queue(self):
        try:
            while True:
                fn = self.api_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _set_status(self, text, loading=False):
        self.status_bar.config(text=text)
        if loading:
            self.loading.pack(side=tk.BOTTOM, fill=tk.X, before=self.status_bar)
            self.loading.start()
        else:
            self.loading.stop()
            self.loading.pack_forget()

    def _run_async(self, target, callback):
        def wrapper():
            try:
                result = target()
                self.api_queue.put(lambda: callback(result, None))
            except Exception as e:
                self.api_queue.put(lambda: callback(None, e))
        threading.Thread(target=wrapper, daemon=True).start()

    def _api_get_all(self):
        r = requests.get(API_BASE, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _api_get_one(self, post_id):
        r = requests.get(f"{API_BASE}/{post_id}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def _api_create(self, data):
        r = requests.post(API_BASE, json=data, timeout=TIMEOUT)
        if r.status_code == 422:
            err = r.json()
            raise APIError(err.get("message", "Data tidak valid"), 422, err.get("errors", {}))
        r.raise_for_status()
        return r.json()

    def _api_update(self, post_id, data):
        r = requests.put(f"{API_BASE}/{post_id}", json=data, timeout=TIMEOUT)
        if r.status_code == 422:
            err = r.json()
            raise APIError(err.get("message", "Data tidak valid"), 422, err.get("errors", {}))
        r.raise_for_status()
        return r.json()

    def _api_delete(self, post_id):
        r = requests.delete(f"{API_BASE}/{post_id}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def load_posts(self):
        self._set_status("Memuat data...", loading=True)
        self.selected_post_id = None
        self.btn_edit.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self._clear_detail()

        def on_result(result, error):
            self._set_status("Siap")
            if error:
                messagebox.showerror("Error", f"Gagal memuat data:\n{error}")
                if isinstance(error, requests.Timeout):
                    messagebox.showerror("Timeout", "Koneksi timeout. Periksa koneksi internet Anda.")
                return
            self.posts = result.get("data", [])
            self._refresh_table()

        self._run_async(self._api_get_all, on_result)

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for p in self.posts:
            vals = (p["id"], p["title"], p["author"], p["status"])
            self.tree.insert("", tk.END, values=vals)

    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            post_id = item["values"][0]
            self.selected_post_id = post_id
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
            self._show_detail(post_id)
        else:
            self.selected_post_id = None
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self._clear_detail()

    def _show_detail(self, post_id):
        self._set_status("Memuat detail...", loading=True)
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, "Memuat detail post...")
        self.detail_text.config(state=tk.DISABLED)

        def on_result(result, error):
            self._set_status("Siap")
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete(1.0, tk.END)
            if error:
                self.detail_text.insert(1.0, f"Gagal memuat detail:\n{error}")
                self.detail_text.config(state=tk.DISABLED)
                return
            post = result.get("data", {})
            lines = []
            lines.append(f"ID         : {post.get('id', '-')}")
            lines.append(f"Title      : {post.get('title', '-')}")
            lines.append(f"Author     : {post.get('author', '-')}")
            lines.append(f"Slug       : {post.get('slug', '-')}")
            lines.append(f"Status     : {post.get('status', '-')}")
            lines.append("")
            lines.append("Body:")
            lines.append(post.get("body", "-"))
            lines.append("")
            lines.append("Komentar:")
            comments = post.get("comments", [])
            if comments:
                for c in comments:
                    lines.append(f"  [{c.get('status', '?')}] {c.get('name', '')}: {c.get('body', '')}")
            else:
                lines.append("  (Tidak ada komentar)")
            self.detail_text.insert(1.0, "\n".join(lines))
            self.detail_text.config(state=tk.DISABLED)

        self._run_async(lambda: self._api_get_one(post_id), on_result)

    def _clear_detail(self):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state=tk.DISABLED)

    def add_post(self):
        dialog = PostFormDialog(self.root, "Tambah Post Baru")
        if not dialog.result:
            return
        data = dialog.result
        self._set_status("Menyimpan data...", loading=True)

        def on_result(result, error):
            self._set_status("Siap")
            if error:
                if isinstance(error, APIError) and error.status_code == 422:
                    msg_lines = ["Validasi gagal:\n"]
                    for field, msgs in error.errors.items():
                        for m in msgs:
                            msg_lines.append(f"  - {field}: {m}")
                    messagebox.showerror("Validasi Gagal", "\n".join(msg_lines))
                elif isinstance(error, requests.ConnectionError):
                    messagebox.showerror("Koneksi Error", "Tidak dapat terhubung ke server.")
                elif isinstance(error, requests.Timeout):
                    messagebox.showerror("Timeout", "Koneksi timeout.")
                else:
                    messagebox.showerror("Error", f"Gagal menambah post:\n{error}")
                return
            post = result.get("data", {})
            messagebox.showinfo("Sukses", f"Post berhasil dibuat!\nID: {post.get('id', '')}")
            self.load_posts()

        self._run_async(lambda: self._api_create(data), on_result)

    def edit_post(self):
        if not self.selected_post_id:
            return
        post_id = self.selected_post_id

        post_data = None
        for p in self.posts:
            if p["id"] == post_id:
                post_data = p
                break

        dialog = PostFormDialog(self.root, "Edit Post", post_data=post_data)
        if not dialog.result:
            return
        data = dialog.result
        self._set_status("Menyimpan perubahan...", loading=True)

        def on_result(result, error):
            self._set_status("Siap")
            if error:
                if isinstance(error, APIError) and error.status_code == 422:
                    msg_lines = ["Validasi gagal:\n"]
                    for field, msgs in error.errors.items():
                        for m in msgs:
                            msg_lines.append(f"  - {field}: {m}")
                    messagebox.showerror("Validasi Gagal", "\n".join(msg_lines))
                elif isinstance(error, requests.ConnectionError):
                    messagebox.showerror("Koneksi Error", "Tidak dapat terhubung ke server.")
                elif isinstance(error, requests.Timeout):
                    messagebox.showerror("Timeout", "Koneksi timeout.")
                else:
                    messagebox.showerror("Error", f"Gagal mengupdate post:\n{error}")
                return
            messagebox.showinfo("Sukses", "Post berhasil diupdate!")
            self.load_posts()

        self._run_async(lambda: self._api_update(post_id, data), on_result)

    def delete_post(self):
        if not self.selected_post_id:
            return
        post_id = self.selected_post_id

        konfirmasi = messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Apakah Anda yakin ingin menghapus post ID {post_id}?\n\n"
            "Semua komentar terkait juga akan terhapus.",
            icon="warning",
        )
        if not konfirmasi:
            return

        self._set_status("Menghapus...", loading=True)

        def on_result(result, error):
            self._set_status("Siap")
            if error:
                if isinstance(error, requests.ConnectionError):
                    messagebox.showerror("Koneksi Error", "Tidak dapat terhubung ke server.")
                elif isinstance(error, requests.Timeout):
                    messagebox.showerror("Timeout", "Koneksi timeout.")
                else:
                    messagebox.showerror("Error", f"Gagal menghapus post:\n{error}")
                return
            messagebox.showinfo("Sukses", f"Post ID {post_id} berhasil dihapus beserta semua komentarnya.")
            self.load_posts()

        self._run_async(lambda: self._api_delete(post_id), on_result)


def main():
    root = tk.Tk()
    app = PostManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
