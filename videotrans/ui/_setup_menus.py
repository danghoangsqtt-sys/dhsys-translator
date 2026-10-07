from PySide6 import QtCore, QtGui, QtWidgets
from videotrans.ui.menu_list import MENU_CFG_TRANS, MENU_CFG_TTS, MENU_CFG_STT, MENU_CFG_TOOLS, MENU_CFG_HELP, \
    MENU_CFG_PANEL
from videotrans.configure.config import params, tr
from videotrans.ui.provider_visibility import (
    RECOGNITION, TRANSLATION, TTS, apply_menu_visibility, refresh_registered_combos,
)
from videotrans.util.help_misc import open_url, show_popup
from videotrans.winform import get_win


def _make_action(ui, obj=None,menu=None,add_hr=True):
    k,title,_inst=obj
    action = QtGui.QAction()
    action.setObjectName(k)
    action.setText(title)
    setattr(ui, k, action)
    if _inst is not False:
        if _inst is None:
            action.triggered.connect(lambda :get_win(k))
        elif isinstance(_inst,str) and _inst.startswith('http'):
            action.triggered.connect(lambda :open_url(_inst))
        elif isinstance(_inst,str):
            action.triggered.connect(lambda :show_popup(title,_inst))

    if menu:
        menu.addAction(action)
        if add_hr:
            menu.addSeparator()
    return action



def _fill_menu(menu, actions):
    for action in actions:
        menu.addAction(action)
        menu.addSeparator()




def _setup_actions_and_menus(ui, MainWindow):
    ui.menuBar = QtWidgets.QMenuBar()
    ui.menuBar.setObjectName("menuBar")
    ui.menu_Key = QtWidgets.QMenu(ui.menuBar)
    ui.menu_Key.setObjectName("menu_Key")
    ui.menu_TTS = QtWidgets.QMenu(ui.menuBar)
    ui.menu_TTS.setObjectName("menu_TTS")
    ui.menu_RECOGN = QtWidgets.QMenu(ui.menuBar)
    ui.menu_RECOGN.setObjectName("menu_RECOGN")
    ui.menu = QtWidgets.QMenu(ui.menuBar)
    ui.menu.setObjectName("menu")
    ui.menu_H = QtWidgets.QMenu(ui.menuBar)
    ui.menu_H.setObjectName("menu_H")
    MainWindow.setMenuBar(ui.menuBar)

    ui.toolBar = QtWidgets.QToolBar()
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(ui.toolBar.sizePolicy().hasHeightForWidth())
    ui.toolBar.setSizePolicy(sizePolicy)
    ui.toolBar.setMinimumSize(QtCore.QSize(0, 0))
    ui.toolBar.setMaximumSize(QtCore.QSize(16777215, 16777215))
    ui.toolBar.setMovable(True)

    ui.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    ui.toolBar.setFloatable(True)
    ui.toolBar.setObjectName("toolBar")
    ui.toolBar.setStyleSheet("""
    QToolBar QToolButton {
        min-width: 100px; 
        text-align: center; 
    }
""")
    MainWindow.addToolBar(QtCore.Qt.LeftToolBarArea, ui.toolBar)
    # 翻译设置
    ui._provider_actions_by_kind = {
        TRANSLATION: [],
        TTS: [],
        RECOGNITION: [],
    }
    for obj in MENU_CFG_TRANS:
        ui._provider_actions_by_kind[TRANSLATION].append(
            _make_action(ui, obj, ui.menu_Key)
        )


    for obj in MENU_CFG_TTS:
        ui._provider_actions_by_kind[TTS].append(
            _make_action(ui, obj, ui.menu_TTS)
        )

    for obj in MENU_CFG_STT:
        ui._provider_actions_by_kind[RECOGNITION].append(
            _make_action(ui, obj, ui.menu_RECOGN)
        )

    ui.show_all_providers = QtGui.QAction(MainWindow)
    ui.show_all_providers.setObjectName("show_all_providers")
    ui.show_all_providers.setText(tr("Show all providers"))
    ui.show_all_providers.setCheckable(True)
    show_all = bool(params.get("show_all_providers", False))
    ui.show_all_providers.setChecked(show_all)
    for provider_menu in (ui.menu_Key, ui.menu_TTS, ui.menu_RECOGN):
        provider_menu.addSeparator()
        provider_menu.addAction(ui.show_all_providers)

    def set_show_all(checked):
        handler = getattr(MainWindow, "set_show_all_providers", None)
        if callable(handler):
            handler(checked)
            return
        params.getset_params({"show_all_providers": bool(checked)})
        apply_menu_visibility(ui, show_all=bool(checked))
        refresh_registered_combos(show_all=bool(checked))

    ui.show_all_providers.toggled.connect(set_show_all)
    apply_menu_visibility(ui, show_all=show_all)

    for obj in MENU_CFG_TOOLS:
        _make_action(ui, obj,ui.menu)

    for obj in MENU_CFG_HELP:
        _make_action(ui, obj,ui.menu_H)


    for obj in MENU_CFG_PANEL:
        _make_action(ui, obj,ui.toolBar,False)











    ui.menuBar.addAction(ui.menu_Key.menuAction())
    ui.menuBar.addAction(ui.menu_TTS.menuAction())
    ui.menuBar.addAction(ui.menu_RECOGN.menuAction())
    ui.menuBar.addAction(ui.menu.menuAction())
    ui.menuBar.addAction(ui.menu_H.menuAction())

    # ui.toolBar.addAction(ui.action_biaozhun)
    # ui.toolBar.addAction(ui.action_tiquzimu)
    # ui.toolBar.addAction(ui.fn_recogn)
    # ui.toolBar.addAction(ui.fn_peiyin)
    # ui.toolBar.addAction(ui.fn_fanyisrt)
    # ui.toolBar.addAction(ui.fn_peiyinrole)
    # ui.toolBar.addAction(ui.fn_vas)
