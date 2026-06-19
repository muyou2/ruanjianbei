# Python 程序设计与数据分析：主题化学习手册

本文档为“智学方舟”项目原创示例课程资料，不声称摘录自任何高校教材。每个主题均包含解释、代码、常见错误和练习建议。

## 1. Python 基础语法

知识点解释：Python 使用缩进表示代码块，变量在赋值时建立，表达式可以组合运算符和函数调用。

```python
name = "小林"
hours = 2
print(f"{name} 今天学习 {hours} 小时")
```

常见错误：混用全角标点、缩进不一致、在变量赋值前使用变量。练习建议：编写一个输入姓名和学习时间并输出计划的小程序。

## 2. 数据类型与容器

知识点解释：常用标量类型有整数、浮点数、字符串和布尔值；列表有顺序且可修改，元组不可修改，字典保存键值映射，集合用于去重。

```python
student = {"name": "小林", "weak_points": ["函数", "Pandas"]}
student["weak_points"].append("缺失值")
```

常见错误：把字典键当作列表索引、修改元组、使用可变对象作为字典键。练习建议：用字典保存一名学生的三次测验成绩并计算平均值。

## 3. 条件语句与循环

知识点解释：`if/elif/else` 根据条件选择分支，`for` 适合遍历已知序列，`while` 适合条件驱动的重复。

```python
scores = [58, 72, 91]
for score in scores:
    label = "达标" if score >= 60 else "需复习"
    print(score, label)
```

常见错误：循环边界多一次或少一次、忘记更新 while 条件、把赋值写成比较。练习建议：筛选低于 60 分的成绩并记录索引。

## 4. 函数设计

知识点解释：函数将输入、处理过程和输出封装起来。参数负责接收数据，`return` 返回结果；单一职责有利于测试和复用。

```python
def pass_rate(scores: list[float], line: float = 60) -> float:
    passed = sum(score >= line for score in scores)
    return passed / len(scores) if scores else 0.0
```

常见错误：忘记 return、使用可变默认参数、函数内部意外修改外部列表。练习建议：把成绩清洗、统计和输出拆成三个函数。

## 5. 异常处理与调试

知识点解释：异常用于描述运行时错误。应捕获能够处理的具体异常，并保留足够上下文，不能用空的 `except` 隐藏所有问题。

```python
try:
    score = float(input("成绩："))
except ValueError:
    print("请输入数字")
```

常见错误：捕获范围过大、只看错误第一行、不阅读堆栈最后一行。练习建议：为 CSV 读取程序处理文件不存在和数值格式错误。

## 6. 文件读写

知识点解释：使用 `with` 管理文件可以保证资源释放。文本编码应明确指定，结构化数据可使用 CSV 或 JSON。

```python
from pathlib import Path
text = Path("note.txt").read_text(encoding="utf-8")
```

常见错误：硬编码绝对路径、遗漏编码、忘记关闭文件。练习建议：读取学习日志并统计每个主题出现次数。

## 7. 面向对象基础

知识点解释：类描述属性和行为，对象是类的实例。面向对象适合表达有稳定状态和操作的业务实体。

```python
class Student:
    def __init__(self, name: str):
        self.name = name
        self.scores = []

    def add_score(self, score: float):
        self.scores.append(score)
```

常见错误：忘记 `self`、把实例属性误写成类属性、为了简单脚本过度设计类。练习建议：实现学生对象并计算最近一次成绩变化。

## 8. NumPy 数组计算

知识点解释：NumPy 数组支持向量化、布尔索引和广播。执行运算前必须理解数组形状。

```python
import numpy as np
scores = np.array([58, 72, 91])
normalized = (scores - scores.mean()) / scores.std()
```

常见错误：形状不兼容、整数数组保存浮点结果、把逐元素乘法误认为矩阵乘法。练习建议：计算一组成绩的标准分并筛选高于平均值的记录。

## 9. Pandas Series 和 DataFrame

知识点解释：Series 是带索引的一维数据，DataFrame 是二维表格。列通常表示变量，行表示观测。

