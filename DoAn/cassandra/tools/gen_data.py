"""Sinh 02_data.cql và csv/customers_import.csv cho keyspace ride_booking.

Dữ liệu cố định (không ngẫu nhiên) để mọi bảng phi chuẩn hóa khớp nhau:
cùng một chuyến đi được ghi vào rides, rides_by_customer, rides_by_area_date,
rides_by_driver_month, payments_by_city_date, ratings_by_driver trong MỘT logged BATCH.

Chạy lại sau khi sửa danh sách bên dưới:
    python DoAn/cassandra/tools/gen_data.py
"""
import hashlib
import math
import pathlib
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
TZ = '+0700'

# ----------------------------------------------------------------------------
# Danh mục
# ----------------------------------------------------------------------------
CUSTOMERS = [  # id, họ tên, phone, email, địa chỉ, ngày tạo
    ('CUST001', 'Nguyễn Văn An',   '0901000001', 'an.nguyen@gmail.com',    '12 Lê Lợi, Quận 1, TP.HCM',               '2026-08-01 09:00:00'),
    ('CUST002', 'Trần Thị Bình',   '0901000002', 'binh.tran@gmail.com',    '25 Lũy Bán Bích, Tân Phú, TP.HCM',        '2026-08-03 10:30:00'),
    ('CUST003', 'Lê Hoàng Cường',  '0901000003', 'cuong.le@gmail.com',     '208 Xô Viết Nghệ Tĩnh, Bình Thạnh, TP.HCM', '2026-08-05 14:00:00'),
    ('CUST004', 'Phạm Thu Dung',   '0901000004', 'dung.pham@gmail.com',    '41 Nguyễn Thị Minh Khai, Quận 3, TP.HCM', '2026-08-10 08:45:00'),
    ('CUST005', 'Hoàng Minh Đức',  '0901000005', 'duc.hoang@gmail.com',    '99 Quang Trung, Gò Vấp, TP.HCM',          '2026-08-12 19:20:00'),
    ('CUST006', 'Võ Ngọc Hân',     '0901000006', 'han.vo@gmail.com',       '140 Lê Trọng Tấn, Tân Phú, TP.HCM',       '2026-08-20 07:10:00'),
    ('CUST007', 'Đặng Quốc Huy',   '0901000007', 'huy.dang@gmail.com',     '144 Xuân Thủy, Cầu Giấy, Hà Nội',         '2026-08-22 16:00:00'),
    ('CUST008', 'Bùi Lan Hương',   '0901000008', 'huong.bui@gmail.com',    '15 Hàng Bài, Hoàn Kiếm, Hà Nội',          '2026-09-01 11:15:00'),
    ('CUST009', 'Ngô Thanh Khoa',  '0901000009', 'khoa.ngo@gmail.com',     '58 Tôn Đức Thắng, Đống Đa, Hà Nội',       '2026-09-05 13:40:00'),
    ('CUST010', 'Đỗ Mai Linh',     '0901000010', 'linh.do@gmail.com',      '22 Trần Thái Tông, Cầu Giấy, Hà Nội',     '2026-09-10 20:05:00'),
]

# id, họ tên, GPLX, phone, thành phố, quận hoạt động, xe (id, biển số, mẫu, màu)
DRIVERS = [
    ('DRV_551', 'Lý Văn Phúc',       '790112345601', '0912000551', 'HCM', 'TAN_PHU',    ('VEH_551', '51F-123.45',  'Toyota Vios',        'Trắng')),
    ('DRV_552', 'Trương Minh Quang', '790112345602', '0912000552', 'HCM', 'Q1',         ('VEH_552', '51G-234.56',  'Kia Morning',        'Bạc')),
    ('DRV_553', 'Huỳnh Tấn Sang',    '790112345603', '0912000553', 'HCM', 'BINH_THANH', ('VEH_553', '59X1-345.67', 'Honda Vision',       'Đỏ')),
    ('DRV_554', 'Phan Văn Tài',      '790112345604', '0912000554', 'HCM', 'Q3',         ('VEH_554', '51H-456.78',  'Hyundai Grand i10',  'Xanh dương')),
    ('DRV_555', 'Nguyễn Hữu Thắng',  '790112345605', '0912000555', 'HCM', 'Q1',         ('VEH_555', '51K-567.89',  'Toyota Innova',      'Xám')),
    ('DRV_556', 'Mai Xuân Trường',   '790112345606', '0912000556', 'HCM', 'GO_VAP',     ('VEH_556', '59T2-678.90', 'Yamaha Sirius',      'Đen')),
    ('DRV_557', 'Đinh Công Vinh',    '010112345607', '0913000557', 'HN',  'CAU_GIAY',   ('VEH_557', '30H-111.22',  'Toyota Vios',        'Đen')),
    ('DRV_558', 'Tạ Quang Vũ',       '010112345608', '0913000558', 'HN',  'HOAN_KIEM',  ('VEH_558', '29B1-222.33', 'Honda Wave Alpha',   'Xanh lá')),
    ('DRV_559', 'Lương Thế Anh',     '010112345609', '0913000559', 'HN',  'DONG_DA',    ('VEH_559', '30K-333.44',  'Mazda 2',            'Đỏ')),
    ('DRV_560', 'Kiều Văn Bảo',      '010112345610', '0913000560', 'HN',  'CAU_GIAY',   ('VEH_560', '30G-444.55',  'VinFast VF 5',       'Trắng')),
]

