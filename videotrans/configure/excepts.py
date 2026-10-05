import re,sys
import aiohttp
import requests
from requests.exceptions import TooManyRedirects, MissingSchema, InvalidSchema, InvalidURL, ProxyError, SSLError, \
    Timeout, ConnectionError as ReqConnectionError, RetryError, HTTPError
from tenacity import RetryError as TenRetryError
import httpx
from videotrans.configure.config import defaulelang


# 内部已整理好错误提示消息的异常，将ex=None,message='{错误消息}'
class VideoTransError(Exception):
    def __init__(self, message=''):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return str(self.message)


class TranslateSrtError(VideoTransError):
    pass


class DubbingSrtError(VideoTransError):
    pass


class SpeechToTextError(VideoTransError):
    pass


class LLMSegmentError(VideoTransError):
    pass

class FFmpegError(VideoTransError):
    pass

class DownloadModelsError(VideoTransError):
    pass


class SttTimeoutError(VideoTransError):
    pass




# 出现该类异常时，需要立即停止任务
class StopTask(VideoTransError):
    pass


class StopRetry(VideoTransError):
    pass


# 不可恢复，无需继续重试的异常
NO_RETRY_EXCEPT = (
    ConnectionError,

    TooManyRedirects,  # 重定向次数过多
    InvalidURL,  # URL 格式无效
    # 代理错误
    ProxyError,
    MissingSchema,
    InvalidSchema,
    SSLError,
    ReqConnectionError,

    httpx.ProxyError,
    httpx.ConnectError,
    httpx.InvalidURL,
    httpx.LocalProtocolError,
    httpx.ProtocolError,
    httpx.TooManyRedirects,
    httpx.UnsupportedProtocol,

    StopRetry,
    StopTask
)

"""检查错误信息中是否包含本地地址"""
def _is_local_address(url_or_message):
    if not url_or_message:
        return False

    text = str(url_or_message).lower()
    local_indicators = ['127.0.0.1', 'localhost', '0.0.0.0', '::1', '[::1]']

    return any(indicator in text for indicator in local_indicators)


"""尝试从错误信息中提取API地址"""


def _extract_api_url_from_error(error):
    error_str = str(error)

    # 查找URL模式
    url_patterns = [
        r'https?://[^\s\'"]+',
        r'www\.[^\s\'"]+\.[a-z]{2,}',
        r'[a-zA-Z0-9.-]+\.[a-z]{2,}',
    ]

    for pattern in url_patterns:
        matches = re.findall(pattern, error_str)
        if matches:
            return matches[0]

    return None


"""处理连接错误的详细信息"""


def _handle_connection_error_detail(error, lang):
    error_str = str(error).lower()

    # 检查是否为本地地址
    is_local = _is_local_address(error_str)
    api_url = _extract_api_url_from_error(error)

    base_message = ""

    if "dns" in error_str or "name or service not known" in error_str:
        base_message = (
            "Không phân giải được tên miền; không tìm thấy địa chỉ máy chủ" if lang == 'vi_VN'
            else "Domain name resolution failed, cannot find server address"
        )
    elif "ProxyError" in error_str:
        base_message = (
            "Cấu hình proxy sai hoặc proxy không khả dụng. Hãy kiểm tra proxy hoặc tắt proxy và xóa địa chỉ đã nhập." if lang == 'vi_VN'
            else "The proxy address is not available, please check"
        )

    elif "refused" in error_str or "10061" in error_str or "积极拒绝" in error_str:
        if is_local:
            base_message = (
                "Kết nối bị từ chối. Hãy đảm bảo dịch vụ cục bộ đã khởi động và đang chạy." if lang == 'vi_VN'
                else "Connection refused, please ensure the local service is started and running"
            )
        else:
            base_message = (
                "Kết nối bị từ chối; không thể kết nối tới dịch vụ đích." if lang == 'vi_VN'
                else "Connection refused"
            )
    elif "reset" in error_str:
        base_message = (
            "Kết nối bị đặt lại; mạng có thể không ổn định." if lang == 'vi_VN'
            else "Connection reset, network may be unstable"
        )
    elif "timeout" in error_str or "timed out" in error_str:
        base_message = (
            "Kết nối hết thời gian chờ. Hãy kiểm tra đường truyền mạng." if lang == 'vi_VN'
            else "Connection timeout, please check network stability"
        )
    elif "max retries exceeded" in error_str:
        if is_local:
            if "0.0.0.0" in error_str:
                base_message = (
                    "Địa chỉ API không thể là 0.0.0.0; hãy đổi thành 127.0.0.1." if lang == 'vi_VN'
                    else "The API address cannot be 0.0.0.0, please change it to 127.0.0.1"
                )
            else:
                base_message = (
                    "Kết nối vẫn thất bại sau nhiều lần thử. Hãy kiểm tra dịch vụ cục bộ đã khởi động." if lang == 'vi_VN'
                    else "Multiple connection retries failed, please ensure local service is properly started"
                )
        else:
            base_message = (
                "Kết nối vẫn thất bại sau nhiều lần thử; dịch vụ có thể tạm thời không khả dụng." if lang == 'vi_VN'
                else "Multiple connection retries failed, service may be temporarily unavailable"
            )

    else:
        base_message = (
            "Kết nối mạng thất bại." if lang == 'vi_VN'
            else "Network connection failed"
        )

    # 为中文用户添加额外提示
    if lang == 'vi_VN' and api_url and not is_local:
        if "api.msedgeservices.com" in api_url.lower():
            base_message += " Edge TTS có thể đang giới hạn yêu cầu; hãy đợi một lúc rồi thử lại."
            return base_message
        if "edge.microsoft.com" in api_url.lower():
            base_message += " Microsoft Translator có thể đang giới hạn yêu cầu; hãy đợi một lúc rồi thử lại."
            return base_message
        # 检查是否为国外知名API服务
        foreign_apis = ['openai', 'anthropic', 'claude', 'elevenlabs', 'deepgram', 'google', 'aws.amazon']
        if any(api in api_url.lower() for api in foreign_apis):
            base_message += " Một số dịch vụ có thể cần kết nối mạng phù hợp để truy cập."

    return base_message



