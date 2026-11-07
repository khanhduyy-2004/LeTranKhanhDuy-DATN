# KDSeaFood – Website hải sản trực tuyến

Đồ án tốt nghiệp – Lê Trần Khánh Duy – 2210900020 – K22CNT3 – Trường Đại học Nguyễn Trãi
Công nghệ: **Python Flask** (MVC + Blueprint) · **MySQL** · HTML / CSS / JavaScript · Bootstrap 5 · Chart.js

## 1. Cài đặt

Yêu cầu: Python 3.13, MySQL 8.4 LTS (hoặc MariaDB qua XAMPP).

**Cách nhanh (Windows):** bấm đúp `setup_windows.bat` → nhập mật khẩu root MySQL → xong; sau đó bấm đúp `run_windows.bat`.
macOS / Linux: `bash setup_mac_linux.sh`.

**Cách thủ công:**

```bash
# 1) Tạo môi trường ảo & cài thư viện
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

# 2) Tạo cơ sở dữ liệu + dữ liệu mẫu
mysql -u root -p < database/kdseafood.sql      # hoặc mở file trong MySQL Workbench rồi chạy

# 3) Cấu hình kết nối
copy .env.example .env           # macOS/Linux: cp .env.example .env
#    → sửa DB_USER, DB_PASSWORD trong file .env

# 4) Chạy
python run.py                    # mở http://127.0.0.1:5000
```

Toàn bộ Bootstrap, Bootstrap Icons, Chart.js và font chữ đã được tải sẵn vào `app/static/vendor`, **chạy được không cần Internet**.

## 2. Tài khoản mẫu (mật khẩu đều là `123456`)

| Vai trò | Tên đăng nhập | Ghi chú |
|---|---|---|
| Quản trị viên | `admin` | Đăng nhập xong tự chuyển vào `/admin` |
| Khách hàng | `khach01`, `khach02` | Đã có đơn hàng, địa chỉ, yêu thích |
| Khách hàng bị khóa | `khach03` | Dùng để thử chức năng khóa tài khoản |

## 3. Chức năng

**Khách vãng lai:** xem sản phẩm theo danh mục; lọc theo khoảng giá, số sao, còn hàng; sắp xếp (mới nhất, giá, bán chạy, đánh giá); tìm kiếm có gợi ý tức thời; xem chi tiết; đăng ký.

**Khách hàng:** đăng nhập/đăng xuất; hồ sơ, ảnh đại diện, đổi mật khẩu; sổ nhiều địa chỉ; giỏ hàng (lưu theo tài khoản, bán lẻ 0,5 kg); đặt hàng (COD / chuyển khoản / VNPay sandbox mô phỏng); theo dõi đơn theo các bước + lịch sử trạng thái; hủy đơn khi “Chờ xác nhận”; yêu thích; đánh giá sản phẩm đã mua.

**Quản trị viên:** tổng quan doanh thu (hôm nay, tháng, biểu đồ 12 tháng, đơn theo trạng thái, top bán chạy, sắp hết hàng); quản lý danh mục; quản lý sản phẩm (nhiều ảnh, ảnh đại diện, ẩn/hiện, nổi bật, tồn kho); quản lý đơn hàng (lọc, cập nhật trạng thái có ghi lịch sử); quản lý khách hàng (khóa/mở khóa, đặt lại mật khẩu, xem lịch sử mua); duyệt đánh giá.

## 4. Quy tắc nghiệp vụ chính

- Đặt hàng chạy trong **một giao dịch**: khóa dòng sản phẩm (`SELECT … FOR UPDATE`) → kiểm tra tồn kho → tạo đơn + chi tiết (lưu tên, giá tại thời điểm mua) → trừ kho → ghi lịch sử → xóa giỏ.
- Trạng thái đơn chỉ đi tiến: Chờ xác nhận → Đã xác nhận → Đang chuẩn bị → Đang giao → Đã giao; được hủy khi chưa giao xong. Hủy đơn hoàn lại tồn kho (đơn đã thanh toán → “Đã hoàn tiền”).
- “Đã giao” mới được tính doanh thu và cộng số lượng đã bán; đơn COD chuyển “Đã thanh toán”.
- Phí giao hàng 30.000₫, miễn phí từ 1.000.000₫ (sửa trong `config.py`).
- Đánh giá chỉ dành cho khách đã nhận hàng, mỗi khách 1 lần/sản phẩm, hiển thị sau khi quản trị viên duyệt.
- Không xóa được danh mục đang có sản phẩm.
- Bảo mật: mật khẩu băm (Werkzeug PBKDF2), chống CSRF (Flask-WTF), truy vấn tham số hóa chống SQL Injection, Jinja2 tự escape chống XSS, khách chỉ xem/hủy đơn của chính mình.

## 5. Cấu trúc thư mục (MVC)

```
kdseafood/
├── run.py                  # điểm khởi chạy
├── config.py               # cấu hình (CSDL, phí ship, phân trang…)
├── requirements.txt
├── database/kdseafood.sql  # 13 bảng + 5 view + dữ liệu mẫu
└── app/
    ├── __init__.py         # Application Factory, đăng ký Blueprint
    ├── db.py               # kết nối PyMySQL, query/execute/transaction
    ├── utils.py            # phân quyền, slug tiếng Việt, định dạng tiền, upload ảnh
    ├── models/             # MODEL – truy vấn SQL theo từng nhóm bảng
    │   ├── product.py  category.py  cart.py  order.py  user.py  admin.py
    │   └── address.py  review.py  wishlist.py  banner.py  stats.py
    ├── controllers/        # CONTROLLER – Blueprint
    │   ├── main.py  auth.py  product.py  cart.py  order.py  account.py
    │   └── admin/  (dashboard, categories, products, orders, customers, reviews)
    ├── templates/          # VIEW – Jinja2
    └── static/             # css, js, img, vendor (Bootstrap…), uploads
```

## 6. Ảnh sản phẩm

Dữ liệu mẫu trỏ tới `/static/uploads/products/<slug>-1.jpg` và `-2.jpg`. Khi chưa có file, web tự hiển thị ảnh minh họa. Có thể chép ảnh thật vào đúng thư mục với đúng tên, hoặc tải ảnh lên trong trang **Quản trị → Sản phẩm → Sửa**.