PLACES = {  # tên ngắn: (địa chỉ hiển thị, lat, lng, quận)
    'LE_DUAN':     ('456 Lê Duẩn, Q1',                    10.7820, 106.6990, 'Q1'),
    'NGUYEN_HUE':  ('123 Nguyễn Huệ, Q1',                 10.7740, 106.7040, 'Q1'),
    'BEN_THANH':   ('Chợ Bến Thành, Q1',                  10.7725, 106.6980, 'Q1'),
    'HUIT':        ('140 Lê Trọng Tấn, Tân Phú',          10.8066, 106.6283, 'TAN_PHU'),
    'AEON_TP':     ('Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng', 10.8015, 106.6176, 'TAN_PHU'),
    'TSN':         ('Sân bay Tân Sơn Nhất, Tân Bình',     10.8185, 106.6588, 'TAN_BINH'),
    'VO_VAN_TAN':  ('2 Võ Văn Tần, Q3',                   10.7790, 106.6920, 'Q3'),
    'CON_RUA':     ('Hồ Con Rùa, Q3',                     10.7828, 106.6959, 'Q3'),
    'LANDMARK81':  ('Landmark 81, 720A Điện Biên Phủ, Bình Thạnh', 10.7950, 106.7218, 'BINH_THANH'),
    'EMART_GV':    ('Emart Phan Văn Trị, Gò Vấp',         10.8270, 106.6880, 'GO_VAP'),
    'HO_GUOM':     ('Hồ Hoàn Kiếm, Hoàn Kiếm',            21.0287, 105.8524, 'HOAN_KIEM'),
    'HANG_BAI':    ('15 Hàng Bài, Hoàn Kiếm',             21.0236, 105.8524, 'HOAN_KIEM'),
    'XUAN_THUY':   ('144 Xuân Thủy, Cầu Giấy',            21.0368, 105.7826, 'CAU_GIAY'),
    'KEANGNAM':    ('Keangnam Landmark 72, Nam Từ Liêm',  21.0170, 105.7838, 'NAM_TU_LIEM'),
    'VAN_MIEU':    ('Văn Miếu, 58 Quốc Tử Giám, Đống Đa', 21.0294, 105.8355, 'DONG_DA'),
    'GA_HN':       ('Ga Hà Nội, 120 Lê Duẩn, Đống Đa',    21.0245, 105.8412, 'DONG_DA'),
    'NOI_BAI':     ('Sân bay Nội Bài, Sóc Sơn',           21.2187, 105.8042, 'SOC_SON'),
}