def _nofoundfile(e,lang):
    filename=getattr(e, 'filename', '')
    if sys.platform=='win32' and filename and "/tmp/" not in filename and len(filename)>250:
        return f'Hãy kiểm tra tệp có tồn tại không. Nếu có, tên hoặc đường dẫn có thể quá dài; hãy dùng tên ngắn hơn và chuyển tệp lên thư mục gần gốc hơn:\n{filename}' if lang=='vi_VN' else f'The filename may be too long. Please rename it to a shorter name and move it to a shallow directory.:\n{filename}'
    return f"Không tìm thấy tệp: {filename}" if lang == 'vi_VN' else f"File not found: {filename}"

# 根据异常类型，返回整理后的可读性错误消息
def get_msg_from_except(ex:Exception)->str:
    if isinstance(ex, VideoTransError):
        return str(ex)

    lang = defaulelang
    if isinstance(ex, TenRetryError):
        try:
            ex = ex.last_attempt.exception()
        except AttributeError:
            pass
    from elevenlabs.core import ApiError as ApiError_11
    import httpcore
    from deepgram.clients.common.v1.errors import DeepgramApiError
    from openai import AuthenticationError, PermissionDeniedError, NotFoundError, BadRequestError, RateLimitError, \
    APIConnectionError, APIError, ContentFilterFinishReasonError, InternalServerError, LengthFinishReasonError
    # 异常处理映射
    exception_handlers = {
        # === 认证和权限问题 ===
        AuthenticationError: lambda e: (
            f"Khóa API không hợp lệ. Hãy kiểm tra lại khóa: {e.message}" if lang == 'vi_VN'
            else (e.body.get('message') if e.body else e.message)
        ),

        PermissionDeniedError: lambda e: (
            f"Khóa API không có quyền truy cập. Hãy kiểm tra quyền: {e.message}" if lang == 'vi_VN'
            else (e.body.get('message') if e.body else e.message)
        ),

        # === 频率限制 ===
        # === 资源不存在问题 ===
        # === 请求参数问题 ===
        # === 服务端问题 ===
        (RateLimitError,InternalServerError, NotFoundError, BadRequestError, APIConnectionError, APIError): lambda e: e.body.get('message') if hasattr(e, 'body') and e.body else e.message,

        LengthFinishReasonError: lambda e: f'Nội dung vượt giới hạn token. Hãy rút ngắn nội dung, tăng max_token hoặc giảm số dòng phụ đề mỗi lần gửi.\n{e}' if lang == 'vi_VN' else f'{e}',
        ContentFilterFinishReasonError: lambda
            e: f"Nội dung bị bộ lọc an toàn của AI từ chối: {e}" if lang == 'vi_VN' else f'Content triggers AI risk control and is filtered\n{e}',

        # === 配置和地址问题 ===
        (TooManyRedirects, MissingSchema, InvalidSchema, InvalidURL): lambda e: (
            f"Địa chỉ yêu cầu không hợp lệ. Hãy kiểm tra cấu hình: {e.message}" if lang == 'vi_VN'
            else f"Request URL format is incorrect, check configuration {e.message}"
        ),

        (ProxyError, aiohttp.client_exceptions.ClientProxyConnectionError): lambda e: (
            "Cấu hình proxy sai hoặc proxy không khả dụng. Hãy kiểm tra proxy hoặc tắt proxy và xóa địa chỉ đã nhập." if lang == 'vi_VN'
            else "Proxy configuration issue, check settings or disable proxy"
        ),
        SSLError: lambda e: (
            "Kết nối bảo mật thất bại. Hãy kiểm tra giờ hệ thống và mạng; nếu dùng proxy, hãy tắt rồi thử lại." if lang == 'vi_VN'
            else "Secure connection failed, check system time or network settings"
        ),

        (HTTPError, RetryError): lambda e: f'{e}',

        DeepgramApiError: lambda e: e.message if hasattr(e, 'message') else str(e),
        ApiError_11: lambda e: e.body.get('detail', {}).get('message', e.body) if hasattr(e, 'body') else str(e),
        # === 网络连接问题 ===
        (ReqConnectionError, ConnectionError, ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError,
         httpcore.ConnectTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadError, Timeout): lambda e: (
            _handle_connection_error_detail(e, lang)
        ),

        (RuntimeError, ValueError, requests.exceptions.RequestException): lambda e: f"{e}",

        FileNotFoundError: lambda e: (
            _nofoundfile(e,lang)
        ),

        PermissionError: lambda e: (
            f"{e}：{getattr(e, 'filename', '')}"
        ),

        FileExistsError: lambda e: (
            f"Tệp đã tồn tại: {getattr(e, 'filename', '')}" if lang == 'vi_VN'
            else f"File already exists: {getattr(e, 'filename', '')}"
        ),

        # === 操作系统错误 ===
        OSError: lambda e: (
            f"Lỗi hệ thống ({e.errno}): {e.strerror}" if lang == 'vi_VN'
            else f"System Error ({e.errno}): {e.strerror}"
        ),

        # === 数据处理错误 ===
        KeyError: lambda e: (
            f"Thiếu khóa bắt buộc khi xử lý dữ liệu: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        IndexError: lambda e: (
            f"Chỉ số vượt phạm vi danh sách hoặc chuỗi: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        LookupError: lambda e: (
            f"Không tìm thấy khóa hoặc chỉ số được yêu cầu: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        UnicodeDecodeError: lambda e: (
            f"Không giải mã được tệp hoặc dữ liệu; định dạng mã hóa không hợp lệ: {e.reason}" if lang == 'vi_VN'
            else f" {e.reason}"
        ),

        # === 程序内部错误 ===
        AttributeError: lambda e: (
            f"Lỗi nội bộ ứng dụng: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        NameError: lambda e: (
            f"Lỗi nội bộ ứng dụng: biến chưa được định nghĩa '{e.name}'" if lang == 'vi_VN' else f"{e}"
        ),

        TypeError: lambda e: (
            f"Lỗi nội bộ ứng dụng: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        RecursionError: lambda e: (
            f"Lỗi nội bộ ứng dụng: đệ quy quá sâu: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        ZeroDivisionError: lambda e: (
            f"Lỗi tính toán: chia cho 0: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        OverflowError: lambda e: (
            f"Lỗi tính toán: giá trị vượt quá giới hạn: {e}" if lang == 'vi_VN'
            else f"{e}"
        ),

        BrokenPipeError: lambda e: (
            "Kết nối đường ống bị hỏng; hãy kiểm tra mạng." if lang == 'vi_VN'
            else "Broken pipe error, check network connection"
        ),
    }

    # 遍历映射，查找匹配的处理器
    for exc_types, handler in exception_handlers.items():
        if isinstance(ex, exc_types):
            return handler(ex)

    # === 后备处理逻辑 ===
    error_str = str(ex)
    if any(keyword in error_str.lower() for keyword in [
        'connection', 'connect', 'refused', 'reset', 'timeout', 'retries',
        '连接', '拒绝', '重置', '超时', '重试', 'host', 'port', 'http', 'tcp', 'ProxyError'
    ]):
        return _handle_connection_error_detail(ex, lang)

    _msg = None
    if hasattr(ex, 'detail') and ex.detail:
        _msg = ex.detail
    elif hasattr(ex, 'body') and ex.body:
        _msg = ex.body
    elif hasattr(ex, 'error'):
        _msg = ex.error

    if _msg and isinstance(_msg, dict):
        if message := _msg.get('message'):
            return str(message)
        if error_info := _msg.get('error'):
            if isinstance(error_info, dict):
                return str(error_info.get('message', error_info))
            return str(error_info)
        return str(_msg)
    # 默认错误消息
    return ''
