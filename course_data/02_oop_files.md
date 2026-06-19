# 面向对象、文件与工程实践

## 类与对象

类用于描述一类对象共有的数据和行为，对象是类的实例。并非所有问题都需要类：当数据和行为需要长期保持一致、存在多个实例或需要清晰边界时，类更合适。

```python
from dataclasses import dataclass

@dataclass
class CourseProgress:
    topic: str
    minutes: int
    score: float = 0

    def passed(self) -> bool:
        return self.score >= 60
```

`dataclass` 可以自动生成初始化、表示和比较方法，适合数据对象。组合通常比深层继承更容易理解和测试。

## 文件处理

使用 `with` 管理文件能够确保资源被关闭。文本文件要明确编码。

```python
from pathlib import Path

path = Path("notes.txt")
content = path.read_text(encoding="utf-8")
path.write_text(content + "\n复习完成", encoding="utf-8")
```

CSV 适合二维表格数据，JSON 适合嵌套结构和接口传输。处理外部文件时必须考虑文件不存在、编码错误、字段缺失和数据类型异常。

## 模块与项目结构

把相关函数和类放入模块，通过包组织更大的项目。入口代码应放在：

```python
if __name__ == "__main__":
    main()
```

配置、业务逻辑和输入输出应尽量分离。密钥使用环境变量，不写入源代码和版本库。

## 测试思维

测试关注可观察行为。一个函数至少考虑：

- 典型输入；
- 空值与边界；
- 非法输入；
- 重复调用；
- 修复过的历史缺陷。

测试失败时先判断是实现错误、测试预期错误还是环境问题，不要为了“变绿”而删除有价值的断言。