# ride_id, khách, tài xế (None = chưa có), thành phố, đón, đến, ngày giờ đặt, trạng thái,
# thanh toán, mã KM, đánh giá (sao, nhận xét, tags) hoặc None, lý do hủy
RIDES = [
    ('RIDE_1001', 'CUST001', 'DRV_555', 'HCM', 'LE_DUAN',    'NGUYEN_HUE', '2026-10-03 08:15', 'COMPLETED', 'CASH',    None,      (5, 'Tài xế thân thiện, xe sạch', ['Lịch sự', 'Xe sạch']), None),
    ('RIDE_1002', 'CUST002', 'DRV_551', 'HCM', 'AEON_TP',    'HUIT',       '2026-09-28 07:05', 'COMPLETED', 'MOMO',    None,      (5, 'Đến đúng giờ', ['Đúng giờ']), None),
    ('RIDE_1003', 'CUST006', 'DRV_551', 'HCM', 'HUIT',       'TSN',        '2026-09-28 16:40', 'COMPLETED', 'ZALOPAY', 'GIAM20',  (4, 'Chạy hơi nhanh', ['Đúng giờ']), None),
    ('RIDE_1004', 'CUST003', 'DRV_553', 'HCM', 'LANDMARK81', 'BEN_THANH',  '2026-09-28 19:30', 'COMPLETED', 'CASH',    None,      (5, 'Rất tốt', ['Lịch sự']), None),
    ('RIDE_1005', 'CUST004', 'DRV_554', 'HCM', 'CON_RUA',    'LANDMARK81', '2026-09-29 08:00', 'COMPLETED', 'CARD',    'HCMXANH', (5, 'Xe thơm, nhạc nhẹ', ['Xe sạch', 'Lịch sự']), None),
    ('RIDE_1006', 'CUST005', 'DRV_556', 'HCM', 'EMART_GV',   'VO_VAN_TAN', '2026-09-29 12:20', 'CANCELLED', 'CASH',    None,      None, 'Khách đổi lịch'),
    ('RIDE_1007', 'CUST001', 'DRV_552', 'HCM', 'NGUYEN_HUE', 'TSN',        '2026-09-29 17:45', 'COMPLETED', 'MOMO',    'GIAM20',  (3, 'Đi đường vòng', ['Đường vòng']), None),
    ('RIDE_1008', 'CUST002', None,      'HCM', 'HUIT',       'AEON_TP',    '2026-09-30 06:50', 'CANCELLED', 'CASH',    None,      None, 'Không có tài xế nhận'),
    ('RIDE_1009', 'CUST006', 'DRV_551', 'HCM', 'HUIT',       'BEN_THANH',  '2026-09-30 09:10', 'COMPLETED', 'ZALOPAY', None,      (5, 'Tài xế hỗ trợ mang đồ', ['Nhiệt tình']), None),
    ('RIDE_1010', 'CUST003', 'DRV_555', 'HCM', 'BEN_THANH',  'CON_RUA',    '2026-09-30 18:05', 'COMPLETED', 'CASH',    None,      None, None),
    ('RIDE_1011', 'CUST004', 'DRV_554', 'HCM', 'VO_VAN_TAN', 'TSN',        '2026-10-01 05:30', 'COMPLETED', 'CARD',    None,      (5, 'Đón sớm đúng hẹn', ['Đúng giờ']), None),
    ('RIDE_1012', 'CUST005', 'DRV_556', 'HCM', 'EMART_GV',   'LANDMARK81', '2026-10-01 10:15', 'COMPLETED', 'MOMO',    'HCMXANH', (4, 'Ổn', []), None),
    ('RIDE_1013', 'CUST001', 'DRV_553', 'HCM', 'LE_DUAN',    'LANDMARK81', '2026-10-01 20:00', 'COMPLETED', 'CASH',    None,      (5, 'Tốt', ['Lịch sự']), None),
    ('RIDE_1014', 'CUST002', 'DRV_552', 'HCM', 'AEON_TP',    'NGUYEN_HUE', '2026-10-02 07:30', 'CANCELLED', 'MOMO',    None,      None, 'Tài xế báo hỏng xe'),
    ('RIDE_1015', 'CUST006', 'DRV_551', 'HCM', 'HUIT',       'EMART_GV',   '2026-10-02 11:45', 'COMPLETED', 'ZALOPAY', 'GIAM20',  (5, 'Rất hài lòng', ['Đúng giờ', 'Lịch sự']), None),
    ('RIDE_1016', 'CUST003', 'DRV_555', 'HCM', 'LANDMARK81', 'TSN',        '2026-10-02 15:00', 'COMPLETED', 'CARD',    None,      (4, 'Xe hơi nóng', ['Đúng giờ']), None),
    ('RIDE_1017', 'CUST005', 'DRV_556', 'HCM', 'VO_VAN_TAN', 'EMART_GV',   '2026-10-03 09:40', 'COMPLETED', 'CASH',    None,      None, None),
    ('RIDE_1018', 'CUST004', 'DRV_554', 'HCM', 'CON_RUA',    'BEN_THANH',  '2026-10-03 13:10', 'COMPLETED', 'MOMO',    None,      (5, 'Nhanh', ['Đúng giờ']), None),
    ('RIDE_1019', 'CUST006', 'DRV_553', 'HCM', 'HUIT',       'LANDMARK81', '2026-10-03 18:25', 'COMPLETED', 'ZALOPAY', 'HCMXANH', (5, 'Tốt', ['Lịch sự']), None),
    ('RIDE_1020', 'CUST002', 'DRV_551', 'HCM', 'AEON_TP',    'TSN',        '2026-10-04 06:20', 'COMPLETED', 'MOMO',    None,      (5, 'Đúng giờ ra sân bay', ['Đúng giờ']), None),
    ('RIDE_1021', 'CUST001', 'DRV_555', 'HCM', 'NGUYEN_HUE', 'VO_VAN_TAN', '2026-10-04 08:05', 'COMPLETED', 'CASH',    None,      None, None),
    ('RIDE_1022', 'CUST003', 'DRV_552', 'HCM', 'BEN_THANH',  'LANDMARK81', '2026-10-04 09:30', 'ONGOING',   'CARD',    None,      None, None),
    ('RIDE_1023', 'CUST005', 'DRV_556', 'HCM', 'EMART_GV',   'TSN',        '2026-10-04 09:50', 'ACCEPTED',  'MOMO',    'GIAM20',  None, None),
    ('RIDE_1024', 'CUST006', None,      'HCM', 'HUIT',       'AEON_TP',    '2026-10-04 10:00', 'REQUESTED', 'ZALOPAY', None,      None, None),
    ('RIDE_1025', 'CUST007', 'DRV_557', 'HN',  'XUAN_THUY',  'HO_GUOM',    '2026-09-28 08:10', 'COMPLETED', 'MOMO',    None,      (5, 'Tài xế vui vẻ', ['Lịch sự']), None),
    ('RIDE_1026', 'CUST008', 'DRV_558', 'HN',  'HANG_BAI',   'VAN_MIEU',   '2026-09-29 14:30', 'COMPLETED', 'CASH',    'HANOI10', (4, 'Ổn', []), None),
    ('RIDE_1027', 'CUST009', 'DRV_559', 'HN',  'GA_HN',      'NOI_BAI',    '2026-09-30 04:45', 'COMPLETED', 'CARD',    None,      (5, 'Đón đúng giờ dù sáng sớm', ['Đúng giờ', 'Nhiệt tình']), None),
    ('RIDE_1028', 'CUST010', 'DRV_560', 'HN',  'XUAN_THUY',  'KEANGNAM',   '2026-10-01 18:15', 'CANCELLED', 'ZALOPAY', None,      None, 'Khách hủy do kẹt xe'),
    ('RIDE_1029', 'CUST007', 'DRV_560', 'HN',  'KEANGNAM',   'VAN_MIEU',   '2026-10-02 09:00', 'COMPLETED', 'ZALOPAY', 'GIAM20',  (5, 'Xe điện êm', ['Xe sạch']), None),
    ('RIDE_1030', 'CUST008', 'DRV_558', 'HN',  'HO_GUOM',    'GA_HN',      '2026-10-03 17:20', 'COMPLETED', 'MOMO',    None,      (3, 'Tài xế nghe điện thoại khi lái', ['Mất tập trung']), None),
    ('RIDE_1031', 'CUST009', 'DRV_557', 'HN',  'VAN_MIEU',   'XUAN_THUY',  '2026-10-04 07:40', 'COMPLETED', 'CASH',    'HANOI10', (5, 'Tốt', ['Lịch sự']), None),
    ('RIDE_1032', 'CUST010', 'DRV_559', 'HN',  'XUAN_THUY',  'HANG_BAI',   '2026-10-04 09:15', 'ONGOING',   'MOMO',    None,      None, None),
    ('RIDE_1033', 'CUST004', 'DRV_554', 'HCM', 'BEN_THANH',  'CON_RUA',    '2026-10-04 07:10', 'COMPLETED', 'CARD',    None,      (5, 'Đúng giờ', ['Đúng giờ']), None),
    ('RIDE_1034', 'CUST003', 'DRV_553', 'HCM', 'LE_DUAN',    'LANDMARK81', '2026-10-04 07:45', 'COMPLETED', 'CASH',    None,      None, None),
    ('RIDE_1035', 'CUST005', 'DRV_553', 'HCM', 'NGUYEN_HUE', 'EMART_GV',   '2026-10-04 08:30', 'COMPLETED', 'MOMO',    None,      (4, 'Xe ổn, hơi chậm', []), None),
    ('RIDE_1036', 'CUST002', 'DRV_555', 'HCM', 'BEN_THANH',  'NGUYEN_HUE', '2026-10-04 09:05', 'CANCELLED', 'CASH',    None,      None, 'Khách đổi ý'),
]

