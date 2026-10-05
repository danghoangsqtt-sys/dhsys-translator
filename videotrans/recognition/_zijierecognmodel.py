import json
import math
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List,  Union

import requests
from pydub import AudioSegment

from videotrans.configure.excepts import SpeechToTextError
from videotrans.configure.config import params, logger
from videotrans.recognition._base import BaseRecogn
from videotrans.task.taskcfg import SrtItem
from videotrans.util.help_ffmpeg import runffmpeg,get_audio_time
from videotrans.util._srt_parse import ms_to_time_string

_error = {
    "20000003": "Silent audio",

    "45000001": "Missing required fields in request parameters / Invalid field value",
    "45000002": "Empty audio",
    "45000151": "Incorrect audio format",

    "550XXXX": "Internal service error",
    "55000031": "Server Busy"
}

@dataclass
class ZijieRecogn(BaseRecogn):

    def _exec(self) -> Union[List[SrtItem], None]:
        if self._exit():  return
        audio_ms=get_audio_time(self.audio_file)
        mp3_tmp = f'{self.cache_folder}/recogn-{time.time()}.mp3'
        runffmpeg([
            "-y",
            "-i",
            Path(self.audio_file).as_posix(),
            "-ac",
            "1",
            "-ar",
            "16000",
            mp3_tmp
        ])
        mp3_list=[]
        # 大于两小时需分片
        if audio_ms<7200000:
            mp3_list.append({"offset":0,"filename":mp3_tmp})
        else:
            # 每1个小时为一个分片
            _chunk_ms=3600000
            _total=math.ceil(audio_ms/_chunk_ms)
            audio_data=AudioSegment.from_file(mp3_tmp,format="mp3")
            for i in range(_total):
                _chunk_mp3=f'{mp3_tmp}-{i}.mp3'
                _start_ms=i*_chunk_ms
                if i==_total-1:
                    audio_data[_start_ms:].export(_chunk_mp3,format="mp3")
                else:
                    audio_data[_start_ms:_start_ms+_chunk_ms].export(_chunk_mp3,format="mp3")
                mp3_list.append({"offset":_start_ms,"filename":_chunk_mp3})
            logger.debug(f'Volcengine fast ASR: input audio is longer than two hours ({audio_ms/1000}s), split into {_total} hourly clips\n{mp3_list=}')


        submit_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
        appid = params.get('zijierecognmodel_appid', '')
        token=params.get('zijierecognmodel_token', '')
        srt_list = []


        for i,obj in enumerate(mp3_list):
            task_id = str(uuid.uuid4())
            headers = {
                "X-Api-App-Key": appid,
                "X-Api-Access-Key":token,
                "X-Api-Resource-Id": "volc.bigasr.auc_turbo",
                "X-Api-Request-Id": task_id,
                "X-Api-Sequence": "-1"
            }
            request = {
                "user": {
                    "uid": appid
                },
                "audio": {
                    "data": self._audio_to_base64(obj['filename']),
                    "format":"mp3"
                },
                "request": {
                    "model_name": "bigmodel",
                    "model_version": "400",
                    "enable_itn": True,
                    "enable_punc": True,
                    "enable_ddc": True,
                    "show_utterances": True,
                    "enable_auto_lang":True,
                    # "vad_segment":True,
                    # "end_window_size":300,
                }
            }

            response = requests.post(submit_url, json=request, headers=headers)
            response.raise_for_status()
            code = response.headers.get('X-Api-Status-Code')
            if not code:
                raise SpeechToTextError(f"Unknown Error:{response.text=},{response.headers=}")
            if str(code) != "20000000":
                raise SpeechToTextError(_error.get(str(code), 'Unknown Error'))

            res = response.json()
            seg_list = res.get('result', {}).get('utterances')
            if not seg_list:
                raise SpeechToTextError(f'No recognition results in returned data:{response=}')


            srt_strings = ""

            for it in seg_list:
                if not it.get('text', '').strip():
                    continue
                start_time=obj['offset']+it['start_time']
                end_time=obj['offset']+it['end_time']
                startraw = ms_to_time_string(ms=start_time)
                endraw = ms_to_time_string(ms=end_time)
                tmp = SrtItem(
                    line=len(srt_list) + 1,
                    start_time=start_time,
                    end_time=end_time,
                    startraw=startraw,
                    endraw=endraw,
                    text=it['text'].strip()
                )
                srt_list.append(tmp)
                srt_strings += f"{tmp['line']}\n{startraw} --> {endraw}\n{tmp['text']}\n\n"

            self.signal(
                text=srt_strings,
                type='replace_subtitle'
            )
        return srt_list
