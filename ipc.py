import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Pillow is optional but recommended for better JPG/resize
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except:
    PIL_OK = False


class WhatsAppOneWindowV2:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Style Chat (One Window)")
        self.root.geometry("1000x720")
        self.root.configure(bg="#ece5dd")

        # contacts: name -> {blocked: bool}
        self.contacts = {}

        # conversations:
        # key = tuple(sorted([userA, userB]))
        # value = list of messages dict:
        #   {"type":"text", "sender":name, "time": "12:30", "text": "..."}
        #   {"type":"image","sender":name,"time": "12:30","photo": PhotoImage}
        self.conversations = {}

        self.active_user = None    # "I am"
        self.current_chat = None   # selected contact in list

        self.images_cache = []     # keep PhotoImage refs so they don't disappear

        self._build_ui()

        # add your default people (you can remove these if you want empty start)
        for n in ["maroo", "iqra", "manahil", "maryam", "lisha"]:
            self._add_contact_internal(n)

        # set default active user
        self.active_user = "manahil" if "manahil" in self.contacts else list(self.contacts.keys())[0]
        self._refresh_active_user_dropdown()
        self._refresh_contacts()

        self.root.mainloop()

    # ===================== UI =====================

    def _build_ui(self):
        main = tk.Frame(self.root, bg="#ece5dd")
        main.pack(fill=tk.BOTH, expand=True)

        # LEFT PANEL
        self.left = tk.Frame(main, bg="#111827", width=280)
        self.left.pack(side=tk.LEFT, fill=tk.Y)
        self.left.pack_propagate(False)

        tk.Label(
            self.left, text="Contacts",
            font=("Segoe UI", 14, "bold"),
            bg="#111827", fg="#E9D5FF"
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # Active user selector
        active_row = tk.Frame(self.left, bg="#111827")
        active_row.pack(fill=tk.X, padx=16, pady=(0, 10))

        tk.Label(
            active_row, text="I am:",
            font=("Segoe UI", 11, "bold"),
            bg="#111827", fg="#cbd5e1"
        ).pack(side=tk.LEFT)

        self.active_user_var = tk.StringVar(value="")
        self.active_user_dropdown = ttk.Combobox(
            active_row,
            textvariable=self.active_user_var,
            state="readonly",
            width=18
        )
        self.active_user_dropdown.pack(side=tk.LEFT, padx=8)
        self.active_user_dropdown.bind("<<ComboboxSelected>>", self._on_active_user_change)

        # Add contact button
        tk.Button(
            self.left, text="+ Add Contact",
            font=("Segoe UI", 11, "bold"),
            bg="#7C3AED", fg="white",
            relief=tk.FLAT, cursor="hand2",
            command=self.add_contact_popup
        ).pack(fill=tk.X, padx=16, pady=(0, 10))

        self.contacts_frame = tk.Frame(self.left, bg="#111827")
        self.contacts_frame.pack(fill=tk.BOTH, expand=True)

        # RIGHT PANEL
        right = tk.Frame(main, bg="#ece5dd")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # CHAT HEADER
        header = tk.Frame(right, bg="#ece5dd")
        header.pack(fill=tk.X, padx=12, pady=8)

        self.chat_title = tk.Label(
            header, text="Select a contact",
            font=("Segoe UI", 13, "bold"),
            bg="#ece5dd", fg="#111827"
        )
        self.chat_title.pack(side=tk.LEFT)

        self.menu_btn = tk.Menubutton(
            header, text="⋮",
            font=("Segoe UI", 14),
            bg="#ece5dd", relief=tk.FLAT
        )
        self.menu_btn.pack(side=tk.RIGHT)

        self.menu = tk.Menu(self.menu_btn, tearoff=0)
        self.menu.add_command(label="Clear Chat", command=self.clear_chat)
        self.menu.add_command(label="Block / Unblock", command=self.toggle_block)
        self.menu.add_command(label="Delete Contact", command=self.delete_contact)
        self.menu_btn.config(menu=self.menu)

        # CHAT AREA (Canvas + scrollbar)
        self.canvas = tk.Canvas(right, bg="#ece5dd", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(right, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_frame = tk.Frame(self.canvas, bg="#ece5dd")
        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")

        # Bottom input area
        bottom = tk.Frame(self.root, bg="#f0f0f0", height=90)
        bottom.pack(fill=tk.X)
        bottom.pack_propagate(False)

        # Better attach button
        self.attach_btn = tk.Button(
            bottom,
            text="📷 Photo",
            font=("Segoe UI", 11, "bold"),
            bg="#e5e7eb",
            fg="#111827",
            activebackground="#d1d5db",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_image
        )
        self.attach_btn.pack(side=tk.LEFT, padx=10, pady=14, ipadx=8, ipady=6)

        self.input_box = tk.Text(
            bottom, height=3,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            bg="#5B2D86", fg="#F5F3FF",
            insertbackground="#E9D5FF",
            relief=tk.FLAT
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=12)
        self.input_box.bind("<Return>", lambda e: self.send_message() or "break")

        tk.Button(
            bottom, text="Send",
            font=("Segoe UI", 12, "bold"),
            bg="#25d366", fg="white",
            relief=tk.FLAT, cursor="hand2",
            command=self.send_message
        ).pack(side=tk.RIGHT, padx=10, pady=14, ipadx=10, ipady=8)

    # ===================== Contacts =====================

    def _add_contact_internal(self, name):
        name = name.strip()
        if not name:
            return False
        if name in self.contacts:
            return False
        self.contacts[name] = {"blocked": False}
        return True

    def add_contact_popup(self):
        name = self._simple_input("New Contact", "Enter contact name:")
        if not name:
            return
        if self._add_contact_internal(name):
            if self.active_user is None:
                self.active_user = name
            self._refresh_active_user_dropdown()
            self._refresh_contacts()
        else:
            messagebox.showinfo("Info", "Contact already exists (or invalid).")

    def _refresh_active_user_dropdown(self):
        names = list(self.contacts.keys())
        self.active_user_dropdown["values"] = names
        if self.active_user in names:
            self.active_user_var.set(self.active_user)
        elif names:
            self.active_user = names[0]
            self.active_user_var.set(self.active_user)

    def _on_active_user_change(self, _event=None):
        picked = self.active_user_var.get()
        if picked:
            self.active_user = picked
            # if currently chatting with myself, reset chat
            if self.current_chat == self.active_user:
                self.current_chat = None
                self.chat_title.config(text="Select a contact")
                self._clear_chat_ui()
            else:
                self._render_chat()

            self._refresh_contacts()

    def _refresh_contacts(self):
        for w in self.contacts_frame.winfo_children():
            w.destroy()

        for name in self.contacts:
            # Don't show myself in contacts list (like WhatsApp)
            if name == self.active_user:
                continue

            btn = tk.Button(
                self.contacts_frame,
                text=name,
                font=("Segoe UI", 11, "bold"),
                bg="#1f2937", fg="#F5F3FF",
                activebackground="#312e81",
                relief=tk.FLAT, anchor="w",
                cursor="hand2",
                command=lambda n=name: self.open_chat(n)
            )
            btn.pack(fill=tk.X, padx=12, pady=6, ipady=10)

    def open_chat(self, name):
        self.current_chat = name
        self.chat_title.config(text=f"{self.active_user}  →  {name}")
        self._render_chat()

    def delete_contact(self):
        if not self.current_chat:
            return
        target = self.current_chat
        if not messagebox.askyesno("Delete", f"Delete {target} and all chats with them?"):
            return

        # remove conversations involving target
        keys_to_delete = []
        for key in self.conversations:
            if target in key:
                keys_to_delete.append(key)
        for k in keys_to_delete:
            del self.conversations[k]

        # remove contact
        del self.contacts[target]

        # if active user deleted (rare) pick another
        if self.active_user == target:
            self.active_user = next(iter(self.contacts), None)

        self.current_chat = None
        self.chat_title.config(text="Select a contact")
        self._clear_chat_ui()
        self._refresh_active_user_dropdown()
        self._refresh_contacts()

    def toggle_block(self):
        if not self.current_chat:
            return
        c = self.contacts[self.current_chat]
        c["blocked"] = not c["blocked"]
        state = "Blocked" if c["blocked"] else "Unblocked"
        messagebox.showinfo("Status", f"{self.current_chat}: {state}")

    def clear_chat(self):
        if not self.current_chat:
            return
        key = tuple(sorted([self.active_user, self.current_chat]))
        self.conversations[key] = []
        self._render_chat()

    # ===================== Chat logic =====================

    def send_message(self):
        if not self.current_chat:
            return
        if self.contacts[self.current_chat]["blocked"]:
            messagebox.showwarning("Blocked", "You cannot send messages to this contact.")
            return

        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            return

        key = tuple(sorted([self.active_user, self.current_chat]))
        self.conversations.setdefault(key, []).append({
            "type": "text",
            "sender": self.active_user,
            "time": datetime.now().strftime("%H:%M"),
            "text": text
        })

        self.input_box.delete("1.0", tk.END)
        self._render_chat()

    def send_image(self):
        if not self.current_chat:
            messagebox.showinfo("Info", "Select a contact first.")
            return
        if self.contacts[self.current_chat]["blocked"]:
            messagebox.showwarning("Blocked", "You cannot send images to this contact.")
            return

        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
        )
        if not path:
            return

        # Without PIL, Tkinter supports PNG/GIF best
        if not PIL_OK:
            ext = os.path.splitext(path)[1].lower()
            if ext not in [".png", ".gif"]:
                messagebox.showerror("PIL Missing", "Pillow not available. Use PNG/GIF or install pillow.")
                return
            photo = tk.PhotoImage(file=path)
        else:
            img = Image.open(path)
            img.thumbnail((320, 320))
            photo = ImageTk.PhotoImage(img)

        self.images_cache.append(photo)

        key = tuple(sorted([self.active_user, self.current_chat]))
        self.conversations.setdefault(key, []).append({
            "type": "image",
            "sender": self.active_user,
            "time": datetime.now().strftime("%H:%M"),
            "photo": photo
        })
        self._render_chat()

    def _render_chat(self):
        self._clear_chat_ui()
        if not self.current_chat or not self.active_user:
            return

        key = tuple(sorted([self.active_user, self.current_chat]))
        msgs = self.conversations.get(key, [])

        if not msgs:
            self._add_system("No messages yet. Say hi 👋")
            return

        for m in msgs:
            is_me = (m["sender"] == self.active_user)
            if m["type"] == "text":
                self._add_text_bubble(m["sender"], m["text"], m["time"], is_me)
            else:
                self._add_image_bubble(m["sender"], m["photo"], m["time"], is_me)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ===================== Bubbles =====================

    def _add_system(self, text):
        frame = tk.Frame(self.chat_frame, bg="#ece5dd")
        frame.pack(fill=tk.X, pady=8)
        tk.Label(
            frame, text=text,
            font=("Segoe UI", 9, "italic"),
            bg="#fff3cd", fg="#856404",
            padx=15, pady=8, wraplength=520
        ).pack()
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _add_text_bubble(self, sender, text, time_str, is_me):
        outer = tk.Frame(self.chat_frame, bg="#ece5dd")
        outer.pack(fill=tk.X, pady=4, padx=10)

        bubble = tk.Frame(outer, bg="#ece5dd")
        bubble.pack(side=tk.RIGHT if is_me else tk.LEFT)

        color = "#dcf8c6" if is_me else "white"

        if not is_me:
            tk.Label(
                bubble, text=sender,
                font=("Segoe UI", 9, "bold"),
                bg=color, fg="#075e54", anchor="w"
            ).pack(fill=tk.X, padx=10, pady=(6, 0))

        tk.Label(
            bubble, text=text,
            font=("Segoe UI", 11),
            bg=color, fg="#303030",
            wraplength=420,
            justify=tk.LEFT,
            padx=10, pady=8
        ).pack(fill=tk.X)

        tk.Label(
            bubble, text=time_str,
            font=("Segoe UI", 8),
            bg=color, fg="#999", anchor="e"
        ).pack(fill=tk.X, padx=10, pady=(0, 6))

    def _add_image_bubble(self, sender, photo, time_str, is_me):
        outer = tk.Frame(self.chat_frame, bg="#ece5dd")
        outer.pack(fill=tk.X, pady=6, padx=10)

        bubble = tk.Frame(outer, bg="#ece5dd")
        bubble.pack(side=tk.RIGHT if is_me else tk.LEFT)

        color = "#dcf8c6" if is_me else "white"

        if not is_me:
            tk.Label(
                bubble, text=sender,
                font=("Segoe UI", 9, "bold"),
                bg=color, fg="#075e54", anchor="w"
            ).pack(fill=tk.X, padx=10, pady=(6, 0))

        box = tk.Frame(bubble, bg=color)
        box.pack()

        tk.Label(box, image=photo, bg=color).pack(padx=10, pady=10)

        tk.Label(
            bubble, text=time_str,
            font=("Segoe UI", 8),
            bg=color, fg="#999", anchor="e"
        ).pack(fill=tk.X, padx=10, pady=(0, 6))

    # ===================== Helpers =====================

    def _clear_chat_ui(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()

    def _simple_input(self, title, prompt):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("320x160")
        win.configure(bg="#0b1220")
        win.grab_set()

        tk.Label(win, text=prompt, bg="#0b1220", fg="#E9D5FF",
                 font=("Segoe UI", 11, "bold")).pack(pady=(14, 8))

        var = tk.StringVar()
        e = tk.Entry(win, textvariable=var, font=("Segoe UI", 11))
        e.pack(padx=14, fill=tk.X)
        e.focus()

        out = {"val": None}

        def ok():
            out["val"] = var.get().strip()
            win.destroy()

        tk.Button(win, text="OK", command=ok,
                  bg="#7C3AED", fg="white", relief=tk.FLAT,
                  font=("Segoe UI", 11, "bold")).pack(pady=14, ipadx=16, ipady=6)

        win.wait_window()
        return out["val"]


if __name__ == "__main__":
    WhatsAppOneWindowV2()
