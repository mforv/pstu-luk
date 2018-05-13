#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import datetime
import asyncio

from PyQt5 import QtGui, QtCore, QtWidgets
from luk_op_gui import Ui_MainWindow

app = QtWidgets.QApplication(sys.argv)
main_window = QtWidgets.QMainWindow()
gui = Ui_MainWindow()
elems = {}


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
            pxm = QtGui.QPixmap(os.path.dirname(os.path.abspath(__file__)) + '/img/' + self.code + str(self.state) + '.png')
            self.widget.setPixmap(pxm)
            self.widget.resize(float(pxm.width()) / 2, float(pxm.height()) / 2)
        else:
            print('Nothing to change')
    
    def set_state(self, new_state):
        '''Устанвить состояние вручную'''
        self.state = new_state
        self.change_sprite()
        self.controller.log(' ' + self.code + ': состояние изменено на ' + str(self.state))

    def change_state(self, condition=None, *args, **kwargs):
        '''Проверить, выполняется ли некое условие (или его отсутствие), после чего поменять состояние на противположное'''
        if condition is not None and callable(condition):
            if condition(*args, **kwargs):
                #time.sleep(2)
                self.state = 1 - self.state
                self.change_sprite()
                self.controller.log(' ' + self.code + ': состояние изменено на ' + str(self.state))
        else:
            #time.sleep(2)
            self.state = 1 - self.state
            self.change_sprite()
            self.controller.log(' ' + self.code + ': состояние изменено на ' + str(self.state))


# Класс-контроллер, в перспективе должен работать в отдельном процессе/потоке
class ScenarioController:

    def __init__(self, log_widget, temp_widget, temp=60, critical_temp=200):
        self.log_w = log_widget
        self.temp = temp
        self.temp_widget = temp_widget
        self.crit_t = critical_temp

    def execute_scenario(self, scenario): # последовательно выполнить все действия, если выполнены их условия, в сценарии scenario
        for action in scenario.keys():
            if scenario[action][1] is not None and callable(scenario[action][1]):
                if scenario[action][1]():
                    scenario[action][0]()
            elif scenario[action][1]:  # возможно, стоит приравнять отсутствие условия к его выполненности, но пока лучше перестраховаться и дописать True
                scenario[action][0]()
            else:
                pass
    
    def log(self, msg):
        '''Логирование в консоль и в интерфейс'''
        print(str(datetime.datetime.now()) + str(msg))
        self.log_w.append(str(datetime.datetime.now()) + str(msg))

    def set_temp(self, new_temp):
        '''Вручную установить температуру'''
        self.temp = new_temp
        self.temp_widget.display(new_temp)
        self.log(" Значение температуры установлено на %s" % new_temp)

    # def raise_temp(self, max_temp=200, time_step=2, temp_step=2):  # повышение температуры
    #     while self.temp < max_temp:
    #         self.temp += temp_step      
    #         self.log(" Температура повысилась на %s (тек. знач.: %s" % temp_step, self.temp)
    #         time.sleep(time_step)

    # def lower_temp(self, target_temp=60, time_step=2, temp_step=2):  # снижение температуры
    #     while self.temp > target_temp:
    #         self.temp -= temp_step
    #         self.log(" Температура снизилась на %s (тек. знач.: %s" % temp_step, self.temp)
    #         time.sleep(time_step)

    def make_call(self):
        '''Сымитировать звонок диспетчеру'''
        self.log(" Сделан звонок диспетчеру\n=== Сценарий завершен ===")

    def demo_scene(self):
        self.log(" === Сценарий начат ===")
        self.execute_scenario(scenario)



if __name__ == '__main__':
    gui.setupUi(main_window)
    # Создаем экземпляр контроллера и наполняем elems экземплярами Элементов, 
    # связывая их с условными обозначениями и элементами интерфейса
    sc = ScenarioController(gui.log, gui.ctgt)
    elems['сс'] = Element(sc, 'сс', gui.ss)
    elems['зугт'] = Element(sc, 'зугт', gui.gt)
    elems['зуку'] = Element(sc, 'зуку', gui.zuku)
    elems['втг'] = Element(sc, 'втг', gui.vtg, 1)
    elems['запг'] = Element(sc, 'запг', gui.zapg, 1)
    elems['загб'] = Element(sc, 'загб', gui.zagb, 1)
    
    # Прописанное начало сценария, пока без корутин с проверками условий (состояние элементов, таймер и т.д.), 
    # все действия надо делать В РУЧНОМ РЕЖИМЕ
    scenario = {
        "сброс_журналирование": (lambda: sc.log(' === Сброс состояний начат ==='), True),
        "сброс_температуры": (lambda: sc.set_temp(60), True),
        "сброс_состояния_сс": (lambda: elems['сс'].set_state(0), True),
        "сброс_состояния_зугт": (lambda: elems['зугт'].set_state(0), True),
        "сброс_состояния_зуку": (lambda: elems['зуку'].set_state(0), True),
        "сброс_состояния_втг": (lambda: elems['втг'].set_state(1), True),
        "сброс_состояния_запг": (lambda: elems['запг'].set_state(1), True),
        "сброс_состояния_загб": (lambda: elems['загб'].set_state(1), True),
        "сброс_завершение": (lambda: sc.log(' === Сброс состояний завершен ==='), True),
        "старт_сценария": (lambda: sc.set_temp(200), True),
        "переход_сс": (elems['сс'].change_state, lambda: sc.temp > 60) # условие тестовое, можно посмотреть вживую, если в предыдущем действии заменить 200 на 40, например
    }

    # Пока руками приписывание кнопкам действий

    gui.btn_gt.clicked.connect(elems['зугт'].change_state)
    gui.btn_ku.clicked.connect(elems['зуку'].change_state)
    gui.btn_vtg.clicked.connect(elems['втг'].change_state)
    gui.btn_pg.clicked.connect(elems['запг'].change_state)
    gui.btn_gb.clicked.connect(elems['загб'].change_state)
    gui.btn_call.clicked.connect(sc.make_call)
    gui.btn_start.clicked.connect(sc.demo_scene)

    # Запуск интерфейса
    main_window.show()
    sys.exit(app.exec_())

