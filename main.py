import os
import requests
from mcp.server.fastmcp import FastMCP

# Khởi tạo MCP Server
mcp = FastMCP("KiotViet-Spark-Bridge")

# Cấu hình Host và Port tự động từ môi trường Render
mcp.settings.host = "0.0.0.0"
mcp.settings.port = int(os.getenv("PORT", 8000))

CLIENT_ID = os.getenv("KIOTVIET_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("KIOTVIET_CLIENT_SECRET", "")
RETAILER = os.getenv("KIOTVIET_RETAILER", "")

def get_access_token():
    url = "https://id.kiotviet.vn/connect/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scopes": "PublicApi.Access"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Lỗi kết nối token: {e}")
    return None

@mcp.tool()
def tra_cuu_ton_kho(ten_hoac_ma_san_pham: str) -> str:
    """Tra cứu tồn kho và giá bán sản phẩm theo tên hoặc mã hàng hóa trên KiotViet."""
    token = get_access_token()
    if not token:
        return "Lỗi: Không thể xác thực với KiotViet. Vui lòng kiểm tra API Key."

    headers = {
        "Retailer": RETAILER,
        "Authorization": f"Bearer {token}"
    }
    url = f"https://public.kiotviet.vn/products?kw={ten_hoac_ma_san_pham}&pageSize=5"
    
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        return f"Không thể lấy thông tin sản phẩm (Mã lỗi: {res.status_code})"

    data = res.json().get("data", [])
    if not data:
        return f"Không tìm thấy sản phẩm nào khớp với từ khóa: '{ten_hoac_ma_san_pham}'"

    ket_qua = []
    for item in data:
        ten = item.get("fullName") or item.get("name")
        ma = item.get("code")
        gia = item.get("basePrice", 0)
        ton = item.get("onHand", 0)
        ket_qua.append(f"• [{ma}] {ten} | Tồn kho: {ton} | Giá bán: {gia:,.0f} VNĐ")

    return "\n".join(ket_qua)

@mcp.tool()
def kiem_tra_cong_no_khach_hang(ten_hoac_sdt: str) -> str:
    """Tra cứu dư nợ và thông tin của khách hàng hoặc đại lý."""
    token = get_access_token()
    if not token:
        return "Lỗi xác thực KiotViet."

    headers = {
        "Retailer": RETAILER,
        "Authorization": f"Bearer {token}"
    }
    url = f"https://public.kiotviet.vn/customers?searchText={ten_hoac_sdt}&pageSize=5"
    
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code != 200:
        return f"Lỗi truy vấn dữ liệu khách hàng (Mã lỗi: {res.status_code})"

    data = res.json().get("data", [])
    if not data:
        return f"Không tìm thấy khách hàng nào với thông tin: '{ten_hoac_sdt}'"

    ket_qua = []
    for c in data:
        ten = c.get("name")
        ma = c.get("code")
        sdt = c.get("contactNumber", "Chưa có SĐT")
        no = c.get("debt", 0)
        ket_qua.append(f"• [{ma}] {ten} (SĐT: {sdt}) | Công nợ hiện tại: {no:,.0f} VNĐ")

    return "\n".join(ket_qua)

if __name__ == "__main__":
    mcp.run(transport="sse")