```python
import pandas as pd
df = pd.DataFrame({"name": ["甲", "乙"], "score": [82, 76]})
print(df["score"].mean())
```

常见错误：混淆 `df["col"]` 与 `df[["col"]]`、链式赋值、误解索引标签。练习建议：创建课程成绩表并新增是否达标列。

## 10. 数据读取与保存

知识点解释：读取数据后应先检查编码、分隔符、列名、数据类型和行数，保存时明确是否保留索引。

```python
df = pd.read_csv("scores.csv", encoding="utf-8")
df.to_csv("clean_scores.csv", index=False, encoding="utf-8-sig")
```

常见错误：分隔符错误导致只有一列、保存额外索引列、把数字列读成字符串。练习建议：读取 CSV，打印 `head()`、`info()` 和形状。

## 11. 缺失值处理

知识点解释：删除、填充或保留缺失值必须结合字段含义、缺失比例和缺失机制。不能默认所有空值都是错误。

```python
missing = df.isna().sum()
df["age"] = df["age"].fillna(df["age"].median())
```

常见错误：不检查比例就删除整行、均值填充类别字段、填充后不验证。练习建议：比较删除和中位数填充对样本量与均值的影响。

## 12. 重复值处理

知识点解释：重复记录应先确定业务主键和重复定义。完全重复与同一订单号的冲突记录不是同一问题。

```python
duplicate_count = df.duplicated(subset=["student_id", "exam"]).sum()
df = df.drop_duplicates(subset=["student_id", "exam"], keep="last")
```

常见错误：无主键地删除所有重复、没有记录保留规则、去重后不检查行数。练习建议：为重复成绩记录设计“保留最新时间”的规则。

## 13. 数据筛选与排序

知识点解释：布尔条件用于筛选行，`sort_values` 用于排序。多个条件必须分别加括号。

```python
risk = df[(df["score"] < 60) & (df["attempts"] >= 2)]
risk = risk.sort_values("score")
```

常见错误：使用 Python 的 `and/or` 连接 Series、忘记括号、排序后误以为索引自动重排。练习建议：筛选多次练习仍未达标的知识点。

## 14. 分组聚合

知识点解释：`groupby` 按类别拆分数据，再执行统计并合并结果。统计口径必须清晰。

```python
summary = df.groupby("topic", as_index=False).agg(
    average_score=("score", "mean"),
    students=("student_id", "nunique"),
)
```

常见错误：把记录数当作学生数、聚合后索引结构不清、忽略缺失分组。练习建议：统计各主题平均成绩、人数和不及格率。

## 15. 数据可视化基础

知识点解释：图表应服务于问题。类别比较使用条形图，时间变化使用折线图，数值关系可使用散点图。

```python
summary.plot(kind="bar", x="topic", y="average_score", legend=False)
```

常见错误：坐标轴没有单位、颜色过多、用截断坐标夸大差异。练习建议：为各主题平均成绩制作图表并写出一句证据化结论。

## 16. 综合项目：学生成绩数据分析

知识点解释：项目包含问题定义、数据检查、清洗、统计、可视化、结论和限制。

```python
scores = pd.read_csv("student_scores.csv")
report = scores.groupby("course")["score"].agg(["mean", "median", "count"])
```

常见错误：把相关性解释为因果、忽略补考记录、没有说明缺失成绩。练习建议：识别薄弱课程，比较不同专业成绩，并说明样本限制。

## 17. 综合项目：电商订单数据分析

知识点解释：订单分析常关注销售额、客单价、复购、品类和时间趋势，必须先明确取消订单和退款口径。

```python
orders = pd.read_csv("orders.csv")
orders["revenue"] = orders["quantity"] * orders["unit_price"]
daily = orders.groupby("order_date", as_index=False)["revenue"].sum()
```

常见错误：重复订单导致销售额翻倍、把退款计入收入、日期仍是字符串。练习建议：完成订单清洗、月度销售趋势、热销品类和异常订单说明。

