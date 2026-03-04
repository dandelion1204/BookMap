import os
import re
import pandas as pd
import glob
from datetime import datetime, timezone, timedelta
from django.db import transaction
from django.conf import settings
from .models import SchoolTexbook

def clean_val(val, length=None):
    """處理儲存格：去換行、去空格、限制長度"""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    text = str(val).replace('\n', '').strip()
    return text[:length] if length else text

def sync_excel_to_db():
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    search_pattern = os.path.join(data_dir, "*國小*.xlsx")
    matched_files = glob.glob(search_pattern)

    if matched_files:
        excel_path = matched_files[0]
        print(f"成功找到 Excel 檔案：{excel_path}")
    else:
        print("錯誤：在 data 資料夾中找不到包含『國小』關鍵字的 Excel 檔案")
        return False

    try:
        xl = pd.ExcelFile(excel_path)
        all_new_records = []

        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)

            if df.shape[0] < 4: continue
            row_4_full_text = "".join(df.iloc[3].fillna('').astype(str))
            if '版本表' not in row_4_full_text: continue

            district = re.sub(r'\d+', '', sheet_name)
            level = "國小"

            # 定義年級清單
            if level == "國小":
                valid_grades = ['一', '二', '三', '四', '五', '六']
            else:
                valid_grades = ['七', '八', '九', '一', '二', '三']

            data_start_idx = 5

            def process_subset(sub_df):
                sub_df.columns = ['school', 'grade', 'chinese', 'math', 'science', 'social', 'english']
                subset_records = []
                last_school = ""

                grade_map = {
                            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                            '七': 7, '八': 8, '九': 9
                }

                for _, row in sub_df.iterrows():
                    raw_school = clean_val(row['school'])
                    raw_grade = clean_val(row['grade'])
                    g_num = grade_map.get(raw_grade, 0) # 找不到就給 0

                    if raw_grade in valid_grades:
                        # --- 核心修正點 ---
                        # 如果是該校的第一個年級 (如 '一')
                        if raw_grade == valid_grades[0]:
                            if raw_school != "":
                                # 有新校名，更新追蹤標籤
                                last_school = raw_school
                            else:
                                # 沒校名卻出現 '一'，說明進入了空白範例區，清除標籤
                                last_school = ""

                        # 只有在校名標籤有效時，才存入資料
                        if last_school != "":
                            subset_records.append(SchoolTexbook(
                                district=clean_val(district, 10),
                                level=clean_val(level, 10),
                                school=last_school[:10],
                                grade=raw_grade[:5],
                                grade_num=g_num,  # 存入數字 1, 2, 3...
                                sub_chinese=clean_val(row['chinese'], 20),
                                sub_math=clean_val(row['math'], 20),
                                sub_science=clean_val(row['science'], 20),
                                sub_social=clean_val(row['social'], 20),
                                sub_english=clean_val(row['english'], 20),
                            ))
                return subset_records

            # 處理左半
            all_new_records.extend(process_subset(df.iloc[data_start_idx:, 0:7].copy()))
            # 處理右半
            if df.shape[1] >= 15:
                all_new_records.extend(process_subset(df.iloc[data_start_idx:, 8:15].copy()))

        # 4. 寫入與回饋
        if all_new_records:
            with transaction.atomic():
                tw_tz = timezone(timedelta(hours=8))
                tw_now = datetime.now(tw_tz)
                print('CurrentTime:',tw_now)
                deleted_count, _ = SchoolTexbook.objects.filter(level='國小').delete()
                print(f"成功清理：刪除 {deleted_count} 筆舊資料。")

                SchoolTexbook.objects.bulk_create(all_new_records)
                print(f"成功更新：寫入 {len(all_new_records)} 筆新資料。")

                #tracker.last_modified = current_mtime
                #tracker.save()
            return True

    except Exception as e:
        print(f"執行錯誤: {e}")
        return False

    return False

def sync_excel_to_db_jr():
    # 讀取 Excel
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    search_pattern = os.path.join(data_dir, "*國中*.xlsx")
    matched_files = glob.glob(search_pattern)

    if matched_files:
        excel_path = matched_files[0]
        print(f"成功找到 Excel 檔案：{excel_path}")
    else:
        print("錯誤：在 data 資料夾中找不到包含『國中』關鍵字的 Excel 檔案")
        return False

    instances = []

    # 年級與數字對照
    grade_info = [
        {'name': '一', 'num': 1, 'cols': [1, 2, 3, 4, 5]},   # 第一組 國英數自社
        {'name': '二', 'num': 2, 'cols': [6, 7, 8, 9, 10]},  # 第二組 國英數自社
        {'name': '三', 'num': 3, 'cols': [11, 12, 13, 14, 15]} # 第三組 國英數自社
    ]

    xls = pd.ExcelFile(excel_path)

    for sheet_name in xls.sheet_names:
        # 1. 擷取區域 (北桃/南桃)
        district = ""
        if "北桃" in sheet_name:
            district = "北桃"
        elif "南桃" in sheet_name:
            district = "南桃"
        else:
            continue

        # 2. 讀取資料：根據檔案，標題在第 4 列 (header=3)
        # 由於欄位名稱重複，pandas 會自動重新命名成 國文, 國文.1, 國文.2
        df = pd.read_excel(xls, sheet_name=sheet_name, header=3)

        # 3. 過濾掉底部的備註文字與空行
        footer_text = "此表僅供參考"
        df = df[~df.iloc[:, 0].astype(str).str.contains(footer_text)]
        df = df.dropna(subset=[df.columns[0]]) # 確保學校名稱不是空的

        for _, row in df.iterrows():
            school_name = str(row.iloc[0]).strip()

            # 針對三個年級分別建立資料
            for g in grade_info:
                # 取得該年級對應的五個學科
                # iloc[col_index] 確保精確抓到位置，不受欄位重名影響
                try:
                    item = SchoolTexbook(
                        district=district,
                        level='國中',
                        school=school_name,
                        grade=g['name'],
                        grade_num=g['num'],
                        sub_chinese=row.iloc[g['cols'][0]],
                        sub_english=row.iloc[g['cols'][1]],
                        sub_math=row.iloc[g['cols'][2]],
                        sub_science=row.iloc[g['cols'][3]],
                        sub_social=row.iloc[g['cols'][4]]
                    )
                    instances.append(item)
                except Exception as e:
                    print(f"處理 {school_name} {g['name']}年級時出錯: {e}")

    # 4. 批量寫入資料庫
    if instances:
        with transaction.atomic():
            tw_tz = timezone(timedelta(hours=8))
            tw_now = datetime.now(tw_tz)
            print('CurrentTime:',tw_now)
            deleted_count, _ = SchoolTexbook.objects.filter(level='國中').delete()
            print(f"成功清理：刪除 {deleted_count} 筆舊資料。")

            SchoolTexbook.objects.bulk_create(instances)
            print(f"成功更新：寫入 {len(instances)} 筆新資料。")
    else:
        print("未發現有效資料。")
