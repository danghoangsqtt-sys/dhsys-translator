from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import Qt, QIcon

from videotrans.configure.config import ROOT_DIR, tr, defaulelang
from videotrans.ui._legal_terms import legal_terms_html


class Ui_lawalert(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.main=parent
        self.setupUi(self)
        self.setWindowIcon(QIcon(f"{ROOT_DIR}/videotrans/styles/icon.ico"))

    def setupUi(self, lawalert):

        lawalert.setObjectName("lawalert")
        lawalert.setWindowModality(QtCore.Qt.ApplicationModal)
        lawalert.resize(950, 600)
        flags = QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lawalert.sizePolicy().hasHeightForWidth())
        lawalert.setSizePolicy(sizePolicy)
        self.v1 = QtWidgets.QVBoxLayout(lawalert)
        # 将 v1 设为垂直顶部对齐
        self.v1.setAlignment(Qt.AlignTop)

        self.text1 = QtWidgets.QTextEdit()
        self.text1.setObjectName("text1")
        self.text1.setReadOnly(True)
        self.text1.setMinimumHeight(400)
        self.text1.setHtml(legal_terms_html(defaulelang))
        # text1的边框合为0
        self.text1.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.text1.setStyleSheet("""
        border:none;
        """)
        self.v1.addWidget(self.text1)


        lawbtn = QtWidgets.QPushButton()
        lawbtn.setFixedHeight(35)
        lawbtn.setMaximumWidth(300)

        lawbtn.setCursor(Qt.PointingHandCursor)
        lawbtn.setText(tr("I Agree and Continue"))
        lawbtn.clicked.connect(lambda :self._close(True))

        dont = QtWidgets.QPushButton()
        dont.setFixedHeight(35)
        dont.setMaximumWidth(200)

        dont.setCursor(Qt.PointingHandCursor)
        dont.setText(tr("Disagree"))
        dont.clicked.connect(lambda :self._close(False))

        btn_h=QtWidgets.QHBoxLayout()
        btn_h.addWidget(lawbtn)
        btn_h.addWidget(dont)
        self.v1.addLayout(btn_h)

        lawalert.setWindowTitle('pyVideoTrans '+tr('Software License Agreement'))

    def _close(self,res=True):
        if res:
            Path(ROOT_DIR+"/.agree.txt").write_text("Yes,I Agree and Continue ")
            self.close()
        else:
            self.hide()
            self.main.close()
            Path(ROOT_DIR+"/.agree.txt").unlink(missing_ok=True)
            self.close()