PROMOTIONS = [  # code, mô tả, %, tối đa, cước tối thiểu, thành phố, giới hạn lượt
    ('GIAM20',  'Giảm 20% tối đa 30.000đ cho mọi chuyến', 20, 30000.0, 50000.0, ['HCM', 'HN'], 500),
    ('HCMXANH', 'Giảm 15% tối đa 20.000đ tại TP.HCM',      15, 20000.0, 30000.0, ['HCM'],       200),
    ('HANOI10', 'Giảm 10% tối đa 15.000đ tại Hà Nội',      10, 15000.0, 30000.0, ['HN'],        200),
]

AVAILABLE_NOW = ['DRV_551', 'DRV_553', 'DRV_554', 'DRV_557', 'DRV_558', 'DRV_560']  # đang trực tuyến lúc 10:00 ngày 04/10
PASSWORD_DEMO = '123456'
NOW = datetime(2026, 10, 4, 10, 0)


# ----------------------------------------------------------------------------
def q(s):
    return "'" + s.replace("'", "''") + "'"


def ts(d):
    return q(d.strftime('%Y-%m-%d %H:%M:%S') + TZ)


def money(x):
    return f'{x:.1f}'


def point(p):
    _, lat, lng, _ = PLACES[p]
    return f'{{lat: {lat}, lng: {lng}}}'


