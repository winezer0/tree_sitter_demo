from enum import Enum


class AuditStatus(Enum):
    """验证状态枚举"""
    TRUE = 'TRUE'
    FALSE = 'FALSE'
    UNKNOWN = 'UNKNOWN'

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls]

    @classmethod
    def choicesKnown(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls if member != cls.UNKNOWN]

    @classmethod
    def format(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member.value
        print(f"AuditStatus 发现非预期格式:{string} 返回 {cls.UNKNOWN.value} 允许格式:{cls.choices()}")
        return cls.UNKNOWN.value

    @classmethod
    def toType(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member
        return string

    @classmethod
    def size(cls):
        return len(cls.choices())

class SeverityLevel(Enum):
    """风险级别枚举"""
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    UNKNOWN = 'UNKNOWN'

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls]

    @classmethod
    def choicesKnown(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls if member != cls.UNKNOWN]

    @classmethod
    def format(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member.value
        print(f"SeverityLevel 发现非预期格式:{string} 返回{cls.UNKNOWN.value} 允许格式:{cls.choices()}")
        return cls.UNKNOWN.value

    @classmethod
    def toType(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member
        return string

    @classmethod
    def size(cls):
        return len(cls.choices())

class VerifyStatus(Enum):
    """风险级别枚举"""
    # 已弃用 HIGH = 'HIGH' MEDIUM = 'MEDIUM' LOW = 'LOW'  NONE = 'NONE'  UNKNOWN = 'UNKNOWN'
    TEN = "10"
    NINE = "9"
    EIGHT = "8"
    SEVEN = "7"
    SIX = "6"
    FIVE = "5"
    FOUR = "4"
    THREE = "3"
    TWO = "2"
    ONE = "1"
    ZERO = "0"
    UNKNOWN = "-1"

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls]

    @classmethod
    def choicesKnown(cls):
        """返回所有可选值"""
        return [str(member.value) for member in cls if member != cls.UNKNOWN]

    @classmethod
    def format(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member.value
        print(f"VerifyStatus 发现非预期格式:{string} 返回{cls.UNKNOWN.value} 允许格式:{cls.choices()}")
        return cls.UNKNOWN.value

    @classmethod
    def toType(cls, string) -> str:
        for member in cls:
            if str(member.value).lower() == str(string).lower():
                return member
        return string

    @classmethod
    def choicesShort(cls):
        """返回所有可选值"""
        return f"{cls.ZERO}-{cls.NINE}"

    @classmethod
    def size(cls):
        return len(cls.choices())


if __name__ == '__main__':
    print(type(SeverityLevel.toType('MEDIUM')))  # <enum 'SeverityLevel'>
    print(isinstance(SeverityLevel.toType('MEDIUM'), Enum))  # True
