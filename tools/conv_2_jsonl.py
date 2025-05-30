import pandas as pd
import sys

# 读取CSV文件
df = pd.read_csv(sys.argv[1])
print(len(df))

# 选择需要的字段（例如 'field1', 'field2'）
#selected_fields = ['field1', 'field2']  # 根据需要修改字段名称
#df = df[selected_fields]

# 将DataFrame写入JSONL文件，并确保中文不被转义
df.to_json('output.jsonl', orient='records', lines=True, force_ascii=False)

# 后处理，替换所有的 \/ 为 /
with open('output.jsonl', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复路径中的转义斜杠
content = content.replace(r'\/', '/')

# 将修正后的内容重新写回到文件
with open('output_fixed.jsonl', 'w', encoding='utf-8') as f:
    f.write(content)

