# -*- coding: utf-8 -*-
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from videotrans.configure.config import ROOT_DIR, app_cfg, settings, logger
from videotrans.configure import config


def check_hw_on_start(force=False):
    get_video_codec(264,force)
    get_video_codec(265,force)


def get_video_codec(compat=None,force=False) -> str:
    import torch
    _codec_cache = app_cfg.codec_cache
    try:
        if not _codec_cache and Path(f'{ROOT_DIR}/videotrans/codec.json').exists():
            _codec_cache = json.loads(Path(f'{ROOT_DIR}/videotrans/codec.json').read_text(encoding='utf-8-sig'))
    except Exception as e:
        logger.error(f'parse codec.json error:{e}')

    plat = platform.system()
    if compat and compat in [264, 265]:
        video_codec_pref = compat
    else:
        try:
            video_codec_pref = int(settings.get('video_codec', 264))
        except (ValueError, TypeError):
            logger.warning("'video_codec' in configuration is invalid. Will default to H.264 (264).")
            video_codec_pref = 264

    cache_key = f'{plat}-{video_codec_pref}'
    if not force and cache_key in _codec_cache:
        logger.debug(f"Return cached codec {cache_key}: {_codec_cache[cache_key]}")
        return _codec_cache[cache_key]

    h_prefix, default_codec = ('hevc', 'libx265') if video_codec_pref == 265 else ('h264', 'libx264')
    if video_codec_pref not in [264, 265]:
        logger.warning(f"unexpected \'video_codec\' value \'{video_codec_pref}\'. Will treat as H.264.")

    ENCODER_PRIORITY = {
        'Darwin': ['videotoolbox'],
        'Windows': ['nvenc', 'qsv', 'amf'],
        'Linux': ['nvenc', 'vaapi', 'qsv']
    }

    try:
        test_input_file = Path(ROOT_DIR) / "videotrans/styles/no-remove.mp4"
        temp_dir = Path(config.TEMP_DIR)
    except Exception as e:
        logger.warning(f"Error preparing hardware encoder for testing: {e}. Software encoding will be used. {default_codec}.")
        _codec_cache[cache_key] = default_codec
        return default_codec

    def test_encoder_internal(encoder_to_test: str, timeout: int = 20) -> bool:
        timestamp = int(time.time() * 1000)
        output_file = temp_dir / f"test_{encoder_to_test}_{timestamp}.mp4"
        command = [
            "ffmpeg", "-y", "-hide_banner",
            "-t", "1", "-i", str(test_input_file),
            "-c:v", encoder_to_test, "-f", "mp4", str(output_file)
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        logger.debug(f"Testing if encoder is available: {encoder_to_test}...")
        success = False
        try:

            subprocess.run(
                command, check=True, capture_output=True, text=True,
                encoding='utf-8', errors='ignore', creationflags=creationflags, timeout=timeout
            )
            logger.debug(f"hardware encoder \'{encoder_to_test}\' Available.\'")
            success = True
        except FileNotFoundError:
            logger.error("'ffmpeg' command not found in PATH. Encoder test failed.")
            raise
        except subprocess.CalledProcessError:
            logger.warning(f"hardware encoder \'{encoder_to_test}\' Unavailable\'")
            raise
        except PermissionError:
            logger.warning(f"Hardware encoder test failed: write to {output_file} was denied with permissions. {command=}")
            raise
        except subprocess.TimeoutExpired:
            logger.warning(f"hardware encoder \'{encoder_to_test}\' Test timed out after {timeout} seconds.{command=}")
            raise
        except Exception as e:
            logger.warning(f"Test hardware encoder {encoder_to_test} Unexpected error occurred: {e} {command=}")
            raise
        finally:
            try:
                if output_file.exists():
                    output_file.unlink(missing_ok=True)
            except OSError:
                pass
            return success

    selected_codec = default_codec

    encoders_to_test = ENCODER_PRIORITY.get(plat, [])
    if not encoders_to_test:
        logger.debug(f"Unsupported platform: {plat}. Software encoder will be used. {default_codec}.")
    else:
        logger.debug(f"Platform: {plat}. Best priority codec for is being detected as \'{h_prefix}\' encoder: {encoders_to_test}")
        try:
            for encoder_suffix in encoders_to_test:
                if encoder_suffix == 'nvenc':
                    try:
                        if not torch.cuda.is_available():
                            logger.debug("CUDA is not available, skipping nvenc test.")
                            continue
                    except ImportError:
                        logger.error("torch module could not be found, direct nvenc test will be attempted.")

                full_encoder_name = f"{h_prefix}_{encoder_suffix}"
                if test_encoder_internal(full_encoder_name):
                    selected_codec = full_encoder_name
                    logger.debug(f"Selected hardware encoder: {selected_codec}")
                    break
            else:
                logger.debug(f"All hardware accelerators failed the test. Software encoder: {selected_codec}")

            _codec_cache[cache_key] = selected_codec
            Path(f"{ROOT_DIR}/videotrans/codec.json").write_text(json.dumps(_codec_cache))
        except Exception as e:
            logger.exception(f"An unexpected error occurred during encoder testing. Using software encoder: {e}", exc_info=True)
            selected_codec = default_codec

    _codec_cache[cache_key] = selected_codec

    logger.debug(f"Final selected encoder: {selected_codec}")
    return selected_codec
