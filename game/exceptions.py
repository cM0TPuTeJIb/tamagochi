"""Модуль с исключениями"""


class GameException(Exception):
    """Базовое исключение игры, от него наследуются все остальные"""


class TamagochiIsGone(GameException):
    """Ошибка при смерти тамагочи"""


class NotEnoughMoney(GameException):
    """Ошибка когда не хватает монет для покупки"""


class EmptyBag(GameException):
    """Ошибка когда в сумке нет нужных предметов (еды или лекарств)"""


class MedicineIsEmpty(GameException):
    """Ошибка когда у лекарства закончились использования"""


class TamagochiIsTired(GameException):
    """Ошибка когда у тамагочи не хватает энергии для действия"""


class InvalidChoice(GameException):
    """Ошибка когда игрок выбрал несуществующий пункт меню"""


class ActionCancelled(GameException):
    """Игрок отменил действие"""
