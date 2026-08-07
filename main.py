import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# 1. Khởi tạo MCP Server
mcp = FastMCP("KiotViet-MCP")

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
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception as e:
        print(f"Lỗi kết nối KiotViet: {e}")
    return None

@mcp.tool()
def tra_cuu_ton_kho(ten_hoac_ma_san_pham: str) -> str:
    """Tra cứu tồn kho và giá bán sản phẩm trên KiotViet theo tên hoặc mã sản phẩm."""
    token = get_access_token()
    if not token:
        return "Lỗi: Không lấy được token xác thực KiotViet."

    headers = {"Retailer": RETAILER, "Authorization": f"Bearer {token}"}
    url = f"https://public.kiotviet.vn/products?kw={ten_hoac_ma_san_pham}&pageSize=5"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Lỗi gọi KiotViet API (Mã: {res.status_code})"
        
        data = res.json().get("data", [])
        if not data:
            return f"Không tìm thấy sản phẩm '{ten_hoac_ma_san_pham}'."

        ket_qua = []
        for item in data:
            ten = item.get("fullName") or item.get("name")
            ma = item.get("code")
            gia = item.get("basePrice", 0)
            ton = item.get("onHand", 0)
            ket_qua.append(f"• [{ma}] {ten} | Tồn: {ton} | Giá: {gia:,.0f} VNĐ")
        return "\n".join(ket_qua)
    except Exception as e:
        return f"Lỗi xử lý: {e}"

@mcp.tool()
def kiem_tra_cong_no_khach_hang(ten_hoac_sdt: str) -> str:
    """Tra cứu dư nợ công nợ khách hàng hoặc đại lý trên KiotViet."""
    token = get_access_token()
    if not token:
        return "Lỗi xác thực KiotViet."

    headers = {"Retailer": RETAILER, "Authorization": f"Bearer {token}"}
    url = f"https://public.kiotviet.vn/customers?searchText={ten_hoac_sdt}&pageSize=5"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Lỗi truy vấn (Mã: {res.status_code})"

        data = res.json().get("data", [])
        if not data:
            return f"Không tìm thấy khách hàng '{ten_hoac_sdt}'."

        ket_qua = []
        for c in data:
            ten = c.get("name")
            ma = c.get("code")
            sdt = c.get("contactNumber", "N/A")
            no = c.get("debt", 0)
            ket_qua.append(f"• [{ma}] {ten} (SĐT: {sdt}) | Công nợ: {no:,.0f} VNĐ")
        return "\n".join(ket_qua)
    except Exception as e:
        return f"Lỗi xử lý: {e}"

# 2. Tạo ứng dụng FastAPI chính
app = FastAPI(title="KiotViet MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Bộ lọc phản hồi 200 OK cho các lượt kiểm tra URL từ Gemini
@app.middleware("http")
async def handle_sse_probe_and_headers(request: Request, call_next):
    if request.url.path == "/sse" and request.method in ["GET", "HEAD"]:
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" not in accept_header:
            return JSONResponse(
                content={"status": "ok", "service": "KiotViet MCP Server", "transport": "sse"},
                status_code=200
            )
    return await call_next(request)

# 4. Tích hợp MCP SSE vào ứng dụng
mcp_sse_app = mcp.sse_app()
app.mount("/", mcp_sse_app)
