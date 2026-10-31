#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phân tích Bank Marketing theo tiểu luận Chương 1–5.

Chạy: python bank_marketing.py
Hoặc: python bank_marketing.py --data duong_dan.csv --output ket_qua
Phụ thuộc: pandas, numpy, matplotlib. Không cần mạng khi chạy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
NUMERIC = ['age', 'duration', 'campaign', 'pdays', 'previous', 'emp.var.rate',
           'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed']
CATEGORY = ['job', 'marital', 'education', 'default', 'housing', 'loan',
            'contact', 'month', 'day_of_week', 'poutcome']
EXPECTED = NUMERIC + CATEGORY + ['y']
AGE_LABELS = ['Dưới 30', '30–39', '40–49', '50–59', '60+']
CALL_LABELS = ['1 lần', '2–3 lần', '4–5 lần', 'Trên 5 lần']
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
DAYS = ['mon', 'tue', 'wed', 'thu', 'fri']

# CHƯƠNG 1: Mục tiêu và cơ sở tính toán.
# Tỷ lệ đăng ký (%) = số y=yes / số quan sát của chính nhóm * 100.
# Chênh lệch điểm phần trăm = tỷ lệ nhóm - tỷ lệ toàn mẫu.
# Một dòng là một quan sát, không khẳng định là một khách hàng duy nhất.
# Không có chi phí/giá trị tiền gửi nên không tính lợi nhuận hoặc ROI.
def chapter1(out: Path) -> None:
    (out / 'chuong_1_pham_vi.md').write_text('''# Chương 1 — Phạm vi và phương pháp
Phân tích hiệu quả phản hồi chiến dịch marketing ngân hàng qua tỷ lệ đăng ký tiền gửi.

Câu hỏi: tỷ lệ chung; khác biệt theo đặc điểm khách hàng; tháng, thứ, kênh và
số lần liên hệ; lịch sử chiến dịch; định hướng thử nghiệm tiếp theo.

Tỷ lệ nhóm = số đăng ký / tổng số quan sát của nhóm × 100%.
Chênh lệch so với chung tính bằng điểm phần trăm trên số chưa làm tròn.
Luôn trình bày quy mô nhóm và số đăng ký, không chỉ xếp hạng tỷ lệ.
Chương 1 là lý thuyết, không tạo thêm dữ liệu thực nghiệm.
Logistic Regression chỉ là hướng mở rộng, không thuộc kết quả tiểu luận.
Nguồn dữ liệu theo tiểu luận: UCI Bank Marketing, DOI 10.24432/C5K306.
''', encoding='utf-8')


def read_data(path: Path) -> pd.DataFrame:
    """Đọc đúng phiên bản CSV; hỗ trợ ZIP, kể cả ZIP lồng tối đa 5 tầng."""
    def find_csv(blob: bytes, depth=0):
        if depth > 5:
            raise ValueError('ZIP lồng quá 5 tầng.')
        with ZipFile(BytesIO(blob)) as z:
            for name in z.namelist():
                if Path(name).name == 'bank-additional-full.csv':
                    return z.read(name)
            for name in z.namelist():
                if name.lower().endswith('.zip'):
                    found = find_csv(z.read(name), depth + 1)
                    if found is not None:
                        return found
        return None
    if path.suffix.lower() == '.zip':
        content = find_csv(path.read_bytes())
        if content is None:
            raise ValueError('Không tìm thấy bank-additional-full.csv trong ZIP.')
        df = pd.read_csv(BytesIO(content), sep=';')
    else:
        df = pd.read_csv(path, sep=';')
    if set(df.columns) != set(EXPECTED) or len(df.columns) != 21:
        raise ValueError('Cần CSV gốc có 21 cột, phân cách bằng dấu ;. Không dùng CSV đã xử lý.')
    if df.empty or df.isna().any().any():
        raise ValueError('Dữ liệu rỗng hoặc có ô thiếu ngoài quy trình tiểu luận; cần kiểm tra lại.')
    if set(df.y.unique()) != {'yes', 'no'}:
        raise ValueError('Biến y phải chứa đúng hai nhãn yes và no.')
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors='raise')
        if not np.isfinite(df[col]).all():
            raise ValueError(f'{col} có giá trị không hữu hạn.')
    return df


def save_table(table: pd.DataFrame, folder: Path, name: str, index=True):
    table.to_csv(folder / f'{name}.csv', index=index, encoding='utf-8-sig')


def group_stats(df: pd.DataFrame, col: str, order=None, sort=False) -> pd.DataFrame:
    t = df.groupby(col, observed=True, dropna=False)['dang_ky'].agg(so_quan_sat='size', so_dang_ky='sum')
    t['ty_le_dang_ky_pct'] = t.so_dang_ky / t.so_quan_sat * 100
    t['chenh_lech_diem_phan_tram'] = t.ty_le_dang_ky_pct - df.dang_ky.mean() * 100
    if order is not None:
        t = t.reindex([x for x in order if x in t.index])
    if sort:
        t = t.sort_values('ty_le_dang_ky_pct', ascending=False, kind='stable')
    return t


