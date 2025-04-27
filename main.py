import sqlite3
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

# Background color
Window.clearcolor = (0.1, 0.05, 0.2, 1)

# --- DATABASE SETUP ---
conn = sqlite3.connect("gym_members.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mobile TEXT,
    join_date TEXT,
    last_billed_date TEXT,
    photo_path TEXT,
    status TEXT
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS payment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    amount REAL,
    date TEXT
)''')
conn.commit()
conn.close()


# --- LOGIN SCREEN ---
class LoginScreen(BoxLayout):
    def __init__(self, login_success_callback, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=30, **kwargs)
        self.login_success_callback = login_success_callback

        self.add_widget(Image(
            source="login_logo.png", size_hint_y=None, height=120,
            allow_stretch=True, keep_ratio=True))
        self.add_widget(Label(
            text='[b][size=24]FlexFit Login[/size][/b]',
            markup=True, size_hint_y=None, height=50))

        self.username_input = TextInput(
            hint_text="Username", multiline=False,
            size_hint_y=None, height=40)
        self.password_input = TextInput(
            hint_text="Password", password=True, multiline=False,
            size_hint_y=None, height=40)

        self.add_widget(self.username_input)
        self.add_widget(self.password_input)

        self.message = Label(
            text="", color=(1, 0, 0, 1),
            size_hint_y=None, height=30, markup=True)
        self.add_widget(self.message)

        login_btn = Button(
            text="Login", size_hint_y=None, height=40,
            background_color=(0, 0.7, 1, 1))
        login_btn.bind(on_press=self.try_login)
        self.add_widget(login_btn)

    def play_sound(self, file_name):
        sound = SoundLoader.load(file_name)
        if sound:
            sound.play()

    def try_login(self, instance):
        user = self.username_input.text.strip()
        pw   = self.password_input.text.strip()
        if user == "Rsani" and pw == "sani01":
            self.play_sound("sounds/success.wav")
            self.message.text = ""
            # <-- this triggers the screen change
            self.login_success_callback()
        else:
            self.play_sound("sounds/failure.wav")
            self.message.text = "[color=ff0000]Incorrect username or password[/color]"


# --- MAIN APP SCREEN ---
class GymApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.photo_path = None

        # --- Header ---
        self.add_widget(Label(
            text='[b][size=26]\U0001F525 Welcome to FlexFit \U0001F525[/size][/b]',
            markup=True, size_hint_y=None, height=50))
        self.add_widget(Label(
            text='[b][size=22]Membership Management System[/size][/b]',
            markup=True, size_hint_y=None, height=40))

        # --- Search Bar ---
        search_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
        self.search_input = TextInput(
            hint_text="Search by Name", size_hint=(0.8, 1))
        search_btn = Button(
            text="Search", size_hint=(0.2, 1),
            background_color=(0.2, 0.6, 1, 1))
        search_btn.bind(on_press=self.refresh_data)
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(search_btn)
        self.add_widget(search_layout)

        # --- Member Form ---
        form_layout = BoxLayout(size_hint_y=None, height=50, spacing=5)
        self.name_input   = TextInput(hint_text="Name", size_hint=(0.2,1))
        self.mobile_input = TextInput(
            hint_text="Mobile", input_filter='int', size_hint=(0.2,1))
        self.day_spinner   = Spinner(
            text='01', values=[f"{i:02d}" for i in range(1,32)],
            size_hint=(0.15,1), background_color=(0,0,0,1),
            color=(1,1,1,1))
        self.month_spinner = Spinner(
            text='01', values=[f"{i:02d}" for i in range(1,13)],
            size_hint=(0.15,1), background_color=(0,0,0,1),
            color=(1,1,1,1))
        self.year_spinner = Spinner(
            text=str(datetime.now().year),
            values=[str(y) for y in range(2020,2031)],
            size_hint=(0.2,1), background_color=(0,0,0,1),
            color=(1,1,1,1))

        upload_btn = Button(
            text="Upload Photo", size_hint=(0.2,1),
            background_color=(1,0.5,0,1))
        upload_btn.bind(on_press=self.upload_photo)

        self.preview_image = Image(size_hint=(None,None), size=(30,30))

        form_layout.add_widget(self.name_input)
        form_layout.add_widget(self.mobile_input)
        form_layout.add_widget(self.day_spinner)
        form_layout.add_widget(self.month_spinner)
        form_layout.add_widget(self.year_spinner)
        form_layout.add_widget(upload_btn)
        form_layout.add_widget(self.preview_image)
        self.add_widget(form_layout)

        # --- Buttons ---
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
        add_btn            = Button(text="Add Member", background_color=(0,1,0,1))
        add_btn.bind(on_press=self.add_member)
        refresh_btn        = Button(text="Refresh", background_color=(0.5,0.8,1,1))
        refresh_btn.bind(on_press=self.refresh_data)
        activation_btn     = Button(text="Activation", background_color=(0,0.6,1,1))
        activation_btn.bind(on_press=self.show_activation_popup)
        payment_history_btn= Button(text="Payment History", background_color=(1,0.6,0,1))
        payment_history_btn.bind(on_press=self.show_payment_history)

        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(activation_btn)
        btn_layout.add_widget(payment_history_btn)
        self.add_widget(btn_layout)

        # --- Member & Due Lists ---
        self.add_widget(Label(text="[b]Members List[/b]", markup=True, size_hint_y=None, height=30))
        self.members_scroll = self._create_scroll()
        self.add_widget(self.members_scroll)

        self.add_widget(Label(text="[b]Bill Due[/b]", markup=True, size_hint_y=None, height=30))
        self.bill_scroll = self._create_scroll()
        self.add_widget(self.bill_scroll)

        # --- DateTime footer ---
        self.datetime_label = Label(size_hint_y=None, height=30, markup=True)
        self.add_widget(self.datetime_label)
        Clock.schedule_interval(self._update_time, 1)

        # initial load
        self.refresh_data()

    def _create_scroll(self):
        scroll = ScrollView(size_hint=(1,None), height=150)
        layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        layout.bind(minimum_height=layout.setter('height'))
        scroll.add_widget(layout)
        scroll.layout = layout
        return scroll

    def _update_time(self, dt):
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.datetime_label.text = f"[color=ffffff]{now}[/color]"

    def play_sound(self, file_name):
        sound = SoundLoader.load(file_name)
        if sound:
            sound.play()

    def upload_photo(self, instance):
        chooser = FileChooserIconView(filters=['*.png','*.jpg','*.jpeg'])
        select_btn = Button(text="Select", size_hint=(1,None), height=40)
        popup_box = BoxLayout(orientation='vertical')
        popup_box.add_widget(chooser)
        popup_box.add_widget(select_btn)
        popup = Popup(title="Choose Photo", content=popup_box, size_hint=(0.8,0.8))

        def on_select(_):
            if chooser.selection:
                self.photo_path = chooser.selection[0]
                self.preview_image.source = self.photo_path
                self.preview_image.reload()
            popup.dismiss()

        select_btn.bind(on_press=on_select)
        popup.open()

    def add_member(self, instance):
        name = self.name_input.text.strip()
        mobile = self.mobile_input.text.strip()
        join_date = f"{self.year_spinner.text}-{self.month_spinner.text}-{self.day_spinner.text}"
        if not name or not mobile:
            return

        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO members
              (name, mobile, join_date, last_billed_date, photo_path, status)
            VALUES (?,?,?,?,?,?)
        """, (name, mobile, join_date, join_date, self.photo_path, 'active'))
        conn.commit()
        conn.close()

        self.play_sound("sounds/add.wav")
        self._clear_form()
        self.refresh_data()

    def _clear_form(self):
        self.name_input.text = ""
        self.mobile_input.text = ""
        self.photo_path = None
        self.preview_image.source = ""

    def refresh_data(self, *args):
        self.members_scroll.layout.clear_widgets()
        self.bill_scroll.layout.clear_widgets()

        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        search = self.search_input.text.lower()
        cur.execute("SELECT id,name,mobile,join_date,last_billed_date,photo_path,status FROM members")
        for mid, name, mobile, jd, lb, photo, status in cur.fetchall():
            if search and search not in name.lower():
                continue

            # Member row
            row = BoxLayout(size_hint_y=None, height=30)
            color = (0,1,0,1) if status=='active' else (1,0,0,1)
            row.add_widget(Label(text=f"{name} | {mobile} | {status}",
                                 size_hint_x=0.4, color=color))
            photo_btn = Button(text="Photo", size_hint_x=0.2, background_color=(1,0.8,0.8,1))
            photo_btn.bind(on_press=lambda i, p=photo: self.show_photo(p))
            edit_btn = Button(text="Edit", size_hint_x=0.4, background_color=(1,1,0,1))
            edit_btn.bind(on_press=lambda i, m=mid: self.edit_member(m))
            row.add_widget(photo_btn)
            row.add_widget(edit_btn)
            self.members_scroll.layout.add_widget(row)

            # Bill-due row?
            today = datetime.today()
            jdt = datetime.strptime(jd, "%Y-%m-%d")
            lbd = datetime.strptime(lb, "%Y-%m-%d")
            ndue = (lbd + relativedelta(months=1))
            # try to keep join-day
            try:
                ndue = ndue.replace(day=jdt.day)
            except:
                ndue = (ndue.replace(day=1) +
                        relativedelta(months=1) -
                        relativedelta(days=1))

            if today >= ndue:
                drow = BoxLayout(size_hint_y=None, height=30)
                drow.add_widget(Label(
                    text=f"{name} | Due: {ndue.strftime('%d-%m-%Y')}",
                    size_hint_x=0.4))
                db_photo = Button(text="Photo", size_hint_x=0.2,
                                  background_color=(1,0.8,0.8,1))
                db_photo.bind(on_press=lambda i, p=photo: self.show_photo(p))
                paid_btn = Button(text="Paid", size_hint_x=0.4,
                                  background_color=(0,1,0,1))
                paid_btn.bind(on_press=lambda i, m=mid: self.ask_payment_amount(m))
                drow.add_widget(db_photo)
                drow.add_widget(paid_btn)
                self.bill_scroll.layout.add_widget(drow)

        conn.close()

    def ask_payment_amount(self, member_id):
        box = BoxLayout(orientation='vertical', spacing=10)
        amt_input = TextInput(hint_text="Enter Amount", input_filter='float')
        submit  = Button(text="Submit", background_color=(0,1,0,1))
        box.add_widget(amt_input)
        box.add_widget(submit)
        popup = Popup(title="Payment Amount", content=box,
                      size_hint=(0.7,0.4))

        def _on_submit(_):
            try:
                amt = float(amt_input.text)
                self.mark_paid(member_id, amt)
                popup.dismiss()
            except:
                pass

        submit.bind(on_press=_on_submit)
        popup.open()

    def mark_paid(self, member_id, amount):
        today = datetime.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("UPDATE members SET last_billed_date=? WHERE id=?",
                    (today, member_id))
        cur.execute("""
            INSERT INTO payment_history (member_id, amount, date)
            VALUES (?, ?, ?)
        """, (member_id, amount, today))
        conn.commit()
        conn.close()
        self.play_sound("sounds/paid.wav")
        self.refresh_data()

    def show_photo(self, photo):
        if photo and os.path.exists(photo):
            img = Image(source=photo)
            Popup(title="Photo", content=img, size_hint=(0.7,0.7)).open()

    def edit_member(self, member_id):
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("SELECT name,mobile,join_date,photo_path FROM members WHERE id=?",
                    (member_id,))
        name, mobile, join_date, photo_path = cur.fetchone()
        conn.close()

        layout = BoxLayout(orientation='vertical', spacing=10)
        name_in = TextInput(text=name, hint_text="Name")
        mob_in  = TextInput(text=mobile, hint_text="Mobile", input_filter='int')
        photo_btn = Button(text="Upload New Photo")
        save_btn  = Button(text="Save Changes", background_color=(0,1,0,1))

        def choose_new(_):
            chooser = FileChooserIconView(filters=['*.png','*.jpg','*.jpeg'])
            sel_btn = Button(text="Select", size_hint=(1,None), height=40)
            inner = BoxLayout(orientation='vertical')
            inner.add_widget(chooser)
            inner.add_widget(sel_btn)
            pop2 = Popup(title="Choose New Photo", content=inner, size_hint=(0.8,0.8))

            def do_select(_):
                nonlocal photo_path
                if chooser.selection:
                    photo_path = chooser.selection[0]
                pop2.dismiss()

            sel_btn.bind(on_press=do_select)
            pop2.open()

        photo_btn.bind(on_press=choose_new)

        def do_save(_):
            conn = sqlite3.connect("gym_members.db")
            cur = conn.cursor()
            cur.execute("""
                UPDATE members
                   SET name=?, mobile=?, photo_path=?
                 WHERE id=?
            """, (name_in.text, mob_in.text, photo_path, member_id))
            conn.commit()
            conn.close()
            pop.dismiss()
            self.refresh_data()

        save_btn.bind(on_press=do_save)

        layout.add_widget(name_in)
        layout.add_widget(mob_in)
        layout.add_widget(photo_btn)
        layout.add_widget(save_btn)
        pop = Popup(title="Edit Member", content=layout, size_hint=(0.8,0.8))
        pop.open()

    def show_activation_popup(self, instance):
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("SELECT id,name,status FROM members")
        members = cur.fetchall()
        conn.close()

        content = BoxLayout(orientation='vertical', spacing=10)
        for mid, name, status in members:
            row = BoxLayout(size_hint_y=None, height=30)
            row.add_widget(Label(text=f"{name} | {status}", size_hint_x=0.4))
            act_btn = Button(text="Activate",   size_hint_x=0.2, background_color=(0,1,0,1))
            deact_btn= Button(text="Deactivate", size_hint_x=0.2, background_color=(1,0,0,1))
            del_btn  = Button(text="Delete",     size_hint_x=0.2, background_color=(1,0.5,0,1))
            act_btn.bind(on_press=lambda i,m=mid: self.change_status(m,'active'))
            deact_btn.bind(on_press=lambda i,m=mid: self.change_status(m,'inactive'))
            del_btn.bind(on_press=lambda i,m=mid: self.delete_member(m))
            row.add_widget(act_btn)
            row.add_widget(deact_btn)
            row.add_widget(del_btn)
            content.add_widget(row)

        Popup(title="Activation Control", content=content, size_hint=(0.9,0.9)).open()

    def change_status(self, member_id, status):
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("UPDATE members SET status=? WHERE id=?", (status, member_id))
        conn.commit()
        conn.close()
        self.refresh_data()

    def delete_member(self, member_id):
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM members WHERE id=?", (member_id,))
        conn.commit()
        conn.close()
        self.refresh_data()

    def show_payment_history(self, instance):
        conn = sqlite3.connect("gym_members.db")
        cur = conn.cursor()
        cur.execute('''
            SELECT m.name, p.amount, p.date
              FROM payment_history p
              JOIN members m ON p.member_id=m.id
             ORDER BY p.date DESC
        ''')
        records = cur.fetchall()
        conn.close()

        layout = BoxLayout(orientation='vertical', spacing=10)
        for name, amount, date in records:
            layout.add_widget(Label(
                text=f"{name} | BDT{amount:.2f} | {date}",
                size_hint_y=None, height=30))

        Popup(title="Payment History", content=layout, size_hint=(0.9,0.9)).open()


# --- SCREENS & MANAGER ---
class LoginScreenContainer(Screen):
    # Give it a name so the manager can switch to it
    def __init__(self, on_logged_in_callback, **kwargs):
        super().__init__(name="login_screen", **kwargs)
        self.add_widget(LoginScreen(login_success_callback=on_logged_in_callback))


class MainAppScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="main_screen", **kwargs)
        self.add_widget(GymApp())


class FlexFitApp(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        # pass the on_logged_in callback
        self.login_screen = LoginScreenContainer(on_logged_in_callback=self.on_logged_in)
        self.main_screen  = MainAppScreen()
        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.main_screen)
        # start on login
        self.sm.current = "login_screen"
        return self.sm

    def on_logged_in(self):
        # switch to the main screen by name
        self.sm.current = "main_screen"


if __name__ == "__main__":
    FlexFitApp().run()