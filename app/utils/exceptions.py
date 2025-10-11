# # app/utils/exceptions.py

# class AppException(Exception):
#     """الاستثناء العام لتطبيقك"""
#     def __init__(self, message="حدث خطأ غير متوقع", status_code=400):
#         self.message = message
#         self.status_code = status_code
#         super().__init__(message)


# class StorageError(AppException):
#     """خطأ عام في التخزين"""
#     def __init__(self, message="حدث خطأ أثناء الوصول إلى التخزين"):
#         super().__init__(message=message, status_code=500)


# class StorageConnectionError(StorageError):
#     """فشل الاتصال بمزود التخزين (مثل S3 أو Cloudinary)"""
#     def __init__(self, message="تعذر الاتصال بمزود التخزين"):
#         super().__init__(message=message)


# class VideoGenerationError(AppException):
#     """خطأ في توليد الفيديو من AI أو خدمة خارجية"""
#     def __init__(self, message="فشل توليد الفيديو"):
#         super().__init__(message=message, status_code=500)


# class ExternalServiceException(AppException):
#     """خطأ في الاتصال بخدمة خارجية (مثل AI أو تحليل الفيديو)"""
#     def __init__(self, message="فشل الاتصال بالخدمة الخارجية"):
#         super().__init__(message=message, status_code=502)


# class InvalidResponseException(AppException):
#     """استجابة غير صالحة من خدمة خارجية"""
#     def __init__(self, message="الاستجابة غير صالحة من الخدمة الخارجية"):
#         super().__init__(message=message, status_code=500)


# class WebSocketProcessingException(AppException):
#     """خطأ أثناء التعامل مع WebSocket"""
#     def __init__(self, message="حدث خطأ أثناء معالجة WebSocket"):
#         super().__init__(message=message, status_code=500)


# app/utils/exceptions.py


class AppException(Exception):
    """الاستثناء العام لتطبيقك"""

    def __init__(self, message="حدث خطأ غير متوقع", status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# -------------------- التخزين --------------------


class StorageError(AppException):
    """خطأ عام في التخزين"""

    def __init__(self, message="حدث خطأ أثناء الوصول إلى التخزين"):
        super().__init__(message=message, status_code=500)


class StorageConnectionError(StorageError):
    """فشل الاتصال بمزود التخزين (مثل S3 أو Cloudinary)"""

    def __init__(self, message="تعذر الاتصال بمزود التخزين"):
        super().__init__(message=message)


# -------------------- الفيديو والذكاء الاصطناعي --------------------


class VideoGenerationError(AppException):
    """فشل توليد الفيديو من الذكاء الاصطناعي"""

    def __init__(self, message="فشل توليد الفيديو"):
        super().__init__(message=message, status_code=500)


class AIModelError(AppException):
    """خطأ في استدعاء أو تنفيذ نموذج الذكاء الاصطناعي"""

    def __init__(self, message="حدث خطأ في نموذج الذكاء الاصطناعي"):
        super().__init__(message=message, status_code=500)


# -------------------- التخزين المؤقت / الكاش --------------------


class CacheError(AppException):
    """خطأ في التخزين المؤقت (مثل Redis أو الذاكرة)"""

    def __init__(self, message="حدث خطأ في الكاش"):
        super().__init__(message=message, status_code=500)


# -------------------- الخدمات الخارجية --------------------


class ExternalServiceException(AppException):
    """خطأ في الاتصال بخدمة خارجية (مثل تحليل الفيديو)"""

    def __init__(self, message="فشل الاتصال بالخدمة الخارجية"):
        super().__init__(message=message, status_code=502)


class InvalidResponseException(AppException):
    """استجابة غير صالحة من خدمة خارجية"""

    def __init__(self, message="الاستجابة غير صالحة من الخدمة الخارجية"):
        super().__init__(message=message, status_code=500)


# -------------------- WebSocket --------------------


class WebSocketProcessingException(AppException):
    """خطأ أثناء التعامل مع WebSocket"""

    def __init__(self, message="حدث خطأ أثناء معالجة WebSocket"):
        super().__init__(message=message, status_code=500)
