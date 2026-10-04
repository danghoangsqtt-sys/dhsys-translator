import json
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QFrame

from videotrans.ui.fn_fanyisrt import Ui_fn_fanyisrt
from videotrans.ui.fn_peiyinrole import Ui_fn_peiyinrole
from videotrans.ui.fn_recogn import Ui_fn_recogn
from videotrans.ui.fn_vas import Ui_fn_vas
from videotrans.ui.home import HomePage


app = QApplication.instance() or QApplication([])


def test_home_cards_reflow_inside_narrow_canvas():
    page = HomePage('vi_VN')
    for width in (480, 720, 900, 1280):
        page.resize(width, 720)
        page.show()
        app.processEvents()
        cards = page.findChildren(QFrame, 'toolCard')
        assert len(cards) == 4
        assert all(card.mapTo(page, QPoint()).x() + card.width() <= page.width() for card in cards)
    page.close()


def test_primary_quick_tool_controls_remain_visible_at_480px():
    tools = (
        (Ui_fn_fanyisrt(), ('fanyi_import', 'fanyi_start')),
        (Ui_fn_peiyinrole(), ('hecheng_importbtn', 'hecheng_startbtn')),
        (Ui_fn_vas(), ('ysphb_selectvideo', 'ysphb_startbtn')),
        (Ui_fn_recogn(), ('shibie_startbtn', 'shibie_opendir')),
    )
    for tool, controls in tools:
        tool.resize(480, 720)
        tool.show()
        app.processEvents()
        assert tool.width() == 480
        for name in controls:
            control = getattr(tool, name)
            assert control.mapTo(tool, QPoint()).x() + control.width() <= tool.width(), name
        tool.close()


def test_multiple_speakers_uses_shared_light_table_style_and_compact_menu_is_vietnamese():
    tool = Ui_fn_peiyinrole()
    assert tool.subtitle_table.styleSheet() == ''
    assert tool.label_11.styleSheet() == ''
    catalog = Path(__file__).resolve().parents[1] / 'videotrans' / 'language' / 'vi_VN.json'
    assert json.loads(catalog.read_text(encoding='utf-8'))['Menu'] == 'Danh mục'
