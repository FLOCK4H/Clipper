# c_test_clipboard.py
import PySide6.QtCore
import PySide6.QtGui
import c_clipboarder as clipboard
from c_clipboarder import Collector
import threading
import time
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys
import json
import ctypes
import os
# u - universal
class uButton(QPushButton):
    
    def __init__(self, clip_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clip_instance = clip_instance
        self.animation_hover = QPropertyAnimation(self, b"iconSize")
        self.animation_hover.setDuration(500)
        self.animation_hover.setEasingCurve(QEasingCurve.InOutCubic)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                background: transparent;
                border: 0px solid transparent;
            }
        """)
    def animate_hover(self, **kwargs):
        self.point = kwargs.get("p", None)
        if self.point == "start":
            self.animation_hover.stop()
            self.animation_hover.setEndValue(QSize(50, 70))
            self.animation_hover.start()
        if self.point == "end":
            self.animation_hover.stop()
            self.animation_hover.setEndValue(QSize(40, 60))
            self.animation_hover.start()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.animate_hover(p="start")
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(1, 120, 255, 0.5);
                background: rgba(1, 120, 255, 0.5);
                border: 0px solid transparent;
                border-radius:24px;
            }
        """)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.animate_hover(p="end")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                background: transparent;
                border: 0px solid transparent;
            }
        """)

class MessageWarning():
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

        self.text = str(self.kwargs.get('text', 'H'))
        self.title = str(self.kwargs.get('title', 'T'))

        self.user32 = ctypes.WinDLL("user32")
        self.create_box()

    def create_box(self):
        text_bytes = self.text.encode('utf-8')
        title_bytes = self.title.encode('utf-8')

        message_box = self.user32.MessageBoxA(None, text_bytes, title_bytes, 0x01 | 0x30)
        return message_box

class sButton(QPushButton):
    def __init__(self, clip_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kwargs = kwargs
        
        self.clip_instance = clip_instance

        self.anim_scarab_size = self.define_anim(self, b"iconSize")
        self.anim_recycle_size = self.define_anim(self, b"iconSize")


    def define_anim(self, who, anim, dur=500, easingCurve=QEasingCurve.InOutCubic):
        if anim == b"iconSize":
            name = QPropertyAnimation(who, anim)
            name.setDuration(dur)
            name.setEasingCurve(easingCurve)
        return name

    def animate_buttons(self, anim, **kwargs):

        type = kwargs.get('type', None)
        value = kwargs.get('value', None)
        anim.stop()  
        if type == "start":

            anim.setEndValue(value)
            anim.start()
        if type == "stop":

            anim.setEndValue(value)
            anim.start()

        if type == "1_loop":
            
            anim.setStartValue(QSize(52, 52))
            anim.setEndValue(value)
            anim.start()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.clip_instance.animate_scarab(type="start")
        self.animate_buttons(self.anim_scarab_size, type="start", value=QSize(42, 42))

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.animate_buttons(self.anim_scarab_size, type="stop", value=QSize(30, 30))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.animate_buttons(self.anim_recycle_size, type="1_loop", value=QSize(40, 40))

class ClipButton(QPushButton):
    def __init__(self, clip_instance, icon_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clip_instance = clip_instance
        self.left_arrow = QPixmap("1.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.right_arrow = QPixmap("2.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.ic_type = icon_type
        
        self.setStyleSheet("""
        QPushButton {
            background: transparent;
            border: 2px solid rgba(255, 255, 255, 0);
            padding: 10px;
            border-radius: 2px;
        }

        QPushButton:pressed {
            border: 0.5px solid rgba(0, 0, 255, 20);
            padding: 6px;
            margin: 4px;
            background-color: rgba(0, 0, 255, 0.08);
            border-radius: 8px;
        }
        """)

        self.setFixedSize(40, 60)
        self.setIconSize(QSize(32, 32))
        self.setIcon(self.determine_icon_type())

        self.hover_animation = QPropertyAnimation(self, b"iconSize")
        self.hover_animation.setDuration(500)
        self.hover_animation.setEasingCurve(QEasingCurve.InOutQuint)

    def determine_icon_type(self):
        return self.left_arrow if self.ic_type == "left" else self.right_arrow

    def animate_hover(self, **kwargs):
        if kwargs.get("start", False):
            self.hover_animation.stop()
            self.hover_animation.setEndValue(QSize(90,90))
            self.hover_animation.start()
        elif kwargs.get("end", False):
            self.hover_animation.stop()
            self.hover_animation.setEndValue(QSize(75,75))
            self.hover_animation.start()

    def mousePressEvent(self, e):
        self.clip_instance.animate_shake()
        super().mousePressEvent(e)
    

    def enterEvent(self, event):
        super().enterEvent(event)
        self.animate_hover(start=True)
    
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.animate_hover(end=True)


class CustomTE(QTextEdit):
    mouse_signal = Signal(str)
    
    def __init__(self, clip_instance, *args, **kwargs):
        super().__init__(clip_instance, *args, **kwargs)
        self.clip_instance = clip_instance
        self.simple_flag = False
        self.instantiate_anims()
        self.next_cooldown_time = time.time()
        # caching
        self.border_path = None
        self.border_pen = None
        self.create_border_objects()

    def instantiate_anims(self):
        self.border_animation_progress = 0
        self.border_gradient = QConicalGradient(self.rect().center(), 0)  
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_border)
        self.animation_timer.start(20)

        self.size_animation = QPropertyAnimation(self, b"size")
        self.size_animation.setDuration(200)
        self.size_animation.setEasingCurve(QEasingCurve.Linear)

        self.pos_animation = QPropertyAnimation(self, b"pos")
        self.pos_animation.setDuration(200)
        self.pos_animation.setEasingCurve(QEasingCurve.Linear)

        self.city_animation = QPropertyAnimation(self.clip_instance.city_label, b"pos")
        self.city_animation.setDuration(200)
        self.city_animation.setEasingCurve(QEasingCurve.Linear)
        
    def animate_size(self, **kwargs):

        self.typeof = kwargs.get("p", None)

        self.size_animation.stop()
        self.pos_animation.stop()
        self.city_animation.stop()

        if self.typeof == "start":
            self.size_helper(p="start")
        elif self.typeof == "end":
            self.size_helper(p="end")



    def size_helper(self, **kwargs):
        expansion = 5
        self.point = kwargs.get("p", None)
        self.widths = 243
        self.heights = 320

        if self.point == "start":
            if self.simple_flag == False:
                if self.clip_instance.width() > 340 and self.clip_instance.height() > 390:
                    new_width = self.widths + (expansion * 2)
                    new_height = self.heights + (expansion * 2) 

                    self.size_animation.setEndValue(QSize(new_width, new_height))
                    self.pos_animation.setEndValue(QPoint(41, 35))
                    self.city_animation.setEndValue(QPoint(173, 63))

                    self.size_animation.start()
                    self.pos_animation.start()
                    self.city_animation.start()
                    self.city_animation.finished.connect(lambda: setattr(self, 'simple_flag', True))

        elif self.point == "end":
            if self.simple_flag == True:
                if self.clip_instance.width() > 340 and self.clip_instance.height() > 390:
                    new_width = self.widths 
                    new_height = self.heights

                    self.size_animation.setEndValue(QSize(new_width, new_height))
                    self.pos_animation.setEndValue(QPoint(46, 40))
                    self.city_animation.setEndValue(QPoint(176, 58))

                    self.size_animation.start()
                    self.pos_animation.start()
                    self.city_animation.start()
                    self.city_animation.finished.connect(lambda: setattr(self, 'simple_flag', False))


    def enterEvent(self, event):
        super().enterEvent(event)
        self.animate_size(p="start")
        self.clip_instance.city_label.show()
    
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.animate_size(p="end")


    def resizeEvent(self, event):
        self.create_border_objects()
        super().resizeEvent(event)

    def create_border_objects(self):

        if self.border_path is None:
            self.border_path = QPainterPath()
        if self.border_pen is None:
            self.border_pen = QPen()

        self.border_path.clear()
        self.border_path.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 5, 5)

        self.border_pen.setBrush(QBrush(self.border_gradient))
        self.border_pen.setWidth(2)

    def animate_border(self):
        if self.clip_instance.width() < 320 and self.clip_instance.height() < 350:
            return
        self.border_animation_progress = (self.border_animation_progress + 1) % 360
        self.update_gradient()
        self.update()

    def update_gradient(self):
        self.border_gradient = QConicalGradient(self.rect().center(), 0)
        self.border_gradient.setAngle(self.border_animation_progress)

        self.border_gradient.setColorAt(0.0, QColor('#2730d0')) 
        self.border_gradient.setColorAt(0.25, QColor('#2730d0'))
        self.border_gradient.setColorAt(0.5, QColor('#650510'))
        self.border_gradient.setColorAt(0.75, QColor('#650510'))
        self.border_gradient.setColorAt(1.0, QColor('#2730d0'))
    
        self.border_pen.setBrush(QBrush(self.border_gradient))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.clip_instance.width() < 320 and self.clip_instance.height() < 350:
            return        
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.viewport().rect()).adjusted(1, 1, -1, -1), 5, 5)

        pen = QPen(QBrush(self.border_gradient), 3)
        painter.setPen(pen)

        painter.drawPath(path)

    def mousePressEvent(self, e):
        self.mouse_signal.emit("Mouse clicked!")
        super().mousePressEvent(e)

class blurButton(QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blue_spread = QPixmap("blue_spread.png").scaled(700, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(""" 
                background: transparent;
                border: 0px solid transparent;
        
        
        """)
        self.setIcon(self.blue_spread)
        self.setIconSize(QSize(700, 700))
        self.resize(700, 700)
        self.move(-170, -20)

    def resizeEvent(self, event):
        super().resizeEvent(event)

class ClipUI(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre
        self.setMouseTracking(True)
        self.list_id = 0
        self.view_id = 0
        self.collector = Collector('clipboard.json')
        
        self.collector_thread = threading.Thread(target=self.collector.start_listening, daemon=True)
        self.collector_thread.start()

        self.ease_timer = QTimer()
        self.ease_timer.timeout.connect(self.handle_cb_contents)
        self.ease_timer.start(2000)
        self.scarab_window_icon = QIcon('scarab_window_icon.png')
        self.setWindowIcon(self.scarab_window_icon)
        self.neon_rain = QPixmap("neon_rain.png").scaled(350, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.scarab_icon = QPixmap("scarab.png").scaled(124, 124, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.copy_button = QPixmap("copy.png").scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.copied_button = QPixmap("copied.png").scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.city_part_a = QPixmap("skyscraper.png").scaled(100, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.recycle_icon = QPixmap("recycle.png").scaled(124, 124, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.clipboard_content = None
        self.last_clipboard_content = None

        self.instantinator = []

        self.init_main_ui()
        self.init_ui()
        # Post
        self.recycle.hide()
        self.init_anims()
        self.hovered = False
        self.recycled = False
        self.normal_position = self.pos()
        self.expanded_position = self.normal_position - QPoint(322, 0)
        self.cursor_position = None
        self.populate_lists()
        self.handle_clip_view()

        
    def init_anims(self):
        self.scarab_animation = QPropertyAnimation(self.scarab, b"iconSize")
        self.scarab_pos_animation = QPropertyAnimation(self.scarab, b"pos")

        self.recycle_anim = QPropertyAnimation(self.recycle, b"pos")
        self.recycle_anim.setDuration(500)
        self.recycle_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.scarab_animation.setDuration(500)
        self.scarab_pos_animation.setDuration(400)

        self.scarab_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.scarab_pos_animation.setEasingCurve(QEasingCurve.InQuint)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.rain_animation = QPropertyAnimation(self.rain_label, b"pos")
        self.rain_animation.setDuration(800)
        self.rain_animation.setEasingCurve(QEasingCurve.Linear)

        self.shake_animation = QPropertyAnimation(self, b"pos")
        self.shake_animation.setDuration(500)
        self.shake_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.left_icon_size_animation = QPropertyAnimation(self.arrow_container, b"iconSize")
        self.right_icon_size_animation = QPropertyAnimation(self.right_arr_container, b"iconSize")

        self.copy_animation = QPropertyAnimation(self.copy, b"iconSize")

        for anim in (self.left_icon_size_animation, self.right_icon_size_animation, self.copy_animation):
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.size_animation = QPropertyAnimation(self, b"size")
        self.size_animation.setDuration(400)
        self.size_animation.setEasingCurve(QEasingCurve.InOutQuad)


    def remove_duplicates(self, data):
        unique_data = []
        seen = set()
        for entry in data:
            # Create a unique identifier for each entry to detect duplicates
            identifier = (entry["id"], entry["clipboard"])
            if identifier not in seen:
                seen.add(identifier)
                unique_data.append(entry)
        return unique_data
    
    def populate_lists(self):
        if not os.path.exists('clipboard.json'):
            with open('clipboard.json', 'w') as f:
                json.dump([], f)  # This will create the file and write an empty list as a JSON array

        with open('clipboard.json', 'r') as f:
            data = json.load(f)

        if not data:
            MessageWarning(text="The clipboard.json file is empty.", title="Clipboard Warning!")
            return

        self.remove_duplicates(data)
        self.instantinator = [{"list_id": i, "id": entry["id"], "clipboard": entry["clipboard"]} for i, entry in enumerate(data)]

        self.list_id = len(self.instantinator)
        self.view_id = self.list_id - 1 if not self.recycled else self.list_id - 2
        if self.recycled:
            self.recycled = False

    def handle_cb_contents(self):

        self.clipboard_content = self.collector.last_clipboard_content
        if self.last_clipboard_content == self.clipboard_content:
            return
        
        self.populate_lists()

        self.handle_clip_view()

        if self.last_clipboard_content  != self.clipboard_content:
            self.last_clipboard_content = self.clipboard_content


        
    def enterEvent(self, event):
        self.hovered = True
        self.animate_move(self.expanded_position)
        self.animate_iconSize(self.arrow_container, QSize(75, 75))
        self.animate_iconSize(self.right_arr_container, QSize(75, 75))
        self.animate_size(new_height=400)
        self.animate_rain()
        self.city_label.show()
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.animate_move(self.normal_position)
        self.animate_iconSize(self.arrow_container, QSize(32, 32))
        self.animate_iconSize(self.right_arr_container, QSize(32, 32))
        self.animate_size(new_height=200)
        self.city_label.hide()

        return super().leaveEvent(event)          

    def resizeEvent(self, event):
        self.set_mask()
        self.city_label.move(QPoint(176, 58))
        self.copy.move(230, 40)
        super().resizeEvent(event)

    def animate_move(self, new_position):
        self.animation.stop()
        self.animation.setEndValue(new_position)
        self.animation.start()

    def animate_iconSize(self, button, new_size, **kwargs):
        if button == self.arrow_container:
            anim = self.left_icon_size_animation
        elif button == self.copy_button:
            anim = self.copy_animation
        else:
            anim = self.right_icon_size_animation

        if kwargs.get('start'):
            anim.setStartValue(kwargs.get('start', QSize(30,30)))

        anim.setEndValue(new_size)
        anim.start()

    def handle_arrows(self, **kwargs):

        arrow = kwargs.get('arrow', )

        if arrow == "left":
            self.animate_iconSize(self.arrow_container, QSize(75, 75), start=QSize(30,30))
            if self.view_id > 0:
                self.view_id -= 1
            self.handle_clip_view()

        elif arrow == "right":
            self.animate_iconSize(self.right_arr_container, QSize(75, 75), start=QSize(30,30))
            if self.view_id < (len(self.instantinator) - 1):
                self.view_id += 1
            self.handle_clip_view()

    def animate_scarab(self, **kwargs):
        if self.recycle.isVisible() != True:
            self.recycle.show()
        self.scarab_animation.stop()
        self.scarab_pos_animation.stop()
        self.recycle_anim.stop()
        anim_type = kwargs.get('type', None)

        if anim_type == "start":
            self.recycle_anim.setEndValue(QPoint(135 - 60, 349))
            self.scarab_animation.setEndValue(QSize(40, 40))
            self.scarab_pos_animation.setEndValue(QPoint(135 + 20, 349))
            self.recycle_anim.start()
            self.scarab_animation.start()
            self.scarab_pos_animation.start()

    def animate_size(self, **kwargs):

        self.size_animation.stop()
        current_size = self.size()
        new_size = QSize(kwargs.get('new_width', current_size.width()), kwargs.get('new_height', 400))
        self.size_animation.setTargetObject(self)
        self.size_animation.setPropertyName(b'size')
        self.size_animation.setEndValue(new_size)
        self.size_animation.start()


    def animate_shake(self):


        animation_group = QSequentialAnimationGroup(self.clip)

        for i in range(2):
            # Animation for self.clip
            clip_animation1 = QPropertyAnimation(self.clip, b'pos')
            clip_animation1.setDuration(50)
            clip_animation1.setStartValue(self.clip_initial_pos)
            clip_animation1.setEndValue(self.clip_initial_pos + QPoint(10, 0) if i % 2 == 0 else self.clip_initial_pos - QPoint(10, 0))
            clip_animation1.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(clip_animation1)

            clip_animation2 = QPropertyAnimation(self.clip, b'pos')
            clip_animation2.setDuration(50)
            clip_animation2.setStartValue(clip_animation1.endValue())
            clip_animation2.setEndValue(self.clip_initial_pos)
            clip_animation2.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(clip_animation2)

            # Animation for self.copy
            copy_animation1 = QPropertyAnimation(self.copy, b'pos')
            copy_animation1.setDuration(50)
            copy_animation1.setStartValue(self.copy_initial_pos)
            copy_animation1.setEndValue(self.copy_initial_pos + QPoint(5, 0) if i % 2 == 0 else self.copy_initial_pos - QPoint(5, 0))
            copy_animation1.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(copy_animation1)

            copy_animation2 = QPropertyAnimation(self.copy, b'pos')
            copy_animation2.setDuration(50)
            copy_animation2.setStartValue(copy_animation1.endValue())
            copy_animation2.setEndValue(self.copy_initial_pos)
            copy_animation2.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(copy_animation2)

            # Animation for self.city
            city_anim1 = QPropertyAnimation(self.city_label, b'pos')
            city_anim1.setDuration(50)
            city_anim1.setStartValue(QPoint(173, 63))
            city_anim1.setEndValue(QPoint(173, 63) + QPoint(10, 0) if i % 2 == 0 else QPoint(173, 63) - QPoint(10, 0))
            city_anim1.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(city_anim1)

            city_anim2 = QPropertyAnimation(self.city_label, b'pos')
            city_anim2.setDuration(50)
            city_anim2.setStartValue(city_anim1.endValue())
            city_anim2.setEndValue(QPoint(173, 63))
            city_anim2.setEasingCurve(QEasingCurve.Linear)
            animation_group.addAnimation(city_anim2)

        animation_group.start()


    def reposition(self):
        # size of the screen
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()

        window_width = self.width()
        x_position = screen_width - window_width + 335
        y_position = 200

        self.move(x_position, y_position)

    def copy_handler(self, **kwargs):
        self.copy_anim_handle(icon="copied")
        self.current_id = self.view_id

        for elem in self.instantinator:
            if elem["list_id"] == self.current_id:
                clipboard.set_text(str(elem["clipboard"]))

    def copy_anim_handle(self, **kwargs):
        self.animate_iconSize(self.copy_button, QSize(40, 60), start=QSize(80,80))
        icon = kwargs.get("icon", None)
        if icon == "copy":
            self.copy.setIcon(self.copy_button)
        if icon == "copied":
            self.copy.setIcon(self.copied_button)

    def animate_rain(self):

        self.rain_animation.stop()
        self.rain_animation.setStartValue(self.rain_label.pos())
        self.rain_animation.setEndValue(QPoint(self.rain_label.x(), self.height() + 250))
        self.rain_animation.start()
        self.rain_animation.finished.connect(self.handle_rain)

    def handle_rain(self):
        self.rain_label.move(QPoint(self.rain_label.x(), self.height() - 1000))

    def init_main_ui(self, *args, **kwargs):
        self.setStyleSheet("""
            background-color: #111133;
            color: #d0d0d0;
        """)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.resize(350, 200)



        self.reposition()


        self.border_radius = 24
        self.set_mask()


    def handle_recycling(self):
        self.collector.clear()
        MessageWarning(text="Recycling has been conducted successfully!", title="Clipboard Recycler")
        self.view_id = 0
        self.instantinator = []
        self.set_clipboard(text="")
        self.recycled = True


    def init_ui(self, *args, **kwargs):
        
        self.blur_label = blurButton(self)

        self.copy = uButton(self, self)
        self.copy.setFixedSize(60,60)
        self.copy.setIconSize(QSize(40, 60))
        self.copy.setIcon(self.copy_button)

        self.scarab = sButton(self, self)
        self.scarab.setIconSize(QSize(32,32))
        self.scarab.setStyleSheet(""" 
                background-color: transparent;
                background: transparent;
                border: 0px solid transparent;
        
        """)
        self.scarab.setFixedSize(QSize(100,65))
        self.scarab.setIcon(self.scarab_icon)
        self.scarab.move(self.width() - 230, self.height() + 149)

        self.recycle = sButton(self, self)
        self.recycle.setIconSize(QSize(30,30))
        self.recycle.setStyleSheet(""" 
                background-color: transparent;
                background: transparent;
                border: 0px solid transparent;
        
        """)
        self.recycle.setFixedSize(QSize(100,65))
        self.recycle.setIcon(self.recycle_icon)
        self.recycle.move(self.width() - 250, self.height() + 149)
        self.recycle.clicked.connect(self.handle_recycling)

        self.copy.clicked.connect(self.copy_handler)
        self.copy.move(230, 40)
        self.rain_label = QLabel(self)
        self.rain_label.setStyleSheet(""" 
                background: transparent;
                background-color: transparent;
                border: 0px solid transparent;
        """)
        self.rain_label.setPixmap(self.neon_rain)
        self.rain_label.setScaledContents(True)
        self.rain_label.resize(400, 400)
        self.rain_label.move(0, -self.rain_label.height())




        self.left_rect = QVBoxLayout()
        self.left_rect.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 40, 15, 40)

        self.right_rect = QVBoxLayout()
        self.right_rect.setContentsMargins(0, 0, 0, 0)



        self.city_label = QLabel(self)
        self.city_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.city_label.setStyleSheet(""" 
                background: transparent;
                background-color: transparent;
                border: 0px solid transparent;
        
        
        """)
        transparent_pixmap = QPixmap(self.city_part_a.size())
        transparent_pixmap.fill(Qt.transparent)
    
        painter = QPainter(transparent_pixmap)
        painter.setOpacity(0.15)
        painter.drawPixmap(QPoint(0, 0), self.city_part_a)
        painter.end()

        self.city_label.setPixmap(transparent_pixmap)
        self.city_label.setScaledContents(True)
        self.city_label.resize(100, 300)
        self.city_label.move(QPoint(176, 58))
        self.city_label.hide()

        self.clip = CustomTE(self)
        self.clip.setReadOnly(True)
        self.clip.mouse_signal.connect(self.animate_shake)
        self.clip.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.clip.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.clip.setStyleSheet("""
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop:0 #111033, stop:0.25 #111133, stop:0.5 #111634, stop:0.75 #141634, stop:1 #161634);
                border: 0px solid transparent;
                border-radius: 12px;
        """)
        self.clip_initial_pos = QPoint(42, 35)
        self.copy_initial_pos = self.copy.pos()

        self.arrow_container = ClipButton(self, 'left')


        self.right_arr_container = ClipButton(self, 'right')

        self.arrow_container.clicked.connect(lambda: self.handle_arrows(arrow="left"))
        self.right_arr_container.clicked.connect(lambda: self.handle_arrows(arrow="right"))


        self.right_rect.addWidget(self.right_arr_container)
        self.main_layout.addLayout(self.left_rect)
        self.main_layout.addWidget(self.clip)
        self.left_rect.addWidget(self.arrow_container)

        self.main_layout.addLayout(self.right_rect)
        self.rain_label.raise_()
        self.city_label.raise_()
        self.copy.raise_()

        self.setLayout(self.main_layout)
        self.show()

    def set_clipboard(self, **kwargs):
        self.clip.setText("")
        self.text = kwargs.get('text', '')
        if self.text != "":
            cursor = self.clip.textCursor()

            # text into lines
            lines = self.text.split('\n')
            # Process each line
            for i, line in enumerate(lines):

                format = QTextBlockFormat()
                if i < 2:
                    # Pre
                    format.setTopMargin(int(0.4))
                    format.setLeftMargin(10)
                    format.setRightMargin(50)
                else:
                    # Post
                    format.setTopMargin(int(0.4))
                    format.setLeftMargin(10)
                    format.setTextIndent(0)
                    format.setRightMargin(0)

                format.setBackground(QBrush(QColor("#001133")))
                cursor.setBlockFormat(format)


                charFormat = QTextCharFormat()
                charFormat.setForeground(QBrush(QColor("#e0e0e0"))) 
                
                
                font = QFont("Arial", 13)
                charFormat.setFontWeight(QFont.Bold) 
                
                charFormat.setFont(font)
                cursor.setCharFormat(charFormat)

                # Insert text line and move to the next block
                cursor.insertText(line)
                if i < len(lines) - 1:  # Don't add a new block after the last line
                    cursor.insertBlock()

            # Set the modified cursor back to the text edit
            self.clip.setTextCursor(cursor)
            self.clip.verticalScrollBar().setValue(0)
    def set_mask(self):
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, self.width(), self.height()), self.border_radius, self.border_radius)

        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

    def handle_clip_view(self):
        self.copy_anim_handle(icon="copy")
        for elem in self.instantinator: 
            if self.view_id == elem["list_id"]:
                text = elem["clipboard"]
                self.set_clipboard(text=text) 

if __name__ == '__main__':
    app = QApplication([])
    clip_ui = ClipUI()


    exit_code = app.exec()
    clip_ui.collector.stop_listening = True
    clip_ui.collector_thread.join()
    sys.exit(exit_code)