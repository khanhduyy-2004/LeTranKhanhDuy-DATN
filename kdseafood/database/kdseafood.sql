-- =====================================================================
--  CƠ SỞ DỮ LIỆU WEBSITE HẢI SẢN TRỰC TUYẾN KDSEAFOOD
--  Đồ án tốt nghiệp – Lê Trần Khánh Duy – 2210900020 – K22CNT3
--  Hệ quản trị: MySQL 8.0+ (tương thích MariaDB 10.6+)
--  Bổ sung theo mô hình bán hàng tham khảo: đánh giá có duyệt, yêu thích, lọc giá/đánh giá
--  Tài khoản mẫu: admin / 123456   –   khach01, khach02, khach03 / 123456
--  Mật khẩu băm bằng werkzeug.security.generate_password_hash (Flask)
-- =====================================================================
DROP DATABASE IF EXISTS kdseafood;
CREATE DATABASE kdseafood CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kdseafood;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- 1. QUẢN TRỊ VIÊN
-- ---------------------------------------------------------------------
CREATE TABLE admins (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL,
    phone           VARCHAR(15),
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    last_login_at   DATETIME,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_admins_username UNIQUE (username),
    CONSTRAINT uq_admins_email    UNIQUE (email)
) ENGINE=InnoDB COMMENT='Tài khoản quản trị viên';

-- ---------------------------------------------------------------------
-- 2. NGƯỜI DÙNG / KHÁCH HÀNG
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(15),
    avatar_url      VARCHAR(255),
    is_active       TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '0 = bị khóa',
    last_login_at   DATETIME,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email)
) ENGINE=InnoDB COMMENT='Khách hàng đã đăng ký';

-- ---------------------------------------------------------------------
-- 3. ĐỊA CHỈ NHẬN HÀNG (một khách hàng có nhiều địa chỉ)
-- ---------------------------------------------------------------------
CREATE TABLE addresses (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    receiver_name   VARCHAR(100) NOT NULL,
    phone           VARCHAR(15)  NOT NULL,
    address_line    VARCHAR(255) NOT NULL COMMENT 'Số nhà, tên đường',
    ward            VARCHAR(100),
    district        VARCHAR(100),
    province        VARCHAR(100) NOT NULL,
    is_default      TINYINT(1)   NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Sổ địa chỉ nhận hàng';

-- ---------------------------------------------------------------------
-- 4. DANH MỤC SẢN PHẨM
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(120) NOT NULL,
    description     TEXT,
    image_url       VARCHAR(255),
    sort_order      INT          NOT NULL DEFAULT 0,
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_categories_name UNIQUE (name),
    CONSTRAINT uq_categories_slug UNIQUE (slug)
) ENGINE=InnoDB COMMENT='Danh mục: cá, tôm, cua ghẹ, mực, ốc, đông lạnh...';

-- ---------------------------------------------------------------------
-- 5. SẢN PHẨM
-- ---------------------------------------------------------------------
CREATE TABLE products (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id     INT UNSIGNED  NOT NULL,
    name            VARCHAR(150)  NOT NULL,
    slug            VARCHAR(170)  NOT NULL,
    price           DECIMAL(12,0) NOT NULL COMMENT 'Giá bán (VNĐ) / 1 đơn vị tính',
    unit           VARCHAR(20)   NOT NULL DEFAULT 'kg' COMMENT 'kg, con, hộp, khay...',
    origin          VARCHAR(100)  COMMENT 'Xuất xứ',
    short_desc      VARCHAR(255),
    description     TEXT,
    stock_quantity  DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Số lượng tồn',
    sold_quantity   DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Số lượng đã bán (đơn đã giao)',
    is_active       TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '0 = ẩn',
    is_featured     TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '1 = nổi bật',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_products_slug UNIQUE (slug),
    CONSTRAINT ck_products_price CHECK (price >= 0),
    CONSTRAINT ck_products_stock CHECK (stock_quantity >= 0),
    -- RESTRICT: không cho xóa danh mục đang có sản phẩm
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_products_category (category_id, is_active),
    INDEX idx_products_name (name)
) ENGINE=InnoDB COMMENT='Sản phẩm hải sản';

CREATE TABLE product_images (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id      INT UNSIGNED NOT NULL,
    image_url       VARCHAR(255) NOT NULL,
    is_primary      TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '1 = ảnh đại diện',
    sort_order      INT          NOT NULL DEFAULT 0,
    CONSTRAINT fk_images_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_images_product (product_id, sort_order)
) ENGINE=InnoDB COMMENT='Hình ảnh sản phẩm';

-- ---------------------------------------------------------------------
-- 6. BANNER TRANG CHỦ
-- ---------------------------------------------------------------------
CREATE TABLE banners (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    image_url       VARCHAR(255) NOT NULL,
    link_url        VARCHAR(255),
    sort_order      INT          NOT NULL DEFAULT 0,
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Banner / slider trang chủ';

-- ---------------------------------------------------------------------
-- 7. GIỎ HÀNG
-- ---------------------------------------------------------------------
CREATE TABLE cart_items (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED  NOT NULL,
    product_id      INT UNSIGNED  NOT NULL,
    quantity        DECIMAL(10,2) NOT NULL,
    added_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_cart_user_product UNIQUE (user_id, product_id),
    CONSTRAINT ck_cart_quantity CHECK (quantity > 0),
    CONSTRAINT fk_cart_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Giỏ hàng của khách hàng';

-- ---------------------------------------------------------------------
-- 8. ĐƠN HÀNG
--   status: pending=Chờ xác nhận, confirmed=Đã xác nhận, preparing=Đang chuẩn bị,
--           shipping=Đang giao, delivered=Đã giao, cancelled=Đã hủy
--   Địa chỉ nhận hàng được lưu bản sao (snapshot) để không bị đổi khi khách sửa sổ địa chỉ
-- ---------------------------------------------------------------------
CREATE TABLE orders (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_code       VARCHAR(20)   NOT NULL COMMENT 'VD: KD2610300001',
    user_id          INT UNSIGNED  NOT NULL,
    receiver_name    VARCHAR(100)  NOT NULL,
    receiver_phone   VARCHAR(15)   NOT NULL,
    shipping_address VARCHAR(500)  NOT NULL,
    subtotal         DECIMAL(12,0) NOT NULL DEFAULT 0,
    shipping_fee     DECIMAL(12,0) NOT NULL DEFAULT 0,
    discount_amount  DECIMAL(12,0) NOT NULL DEFAULT 0,
    total_amount     DECIMAL(12,0) NOT NULL DEFAULT 0,
    payment_method   ENUM('cod','bank_transfer','vnpay_sandbox') NOT NULL DEFAULT 'cod',
    payment_status   ENUM('unpaid','paid','refunded')            NOT NULL DEFAULT 'unpaid',
    transaction_ref  VARCHAR(100)  COMMENT 'Mã giao dịch thanh toán (sandbox)',
    status           ENUM('pending','confirmed','preparing','shipping','delivered','cancelled')
                                   NOT NULL DEFAULT 'pending',
    note             VARCHAR(500)  COMMENT 'Ghi chú của khách hàng',
    cancel_reason    VARCHAR(255),
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    delivered_at     DATETIME,
    CONSTRAINT uq_orders_code UNIQUE (order_code),
    CONSTRAINT ck_orders_total CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_orders_user    (user_id, created_at),
    INDEX idx_orders_status  (status, created_at),
    INDEX idx_orders_created (created_at)
) ENGINE=InnoDB COMMENT='Đơn hàng';

CREATE TABLE order_items (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id        INT UNSIGNED  NOT NULL,
    product_id      INT UNSIGNED,
    product_name    VARCHAR(150)  NOT NULL COMMENT 'Lưu tên tại thời điểm đặt',
    unit            VARCHAR(20)   NOT NULL,
    unit_price      DECIMAL(12,0) NOT NULL COMMENT 'Giá tại thời điểm đặt',
    quantity        DECIMAL(10,2) NOT NULL,
    line_total      DECIMAL(14,0) AS (ROUND(unit_price * quantity, 0)) STORED,
    CONSTRAINT ck_items_quantity CHECK (quantity > 0),
    CONSTRAINT fk_items_order   FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_items_product (product_id)
) ENGINE=InnoDB COMMENT='Chi tiết đơn hàng';

-- ---------------------------------------------------------------------
-- 9. LỊCH SỬ TRẠNG THÁI ĐƠN HÀNG
--   Người xử lý: admin (changed_by_admin_id), khách hàng tự hủy (changed_by_user_id),
--   hoặc hệ thống khi tạo đơn (cả hai NULL)
-- ---------------------------------------------------------------------
CREATE TABLE order_status_history (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id            INT UNSIGNED NOT NULL,
    old_status          ENUM('pending','confirmed','preparing','shipping','delivered','cancelled'),
    new_status          ENUM('pending','confirmed','preparing','shipping','delivered','cancelled') NOT NULL,
    changed_by_admin_id INT UNSIGNED,
    changed_by_user_id  INT UNSIGNED,
    note                VARCHAR(255),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_order FOREIGN KEY (order_id)            REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_admin FOREIGN KEY (changed_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL,
    CONSTRAINT fk_history_user  FOREIGN KEY (changed_by_user_id)  REFERENCES users(id)  ON DELETE SET NULL,
    INDEX idx_history_order (order_id, created_at)
) ENGINE=InnoDB COMMENT='Lịch sử thay đổi trạng thái đơn hàng';
-- ---------------------------------------------------------------------
-- 10. ĐÁNH GIÁ SẢN PHẨM (chỉ khách đã mua & nhận hàng; quản trị viên duyệt trước khi hiển thị)
-- ---------------------------------------------------------------------
CREATE TABLE reviews (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id      INT UNSIGNED NOT NULL,
    user_id         INT UNSIGNED NOT NULL,
    rating          TINYINT UNSIGNED NOT NULL COMMENT '1 – 5 sao',
    title           VARCHAR(150),
    content         TEXT,
    status          ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_reviews_user_product UNIQUE (user_id, product_id),
    CONSTRAINT ck_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_reviews_product (product_id, status)
) ENGINE=InnoDB COMMENT='Đánh giá sản phẩm';

-- ---------------------------------------------------------------------
-- 11. SẢN PHẨM YÊU THÍCH
-- ---------------------------------------------------------------------
CREATE TABLE wishlists (
    user_id         INT UNSIGNED NOT NULL,
    product_id      INT UNSIGNED NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, product_id),
    CONSTRAINT fk_wishlists_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    CONSTRAINT fk_wishlists_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Danh sách yêu thích';


-- =====================================================================
-- DỮ LIỆU MẪU
-- =====================================================================

INSERT INTO admins (username, password_hash, full_name, email, phone) VALUES
    ('admin', 'pbkdf2:sha256:1000000$OrfXbkZQGbFuurww$c6136f6b6f090b4fc2ec1232f4fa2ed79ab46bb15bd812be7fba821784ed3a3f', 'Lê Trần Khánh Duy', 'admin@kdseafood.vn', '0779329341');

INSERT INTO users (username, email, password_hash, full_name, phone, is_active) VALUES
    ('khach01', 'khach01@gmail.com', 'pbkdf2:sha256:1000000$OrfXbkZQGbFuurww$c6136f6b6f090b4fc2ec1232f4fa2ed79ab46bb15bd812be7fba821784ed3a3f', 'Nguyễn Văn An', '0912345678', 1),
    ('khach02', 'khach02@gmail.com', 'pbkdf2:sha256:1000000$OrfXbkZQGbFuurww$c6136f6b6f090b4fc2ec1232f4fa2ed79ab46bb15bd812be7fba821784ed3a3f', 'Trần Thị Bình', '0987654321', 1),
    ('khach03', 'khach03@gmail.com', 'pbkdf2:sha256:1000000$OrfXbkZQGbFuurww$c6136f6b6f090b4fc2ec1232f4fa2ed79ab46bb15bd812be7fba821784ed3a3f', 'Lê Minh Cường', '0905111222', 0);

INSERT INTO addresses (user_id, receiver_name, phone, address_line, ward, district, province, is_default) VALUES
    (1, 'Nguyễn Văn An', '0912345678', '12 Nguyễn Trãi', 'Phường Thượng Đình', 'Quận Thanh Xuân', 'Hà Nội', 1),
    (1, 'Nguyễn Văn An (cơ quan)', '0912345678', '36 Lê Văn Lương', 'Phường Nhân Chính', 'Quận Thanh Xuân', 'Hà Nội', 0),
    (2, 'Trần Thị Bình', '0987654321', '88 Cầu Giấy', 'Phường Quan Hoa', 'Quận Cầu Giấy', 'Hà Nội', 1),
    (3, 'Lê Minh Cường', '0905111222', '5 Trần Phú', 'Phường Hải Châu 1', 'Quận Hải Châu', 'Đà Nẵng', 1);

INSERT INTO categories (name, slug, description, image_url, sort_order) VALUES
    ('Cá biển', 'ca-bien', 'Cá hồi, cá bớp, cá thu, cá mú tươi đánh bắt trong ngày.', '/static/uploads/categories/ca-bien.jpg', 1),
    ('Tôm', 'tom', 'Tôm hùm, tôm sú, tôm càng xanh tươi sống.', '/static/uploads/categories/tom.jpg', 2),
    ('Cua & Ghẹ', 'cua-ghe', 'Cua gạch, cua thịt Cà Mau, ghẹ xanh, ghẹ đỏ.', '/static/uploads/categories/cua-ghe.jpg', 3),
    ('Mực', 'muc', 'Mực ống, mực lá, mực trứng tươi và một nắng.', '/static/uploads/categories/muc.jpg', 4),
    ('Ốc & Nghêu sò', 'oc-ngheu-so', 'Ốc hương, ngao hai cồi, sò điệp, hàu sữa.', '/static/uploads/categories/oc-ngheu-so.jpg', 5),
    ('Hải sản đông lạnh', 'hai-san-dong-lanh', 'Hải sản cấp đông, sơ chế sẵn, tiện bảo quản.', '/static/uploads/categories/hai-san-dong-lanh.jpg', 6);

INSERT INTO products (category_id, name, slug, price, unit, origin, short_desc, description, stock_quantity, sold_quantity, is_featured) VALUES
    (2, 'Tôm hùm bông', 'tom-hum-bong', 1500000, 'kg', 'Nha Trang, Khánh Hòa', 'Tôm hùm bông tươi sống, size 600–800g/con, thịt chắc ngọt.', 'Tôm hùm bông tươi sống, size 600–800g/con, thịt chắc ngọt. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Nha Trang, Khánh Hòa. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 20.00, 2.50, 1),
    (2, 'Tôm sú cọp', 'tom-su-cop', 450000, 'kg', 'Quảng Nam', 'Tôm sú cọp size 20–25 con/kg, đánh bắt hàng ngày.', 'Tôm sú cọp size 20–25 con/kg, đánh bắt hàng ngày. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Quảng Nam. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 50.50, 3.50, 1),
    (2, 'Tôm càng xanh', 'tom-cang-xanh', 380000, 'kg', 'Cần Thơ', 'Tôm càng xanh sông size 8–10 con/kg.', 'Tôm càng xanh sông size 8–10 con/kg. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Cần Thơ. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 30.00, 0.00, 0),
    (3, 'Cua gạch Cà Mau', 'cua-gach-ca-mau', 650000, 'kg', 'Cà Mau', 'Cua gạch son loại 1, từ 500g/con trở lên.', 'Cua gạch son loại 1, từ 500g/con trở lên. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Cà Mau. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 15.00, 1.00, 1),
    (3, 'Ghẹ xanh loại 1', 'ghe-xanh-loai-1', 380000, 'kg', 'Phan Thiết, Bình Thuận', 'Ghẹ xanh tươi sống, thịt chắc, đậm vị biển.', 'Ghẹ xanh tươi sống, thịt chắc, đậm vị biển. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Phan Thiết, Bình Thuận. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 30.00, 2.00, 0),
    (1, 'Cá hồi Na Uy nguyên con', 'ca-hoi-na-uy', 420000, 'kg', 'Na Uy (nhập khẩu)', 'Cá hồi Na Uy nguyên con 3–4kg/con.', 'Cá hồi Na Uy nguyên con 3–4kg/con. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Na Uy (nhập khẩu). Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 8.00, 2.00, 1),
    (1, 'Cá bớp biển', 'ca-bop-bien', 320000, 'kg', 'Vũng Tàu', 'Cá bớp biển tươi, thịt trắng dai, ít xương.', 'Cá bớp biển tươi, thịt trắng dai, ít xương. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Vũng Tàu. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 18.00, 0.00, 0),
    (1, 'Cá thu cắt khúc', 'ca-thu-cat-khuc', 280000, 'kg', 'Phú Quốc, Kiên Giang', 'Cá thu tươi cắt khúc sẵn, tiện chế biến.', 'Cá thu tươi cắt khúc sẵn, tiện chế biến. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Phú Quốc, Kiên Giang. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 25.00, 0.00, 0),
    (4, 'Mực ống tươi', 'muc-ong-tuoi', 360000, 'kg', 'Quảng Ninh', 'Mực ống size 8–10 con/kg, câu đêm.', 'Mực ống size 8–10 con/kg, câu đêm. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Quảng Ninh. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 22.00, 1.00, 1),
    (4, 'Mực một nắng', 'muc-mot-nang', 650000, 'kg', 'Phan Thiết, Bình Thuận', 'Mực một nắng loại đặc biệt, phơi tự nhiên.', 'Mực một nắng loại đặc biệt, phơi tự nhiên. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Phan Thiết, Bình Thuận. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 6.00, 0.00, 0),
    (5, 'Ốc hương cỡ lớn', 'oc-huong-co-lon', 550000, 'kg', 'Phú Quốc, Kiên Giang', 'Ốc hương 30–40 con/kg, thịt giòn ngọt.', 'Ốc hương 30–40 con/kg, thịt giòn ngọt. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Phú Quốc, Kiên Giang. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 25.50, 1.00, 0),
    (5, 'Hàu sữa Pháp', 'hau-sua-phap', 25000, 'con', 'Vân Đồn, Quảng Ninh', 'Hàu sữa giống Pháp nuôi tại Vân Đồn, size lớn.', 'Hàu sữa giống Pháp nuôi tại Vân Đồn, size lớn. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Vân Đồn, Quảng Ninh. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 200.00, 12.00, 1),
    (6, 'Tôm thẻ bóc nõn đông lạnh', 'tom-the-boc-non', 145000, 'hộp', 'Sóc Trăng', 'Hộp 500g tôm thẻ bóc nõn, cấp đông IQF.', 'Hộp 500g tôm thẻ bóc nõn, cấp đông IQF. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Sóc Trăng. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 40.00, 2.00, 0),
    (6, 'Chả cá thác lác', 'cha-ca-thac-lac', 95000, 'hộp', 'Hậu Giang', 'Hộp 500g chả cá thác lác quết tay, cấp đông.', 'Hộp 500g chả cá thác lác quết tay, cấp đông. Sản phẩm được tuyển chọn kỹ, bảo quản lạnh theo tiêu chuẩn và giao trong ngày tại nội thành. Xuất xứ: Hậu Giang. Bảo quản ở 0–4°C nếu dùng trong ngày hoặc cấp đông -18°C để dùng lâu hơn.', 4.00, 0.00, 0);

INSERT INTO product_images (product_id, image_url, is_primary, sort_order) VALUES
    (1, '/static/uploads/products/tom-hum-bong-1.jpg', 1, 1),
    (1, '/static/uploads/products/tom-hum-bong-2.jpg', 0, 2),
    (2, '/static/uploads/products/tom-su-cop-1.jpg', 1, 1),
    (2, '/static/uploads/products/tom-su-cop-2.jpg', 0, 2),
    (3, '/static/uploads/products/tom-cang-xanh-1.jpg', 1, 1),
    (3, '/static/uploads/products/tom-cang-xanh-2.jpg', 0, 2),
    (4, '/static/uploads/products/cua-gach-ca-mau-1.jpg', 1, 1),
    (4, '/static/uploads/products/cua-gach-ca-mau-2.jpg', 0, 2),
    (5, '/static/uploads/products/ghe-xanh-loai-1-1.jpg', 1, 1),
    (5, '/static/uploads/products/ghe-xanh-loai-1-2.jpg', 0, 2),
    (6, '/static/uploads/products/ca-hoi-na-uy-1.jpg', 1, 1),
    (6, '/static/uploads/products/ca-hoi-na-uy-2.jpg', 0, 2),
    (7, '/static/uploads/products/ca-bop-bien-1.jpg', 1, 1),
    (7, '/static/uploads/products/ca-bop-bien-2.jpg', 0, 2),
    (8, '/static/uploads/products/ca-thu-cat-khuc-1.jpg', 1, 1),
    (8, '/static/uploads/products/ca-thu-cat-khuc-2.jpg', 0, 2),
    (9, '/static/uploads/products/muc-ong-tuoi-1.jpg', 1, 1),
    (9, '/static/uploads/products/muc-ong-tuoi-2.jpg', 0, 2),
    (10, '/static/uploads/products/muc-mot-nang-1.jpg', 1, 1),
    (10, '/static/uploads/products/muc-mot-nang-2.jpg', 0, 2),
    (11, '/static/uploads/products/oc-huong-co-lon-1.jpg', 1, 1),
    (11, '/static/uploads/products/oc-huong-co-lon-2.jpg', 0, 2),
    (12, '/static/uploads/products/hau-sua-phap-1.jpg', 1, 1),
    (12, '/static/uploads/products/hau-sua-phap-2.jpg', 0, 2),
    (13, '/static/uploads/products/tom-the-boc-non-1.jpg', 1, 1),
    (13, '/static/uploads/products/tom-the-boc-non-2.jpg', 0, 2),
    (14, '/static/uploads/products/cha-ca-thac-lac-1.jpg', 1, 1),
    (14, '/static/uploads/products/cha-ca-thac-lac-2.jpg', 0, 2);

INSERT INTO banners (title, image_url, link_url, sort_order) VALUES
    ('Tôm hùm tươi sống – Giảm 10% cuối tuần', '/static/uploads/banners/banner-1.jpg', '/products?category=2', 1),
    ('Cua gạch Cà Mau chính gốc', '/static/uploads/banners/banner-2.jpg', '/products?category=3', 2),
    ('Hải sản sạch – Giao tận nhà trong 2 giờ', '/static/uploads/banners/banner-3.jpg', '/products', 3);

INSERT INTO cart_items (user_id, product_id, quantity) VALUES
    (1, 10, 0.50),
    (1, 12, 6.00),
    (2, 1, 1.00);

INSERT INTO orders (order_code, user_id, receiver_name, receiver_phone, shipping_address, subtotal, shipping_fee, discount_amount, total_amount, payment_method, payment_status, transaction_ref, status, note, cancel_reason, created_at, updated_at, delivered_at) VALUES
    ('KD2606120001', 1, 'Nguyễn Văn An', '0912345678', '12 Nguyễn Trãi, Phường Thượng Đình, Quận Thanh Xuân, Hà Nội', 2900000, 0, 0, 2900000, 'cod', 'paid', NULL, 'delivered', NULL, NULL, '2026-06-12 09:15:00', '2026-06-13 04:15:00', '2026-06-13 04:15:00'),
    ('KD2607030002', 2, 'Trần Thị Bình', '0987654321', '88 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội', 1200000, 0, 0, 1200000, 'bank_transfer', 'paid', NULL, 'delivered', 'Giao giờ hành chính', NULL, '2026-07-03 18:40:00', '2026-07-04 13:40:00', '2026-07-04 13:40:00'),
    ('KD2608210003', 1, 'Nguyễn Văn An (cơ quan)', '0912345678', '36 Lê Văn Lương, Phường Nhân Chính, Quận Thanh Xuân, Hà Nội', 1200000, 0, 0, 1200000, 'cod', 'paid', NULL, 'delivered', NULL, NULL, '2026-08-21 10:05:00', '2026-08-22 05:05:00', '2026-08-22 05:05:00'),
    ('KD2609090004', 2, 'Trần Thị Bình', '0987654321', '88 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội', 1600000, 0, 0, 1600000, 'vnpay_sandbox', 'paid', 'VNP20260909000004', 'delivered', NULL, NULL, '2026-09-09 16:20:00', '2026-09-10 11:20:00', '2026-09-10 11:20:00'),
    ('KD2610020005', 1, 'Nguyễn Văn An', '0912345678', '12 Nguyễn Trãi, Phường Thượng Đình, Quận Thanh Xuân, Hà Nội', 2175000, 0, 0, 2175000, 'cod', 'paid', NULL, 'delivered', 'Gọi trước khi giao', NULL, '2026-10-02 08:30:00', '2026-10-03 03:30:00', '2026-10-03 03:30:00'),
    ('KD2610100006', 3, 'Lê Minh Cường', '0905111222', '5 Trần Phú, Phường Hải Châu 1, Quận Hải Châu, Đà Nẵng', 1300000, 0, 0, 1300000, 'cod', 'unpaid', NULL, 'cancelled', NULL, 'Khách hàng đổi ý, đặt lại sau', '2026-10-10 11:00:00', '2026-10-10 13:00:00', NULL),
    ('KD2610270007', 2, 'Trần Thị Bình', '0987654321', '88 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội', 1140000, 0, 0, 1140000, 'cod', 'unpaid', NULL, 'shipping', NULL, NULL, '2026-10-27 19:10:00', '2026-10-28 10:10:00', NULL),
    ('KD2610290008', 1, 'Nguyễn Văn An', '0912345678', '12 Nguyễn Trãi, Phường Thượng Đình, Quận Thanh Xuân, Hà Nội', 740000, 30000, 0, 770000, 'bank_transfer', 'paid', NULL, 'confirmed', NULL, NULL, '2026-10-29 07:45:00', '2026-10-29 08:45:00', NULL),
    ('KD2610300009', 2, 'Trần Thị Bình', '0987654321', '88 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội', 570000, 30000, 0, 600000, 'cod', 'unpaid', NULL, 'pending', 'Giao sau 17h', NULL, '2026-10-30 09:00:00', '2026-10-30 09:00:00', NULL);

INSERT INTO order_items (order_id, product_id, product_name, unit, unit_price, quantity) VALUES
    (1, 1, 'Tôm hùm bông', 'kg', 1500000, 1.50),
    (1, 4, 'Cua gạch Cà Mau', 'kg', 650000, 1.00),
    (2, 2, 'Tôm sú cọp', 'kg', 450000, 2.00),
    (2, 12, 'Hàu sữa Pháp', 'con', 25000, 12.00),
    (3, 6, 'Cá hồi Na Uy nguyên con', 'kg', 420000, 2.00),
    (3, 9, 'Mực ống tươi', 'kg', 360000, 1.00),
    (4, 11, 'Ốc hương cỡ lớn', 'kg', 550000, 1.00),
    (4, 5, 'Ghẹ xanh loại 1', 'kg', 380000, 2.00),
    (4, 13, 'Tôm thẻ bóc nõn đông lạnh', 'hộp', 145000, 2.00),
    (5, 1, 'Tôm hùm bông', 'kg', 1500000, 1.00),
    (5, 2, 'Tôm sú cọp', 'kg', 450000, 1.50),
    (6, 4, 'Cua gạch Cà Mau', 'kg', 650000, 2.00),
    (7, 9, 'Mực ống tươi', 'kg', 360000, 1.50),
    (7, 12, 'Hàu sữa Pháp', 'con', 25000, 24.00),
    (8, 6, 'Cá hồi Na Uy nguyên con', 'kg', 420000, 1.00),
    (8, 7, 'Cá bớp biển', 'kg', 320000, 1.00),
    (9, 3, 'Tôm càng xanh', 'kg', 380000, 1.00),
    (9, 14, 'Chả cá thác lác', 'hộp', 95000, 2.00);

INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_admin_id, changed_by_user_id, note, created_at) VALUES
    (1, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-06-12 09:15:00'),
    (1, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-06-12 10:15:00'),
    (1, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-06-12 12:15:00'),
    (1, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-06-13 00:15:00'),
    (1, 'shipping', 'delivered', 1, NULL, 'Khách đã nhận hàng', '2026-06-13 04:15:00'),
    (2, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-07-03 18:40:00'),
    (2, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-07-03 19:40:00'),
    (2, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-07-03 21:40:00'),
    (2, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-07-04 09:40:00'),
    (2, 'shipping', 'delivered', 1, NULL, 'Khách đã nhận hàng', '2026-07-04 13:40:00'),
    (3, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-08-21 10:05:00'),
    (3, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-08-21 11:05:00'),
    (3, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-08-21 13:05:00'),
    (3, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-08-22 01:05:00'),
    (3, 'shipping', 'delivered', 1, NULL, 'Khách đã nhận hàng', '2026-08-22 05:05:00'),
    (4, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-09-09 16:20:00'),
    (4, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-09-09 17:20:00'),
    (4, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-09-09 19:20:00'),
    (4, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-09-10 07:20:00'),
    (4, 'shipping', 'delivered', 1, NULL, 'Khách đã nhận hàng', '2026-09-10 11:20:00'),
    (5, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-10-02 08:30:00'),
    (5, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-10-02 09:30:00'),
    (5, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-10-02 11:30:00'),
    (5, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-10-02 23:30:00'),
    (5, 'shipping', 'delivered', 1, NULL, 'Khách đã nhận hàng', '2026-10-03 03:30:00'),
    (6, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-10-10 11:00:00'),
    (6, 'pending', 'cancelled', NULL, 3, 'Khách hàng hủy: đổi ý, đặt lại sau', '2026-10-10 13:00:00'),
    (7, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-10-27 19:10:00'),
    (7, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-10-27 20:10:00'),
    (7, 'confirmed', 'preparing', 1, NULL, 'Đang sơ chế, đóng gói giữ lạnh', '2026-10-27 22:10:00'),
    (7, 'preparing', 'shipping', 1, NULL, 'Đã bàn giao cho shipper', '2026-10-28 10:10:00'),
    (8, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-10-29 07:45:00'),
    (8, 'pending', 'confirmed', 1, NULL, 'Đã gọi xác nhận với khách', '2026-10-29 08:45:00'),
    (9, NULL, 'pending', NULL, NULL, 'Khách hàng đặt hàng', '2026-10-30 09:00:00');

INSERT INTO reviews (product_id, user_id, rating, title, content, status, created_at) VALUES
    (1, 1, 5, 'Tôm rất tươi', 'Tôm hùm còn sống khi giao, thịt chắc ngọt, đóng gói giữ lạnh cẩn thận.', 'approved', '2026-06-13 20:00:00'),
    (4, 1, 4, 'Cua nhiều gạch', 'Cua chắc, nhiều gạch, giao hơi trễ 30 phút nhưng vẫn ổn.', 'approved', '2026-06-13 20:05:00'),
    (2, 2, 5, 'Sẽ ủng hộ tiếp', 'Tôm sú to đều, đúng size như mô tả.', 'approved', '2026-07-04 09:00:00'),
    (12, 2, 4, 'Hàu béo', 'Hàu sữa béo, nướng mỡ hành rất ngon.', 'approved', '2026-07-04 09:10:00'),
    (6, 1, 5, 'Cá hồi chuẩn', 'Thịt cá hồi đỏ cam, làm sashimi rất ngon.', 'pending', '2026-08-22 19:00:00');

INSERT INTO wishlists (user_id, product_id) VALUES
    (1, 9),
    (1, 11),
    (2, 4);


-- =====================================================================
-- VIEW PHỤC VỤ THỐNG KÊ (doanh thu chỉ tính đơn đã giao)
-- =====================================================================
CREATE OR REPLACE VIEW v_revenue_by_month AS
SELECT DATE_FORMAT(delivered_at, '%Y-%m') AS month,
       COUNT(*)                           AS order_count,
       SUM(total_amount)                  AS revenue
FROM orders
WHERE status = 'delivered'
GROUP BY DATE_FORMAT(delivered_at, '%Y-%m');

CREATE OR REPLACE VIEW v_best_selling_products AS
SELECT p.id, p.name, p.unit,
       SUM(oi.quantity)   AS total_sold,
       SUM(oi.line_total) AS total_revenue
FROM order_items oi
JOIN orders   o ON o.id = oi.order_id AND o.status = 'delivered'
JOIN products p ON p.id = oi.product_id
GROUP BY p.id, p.name, p.unit;

CREATE OR REPLACE VIEW v_low_stock_products AS
SELECT p.id, p.name, c.name AS category_name, p.unit, p.stock_quantity
FROM products p
JOIN categories c ON c.id = p.category_id
WHERE p.is_active = 1 AND p.stock_quantity < 10;

CREATE OR REPLACE VIEW v_product_rating AS
SELECT product_id, ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS review_count
FROM reviews WHERE status = 'approved' GROUP BY product_id;

CREATE OR REPLACE VIEW v_order_count_by_status AS
SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status;
