#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import math
import datetime

from PyQt5 import QtGui, QtCore, QtWidgets
import luk_op_gui_upd as gui

elems = {}

# Override-класс интерфейса для реализации обработки кастомных сигналов
class LukWidget(QtWidgets.QMainWindow, gui.Ui_MainWindow):

    resized = QtCore.pyqtSignal()

    def __init__(self, controller):
        super(LukWidget, self).__init__()
        self.setupUi(self)
        self.resized.connect(self.scale_elems)
        self.sc = controller
        self.sc.new_log_entry.connect(self.new_log_entry)  # соединяем один слот с сигналом
        self.sc.new_temp_value.connect(self.new_temp_value)  # другой слот с сигналом
        self.sc.scenario_ended.connect(self.stop_controller)
        self.w = self.window().width()
        self.h = self.window().height()
        children = self.findChildren(QtWidgets.QWidget)
        for child in children:
            child.setMouseTracking(True)
    
    def new_log_entry(self, msg):
        self.log.append(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ' ' + str(msg))
    
    def new_temp_value(self, value, crit_t):
        if value >= crit_t:
            display_color_window = QtGui.QColor(150, 0, 0)
            display_color_text = QtGui.QColor(255, 170, 170)
        else:
            display_color_window = QtGui.QColor(0, 85, 0)
            display_color_text = QtGui.QColor(170, 255, 0)
        tmp_plt = self.ctgt.palette()
        brush = QtGui.QBrush(display_color_window)
        brush.setStyle(QtCore.Qt.SolidPattern)
        tmp_plt.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(display_color_text)
        brush.setStyle(QtCore.Qt.SolidPattern)
        tmp_plt.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        self.ctgt.setPalette(tmp_plt)
        self.label_8.setPalette(tmp_plt)
        self.ctgt.display(value)
    
    def stop_controller(self, code):
        self.log.append("=== Сценарий завершен ===")
        self.log.append("Код завершения: " + str(code))
        self.sc.exit()
    
    def resizeEvent(self, event):
        self.resized.emit()
        return super(LukWidget, self).resizeEvent(event)
    
    def scale_elems(self):
        children = self.centralwidget.findChildren(QtWidgets.QWidget)
        w1 = self.window().width()
        h1 = self.window().height()
        h_scale_rate = h1 / self.h
        for widget in children:
            if widget.height() > 0:
                aspect =  widget.width() / widget.height()
            else:
                aspect = 1
            new_height = widget.height() * h_scale_rate
            new_width = new_height * aspect
            widget.setGeometry(round(widget.geometry().x() * h_scale_rate), round(widget.geometry().y() * h_scale_rate), new_width, new_height)
        self.w = w1
        self.h = h1

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = event.pos()
        print("Mouse at " + str(pos.x()) + ", " + str(pos.y()), file=sys.stderr)
        #self.log(pos)


# Класс, минимально описыващий элементы установки для реализации логики
class Element:
    def __init__(self, controller, code, widget, initial_state=0):
        self.controller = controller
        self.code = code
        self.widget = widget
        self.state = initial_state

    def change_sprite(self):
        '''В интерфейсе заменить спрайт одного состояния на спрайт другого состояния'''
        if self.widget is not None:
            self.update_colors(self.state)
        else:
            print('Warning: Nothing to change', file=sys.stderr)
    
    def update_colors(self, color_state = 0):
        '''Перерисовываем спрайт с наложением соответствующего состоянию цвета'''
        if self.widget is not None:
            if os.path.exists(os.path.dirname(os.path.abspath(__file__)) + '/img/' + self.code + '.png'):
                pxm = QtGui.QPixmap(os.path.dirname(os.path.abspath(__file__)) + '/img/' + self.code + '.png')
            else:
                pxm = QtGui.QPixmap(os.path.dirname(os.path.abspath(__file__)) + '/img/temp.png')
            if color_state == 0:
                widget_color = QtGui.QColor(170, 255, 0, 150)
            else:
                widget_color = QtGui.QColor(255, 170, 170, 150)
            p = QtGui.QPainter(pxm)
            p.setCompositionMode(QtGui.QPainter.CompositionMode_SourceAtop)
            p.fillRect(pxm.rect(), widget_color)
            p.end()
            self.widget.setPixmap(pxm)
        else:
            print('Warning: Nothing to update', file=sys.stderr)
    
    def set_state(self, new_state, condition=None, *args, **kwargs):
        '''Установить состояние вручную'''
        if condition is not None and callable(condition):
            cond = condition(*args, **kwargs)
            if cond[0]:
                self.state = new_state
                self.change_sprite()
                self.controller.log(self.code + ': состояние установлено на ' + str(self.state) + ' по условию ' + str(cond[1]))
            else:
                pass #self.controller.log(self.code + ': был запрос на установку состояния ' + str(new_state) + '; не выполнено условие ' + str(cond[1]))
        else:
            self.state = new_state
            self.change_sprite()
            self.controller.log(self.code + ': состояние установлено на ' + str(self.state) + ' без условия')

    def change_state(self, condition=None, *args, **kwargs):
        '''Проверить, выполняется ли некое условие (или его отсутствие), после чего поменять состояние на противположное'''
        if condition is not None and callable(condition):
            cond = condition(*args, **kwargs)
            if cond[0]:
                self.state = 1 - self.state
                self.change_sprite()
                self.controller.log(self.code + ': состояние с ' + str(1 - self.state) + ' изменено на ' + str(self.state) + ' по условию ' + str(cond[1]))
            else:
                pass #self.controller.log(self.code + ': был запрос на изменение состояния с ' + str(self.state) + ' на ' + str(1 - self.state) + '; не выполнено условие ' + str(cond[1]))
        else:
            self.state = 1 - self.state
            self.change_sprite()
            self.controller.log(self.code + ': состояние с ' + str(1 - self.state) + ' изменено на ' + str(self.state) + ' без условия')


