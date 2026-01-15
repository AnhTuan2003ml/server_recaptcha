"""
Email Service - Gửi email OTP qua Gmail SMTP
"""
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    """Service để gửi email OTP"""
    
    # Cấu hình SMTP Gmail
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    def __init__(self):
        """Khởi tạo EmailService và load config từ file"""
        self.sender_email = None
        self.sender_password = None
        self._load_config()
    
    def _load_config(self):
        """Load cấu hình email từ file email_config.json"""
        try:
            # Đường dẫn đến file config: từ app/services/ -> ../../config/email_config.json
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'config',
                'email_config.json'
            )
            config_path = os.path.abspath(config_path)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.sender_email = config.get('sender')
            self.sender_password = config.get('password')
            
            if not self.sender_email or not self.sender_password:
                print("[WARNING] Email config không đầy đủ!")
                
        except FileNotFoundError:
            print(f"[ERROR] Không tìm thấy file email_config.json tại: {config_path}")
        except json.JSONDecodeError:
            print("[ERROR] File email_config.json không hợp lệ!")
        except Exception as e:
            print(f"[ERROR] Lỗi khi load email config: {e}")
    
    def send_otp(self, recipient_email: str, otp_code: str, purpose: str = "đăng ký") -> bool:
        """
        Gửi email OTP đến người nhận
        
        Args:
            recipient_email: Email người nhận
            otp_code: Mã OTP (6 số)
            purpose: Mục đích gửi OTP ("đăng ký" hoặc "đăng nhập")
        
        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        if not self.sender_email or not self.sender_password:
            print("[ERROR] Email config chưa được thiết lập!")
            return False
        
        try:
            # Tạo message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Mã OTP {purpose.capitalize()} - Payment App"
            
            # Nội dung email
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2 style="color: #2c3e50; text-align: center;">Mã OTP {purpose.capitalize()}</h2>
                        <p>Xin chào,</p>
                        <p>Bạn đang thực hiện {purpose} tài khoản. Vui lòng sử dụng mã OTP sau đây:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="display: inline-block; background-color: #3498db; color: white; padding: 15px 30px; border-radius: 5px; font-size: 24px; font-weight: bold; letter-spacing: 5px;">
                                {otp_code}
                            </div>
                        </div>
                        <p><strong>Mã OTP này có hiệu lực trong 5 phút.</strong></p>
                        <p>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">
                            Đây là email tự động, vui lòng không trả lời email này.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Gửi email
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()  # Bật TLS
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Đã gửi email OTP đến {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"[ERROR] Xác thực email thất bại! Kiểm tra lại email và password trong email_config.json")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] Lỗi SMTP khi gửi email: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Lỗi khi gửi email đến {recipient_email}: {e}")
            return False
    
    def send_new_password(self, recipient_email: str, new_password: str) -> bool:
        """
        Gửi email chứa mật khẩu mới đến người nhận
        
        Args:
            recipient_email: Email người nhận
            new_password: Mật khẩu mới
        
        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        if not self.sender_email or not self.sender_password:
            print("[ERROR] Email config chưa được thiết lập!")
            return False
        
        try:
            # Tạo message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Mật Khẩu Mới - Payment App"
            
            # Nội dung email
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2 style="color: #2c3e50; text-align: center;">Mật Khẩu Mới</h2>
                        <p>Xin chào,</p>
                        <p>Bạn đã yêu cầu đặt lại mật khẩu. Dưới đây là mật khẩu mới của bạn:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="display: inline-block; background-color: #27ae60; color: white; padding: 15px 30px; border-radius: 5px; font-size: 18px; font-weight: bold; font-family: monospace;">
                                {new_password}
                            </div>
                        </div>
                        <p><strong>Vui lòng đăng nhập và đổi mật khẩu sau khi sử dụng.</strong></p>
                        <p style="color: #e74c3c;"><strong>⚠️ Lưu ý: Đây là email quan trọng, vui lòng không chia sẻ với ai!</strong></p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">
                            Đây là email tự động, vui lòng không trả lời email này.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Gửi email
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()  # Bật TLS
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Đã gửi email mật khẩu mới đến {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"[ERROR] Xác thực email thất bại! Kiểm tra lại email và password trong email_config.json")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] Lỗi SMTP khi gửi email: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Lỗi khi gửi email đến {recipient_email}: {e}")
            return False


# Singleton instance
_email_service_instance: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Lấy instance của EmailService (singleton pattern)"""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance
