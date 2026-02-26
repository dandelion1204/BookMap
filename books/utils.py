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


    #current_mtime = os.path.getmtime(excel_path)
    #tracker, created = FileImportTracker.objects.get_or_create(
    #    file_name='Books.xlsx',
    #    defaults={'last_modified': 0}
    #)

    #if not created and tracker.last_modified == current_mtime:
    #    return False

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
                deleted_count, _ = SchoolTexbook.objects.all().delete()
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