# Класс-контроллер, работает в отдельном потоке и посылает сигналы интерфейсу
class ScenarioController(QtCore.QThread):

    new_log_entry = QtCore.pyqtSignal(object)  # сигнал для обновления лога
    new_temp_value = QtCore.pyqtSignal(float, float)  # сигнал для обновления цифрового табло
    scenario_ended = QtCore.pyqtSignal(int)  # сигнал для завершения сценария

    def __init__(self, temp=60, critical_temp=200, timer=60.0):
        QtCore.QThread.__init__(self)
        self.active = False
        self.temp = temp
        self.crit_t = critical_temp
        self.action_handler = []
        self.start_time = datetime.datetime.now().timestamp()
        self.current_time = self.start_time
        self.timer = timer
    
    def __del__(self):
        self.wait()

    def execute_scenario(self, scenario): # последовательно выполнить все действия, если выполнены их условия, в сценарии scenario
        for action in scenario.keys():
            self.action_handler.append([scenario[action], 0, self.current_time])
        self.active = True
        while self.active:
            for action in self.action_handler:
                if action[0][1] is not None and callable(action[0][1]):                             # если действие повторяется, пока выполняется условие
                    if action[0][1]() and (self.current_time - action[2]) >= action[0][2]:          # если условие выполнено и при этом прошло достаточно времени для повтора
                        action[0][0]()                                                              # выполняем действие
                        action[2] = self.current_time                                               # указываем время последнего выполнения
                    elif not action[0][1]():                                                        # если условие не выполнено 
                        action[1] += 1                                                              # помечаем, что действие больше не нужно выполнять
                    else:
                        continue                                                                    # если нет, идем дальше
                else:
                    if action[1] == 0:  # если действие не повторяется и не выполнялось еще ни разу
                        action[0][0]()  # выполняем действие
                        action[1] += 1  # помечаем, что оно выполнялось
                    else:
                        continue        # если нет, идем дальше
            self.current_time = datetime.datetime.now().timestamp()
            self.sleep(0.01)
    
    def log(self, msg):
        '''Логирование в консоль и в интерфейс'''
        print(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ' ' + str(msg))
        self.new_log_entry.emit(msg)
    
    def reset_timer(self, new_timer=60.0):
        self.timer = new_timer
        self.start_time = datetime.datetime.now().timestamp()
        self.log("Был сброшен таймер, новое время для выполнения задания: " + str(self.timer) + " сек.")
    
    def set_crit_t(self, new_crit_t):
        self.crit_t = new_crit_t
        self.log('Значение Ткрит установлено на ' + str(self.crit_t))
    
    def display_temp(self):
        self.new_temp_value.emit(self.temp, self.crit_t)

    def set_temp(self, new_temp):
        '''Вручную установить температуру'''
        self.temp = new_temp
        self.display_temp()
        self.log("Значение температуры установлено на %s" % new_temp)
    
    def check(self, cond_desc='[условие перехода без описания]', condition=None, *args, **kwargs):
        '''Проверить выполнения условия перехода и вернуть результат проверки и описание условия для журнала'''
        if condition is not None and callable(condition):
            cond = condition(*args, **kwargs)
            if cond:
                return (True, cond_desc)
            else:
                return (False, cond_desc)
        else:
            return (False, cond_desc)

    def raise_temp(self, raise_by=15):
        '''Повышение температуры'''
        self.temp += raise_by
        self.display_temp()
        self.log("Температура повысилась на %s (тек. знач.: %s)" % (raise_by, self.temp))

    def lower_temp(self, lower_by=15):
        '''Снижение температуры'''
        self.temp -= lower_by
        self.display_temp()
        self.log("Температура снизилась на %s (тек. знач.: %s)" % (lower_by, self.temp))

    def make_call(self):
        '''Сымитировать звонок диспетчеру'''
        self.active = False
        self.log("Сделан звонок диспетчеру")
        self.scenario_ended.emit(0)
    
    def fail(self):
        self.active = False
        self.log("Задание не выполнено в срок")
        self.scenario_ended.emit(1)

    def run(self):
        '''Запуск сценария'''
        self.log("=== Сценарий начат ===")
        self.execute_scenario(scenario)



