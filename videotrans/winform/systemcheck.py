from pathlib import Path


def openwin():
    from videotrans.winform import get_cls

    return get_cls(Path(__file__).stem)()

