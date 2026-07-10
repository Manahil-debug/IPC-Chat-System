import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import uuid

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except:
    PIL_OK = False


class ModernMessenger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Messenger")
        self.root.geometry("1300x850")

        # Theme settings
        self.current_theme = "dark"  # "dark" or "light"
        self.themes = {
            "dark": {
                "app_bg": "#0a0a0a",
                "sidebar_bg": "#18191a",
                "sidebar_header": "#242526",
                "chat_bg": "#0a0a0a",
                "chat_header": "#242526",
                "input_bg": "#3a3b3c",
                "input_text": "#e4e6eb",
                "sent_bubble": "#0084ff",
                "sent_glow": "#005fcc",
                "received_bubble": "#3a3b3c",
                "received_glow": "#505152",
                "text_primary": "#e4e6eb",
                "text_secondary": "#b0b3b8",
                "accent": "#9b59b6",
                "accent_hover": "#8e44ad",
                "button_bg": "#3a3b3c",
                "button_hover": "#4e4f50",
                "card_bg": "#242526",
                "card_hover": "#3a3b3c",
                "border": "#3e4042"
            },
            "light": {
                "app_bg": "#f0f2f5",
                "sidebar_bg": "#ffffff",
                "sidebar_header": "#ffffff",
                "chat_bg": "#f0f2f5",
                "chat_header": "#ffffff",
                "input_bg": "#d5f7e1",  # light green
                "input_text": "#050505",
                "sent_bubble": "#00a884",
                "sent_glow": "#008069",
                "received_bubble": "#ffffff",
                "received_glow": "#d1d7db",
                "text_primary": "#111b21",
                "text_secondary": "#667781",
                "accent": "#00a884",
                "accent_hover": "#008069",
                "button_bg": "#f0f2f5",
                "button_hover": "#d1d7db",
                "card_bg": "#ffffff",
                "card_hover": "#f5f5f5",
                "border": "#e4e6eb"
            }
        }

        # Data
        self.contacts = {}
        self.conversations = {}
        self.active_user = None
        self.current_chat = None
        self.images_cache = []

        # Multi-selection state
        self.selected_msg_ids = set()
        self.msg_widgets = {}  # msg_id -> bubble frame

        self._build_ui()

        # Add default contacts
        for n in ["maroo", "iqra", "manahil", "maryam", "lisha"]:
            self._add_contact_internal(n)

        self.active_user = "manahil" if "manahil" in self.contacts else list(self.contacts.keys())[0]
        self._refresh_active_user_dropdown()
        self._refresh_contacts()

        self.root.mainloop()

    # ===================== THEME =====================

    def get_color(self, key):
        return self.themes[self.current_theme][key]

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        self.root.configure(bg=self.get_color("app_bg"))

        # Sidebar
        self.left.configure(bg=self.get_color("sidebar_bg"))
        self.sidebar_header.configure(bg=self.get_color("sidebar_header"))
        self.header_title.configure(bg=self.get_color("sidebar_header"), fg=self.get_color("text_primary"))

        theme_text = "☀️ Light" if self.current_theme == "dark" else "🌙 Dark"
        self.theme_btn.configure(
            text=theme_text,
            bg=self.get_color("button_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("button_hover")
        )

        self.user_section.configure(bg=self.get_color("sidebar_bg"))
        self.user_card.configure(bg=self.get_color("card_bg"))
        self.user_inner.configure(bg=self.get_color("card_bg"))
        self.user_label.configure(bg=self.get_color("card_bg"), fg=self.get_color("text_secondary"))

        self.btn_container.configure(bg=self.get_color("sidebar_bg"))
        self.add_contact_btn.configure(bg=self.get_color("accent"), activebackground=self.get_color("accent_hover"))

        self.contacts_label.configure(bg=self.get_color("sidebar_bg"), fg=self.get_color("text_secondary"))

        self.contacts_container.configure(bg=self.get_color("sidebar_bg"))
        self.contacts_canvas.configure(bg=self.get_color("sidebar_bg"))
        self.contacts_inner_frame.configure(bg=self.get_color("sidebar_bg"))

        # Chat area
        self.right.configure(bg=self.get_color("chat_bg"))
        self.chat_header.configure(bg=self.get_color("chat_header"))
        self.chat_header_content.configure(bg=self.get_color("chat_header"))
        self.chat_info.configure(bg=self.get_color("chat_header"))
        self.chat_title.configure(bg=self.get_color("chat_header"), fg=self.get_color("text_primary"))
        self.chat_status.configure(bg=self.get_color("chat_header"), fg=self.get_color("text_secondary"))
        self.menu_btn.configure(
            bg=self.get_color("chat_header"),
            fg=self.get_color("text_secondary"),
            activebackground=self.get_color("button_hover")
        )

        self.chat_container.configure(bg=self.get_color("chat_bg"))
        self.canvas.configure(bg=self.get_color("chat_bg"))
        self.chat_frame.configure(bg=self.get_color("chat_bg"))

        self.input_main.configure(bg=self.get_color("chat_bg"))
        self.input_box.configure(
            bg=self.get_color("input_bg"),
            fg=self.get_color("input_text"),
            insertbackground=self.get_color("accent")
        )
        self.attach_btn.configure(
            bg=self.get_color("button_bg"),
            fg=self.get_color("text_secondary"),
            activebackground=self.get_color("button_hover")
        )
        self.send_btn.configure(bg=self.get_color("accent"), activebackground=self.get_color("accent_hover"))

        self.menu.configure(
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("accent")
        )

        self.msg_menu.configure(
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("accent"),
            activeforeground="white",
        )

        self._refresh_contacts()
        self._render_chat()

    # ===================== UI BUILD =====================

    def _build_ui(self):
        main_container = tk.Frame(self.root, bg=self.get_color("app_bg"))
        main_container.pack(fill=tk.BOTH, expand=True)

        main = tk.Frame(main_container, bg=self.get_color("app_bg"))
        main.pack(fill=tk.BOTH, expand=True)

        # LEFT SIDEBAR
        self.left = tk.Frame(main, bg=self.get_color("sidebar_bg"), width=360)
        self.left.pack(side=tk.LEFT, fill=tk.Y)
        self.left.pack_propagate(False)

        self.sidebar_header = tk.Frame(self.left, bg=self.get_color("sidebar_header"), height=70)
        self.sidebar_header.pack(fill=tk.X)
        self.sidebar_header.pack_propagate(False)

        header_content = tk.Frame(self.sidebar_header, bg=self.get_color("sidebar_header"))
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.header_title = tk.Label(
            header_content, text="Chats",
            font=("SF Pro Display", 24, "bold"),
            bg=self.get_color("sidebar_header"),
            fg=self.get_color("text_primary")
        )
        self.header_title.pack(side=tk.LEFT)

        theme_text = "☀️ Light" if self.current_theme == "dark" else "🌙 Dark"
        self.theme_btn = tk.Button(
            header_content,
            text=theme_text,
            font=("SF Pro Display", 11, "bold"),
            bg=self.get_color("button_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("button_hover"),
            activeforeground=self.get_color("text_primary"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_theme,
            padx=15, pady=8,
            borderwidth=0
        )
        self.theme_btn.pack(side=tk.RIGHT)

        # Active user section
        self.user_section = tk.Frame(self.left, bg=self.get_color("sidebar_bg"))
        self.user_section.pack(fill=tk.X, padx=15, pady=(15, 10))

        self.user_card = tk.Frame(self.user_section, bg=self.get_color("card_bg"))
        self.user_card.pack(fill=tk.X)

        self.user_inner = tk.Frame(self.user_card, bg=self.get_color("card_bg"))
        self.user_inner.pack(fill=tk.X, padx=15, pady=12)

        self.user_label = tk.Label(
            self.user_inner, text="You are chatting as:",
            font=("SF Pro Display", 10),
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_secondary")
        )
        self.user_label.pack(anchor="w", pady=(0, 5))

        self.active_user_var = tk.StringVar(value="")
        style = ttk.Style()
        style.theme_use('clam')

        self.active_user_dropdown = ttk.Combobox(
            self.user_inner,
            textvariable=self.active_user_var,
            state="readonly",
            font=("SF Pro Display", 12, "bold")
        )
        self.active_user_dropdown.pack(fill=tk.X)
        self.active_user_dropdown.bind("<<ComboboxSelected>>", self._on_active_user_change)

        # Add contact button
        self.btn_container = tk.Frame(self.left, bg=self.get_color("sidebar_bg"))
        self.btn_container.pack(fill=tk.X, padx=15, pady=(10, 15))

        self.add_contact_btn = tk.Button(
            self.btn_container, text="+ New Contact",
            font=("SF Pro Display", 12, "bold"),
            bg=self.get_color("accent"),
            fg="white",
            activebackground=self.get_color("accent_hover"),
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_contact_popup,
            borderwidth=0
        )
        self.add_contact_btn.pack(fill=tk.X, ipady=12)

        self.contacts_label = tk.Label(
            self.left, text="Messages",
            font=("SF Pro Display", 13, "bold"),
            bg=self.get_color("sidebar_bg"),
            fg=self.get_color("text_secondary")
        )
        self.contacts_label.pack(anchor="w", padx=20, pady=(10, 8))

        # Scrollable contacts
        self.contacts_container = tk.Frame(self.left, bg=self.get_color("sidebar_bg"))
        self.contacts_container.pack(fill=tk.BOTH, expand=True)

        self.contacts_scrollbar = ttk.Scrollbar(self.contacts_container, orient="vertical")
        self.contacts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.contacts_canvas = tk.Canvas(
            self.contacts_container,
            bg=self.get_color("sidebar_bg"),
            highlightthickness=0,
            yscrollcommand=self.contacts_scrollbar.set
        )
        self.contacts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.contacts_scrollbar.configure(command=self.contacts_canvas.yview)

        self.contacts_inner_frame = tk.Frame(self.contacts_canvas, bg=self.get_color("sidebar_bg"))
        self.contacts_canvas_window = self.contacts_canvas.create_window((0, 0), window=self.contacts_inner_frame, anchor="nw")

        def configure_contacts_canvas(event):
            self.contacts_canvas.itemconfig(self.contacts_canvas_window, width=event.width)

        def configure_contacts_inner(_event):
            self.contacts_canvas.configure(scrollregion=self.contacts_canvas.bbox("all"))

        self.contacts_canvas.bind("<Configure>", configure_contacts_canvas)
        self.contacts_inner_frame.bind("<Configure>", configure_contacts_inner)

        # RIGHT CHAT AREA
        self.right = tk.Frame(main, bg=self.get_color("chat_bg"))
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_header = tk.Frame(self.right, bg=self.get_color("chat_header"), height=70)
        self.chat_header.pack(fill=tk.X)
        self.chat_header.pack_propagate(False)

        self.chat_header_content = tk.Frame(self.chat_header, bg=self.get_color("chat_header"))
        self.chat_header_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        self.chat_info = tk.Frame(self.chat_header_content, bg=self.get_color("chat_header"))
        self.chat_info.pack(side=tk.LEFT)

        self.chat_title = tk.Label(
            self.chat_info, text="Select a chat to start messaging",
            font=("SF Pro Display", 16, "bold"),
            bg=self.get_color("chat_header"),
            fg=self.get_color("text_primary")
        )
        self.chat_title.pack(anchor="w")

        self.chat_status = tk.Label(
            self.chat_info, text="",
            font=("SF Pro Display", 11),
            bg=self.get_color("chat_header"),
            fg=self.get_color("text_secondary")
        )
        self.chat_status.pack(anchor="w")

        self.menu_btn = tk.Menubutton(
            self.chat_header_content, text="⋮",
            font=("SF Pro Display", 24, "bold"),
            bg=self.get_color("chat_header"),
            fg=self.get_color("text_secondary"),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.get_color("button_hover"),
            activeforeground=self.get_color("text_primary"),
            padx=12, pady=5,
            borderwidth=0
        )
        self.menu_btn.pack(side=tk.RIGHT)

        self.menu = tk.Menu(
            self.menu_btn, tearoff=0,
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("accent"),
            activeforeground="white",
            font=("SF Pro Display", 11),
            borderwidth=0
        )
        self.menu.add_command(label="Clear Chat", command=self.clear_chat)
        self.menu.add_command(label="Block / Unblock", command=self.toggle_block)
        self.menu.add_command(label="Delete Contact", command=self.delete_contact)
        self.menu_btn.config(menu=self.menu)

        # Message context menu (right click)
        self.msg_menu = tk.Menu(
            self.root, tearoff=0,
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            activebackground=self.get_color("accent"),
            activeforeground="white",
            font=("SF Pro Display", 11),
            borderwidth=0
        )
        self.msg_menu.add_command(label="Forward", command=self.forward_selected_messages)
        self.msg_menu.add_separator()
        self.msg_menu.add_command(label="Delete for me", command=self.delete_selected_for_me)
        self.msg_menu.add_command(label="Delete for everyone", command=self.delete_selected_for_everyone)
        self.msg_menu.add_separator()
        self.msg_menu.add_command(label="Clear selection", command=self.clear_selection)

        # Chat scroll area
        self.chat_container = tk.Frame(self.right, bg=self.get_color("chat_bg"))
        self.chat_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.chat_container, bg=self.get_color("chat_bg"), highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chat_scrollbar = ttk.Scrollbar(self.chat_container, orient="vertical", command=self.canvas.yview)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=chat_scrollbar.set)

        self.chat_frame = tk.Frame(self.canvas, bg=self.get_color("chat_bg"))
        self.chat_canvas_window = self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")

        self.chat_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.chat_canvas_window, width=e.width))

        # Mouse wheel chat scrolling (Windows)
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Input
        self.input_main = tk.Frame(self.right, bg=self.get_color("chat_bg"), height=80)
        self.input_main.pack(fill=tk.X, padx=20, pady=15)
        self.input_main.pack_propagate(False)

        self.attach_btn = tk.Button(
            self.input_main,
            text="📷",
            font=("Segoe UI Emoji", 20),
            bg=self.get_color("button_bg"),
            fg=self.get_color("text_secondary"),
            activebackground=self.get_color("button_hover"),
            activeforeground=self.get_color("accent"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_image,
            padx=12, pady=10,
            borderwidth=0
        )
        self.attach_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.input_box = tk.Text(
            self.input_main, height=3,
            font=("SF Pro Display", 12),
            wrap=tk.WORD,
            bg=self.get_color("input_bg"),
            fg=self.get_color("input_text"),
            insertbackground=self.get_color("accent"),
            relief=tk.FLAT,
            padx=15, pady=12,
            borderwidth=0
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_box.bind("<Return>", lambda e: self.send_message() or "break")

        self.send_btn = tk.Button(
            self.input_main, text="➤",
            font=("Segoe UI Symbol", 18, "bold"),
            bg=self.get_color("accent"),
            fg="white",
            activebackground=self.get_color("accent_hover"),
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_message,
            padx=20, pady=15,
            borderwidth=0,
            width=3
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(10, 0))

    # ===================== CONTACTS =====================

    def _add_contact_internal(self, name):
        name = name.strip()
        if not name or name in self.contacts:
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
            messagebox.showinfo("Info", "Contact already exists.")

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
            self.clear_selection()
            if self.current_chat == self.active_user:
                self.current_chat = None
                self.chat_title.config(text="Select a chat to start messaging")
                self.chat_status.config(text="")
                self._clear_chat_ui()
            else:
                self._render_chat()
            self._refresh_contacts()

    def _refresh_contacts(self):
        for w in self.contacts_inner_frame.winfo_children():
            w.destroy()

        for name in self.contacts:
            if name == self.active_user:
                continue

            card = tk.Button(
                self.contacts_inner_frame,
                text=name,
                font=("SF Pro Display", 14, "bold"),
                bg=self.get_color("card_bg"),
                fg=self.get_color("text_primary"),
                activebackground=self.get_color("card_hover"),
                activeforeground=self.get_color("text_primary"),
                relief=tk.FLAT,
                anchor="w",
                cursor="hand2",
                command=lambda n=name: self.open_chat(n),
                borderwidth=0
            )
            card.pack(fill=tk.X, padx=10, pady=3, ipady=15, ipadx=20)

            def on_enter(e, btn=card):
                btn.configure(bg=self.get_color("card_hover"))

            def on_leave(e, btn=card):
                btn.configure(bg=self.get_color("card_bg"))

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

        self.contacts_inner_frame.update_idletasks()
        self.contacts_canvas.configure(scrollregion=self.contacts_canvas.bbox("all"))

    def open_chat(self, name):
        self.current_chat = name
        self.chat_title.config(text=name)
        self.chat_status.config(text="Active now")
        self.clear_selection()
        self._render_chat()

    def delete_contact(self):
        if not self.current_chat:
            return
        target = self.current_chat
        if not messagebox.askyesno("Delete", f"Delete {target}?"):
            return

        keys_to_delete = [k for k in self.conversations if target in k]
        for k in keys_to_delete:
            del self.conversations[k]

        del self.contacts[target]

        if self.active_user == target:
            self.active_user = next(iter(self.contacts), None)

        self.current_chat = None
        self.chat_title.config(text="Select a chat to start messaging")
        self.chat_status.config(text="")
        self.clear_selection()
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
        self.clear_selection()
        self._render_chat()

    # ===================== MULTI-SELECTION + MENU =====================

    def _bind_msg_events(self, bubble, msg_id):
        def left(_e, mid=msg_id):
            self._toggle_select(mid)

        def right(e, mid=msg_id):
            self._show_msg_menu(e, mid)

        bubble.bind("<Button-1>", left)
        bubble.bind("<Button-3>", right)
        for child in bubble.winfo_children():
            child.bind("<Button-1>", left)
            child.bind("<Button-3>", right)

    def _toggle_select(self, msg_id):
        if msg_id in self.selected_msg_ids:
            self.selected_msg_ids.remove(msg_id)
            if msg_id in self.msg_widgets:
                try:
                    self.msg_widgets[msg_id].configure(highlightthickness=0)
                except:
                    pass
            return

        self.selected_msg_ids.add(msg_id)
        if msg_id in self.msg_widgets:
            try:
                self.msg_widgets[msg_id].configure(
                    highlightthickness=2,
                    highlightbackground=self.get_color("accent"),
                    highlightcolor=self.get_color("accent")
                )
            except:
                pass

    def _show_msg_menu(self, event, msg_id):
        if msg_id not in self.selected_msg_ids:
            self._toggle_select(msg_id)
        try:
            self.msg_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.msg_menu.grab_release()

    def clear_selection(self):
        for mid in list(self.selected_msg_ids):
            if mid in self.msg_widgets:
                try:
                    self.msg_widgets[mid].configure(highlightthickness=0)
                except:
                    pass
        self.selected_msg_ids.clear()

    def _get_selected_messages(self):
        if not self.current_chat or not self.active_user or not self.selected_msg_ids:
            return None, []
        key = tuple(sorted([self.active_user, self.current_chat]))
        msgs = self.conversations.get(key, [])
        selected = [m for m in msgs if m.get("id") in self.selected_msg_ids]
        return key, selected

    def delete_selected_for_me(self):
        key, selected = self._get_selected_messages()
        if not selected:
            return

        for msg in selected:
            msg.setdefault("deleted_for", set()).add(self.active_user)

        self.clear_selection()
        self._render_chat()

    def delete_selected_for_everyone(self):
        key, selected = self._get_selected_messages()
        if not selected:
            return

        for msg in selected:
            msg["deleted_all"] = True
            msg["text"] = ""

        self.clear_selection()
        self._render_chat()

    def forward_selected_messages(self):
        key, selected = self._get_selected_messages()
        if not selected:
            return

        forwardable = [m for m in selected if not m.get("deleted_all")]
        if not forwardable:
            messagebox.showinfo("Forward", "Selected messages are deleted.")
            return

        targets = [c for c in self.contacts.keys() if c != self.active_user]
        if not targets:
            messagebox.showinfo("Forward", "No contacts available.")
            return

        chosen = self._choose_contact_popup("Forward to...", targets)
        if not chosen:
            return

        fwd_key = tuple(sorted([self.active_user, chosen]))

        for msg in forwardable:
            new_msg = {
                "id": str(uuid.uuid4()),
                "type": msg["type"],
                "sender": self.active_user,
                "time": datetime.now().strftime("%H:%M"),
                "deleted_all": False,
                "deleted_for": set(),
                "forwarded": True
            }

            if msg["type"] == "text":
                new_msg["text"] = msg.get("text", "")
            else:
                new_msg["photo"] = msg.get("photo")
                if new_msg["photo"] is not None:
                    self.images_cache.append(new_msg["photo"])

            self.conversations.setdefault(fwd_key, []).append(new_msg)

        self.clear_selection()
        messagebox.showinfo("Forward", f"Forwarded {len(forwardable)} message(s) to {chosen} ✅")

    # ===================== CHAT LOGIC =====================

    def send_message(self):
        if not self.current_chat:
            return
        if self.contacts[self.current_chat]["blocked"]:
            messagebox.showwarning("Blocked", "Cannot send messages.")
            return

        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            return

        key = tuple(sorted([self.active_user, self.current_chat]))
        self.conversations.setdefault(key, []).append({
            "id": str(uuid.uuid4()),
            "type": "text",
            "sender": self.active_user,
            "time": datetime.now().strftime("%H:%M"),
            "text": text,
            "deleted_all": False,
            "deleted_for": set(),
            "forwarded": False
        })

        self.input_box.delete("1.0", tk.END)
        self.clear_selection()
        self._render_chat()

    def send_image(self):
        if not self.current_chat:
            messagebox.showinfo("Info", "Select a contact first.")
            return
        if self.contacts[self.current_chat]["blocked"]:
            messagebox.showwarning("Blocked", "Cannot send images.")
            return

        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")]
        )
        if not path:
            return

        if not PIL_OK:
            import os
            ext = os.path.splitext(path)[1].lower()
            if ext not in [".png", ".gif"]:
                messagebox.showerror("Error", "Install Pillow for JPG.")
                return
            photo = tk.PhotoImage(file=path)
        else:
            img = Image.open(path)
            img.thumbnail((350, 350))
            photo = ImageTk.PhotoImage(img)

        self.images_cache.append(photo)

        key = tuple(sorted([self.active_user, self.current_chat]))
        self.conversations.setdefault(key, []).append({
            "id": str(uuid.uuid4()),
            "type": "image",
            "sender": self.active_user,
            "time": datetime.now().strftime("%H:%M"),
            "photo": photo,
            "deleted_all": False,
            "deleted_for": set(),
            "forwarded": False
        })
        self.clear_selection()
        self._render_chat()

    def _render_chat(self):
        self._clear_chat_ui()
        self.msg_widgets.clear()

        if not self.current_chat or not self.active_user:
            return

        key = tuple(sorted([self.active_user, self.current_chat]))
        msgs = self.conversations.get(key, [])

        if not msgs:
            self._add_system("Start the conversation")
            return

        for m in msgs:
            if self.active_user in m.get("deleted_for", set()):
                continue

            is_me = (m["sender"] == self.active_user)

            if m.get("deleted_all"):
                self._add_deleted_bubble(m["sender"], m["time"], is_me, m["id"])
                continue

            if m["type"] == "text":
                self._add_text_bubble(
                    m["sender"], m["text"], m["time"], is_me,
                    msg_id=m["id"],
                    forwarded=m.get("forwarded", False)
                )
            else:
                self._add_image_bubble(
                    m["sender"], m["photo"], m["time"], is_me,
                    msg_id=m["id"],
                    forwarded=m.get("forwarded", False)
                )

        # re-apply highlights after rerender
        for mid in list(self.selected_msg_ids):
            if mid in self.msg_widgets:
                try:
                    self.msg_widgets[mid].configure(
                        highlightthickness=2,
                        highlightbackground=self.get_color("accent"),
                        highlightcolor=self.get_color("accent")
                    )
                except:
                    pass

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ===================== BUBBLES =====================

    def _add_system(self, text):
        frame = tk.Frame(self.chat_frame, bg=self.get_color("chat_bg"))
        frame.pack(fill=tk.X, pady=20)
        tk.Label(
            frame, text=text,
            font=("SF Pro Display", 11, "italic"),
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_secondary"),
            padx=20, pady=12
        ).pack()

    def _add_deleted_bubble(self, sender, time_str, is_me, msg_id):
        outer = tk.Frame(self.chat_frame, bg=self.get_color("chat_bg"))
        outer.pack(fill=tk.X, pady=5, padx=25)

        bubble_container = tk.Frame(outer, bg=self.get_color("chat_bg"))
        bubble_container.pack(side=tk.RIGHT if is_me else tk.LEFT)

        bg_color = self.get_color("sent_bubble") if is_me else self.get_color("received_bubble")
        text_color = "#ffffff" if is_me else self.get_color("text_primary")

        bubble = tk.Frame(bubble_container, bg=bg_color, highlightthickness=0)
        bubble.pack()
        self.msg_widgets[msg_id] = bubble

        tk.Label(
            bubble, text="🚫 This message was deleted",
            font=("SF Pro Display", 11, "italic"),
            bg=bg_color, fg=text_color,
            wraplength=450,
            justify=tk.LEFT,
            padx=15, pady=10
        ).pack(fill=tk.X)

        tk.Label(
            bubble, text=time_str,
            font=("SF Pro Display", 9),
            bg=bg_color,
            fg="#ffffff" if is_me else self.get_color("text_secondary"),
            anchor="e"
        ).pack(fill=tk.X, padx=15, pady=(0, 10))

        self._bind_msg_events(bubble, msg_id)

    def _add_text_bubble(self, sender, text, time_str, is_me, msg_id, forwarded=False):
        outer = tk.Frame(self.chat_frame, bg=self.get_color("chat_bg"))
        outer.pack(fill=tk.X, pady=5, padx=25)

        bubble_container = tk.Frame(outer, bg=self.get_color("chat_bg"))
        bubble_container.pack(side=tk.RIGHT if is_me else tk.LEFT)

        if is_me:
            bg_color = self.get_color("sent_bubble")
            text_color = "#ffffff"
        else:
            bg_color = self.get_color("received_bubble")
            text_color = self.get_color("text_primary")

        bubble = tk.Frame(bubble_container, bg=bg_color, highlightthickness=0)
        bubble.pack()
        self.msg_widgets[msg_id] = bubble

        if forwarded:
            tk.Label(
                bubble, text="↪ Forwarded",
                font=("SF Pro Display", 9, "italic"),
                bg=bg_color, fg=text_color,
                anchor="w"
            ).pack(fill=tk.X, padx=15, pady=(10, 0))

        if not is_me:
            tk.Label(
                bubble, text=sender,
                font=("SF Pro Display", 10, "bold"),
                bg=bg_color,
                fg=self.get_color("accent") if self.current_theme == "light" else "#9b59b6",
                anchor="w"
            ).pack(fill=tk.X, padx=15, pady=(12, 2))

        tk.Label(
            bubble, text=text,
            font=("SF Pro Display", 12),
            bg=bg_color, fg=text_color,
            wraplength=450,
            justify=tk.LEFT,
            padx=15, pady=8
        ).pack(fill=tk.X)

        tk.Label(
            bubble, text=time_str,
            font=("SF Pro Display", 9),
            bg=bg_color,
            fg="#ffffff" if is_me else self.get_color("text_secondary"),
            anchor="e"
        ).pack(fill=tk.X, padx=15, pady=(0, 10))

        self._bind_msg_events(bubble, msg_id)

    def _add_image_bubble(self, sender, photo, time_str, is_me, msg_id, forwarded=False):
        outer = tk.Frame(self.chat_frame, bg=self.get_color("chat_bg"))
        outer.pack(fill=tk.X, pady=5, padx=25)

        bubble_container = tk.Frame(outer, bg=self.get_color("chat_bg"))
        bubble_container.pack(side=tk.RIGHT if is_me else tk.LEFT)

        bg_color = self.get_color("sent_bubble") if is_me else self.get_color("received_bubble")
        text_color = "#ffffff" if is_me else self.get_color("text_primary")

        bubble = tk.Frame(bubble_container, bg=bg_color, highlightthickness=0)
        bubble.pack()
        self.msg_widgets[msg_id] = bubble

        if forwarded:
            tk.Label(
                bubble, text="↪ Forwarded",
                font=("SF Pro Display", 9, "italic"),
                bg=bg_color, fg=text_color,
                anchor="w"
            ).pack(fill=tk.X, padx=15, pady=(10, 0))

        if not is_me:
            tk.Label(
                bubble, text=sender,
                font=("SF Pro Display", 10, "bold"),
                bg=bg_color,
                fg=self.get_color("accent") if self.current_theme == "light" else "#9b59b6",
                anchor="w"
            ).pack(fill=tk.X, padx=15, pady=(12, 5))

        tk.Label(bubble, image=photo, bg=bg_color).pack(padx=12, pady=12)

        tk.Label(
            bubble, text=time_str,
            font=("SF Pro Display", 9),
            bg=bg_color,
            fg="#ffffff" if is_me else self.get_color("text_secondary"),
            anchor="e"
        ).pack(fill=tk.X, padx=15, pady=(0, 10))

        self._bind_msg_events(bubble, msg_id)

    # ===================== HELPERS =====================

    def _clear_chat_ui(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()

    def _simple_input(self, title, prompt):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("450x250")
        win.configure(bg=self.get_color("app_bg"))
        win.grab_set()

        container = tk.Frame(win, bg=self.get_color("card_bg"))
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            container, text=prompt,
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            font=("SF Pro Display", 14, "bold")
        ).pack(pady=(20, 15))

        var = tk.StringVar()

        e = tk.Entry(
            container, textvariable=var,
            font=("SF Pro Display", 13),
            bg=self.get_color("input_bg"),
            fg=self.get_color("input_text"),
            insertbackground=self.get_color("accent"),
            relief=tk.FLAT,
            borderwidth=0
        )
        e.pack(padx=30, fill=tk.X, ipady=12, ipadx=15)
        e.focus()

        out = {"val": None}

        def ok():
            out["val"] = var.get().strip()
            win.destroy()

        btn = tk.Button(
            container, text="Create", command=ok,
            bg=self.get_color("accent"), fg="white",
            activebackground=self.get_color("accent_hover"),
            activeforeground="white",
            relief=tk.FLAT,
            font=("SF Pro Display", 12, "bold"),
            cursor="hand2",
            borderwidth=0
        )
        btn.pack(pady=25, ipadx=35, ipady=12)

        win.wait_window()
        return out["val"]

    def _choose_contact_popup(self, title, contacts_list):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("420x420")
        win.configure(bg=self.get_color("app_bg"))
        win.grab_set()

        container = tk.Frame(win, bg=self.get_color("card_bg"))
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(
            container, text=title,
            bg=self.get_color("card_bg"),
            fg=self.get_color("text_primary"),
            font=("SF Pro Display", 14, "bold")
        ).pack(pady=(10, 10))

        lb = tk.Listbox(
            container,
            font=("SF Pro Display", 12),
            bg=self.get_color("input_bg"),
            fg=self.get_color("input_text"),
            selectbackground=self.get_color("accent"),
            activestyle="none",
            relief=tk.FLAT
        )
        lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for c in contacts_list:
            lb.insert(tk.END, c)

        chosen = {"val": None}

        def do_choose():
            sel = lb.curselection()
            if not sel:
                return
            chosen["val"] = lb.get(sel[0])
            win.destroy()

        tk.Button(
            container,
            text="Forward",
            command=do_choose,
            bg=self.get_color("accent"),
            fg="white",
            activebackground=self.get_color("accent_hover"),
            relief=tk.FLAT,
            font=("SF Pro Display", 12, "bold"),
            cursor="hand2",
            borderwidth=0
        ).pack(pady=(0, 14), ipadx=22, ipady=10)

        win.wait_window()
        return chosen["val"]


if __name__ == "__main__":
    ModernMessenger()