# CHƯƠNG 2: Kiểm tra, giữ dữ liệu gốc, tạo đúng 5 biến.
def chapter2(raw: pd.DataFrame, out: Path) -> pd.DataFrame:
    folder = out / 'chuong_2'; folder.mkdir(exist_ok=True)
    quality = pd.DataFrame({'kieu_du_lieu': raw.dtypes.astype(str),
                            'so_o_thieu': raw.isna().sum(),
                            'so_unknown': raw.eq('unknown').sum()})
    quality['ty_le_unknown_pct'] = quality.so_unknown / len(raw) * 100
    save_table(quality, folder, 'chat_luong_du_lieu')
    save_table(raw.loc[raw.duplicated(keep=False)], folder, 'tat_ca_dong_thuoc_nhom_trung')
    save_table(raw[NUMERIC].describe().T, folder, 'thong_ke_bien_so_goc')
    invalid = {'age_khong_duong': int((raw.age <= 0).sum()),
               'campaign_duoi_1': int((raw.campaign < 1).sum())}
    invalid.update({f'{c}_am': int((raw[c] < 0).sum()) for c in ['duration', 'previous', 'pdays']})
    (folder / 'kiem_tra_mien_gia_tri.json').write_text(json.dumps(invalid, indent=2), encoding='utf-8')
    if any(invalid.values()):
        raise ValueError(f'Dữ liệu vi phạm miền giá trị: {invalid}')
    df = raw.copy()
    df['dang_ky'] = df.y.map({'yes': 1, 'no': 0})
    df['nhom_tuoi'] = pd.cut(df.age, [-np.inf, 29, 39, 49, 59, np.inf], labels=AGE_LABELS)
    df['nhom_so_lan_lien_he'] = pd.cut(df.campaign, [0, 1, 3, 5, np.inf], labels=CALL_LABELS)
    df['co_lich_su'] = np.where(df.previous > 0, 'Có lịch sử', 'Không có lịch sử')
    df['pdays_thuc_te'] = df.pdays.where(df.pdays != 999)
    if df[['nhom_tuoi', 'nhom_so_lan_lien_he']].isna().any().any():
        raise ValueError('Phân nhóm phát sinh giá trị thiếu.')
    cross = pd.crosstab(df.co_lich_su, np.where(df.pdays == 999, 'pdays = 999', 'pdays khác 999'))
    save_table(cross, folder, 'doi_chieu_previous_pdays')
    save_table(pd.crosstab(df.co_lich_su, df.poutcome), folder, 'doi_chieu_previous_poutcome')
    save_table(df, folder, 'du_lieu_da_xu_ly', index=False)
    meta = {'so_dong': len(raw), 'so_cot_goc': raw.shape[1], 'so_cot_sau_xu_ly': df.shape[1],
            'dong_trung_du_giu_lan_dau': int(raw.duplicated().sum()),
            'so_dong_pdays_999': int((raw.pdays == 999).sum()),
            'so_dong_pdays_hop_le': int(df.pdays_thuc_te.notna().sum()),
            'quy_tac': 'Giữ unknown, dòng trùng và ngoại lệ; không ghi đè dữ liệu gốc.'}
    (folder / 'nhat_ky_xu_ly.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return df


def rate_chart(table, title, path, baseline):
    fig, ax = plt.subplots(figsize=(max(8, len(table) * .8), 5.5))
    bars = ax.bar(table.index.astype(str), table.ty_le_dang_ky_pct, color='#458c94')
    for bar, (_, row) in zip(bars, table.iterrows()):
        ax.annotate(f'{row.ty_le_dang_ky_pct:.2f}%\nn={int(row.so_quan_sat):,}',
                    (bar.get_x()+bar.get_width()/2, bar.get_height()),
                    ha='center', va='bottom', fontsize=8, xytext=(0, 3), textcoords='offset points')
    ax.axhline(baseline, color='#b14439', linestyle='--', label=f'Tỷ lệ chung: {baseline:.2f}%')
    ax.set(title=title, ylabel='Tỷ lệ đăng ký (%)', xlabel=table.index.name)
    ax.set_ylim(0, max(float(table.ty_le_dang_ky_pct.max()), baseline) * 1.28)
    ax.tick_params(axis='x', rotation=35); ax.legend(); fig.tight_layout()
    fig.savefig(path, dpi=180); plt.close(fig)


# CHƯƠNG 3: Đặc điểm khách hàng.
def chapter3(df, out):
    folder = out / 'chuong_3'; folder.mkdir(exist_ok=True)
    baseline = df.dang_ky.mean()*100
    overall = df.y.value_counts().reindex(['no', 'yes']).to_frame('so_quan_sat')
    overall['ty_le_pct'] = overall.so_quan_sat / len(df)*100
    save_table(overall, folder, 'tong_quan_dang_ky')
    ax = overall.so_quan_sat.plot.bar(color=['#a4afb3', '#458c94'], rot=0)
    ax.set(title='Kết quả đăng ký tiền gửi', xlabel='Kết quả y', ylabel='Số quan sát')
    ax.figure.tight_layout(); ax.figure.savefig(folder/'hinh_3_1_ket_qua.png', dpi=180); plt.close(ax.figure)
    fig, ax = plt.subplots(); ax.hist(df.age, bins=25, color='#458c94', edgecolor='white')
    ax.set(title='Phân bố tuổi', xlabel='Tuổi (năm)', ylabel='Số quan sát')
    fig.tight_layout(); fig.savefig(folder/'hinh_3_2_phan_bo_tuoi.png', dpi=180); plt.close(fig)
    tables = {}
    for i, (col, title) in enumerate([('nhom_tuoi', 'Nhóm tuổi'), ('job', 'Nghề nghiệp'),
                                   ('marital', 'Tình trạng hôn nhân'), ('education', 'Học vấn'),
                                   ('housing', 'Vay mua nhà'), ('loan', 'Vay cá nhân')], 1):
        order = AGE_LABELS if col == 'nhom_tuoi' else None
        t = group_stats(df, col, order, sort=col in ['job', 'education'])
        tables[col] = t
        save_table(t, folder, f'bang_3_{i}_{col}')
        rate_chart(t, f'Tỷ lệ đăng ký theo {title.lower()}', folder/f'ty_le_{col}.png', baseline)
    save_table(df.groupby('y')[['age']].agg(['count', 'mean', 'median', 'std', 'min', 'max']), folder, 'tuoi_theo_y')
    return tables


# CHƯƠNG 4: Hoạt động liên hệ và lịch sử.
def chapter4(df, out):
    folder = out / 'chuong_4'; folder.mkdir(exist_ok=True)
    tables = {}
    for i, (col, order) in enumerate([('month', MONTHS), ('day_of_week', DAYS),
                 ('nhom_so_lan_lien_he', CALL_LABELS), ('contact', None),
                 ('co_lich_su', ['Không có lịch sử', 'Có lịch sử']),
                 ('poutcome', ['success', 'failure', 'nonexistent'])], 1):
        t = group_stats(df, col, order); tables[col] = t
        save_table(t, folder, f'bang_4_{i}_{col}')
        rate_chart(t, f'Tỷ lệ đăng ký theo {col}', folder/f'ty_le_{col}.png', df.dang_ky.mean()*100)
    valid = df[df.pdays_thuc_te.notna()]
    pdays = valid.pdays_thuc_te.describe().to_frame('gia_tri')
    pdays.loc['so_dang_ky', 'gia_tri'] = valid.dang_ky.sum()
    pdays.loc['ty_le_dang_ky_pct', 'gia_tri'] = valid.dang_ky.mean()*100
    save_table(pdays, folder, 'pdays_chi_tren_gia_tri_hop_le')
    save_table(df.groupby('y')[['campaign', 'duration']].agg(['count', 'mean', 'median', 'std', 'min', 'max']), folder, 'campaign_duration_theo_y')
    fig, ax = plt.subplots()
    ax.bar(['Không đăng ký', 'Đăng ký'], df.groupby('y').duration.median().reindex(['no', 'yes']), color='#458c94')
    ax.set(title='Trung vị thời lượng theo kết quả', ylabel='Thời lượng (giây)')
    fig.tight_layout(); fig.savefig(folder/'duration_trung_vi.png', dpi=180); plt.close(fig)
    for col in ['duration', 'campaign']:
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].hist(df[col], bins=50, color='#458c94'); ax[0].set(xlabel=col, ylabel='Số quan sát', title='Phân phối đầy đủ')
        ax[1].boxplot([df.loc[df.y == k, col] for k in ['no', 'yes']])
        ax[1].set_xticks([1, 2], ['no', 'yes']); ax[1].set(xlabel='y', ylabel=col, title='Phân phối theo kết quả')
        fig.tight_layout(); fig.savefig(folder/f'phan_phoi_{col}.png', dpi=180); plt.close(fig)
    # pdays dùng cột hợp lệ; không tính tương quan trực tiếp trên mã 999.
    cols = [c for c in NUMERIC if c != 'pdays'] + ['pdays_thuc_te', 'dang_ky']
    corrs = []
    for col in cols[:-1]:
        pair = df[[col, 'dang_ky']].dropna()
        corrs.append({'bien': col, 'so_quan_sat': len(pair), 'pearson_voi_dang_ky': pair[col].corr(pair.dang_ky)})
    save_table(pd.DataFrame(corrs), folder, 'tuong_quan_voi_dang_ky', index=False)
    return tables


