# импортирум библиотеки
from enum import Enum

# токен чат-бота
token = "1491880594:AAERR83VtLjon5j5FKkK1LcNpwwwGfPs9tQ"

# файл базы данных
db_file = 'database.vdb'

# перечисляем константы
class States(Enum):
    # начало работы с чат-ботом
    S_START = "0"

    # рейтинг или компания?
    S_RATING_OR_COMPANY = "1"

    # ввод названия компании или поля для рейтинга
    S_ENTER_RATING_OR_COMPANY = "2"