def km(a, b):
    _, la1, lo1, _ = PLACES[a]
    _, la2, lo2, _ = PLACES[b]
    r = 6371.0
    dlat, dlon = math.radians(la2 - la1), math.radians(lo2 - lo1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.sin(dlon / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(h)) * 1.35, 1)  # 1.35: hệ số đường đi thực tế


def fare_of(distance):
    return float(max(15000, round((12000 + 8500 * distance) / 1000) * 1000))


def vehicle_udt(v):
    vid, plate, model, color = v
    return f'{{vehicle_id: {q(vid)}, license_plate: {q(plate)}, model: {q(model)}, color: {q(color)}}}'


cust = {c[0]: c for c in CUSTOMERS}
drv = {d[0]: d for d in DRIVERS}
promo = {p[0]: p for p in PROMOTIONS}

# ----------------------------------------------------------------------------
# Tính toán từng chuyến
# ----------------------------------------------------------------------------
rides = []
for (rid, cid, did, city, src, dst, when, status, method, code, rating, reason) in RIDES:
    req = datetime.strptime(when, '%Y-%m-%d %H:%M')
    dist = 8.6 if rid == 'RIDE_1001' else km(src, dst)
    fare = 85000.0 if rid == 'RIDE_1001' else fare_of(dist)
    discount = 0.0
    if code:
        _, _, pct, cap, min_fare, cities, _ = promo[code]
        assert city in cities and fare >= min_fare, (rid, code)
        discount = float(min(cap, round(fare * pct / 100 / 1000) * 1000))
    acc = req + timedelta(minutes=2) if did else None
    start = acc + timedelta(minutes=6) if acc and status in ('ONGOING', 'COMPLETED') else None
    done = start + timedelta(minutes=round(dist * 2.5 + 5)) if status == 'COMPLETED' else None
    cancel_at = req + timedelta(minutes=8) if status == 'CANCELLED' else None
    hist = [(req, 'REQUESTED')]
    if acc and (status != 'CANCELLED' or did):
        hist.append((acc, 'ACCEPTED'))
    if start:
        hist.append((start, 'ONGOING'))
    if done:
        hist.append((done, 'COMPLETED'))
    if cancel_at:
        hist.append((cancel_at, 'CANCELLED'))
    rides.append(dict(id=rid, cid=cid, did=did, city=city, src=src, dst=dst, req=req, status=status,
                      method=method, code=code, rating=rating, reason=reason, dist=dist, fare=fare,
                      discount=discount, acc=acc if status != 'REQUESTED' else None, start=start,
                      done=done, hist=hist, district=PLACES[src][3]))

# trùng lịch tài xế: không cho hai chuyến của cùng tài xế chồng thời gian
by_drv = defaultdict(list)
for r in rides:
    if r['did']:
        end = r['done'] or (r['req'] + timedelta(minutes=60))
        by_drv[r['did']].append((r['req'], end, r['id']))
for d, spans in by_drv.items():
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        assert a[1] <= b[0], f'{d}: {a[2]} chồng {b[2]}'

ratings = defaultdict(list)
for r in rides:
    if r['rating']:
        ratings[r['did']].append(r['rating'][0])
driver_rating = {d[0]: round(sum(ratings[d[0]]) / len(ratings[d[0]]), 2) if ratings[d[0]] else 5.0 for d in DRIVERS}
busy = {r['did'] for r in rides if r['status'] in ('ACCEPTED', 'ONGOING')}
driver_status = {d[0]: 'BUSY' if d[0] in busy else ('AVAILABLE' if d[0] in AVAILABLE_NOW else 'OFFLINE') for d in DRIVERS}
assert not (busy & set(AVAILABLE_NOW))
promo_used = defaultdict(int)
for r in rides:
    if r['code'] and r['status'] != 'CANCELLED':
        promo_used[r['code']] += 1

# ----------------------------------------------------------------------------
# Ghi 02_data.cql
# ----------------------------------------------------------------------------
L = []
w = L.append
w('-- =====================================================================')
w('-- 02_data.cql — Dữ liệu mẫu cho keyspace ride_booking')
w('-- SINH TỰ ĐỘNG bởi tools/gen_data.py — sửa dữ liệu trong gen_data.py rồi chạy lại.')
w(f'-- {len(CUSTOMERS)} khách hàng, {len(DRIVERS)} tài xế, {len(DRIVERS)} xe, {len(CUSTOMERS) + len(DRIVERS) + 2} tài khoản, '
  f'{len(rides)} chuyến đi (28/09–04/10/2026), {len(PROMOTIONS)} mã khuyến mãi.')