# CHƯƠNG 5: Tổng hợp bằng số tính lại, không hard-code kết quả.
def chapter5(df, customer, campaign, out):
    folder = out / 'chuong_5'; folder.mkdir(exist_ok=True)
    choices = [('Tuổi 60+', customer['nhom_tuoi'].loc['60+']),
               ('Student', customer['job'].loc['student']), ('Retired', customer['job'].loc['retired']),
               ('Single', customer['marital'].loc['single']),
               ('University.degree', customer['education'].loc['university.degree']),
               ('Admin.', customer['job'].loc['admin.'])]
    segments = pd.DataFrame([dict(nhom=name, **row.to_dict()) for name, row in choices])
    save_table(segments, folder, 'nhom_xem_xet_thu_nghiem', index=False)
    baseline = df.dang_ky.mean()*100
    lines = ['# Chương 5 — Tổng hợp, đề xuất và kết luận', '',
             f'Tổng số quan sát: {len(df):,}; số đăng ký: {df.dang_ky.sum():,}; tỷ lệ chung: {baseline:.2f}%.', '',
             '## Đặc điểm khách hàng']
    for name, row in choices:
        lines.append(f'- {name}: {int(row.so_dang_ky):,}/{int(row.so_quan_sat):,}, tỷ lệ {row.ty_le_dang_ky_pct:.2f}%.')
    lines += ['', '## Hoạt động liên hệ và lịch sử']
    for col, table in campaign.items():
        best = table.ty_le_dang_ky_pct.idxmax(); row = table.loc[best]
        lines.append(f'- {col}: nhóm có tỷ lệ cao nhất là {best}, {row.ty_le_dang_ky_pct:.2f}% (n={int(row.so_quan_sat):,}).')
    lines += ['', '## Đề xuất theo tiểu luận',
              '- Xem xét thử nghiệm nhóm tuổi 60+, student, retired, single và university.degree; cân nhắc quy mô nhóm.',
              '- Đánh giá cả số đăng ký và tỷ lệ; không suy ra kết quả của phân khúc kết hợp từ từng đặc điểm riêng.',
              '- Thử nghiệm cellular và lịch gọi trong điều kiện tương đương, có nhóm so sánh.',
              '- Theo dõi số lần gọi, phản hồi; kiểm chứng quy tắc giảm tần suất trước khi áp dụng rộng.',
              '- Phân nhóm chăm sóc theo lịch sử và kết quả trước; pdays=999 không là số ngày thực tế.',
              '- Duration dùng đánh giá sau cuộc gọi; không dùng để chọn khách hàng trước cuộc gọi.', '',
              '## Hạn chế và hướng phát triển',
              'Phân tích mô tả không chứng minh nhân quả. Dữ liệu lịch sử của một ngân hàng không mặc nhiên đại diện thị trường khác. '
              'Giữ unknown và dòng trùng theo Chương 2. Nhóm ít quan sát cần diễn giải thận trọng. '
              'Không có chi phí, giá trị tiền gửi, lợi nhuận để tính ROI. '
              'Thử nghiệm chiến dịch mới, bổ sung dữ liệu chi phí và thống kê trực tiếp phân khúc kết hợp là hướng tiếp theo. '
              'Logistic Regression là phần mở rộng chưa triển khai trong tiểu luận.']
    (folder/'tong_hop_de_xuat.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=BASE/'data'/'bank-additional-full.csv')
    parser.add_argument('--output', type=Path, default=BASE/'outputs')
    args = parser.parse_args()
    if not args.data.is_file():
        parser.error(f'Không tìm thấy dữ liệu: {args.data}. Dùng --data để chỉ định CSV gốc.')
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    raw = read_data(args.data)
    chapter1(out); df = chapter2(raw, out)
    customers = chapter3(df, out); campaigns = chapter4(df, out)
    chapter5(df, customers, campaigns, out)
    manifest = {'input': args.data.name, 'sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(),
                'pandas': pd.__version__, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
                'so_quan_sat': len(df), 'so_dang_ky': int(df.dang_ky.sum()),
                'ty_le_dang_ky_pct': df.dang_ky.mean()*100}
    (out/'thong_tin_lan_chay.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Hoàn tất Chương 1–5: {len(df):,} quan sát; {df.dang_ky.sum():,} đăng ký ({df.dang_ky.mean()*100:.2f}%).')
    print(f'Kết quả: {out}')

if __name__ == '__main__':
    main()