if __name__ == '__main__':
    # Создаем экземпляр приложения, интерфейса и контроллера, 
    # а также наполняем elems экземплярами Элементов, 
    # связывая их с условными обозначениями и элементами интерфейса
    app = QtWidgets.QApplication(sys.argv)
    sc = ScenarioController()
    main_window = LukWidget(sc)
    elems['сс'] = Element(sc, 'сс', main_window.ss)
    elems['зугт'] = Element(sc, 'зугт', main_window.zugt)
    elems['зуку'] = Element(sc, 'зуку', main_window.zuku)
    elems['втг'] = Element(sc, 'втг', main_window.vtg, 1)
    elems['запг'] = Element(sc, 'запг', main_window.zapg, 1)
    elems['загб'] = Element(sc, 'загб', main_window.zagb, 1)

    
    # Прописанное начало сценария, пока без корутин с проверками условий (состояние элементов, таймер и т.д.), 
    # все действия надо делать В РУЧНОМ РЕЖИМЕ
    # Описание действия: 
    # "человекочитаемый ключ": (анонимная функция-действие, граничное условие, периодичность проверки выполненности граничного условия в секундах)
    scenario = {
        "сброс_журналирование": (lambda: sc.log(' === Сброс состояний начат ==='), None, 0), 
        "установка_значения_т_крит": (lambda: sc.set_crit_t(200), None, 0),
        "сброс_температуры": (lambda: sc.set_temp(60.5), None, 0),
        "сброс_состояния_сс": (lambda: elems['сс'].set_state(0), None, 0),
        "сброс_состояния_зугт": (lambda: elems['зугт'].set_state(0), None, 0),
        "сброс_состояния_зуку":(lambda: elems['зуку'].set_state(0), None, 0),
        "сброс_состояния_втг": (lambda: elems['втг'].set_state(1), None, 0),
        "сброс_состояния_запг": (lambda: elems['запг'].set_state(1), None, 0),
        "сброс_состояния_загб": (lambda: elems['загб'].set_state(1), None, 0),
        "сброс_таймера": (lambda: sc.reset_timer(), None, 0),
        "сброс_завершение": (lambda: sc.log(' === Сброс состояний завершен ==='), None, 0),
        "сс_при_критическом_т": (lambda: elems['сс'].set_state(1, lambda: sc.check('Т > Ткрит', lambda: sc.temp > sc.crit_t)), lambda: elems['сс'].state != 1, 1),
        "повышение_температуры": (lambda: sc.raise_temp(60.45), lambda: sc.temp < sc.crit_t and 
                                                                        elems['зугт'].state == 0 and 
                                                                        elems['зуку'].state == 0 and
                                                                        elems['втг'].state == 1 and
                                                                        elems['запг'].state == 1 and
                                                                        elems['загб'].state == 1, 2),
        "снижение_температуры_при_правильных_действиях": (lambda: sc.lower_temp(10.25), lambda: sc.temp > 60 and 
                                                                                                elems['зугт'].state == 1 and 
                                                                                                elems['зуку'].state == 1 and
                                                                                                elems['втг'].state == 0 and
                                                                                                elems['запг'].state == 0 and
                                                                                                elems['загб'].state == 0, 1),
        "возврат_сс_в_норму": (lambda: elems['сс'].set_state(0, lambda: sc.check('Т < Ткрит', lambda: sc.temp < sc.crit_t)), lambda: elems['сс'].state == 1, 1),
        "провал_задания_по_таймеру": (lambda: sc.fail(), lambda: sc.current_time >= sc.start_time + sc.timer and sc.temp >= sc.crit_t, 0.1)
    }

    # Пока руками приписывание кнопкам действия
    main_window.btn_gt.clicked.connect(lambda: elems['зугт'].set_state(1))
    main_window.btn_ku.clicked.connect(lambda: elems['зуку'].set_state(1))
    main_window.btn_vtg.clicked.connect(lambda: elems['втг'].set_state(0))
    main_window.btn_pg.clicked.connect(lambda: elems['запг'].set_state(0))
    main_window.btn_gb.clicked.connect(lambda: elems['загб'].set_state(0))
    main_window.btn_call.clicked.connect(sc.make_call)
    main_window.btn_start.clicked.connect(sc.start)


    # Запуск
    main_window.show()
    sys.exit(app.exec_())

