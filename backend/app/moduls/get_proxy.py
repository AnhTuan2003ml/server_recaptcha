import requests
import json
from typing import Tuple



def get_proxy_from_api(api_key: str) -> str:
	"""
	Lấy proxy từ API wwproxy.com với retry logic khi gặp rate limit
	Nếu rate limit < 10s thì thử lại /available, nếu > 10s thì thử /current
	Returns:
		str: proxy string hoặc empty string nếu lỗi
	"""
	try:
		# Thử gọi /available trước
		url = f"https://wwproxy.com/api/client/proxy/available?key={api_key}"
		response = requests.get(url, timeout=30)

		if response.status_code == 200:
			data = response.json()
			if 'data' in data and isinstance(data['data'], dict):
				proxy_data = data['data']
				proxy = proxy_data.get('proxy', '')
				if proxy:
					print(f"✅ [PROXY] Thành công lấy proxy từ /available")
					return proxy
				else:
					print(f"⚠️ [PROXY] API /available không trả về proxy")
			else:
				print(f"⚠️ [PROXY] API /available response không có 'data'")
		else:
			# Kiểm tra nếu là lỗi rate limit
			try:
				error_data = response.json()
				if (error_data.get('status') == 'BAD_REQUEST' and
					error_data.get('errorCode') == 1 and
					'Thời gian giữa hai lần lấy proxy tối thiểu' in error_data.get('message', '')):

					# Parse thời gian còn lại từ message
					message = error_data.get('message', '')
					import re
					time_match = re.search(r'[Vv]ui lòng chờ thêm (\d+)s\.?', message)
					if time_match:
						wait_seconds = int(time_match.group(1))
						print(f"⏰ [PROXY] Rate limit hit, cần chờ {wait_seconds}s")

						if wait_seconds <= 10:
							# Thời gian còn lại <= 10s: thử lại /available ngay
							print(f"🔄 [PROXY] Thời gian còn lại {wait_seconds}s <= 10s, thử lại /available ngay...")
							retry_response = requests.get(url, timeout=30)
							if retry_response.status_code == 200:
								retry_data = retry_response.json()
								if 'data' in retry_data and isinstance(retry_data['data'], dict):
									proxy_data = retry_data['data']
									proxy = proxy_data.get('proxy', '')
									if proxy:
										print(f"✅ [PROXY] Thành công lấy proxy từ /available")
										return proxy
									else:
										print(f"⚠️ [PROXY] API /available không trả về proxy")
								else:
									print(f"⚠️ [PROXY] API /available response không có 'data'")
							else:
								print(f"⚠️ [PROXY] API /available trả về status code {retry_response.status_code}")
						else:
							# Thời gian còn lại > 10s: thử /current ngay
							print(f"🔄 [PROXY] Thời gian còn lại {wait_seconds}s > 10s, thử /current ngay...")
							current_url = f"https://wwproxy.com/api/client/proxy/current?key={api_key}"
							current_response = requests.get(current_url, timeout=30)

							if current_response.status_code == 200:
								current_data = current_response.json()
								if 'data' in current_data and isinstance(current_data['data'], dict):
									proxy_data = current_data['data']
									proxy = proxy_data.get('proxy', '')
									if proxy:
										print(f"✅ [PROXY] Thành công lấy proxy từ /current")
										return proxy
									else:
										print(f"⚠️ [PROXY] API /current không trả về proxy")
								else:
									print(f"⚠️ [PROXY] API /current response không có 'data'")
							else:
								print(f"⚠️ [PROXY] API /current trả về status code {current_response.status_code}")
					else:
						print(f"⚠️ [PROXY] Không parse được thời gian từ message: {message}")
				else:
					# Kiểm tra nếu là lỗi "Không tìm thấy proxy phù hợp"
					if (error_data.get('status') == 'BAD_REQUEST' and
						error_data.get('errorCode') == 1 and
						'Không tìm thấy proxy phù hợp' in error_data.get('message', '')):
						print(f"🔄 [PROXY] Không tìm thấy proxy phù hợp, thử /current endpoint...")
						current_url = f"https://wwproxy.com/api/client/proxy/current?key={api_key}"
						current_response = requests.get(current_url, timeout=30)

						if current_response.status_code == 200:
							current_data = current_response.json()
							if 'data' in current_data and isinstance(current_data['data'], dict):
								proxy_data = current_data['data']
								proxy = proxy_data.get('proxy', '')
								if proxy:
									print(f"✅ [PROXY] Thành công lấy proxy từ /current")
									return proxy
								else:
									print(f"⚠️ [PROXY] API /current không trả về proxy")
							else:
								print(f"⚠️ [PROXY] API /current response không có 'data'")
						else:
							print(f"⚠️ [PROXY] API /current trả về status code {current_response.status_code}")

					print(f"⚠️ [PROXY] API /available trả về status code {response.status_code}")
					print(f"   Response: {response.text[:200]}")
			except:
				print(f"⚠️ [PROXY] API /available trả về status code {response.status_code}")
				print(f"   Response: {response.text[:200]}")

		return ""
	except Exception as e:
		print(f"❌ [PROXY] Lỗi khi gọi API lấy proxy cho key {api_key[:20]}...: {e}")
		return ""



# Test
if __name__ == "__main__":
	api_key = "UK-5dc4d912-3d23-4ccd-b933-cbe3b1b15030"
	proxy = get_proxy_from_api(api_key)
	print(f"🌐 Proxy: {proxy}")