w('-- Chạy sau 01_schema.cql:  docker exec nosql-cassandra cqlsh -f /tmp/cassandra/02_data.cql')
w('-- INSERT trong Cassandra là upsert: chạy lại nhiều lần không tạo bản ghi trùng,')
w('-- riêng bảng counter ride_stats_by_city sẽ cộng dồn — chỉ chạy phần counter một lần')
w('-- (hoặc TRUNCATE ride_stats_by_city trước khi chạy lại).')
w('-- =====================================================================')
w('USE ride_booking;')
w('')
w('-- ---------------------------------------------------------------------')
w('-- A. Danh mục: khách hàng, tài xế, xe, tài khoản, khuyến mãi')
w('-- ---------------------------------------------------------------------')
for cid, name, phone, email, addr, created in CUSTOMERS:
    w(f'INSERT INTO customers (customer_id, full_name, phone, email, address, created_at) VALUES '
      f'({q(cid)}, {q(name)}, {q(phone)}, {q(email)}, {q(addr)}, {q(created + TZ)});')
w('')
for did, name, lic, phone, city, district, veh in DRIVERS:
    w(f'INSERT INTO drivers (driver_id, full_name, license_number, phone, rating, status) VALUES '
      f'({q(did)}, {q(name)}, {q(lic)}, {q(phone)}, {driver_rating[did]}, {q(driver_status[did])});')
w('')
for did, name, lic, phone, city, district, (vid, plate, model, color) in DRIVERS:
    w(f'INSERT INTO vehicles (vehicle_id, driver_id, license_plate, model, color) VALUES '
      f'({q(vid)}, {q(did)}, {q(plate)}, {q(model)}, {q(color)});')
w('')
pw = hashlib.sha256(PASSWORD_DEMO.encode()).hexdigest()
w(f"-- password_hash = SHA-256 của mật khẩu demo '{PASSWORD_DEMO}' (chỉ dùng cho môi trường học tập)")
accounts = [('admin', 'ADMIN', None, 'Quản trị hệ thống'), ('dieuphoi', 'OPERATOR', None, 'Nhân viên điều phối')]
accounts += [(c[0].lower(), 'CUSTOMER', c[0], c[1]) for c in CUSTOMERS]
accounts += [(d[0].lower().replace('_', ''), 'DRIVER', d[0], d[1]) for d in DRIVERS]
for user, role, ref, name in accounts:
    ref_sql = q(ref) if ref else 'null'
    w(f'INSERT INTO user_accounts (username, password_hash, role, ref_id, full_name, is_active, created_at) VALUES '
      f'({q(user)}, {q(pw)}, {q(role)}, {ref_sql}, {q(name)}, true, {q("2026-09-01 08:00:00" + TZ)}) IF NOT EXISTS;')
w('')
w('-- Mã khuyến mãi tự hết hạn sau 90 ngày (USING TTL 7776000 giây); ứng dụng thật tính TTL = valid_to - now')
for code, desc, pct, cap, min_fare, cities, limit in PROMOTIONS:
    cs = '{' + ', '.join(q(c) for c in cities) + '}'
    w(f'INSERT INTO promotions (promo_code, description, discount_percent, max_discount, min_fare, cities, usage_limit, used_count, valid_from, valid_to) VALUES '
      f'({q(code)}, {q(desc)}, {pct}, {money(cap)}, {money(min_fare)}, {cs}, {limit}, {promo_used[code]}, '
      f'{q("2026-09-01 00:00:00" + TZ)}, {q("2026-12-31 23:59:59" + TZ)}) USING TTL 7776000;')
w('')
w('-- ---------------------------------------------------------------------')
w('-- B. Chuyến đi: mỗi chuyến ghi vào mọi bảng liên quan trong MỘT logged BATCH')
w('--    (đảm bảo hoặc tất cả bảng có chuyến đó, hoặc không bảng nào có)')
w('-- ---------------------------------------------------------------------')
for r in rides:
    c = cust[r['cid']]
    d = drv.get(r['did'])
    src, dst = PLACES[r['src']], PLACES[r['dst']]
    day = r['req'].strftime('%Y-%m-%d')
    yyyymm = int(r['req'].strftime('%Y%m'))
    hist = '{' + ', '.join(f'{ts(t)}: {q(s)}' for t, s in r['hist']) + '}'
    w(f"-- {r['id']}: {c[1]} | {src[0]} -> {dst[0]} | {r['status']}")
    w('BEGIN BATCH')
    cols = ['ride_id', 'customer_id', 'customer_name', 'customer_phone', 'city', 'district', 'pickup_address',
            'destination_address', 'pickup_point', 'dropoff_point', 'distance_km', 'fare', 'discount',
            'payment_method', 'status', 'ride_date', 'requested_at', 'status_history']
    vals = [q(r['id']), q(c[0]), q(c[1]), q(c[2]), q(r['city']), q(r['district']), q(src[0]), q(dst[0]),
            point(r['src']), point(r['dst']), str(r['dist']), money(r['fare']), money(r['discount']),
            q(r['method']), q(r['status']), q(day), ts(r['req']), hist]
    if d:
        cols += ['driver_id', 'driver_name', 'vehicle']
        vals += [q(d[0]), q(d[1]), vehicle_udt(d[6])]
    if r['code']:
        cols.append('promo_code'); vals.append(q(r['code']))
    for col, key in (('accepted_at', 'acc'), ('started_at', 'start'), ('completed_at', 'done')):
        if r[key]:
            cols.append(col); vals.append(ts(r[key]))
    if r['reason']:
        cols.append('cancel_reason'); vals.append(q(r['reason']))
    w(f"  INSERT INTO rides ({', '.join(cols)}) VALUES ({', '.join(vals)});")
    drv_sql = q(d[0]) if d else 'null'
    w(f"  INSERT INTO rides_by_customer (customer_id, ride_date, ride_id, pickup_address, destination_address, driver_id, fare, status) VALUES "
      f"({q(c[0])}, {q(day)}, {q(r['id'])}, {q(src[0])}, {q(dst[0])}, {drv_sql}, {money(r['fare'])}, {q(r['status'])});")
    w(f"  INSERT INTO rides_by_area_date (city, district, ride_date, requested_at, ride_id, customer_id, driver_id, pickup_address, destination_address, fare, status, payment_method) VALUES "
      f"({q(r['city'])}, {q(r['district'])}, {q(day)}, {ts(r['req'])}, {q(r['id'])}, {q(c[0])}, {drv_sql}, {q(src[0])}, {q(dst[0])}, {money(r['fare'])}, {q(r['status'])}, {q(r['method'])});")
    if d:
        w(f"  INSERT INTO rides_by_driver_month (driver_id, yyyymm, requested_at, ride_id, driver_name, vehicle_plate, customer_id, pickup_address, destination_address, distance_km, fare, status) VALUES "
          f"({q(d[0])}, {yyyymm}, {ts(r['req'])}, {q(r['id'])}, {q(d[1])}, {q(d[6][1])}, {q(c[0])}, {q(src[0])}, {q(dst[0])}, {r['dist']}, {money(r['fare'])}, {q(r['status'])});")
    if r['status'] == 'COMPLETED':
        w(f"  INSERT INTO payments_by_city_date (city, pay_date, payment_method, paid_at, ride_id, customer_id, driver_id, district, amount, discount) VALUES "
          f"({q(r['city'])}, {q(r['done'].strftime('%Y-%m-%d'))}, {q(r['method'])}, {ts(r['done'])}, {q(r['id'])}, {q(c[0])}, {q(d[0])}, {q(r['district'])}, {money(r['fare'] - r['discount'])}, {money(r['discount'])});")
    if r['rating']:
        stars, comment, tags = r['rating']
        tag_sql = '[' + ', '.join(q(t) for t in tags) + ']'
        rated = r['done'] + timedelta(minutes=3)
        w(f"  INSERT INTO ratings_by_driver (driver_id, rated_at, ride_id, customer_id, stars, comment, tags) VALUES "
          f"({q(d[0])}, {ts(rated)}, {q(r['id'])}, {q(c[0])}, {stars}, {q(comment)}, {tag_sql});")
    w('APPLY BATCH;')
w('')
w('-- ---------------------------------------------------------------------')
w('-- C. Thống kê bằng counter (chỉ UPDATE +/-; không nằm chung BATCH với bảng thường)')
w('-- ---------------------------------------------------------------------')
stats = defaultdict(lambda: [0, 0, 0])
for r in rides:
    key = (r['city'], int(r['req'].strftime('%Y%m')), r['req'].strftime('%Y-%m-%d'))
    stats[key][0] += 1
    stats[key][1] += r['status'] == 'COMPLETED'
    stats[key][2] += r['status'] == 'CANCELLED'
w('BEGIN COUNTER BATCH')
for (city, yyyymm, day), (req, comp, canc) in sorted(stats.items()):
    w(f'  UPDATE ride_stats_by_city SET rides_requested = rides_requested + {req}, rides_completed = rides_completed + {comp}, '
      f'rides_cancelled = rides_cancelled + {canc} WHERE city = {q(city)} AND yyyymm = {yyyymm} AND ride_date = {q(day)};')
