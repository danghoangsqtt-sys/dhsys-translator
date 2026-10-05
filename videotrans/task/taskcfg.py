import os
from dataclasses import dataclass, asdict
from typing import Optional, Union
from pathlib import Path

from videotrans.configure.config import tr

class _LocalizedChoices:
    def __init__(self, keys):
        self.keys = keys

    def __getitem__(self, index):
        return tr(self.keys[index])


isTrue = _LocalizedChoices({True: "selected", False: "unselected"})
_duanjus = _LocalizedChoices(["default_segment", "llm_resegment"])
_outs = _LocalizedChoices(["monolingual_subtitle", "target_below", "target_above"])
_loops = _LocalizedChoices(["loop_bgm", "extend_bgm"])


def _cuda_status(enabled):
    return tr("cuda_status", tr("enabled" if enabled else "disabled"))


def _speaker_limit(count):
    return tr("unlimited") if count < 1 else count + 1


@dataclass
class InputFile:
    name: Union[os.PathLike, str] = None
    dirname: Union[os.PathLike, str] = None
    basename: str = None
    noextname: str = None
    ext: str = None
    uuid: str = None
    target_dir: Optional[str] = None

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    # 处理：dataclass_obj | dict_obj
    def __or__(self, other):
        if isinstance(other, dict):
            return asdict(self) | other
        return NotImplemented

    # 处理：dict_obj | dataclass_obj
    def __ror__(self, other):
        if isinstance(other, dict):
            return other | asdict(self)
        return NotImplemented

    def get(self, key, default=None):
        return getattr(self, key, default)


@dataclass
class SignMsg:
    type: str = "logs"
    uuid: str = ""
    text: str = ""

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    # 应该在结束状态
    def is_stop(self):
        return self.type in ['end', 'stop', 'succeed', 'error']

    def is_error(self):
        return self.type == 'error'


@dataclass
class SrtItem:
    text: str = ""
    start_time: Union[int, float] = 0
    end_time: Union[int, float] = 0
    startraw: str = ''
    endraw: str = ''
    line: Optional[int] = 1
    time: Optional[str] = ""
    spk: Optional[str] = ""  # 说话人id
    filename: Optional[str] = ""  # 对应音频片段

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def items(self):
        _names = ("line", "time", "start_time", "end_time", "startraw", "endraw", "text", "spk", "filename")
        for k in _names:
            yield k, getattr(self, k)

    def __iter__(self):
        _names = ("line", "time", "start_time", "end_time", "startraw", "endraw", "text", "spk", "filename")
        return iter(_names)


# 视频翻译流程使用全部属性
@dataclass
class TaskCfgBase:
    # 通用区域
    uuid: str = None  # 默认唯一任务id

    name: Union[os.PathLike, str] = None  # 规范化处理的原始文件绝对路径 D:/XXX/1.MP4
    dirname: Union[os.PathLike, str] = None  # 原始文件所在目录 D:/XXX
    noextname: str = None  # 去掉扩展名的原始视频名
    basename: str = None  # noextname + ext 名 1.mp4
    ext: str = None  # 扩展名 mp4

    target_dir: str = None  # 输出文件夹，目标视频输出文件夹

    cache_folder: str = None  # 当前文件的临时文件夹,用于存放临时过程文件

    is_cuda: bool = False  # 是否使用cuda加速

    source_language: str = ""  # 原始语言名称或代码
    source_language_code: str = ""  # 原始语言代码
    source_sub: Union[os.PathLike, str] = None  # 原始字幕文件绝对路径
    source_wav: Union[os.PathLike, str] = None  # 原始语言音频，存在于临时文件夹下
    source_wav_output: Union[os.PathLike, str] = None  # 原始语言音频输出，存在于目标文件夹下

    target_language: str = ""  # 目标语言名称或代码
    target_language_code: str = ""  # 目标语言代码
    target_sub: Union[os.PathLike, str] = None  # 目标字幕文件绝对路径
    target_wav: Union[os.PathLike, str] = None  # 目标语言音频，存在于临时文件夹下
    target_wav_output: Union[os.PathLike, str] = None  # 目标语言音频输出，存在于目标文件夹下


# 语音识别
@dataclass
class TaskCfgSTT(TaskCfgBase):
    ####### 语音识别相关
    detect_language: str = None  # 字幕检测语言代码
    recogn_type: int = None  # 语音识别渠道
    model_name: str = None  # 模型名字
    shibie_audio: Union[os.PathLike, str] = None  # 转为 pcm_s16le  16k 作为语音识别的音频文件
    remove_noise: bool = False  # 是否移除噪声
    enable_diariz: bool = False  # 是否进行说话人识别
    nums_diariz: int = 0  # 是否进行说话人识别
    rephrase: bool = False  # 0 默认断句不处理 1=LLM重新断句
    fix_punc: int = 0  # 0=默认，1=恢复标点符号，2=移除所有标点

    def __repr__(self):
        from videotrans.recognition import ALLOW_CHANGE_MODEL
        from videotrans.util.tools import get_recogn_type
        from videotrans.configure.config import tr, app_cfg
        _msg = [f'[TaskCfgSTT]', tr("task_summary_file", self.name, self.target_dir, self.cache_folder),
                _cuda_status(self.is_cuda), tr("noise_reduction_status", isTrue[self.remove_noise])]
        if self.enable_diariz:
            _msg.append(tr("speaker_diarization_enabled", _speaker_limit(self.nums_diariz)))
        if self.fix_punc > 0:
            _msg.append(tr("punctuation_restored" if self.fix_punc == 1 else "punctuation_removed"))

        _msg.append(
            f"{tr('Speech Recognit')}:{get_recogn_type(self.recogn_type)}, {self.model_name if self.recogn_type in ALLOW_CHANGE_MODEL else ''}  {tr('segmentation')}:{_duanjus[self.rephrase]}")
        _msg.append(tr("source_language_auto") if self.detect_language == 'auto' else
                    f"{tr('source_language')}: {self.detect_language}")
        if app_cfg.proxy:
            _msg.append(tr("proxy_address", app_cfg.proxy))
        return "\n".join(_msg)


# 配音
@dataclass
class TaskCfgTTS(TaskCfgBase):
    ######## 配音相关
    tts_type: int = None  # 语音合成渠道
    volume: str = "+0%"  # 音量
    pitch: str = "+0Hz"  # 音调
    voice_rate: str = "+0%"  # 语速
    voice_role: str = None  # 配音角色
    voice_autorate: bool = False  # 是否音频自动加速
    video_autorate: bool = False  # 是否视频自动慢速
    remove_silent_mid: bool = False  # 是否移除字幕间的空隙
    align_sub_audio: bool = True  # 是否强制对齐字幕和声音

    def __repr__(self):
        _msg = []
        from videotrans.util.tools import get_tts_type
        from videotrans.configure.config import tr, app_cfg

        _msg.append(f'[TaskCfgTTS]')
        _msg.append(tr("task_summary_file", self.name, self.target_dir, self.cache_folder))
        _msg.append(_cuda_status(self.is_cuda))
        _msg.append(
            f"{tr('Dubbing channel')}:{get_tts_type(self.tts_type)}, {tr('voice_role')}:{self.voice_role}, {tr('dubbing_language')}:{self.target_language_code}")
        _msg.append(f'{tr("volume")}:{self.volume}, {tr("speech_rate")}:{self.voice_rate}, {tr("audio_speedup_status", isTrue[self.voice_autorate])}')

        if not self.voice_autorate and not self.video_autorate:
            _msg.append(f'{tr("remove_silence_status", isTrue[self.remove_silent_mid])}, {tr("force_align_status", isTrue[self.align_sub_audio])}')

        if app_cfg.proxy:
            _msg.append(tr("proxy_address", app_cfg.proxy))
        return "\n".join(_msg)


# 字幕翻译
@dataclass
class TaskCfgSTS(TaskCfgBase):
    ######## 字幕翻译相关
    translate_type: int = None  # 字幕翻译渠道

    def __repr__(self):
        _msg = []
        from videotrans.util.tools import get_tanslate_type
        from videotrans.configure.config import tr, settings, app_cfg
        _msg.append(f'[TaskCfgSTS]')
        _msg.append(tr("task_summary_file", self.name, self.target_dir, ""))
        _msg.append(
            f"{tr('Translate channel')}:{get_tanslate_type(self.translate_type)},{tr('source_language')}:{self.source_language_code},{tr('target_language')}:{self.target_language_code}, {isTrue[settings['aisendsrt']]} {tr('Send SRT')}")
        if app_cfg.proxy:
            _msg.append(tr("proxy_address", app_cfg.proxy))
        return "\n".join(_msg)


