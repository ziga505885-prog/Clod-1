from .model import ConditionCategory
ALLOWED_CATEGORIES={c.value for c in ConditionCategory}
SPECIAL_RULES={"address":{"mark":"blue","explanation":False,"scope":"all headings and document"},"date":{"mark":"blue","explanation":False,"scope":"all document"}}
def valid_category(value:str)->bool: return value in ALLOWED_CATEGORIES