w('APPLY BATCH;')
w('')
w('-- ---------------------------------------------------------------------')
w('-- D. Tài xế đang trực tuyến (lúc 10:00 ngày 04/10/2026) và vị trí GPS')
w('--    Dữ liệu mẫu KHÔNG đặt TTL cho drivers_by_area để demo không bị mất;')
w('--    ứng dụng thật ghi kèm USING TTL 300 mỗi lần tài xế gửi tín hiệu (xem 04_queries_advanced.cql).')
w('-- ---------------------------------------------------------------------')
offsets = [(-0.0030, 0.0020), (0.0015, -0.0025), (0.0040, 0.0010), (-0.0010, -0.0035), (0.0025, 0.0030), (-0.0045, 0.0005)]
for i, did in enumerate(AVAILABLE_NOW):
    d = drv[did]
    home = next(p for p in PLACES.values() if p[3] == d[5])
    lat, lng = round(home[1] + offsets[i][0], 4), round(home[2] + offsets[i][1], 4)
    w(f'INSERT INTO drivers_by_area (city, district, driver_id, full_name, phone, rating, vehicle, location, last_seen) VALUES '
      f'({q(d[4])}, {q(d[5])}, {q(did)}, {q(d[1])}, {q(d[3])}, {driver_rating[did]}, {vehicle_udt(d[6])}, '
      f'{{lat: {lat}, lng: {lng}}}, {ts(NOW - timedelta(seconds=30 * (i + 1)))});')
w('')
w('-- driver_locations có default_time_to_live = 86400: các điểm GPS tự xóa sau 24 giờ kể từ lúc chạy script này')
tracks = {  # tài xế -> điểm đầu, điểm cuối, giờ bắt đầu
    'DRV_552': ('BEN_THANH', 'LANDMARK81', datetime(2026, 10, 4, 9, 38)),
    'DRV_559': ('XUAN_THUY', 'HANG_BAI', datetime(2026, 10, 4, 9, 23)),
    'DRV_551': ('AEON_TP', 'HUIT', datetime(2026, 10, 4, 9, 30)),
}
for did, (a, b, t0) in tracks.items():
    pa, pb = PLACES[a], PLACES[b]
    for k in range(6):
        f = k / 5
        lat = round(pa[1] + (pb[1] - pa[1]) * f, 5)
        lng = round(pa[2] + (pb[2] - pa[2]) * f, 5)
        speed = [0.0, 18.5, 26.0, 31.5, 22.0, 12.5][k]
        w(f"INSERT INTO driver_locations (driver_id, day, ts, location, speed_kmh) VALUES "
          f"({q(did)}, '2026-10-04', {ts(t0 + timedelta(minutes=2 * k))}, {{lat: {lat}, lng: {lng}}}, {speed});")
(ROOT / '02_data.cql').write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n')

# ----------------------------------------------------------------------------
# CSV dùng cho phần Import (COPY FROM): 5 khách hàng mới chưa có trong 02_data.cql
# ----------------------------------------------------------------------------
new_customers = [
    ('CUST011', 'Phan Gia Bảo',   '0901000011', 'bao.phan@gmail.com',   '18 Tân Kỳ Tân Quý, Tân Phú, TP.HCM', '2026-10-04 08:00:00'),
    ('CUST012', 'Lâm Khánh Chi',  '0901000012', 'chi.lam@gmail.com',    '7 Phạm Ngọc Thạch, Quận 3, TP.HCM',  '2026-10-04 08:05:00'),
    ('CUST013', 'Châu Minh Nhật', '0901000013', 'nhat.chau@gmail.com',  '310 Nguyễn Oanh, Gò Vấp, TP.HCM',    '2026-10-04 08:10:00'),
    ('CUST014', 'Hà Thu Trang',   '0901000014', 'trang.ha@gmail.com',   '55 Trần Duy Hưng, Cầu Giấy, Hà Nội', '2026-10-04 08:15:00'),
    ('CUST015', 'Quách Tuấn Kiệt', '0901000015', 'kiet.quach@gmail.com', '9 Lý Thường Kiệt, Hoàn Kiếm, Hà Nội', '2026-10-04 08:20:00'),
]
csv_dir = ROOT / 'csv'
csv_dir.mkdir(exist_ok=True)
rows = ['customer_id,full_name,phone,email,address,created_at']
# Thời gian ghi theo UTC (+0000): cqlsh 6.1 COPY FROM hiểu NGƯỢC dấu của độ lệch múi giờ (+0700 bị cộng thay vì trừ),
# trong khi COPY TO luôn xuất UTC — dùng UTC trong CSV để nhập đúng.
for cid, name, phone, email, addr, created in new_customers:
    utc = datetime.strptime(created, '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
    rows.append(f'{cid},{name},{phone},{email},"{addr}",{utc:%Y-%m-%d %H:%M:%S}+0000')
(csv_dir / 'customers_import.csv').write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')

print(f'02_data.cql: {len(L)} dòng, {len(rides)} chuyến, ratings {sum(len(v) for v in ratings.values())}, '
      f'completed {sum(r["status"] == "COMPLETED" for r in rides)}, cancelled {sum(r["status"] == "CANCELLED" for r in rides)}')
print('driver_rating', driver_rating)
print('driver_status', driver_status)
print('promo_used', dict(promo_used))