# 视频翻译所有
@dataclass
class TaskCfgVTT(TaskCfgSTT, TaskCfgTTS, TaskCfgSTS):
    ############## 视频翻译特有
    subtitle_language: str = None  # 软字幕嵌入语言代码，3位
    app_mode: str = "biaozhun"  # 工作模式 biaohzun tiqu
    targetdir_mp4: Union[os.PathLike, str] = None  # 最终输出合成后的mp4
    novoice_mp4: Union[os.PathLike, str] = None  # 从原始视频分离出的无声视频
    is_separate: bool = False  # 是否进行人声、背景音分离
    embed_bgm: bool = True  # 是否需要重新嵌入背景音
    instrument: Union[os.PathLike, str] = None  # 分离出的背景音频
    vocal: Union[os.PathLike, str] = None  # 分离出的人声音频
    clear_cache: bool = False  # 是否清理已存在的文件
    background_music: Union[os.PathLike, str] = None  # 手动添加的背景音频，整理后的完整路径
    subtitle_type: int = 0  # 软硬字幕嵌入类型 0=不嵌入，1=硬字幕，2=软字幕，3=双硬，4=双软
    only_out_mp4: bool = False  # 是否仅仅输出mp4,仅视频翻译使用
    recogn2pass: bool = False  # 对配音音频再次识别
    output_srt: int = 0  # 转录并翻译 模式输出字幕类似，0=单字幕，1=目标语言在线双字幕，2=目标语言在上双字幕
    copysrt_rawvideo: bool = False  # 是否将生成的字幕复制到视频目录下
    loop_backaudio: int = 0  # 循环背景音 或 延长拉伸背景音
    backaudio_volume: float = 0.8  # 背景音量
    batch: bool = False  # True=批量翻译模式, False=单视频翻译模式
    batch_size: int = 0  # batch=True时： 0批量并发模式不限制数量，>0 每批n个

    def __repr__(self):
        _msg = []
        from videotrans.recognition import ALLOW_CHANGE_MODEL
        from videotrans.util.tools import get_recogn_type, get_tanslate_type, get_tts_type
        from videotrans.configure.config import tr, settings, app_cfg

        from videotrans.task.subtitle_output import SUBTITLE_TYPE_KEYS
        _subtitles = [tr(key) for key in SUBTITLE_TYPE_KEYS]

        if self.app_mode == "tiqu":
            _msg.append(tr("work_mode_transcribe_translate"))
        else:
            mode = tr("batch_mode" if self.batch else "single_video_mode")
            batch_info = f" {tr('batch_size', self.batch_size)}" if self.batch and self.batch_size > 0 else ""
            _msg.append(tr("work_mode_translate_video", mode, batch_info))

        _msg.append(tr("task_summary_file", self.name, self.target_dir, self.cache_folder))

        _msg.append(tr("clear_cache_status", isTrue[self.clear_cache]))
        _msg.append(_cuda_status(self.is_cuda))
        _msg.append(tr("noise_reduction_status", isTrue[self.remove_noise]))
        if self.enable_diariz:
            _msg.append(tr("speaker_diarization_enabled", _speaker_limit(self.nums_diariz)))
        if self.fix_punc > 0:
            _msg.append(tr("punctuation_restored" if self.fix_punc == 1 else "punctuation_removed"))

        _msg.append(
            f"{tr('Speech Recognit')}:{get_recogn_type(self.recogn_type)}, {self.model_name if self.recogn_type in ALLOW_CHANGE_MODEL else ''}, {tr('source_language')}: {self.source_language}, {tr('segmentation')}:{_duanjus[self.rephrase]}")

        if self.target_language in [None, 'No', '-'] or self.source_language == self.target_language:
            _msg.append(tr("source_target_same" if self.source_language == self.target_language else "target_language_not_selected"))
        else:
            _msg.append(
                f"{tr('Translate channel')}:{get_tanslate_type(self.translate_type)},{tr('source_language')}:{self.source_language},{tr('target_language')}:{self.target_language}, {isTrue[settings['aisendsrt']]} {tr('Send SRT')}")

        if self.app_mode == 'tiqu':
            if self.copysrt_rawvideo:
                _msg.append(tr("copy_subs_to_video_dir"))
            _msg.append(f"{tr('Subtitle format:')}: {_outs[self.output_srt]}")
        else:

            if self.voice_role in [None, 'No']:
                _msg.append(tr("dubbing_role_not_selected"))
            else:
                _msg.append(
                    f"{tr('Dubbing channel')}:{get_tts_type(self.tts_type)}, {tr('voice_role')}:{self.voice_role}, {tr('dubbing_language')}:{self.target_language}, {tr('secondary_recognition_status', isTrue[self.recogn2pass])}")
                if self.recogn2pass and self.subtitle_type > 2:
                    _msg.append(tr("secondary_recognition_warning"))
                _msg.append(
                    f'{tr("volume")}:{self.volume}, {tr("speech_rate")}:{self.voice_rate}, {tr("audio_speedup_status", isTrue[self.voice_autorate])}, {tr("video_slowdown_status", isTrue[self.video_autorate])}')

                if not self.voice_autorate and not self.video_autorate:
                    _msg.append(f'{tr("remove_silence_status", isTrue[self.remove_silent_mid])}, {tr("force_align_status", isTrue[self.align_sub_audio])}')
            _msg.append(
                f'{tr("subtitle_type_label")}: {_subtitles[self.subtitle_type]} {_outs[self.output_srt] if self.subtitle_type > 2 else ""}')

            _vocal_exists = self.vocal and Path(self.vocal).exists()
            _instr_exists = self.instrument and Path(self.instrument).exists()
            if self.is_separate or self.background_music or _vocal_exists or _instr_exists:

                _str = tr("separate_vocals_bgm_status", isTrue[self.is_separate])
                if self.embed_bgm:
                    _str += f', {tr("reembed_bgm", self.backaudio_volume, _loops[self.loop_backaudio])}'

                if self.background_music:
                    _str += f', {tr("manual_bgm_added", self.background_music)}'
                if _vocal_exists:
                    _str += f', {tr("vocal_file_exists")}'
                if _instr_exists:
                    _str += f', {tr("instrument_file_exists")}'
                _msg.append(_str)
            if self.only_out_mp4:
                _msg.append(tr("output_mp4_only"))
        if app_cfg.proxy:
            _msg.append(tr("proxy_address", app_cfg.proxy))
        return "\n".join(_msg)
