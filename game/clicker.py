"""Модуль с интерфейсом и реализацией кликера"""

import random
from abc import ABC, abstractmethod


class AbstractClicker(ABC):
    """Интерфейс для кликера"""

    @abstractmethod
    def __init__(self) -> None:
        """Абстрактный метод инициализации"""
        raise NotImplementedError

    @abstractmethod
    def click(self) -> None:
        """Абстрактный метод клика для накапливания монет"""
        raise NotImplementedError

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Абстрактное свойство для доступа к количеству монет за клик"""
        raise NotImplementedError


class SimpleRandomClicker(AbstractClicker):
    """Кликер, который за клик приносит случайное число монет из диапазона"""

    def __init__(
        self,
        min_income: int,
        max_income: int,
        rng: random.Random | None = None,
    ) -> None:
        """
        Инициализация кликера

        :param min_income: минимальный доход за клик
        :param max_income: максимальный доход за клик
        :param rng: генератор случайных чисел (удобно подменять в тестах)
        :raises ValueError: если границы дохода заданы некорректно
        """
        if min_income < 0 or min_income > max_income:
            raise ValueError(
                'Нужно 0 <= min_income <= max_income, '
                f'получено {min_income} и {max_income}'
            )
        self._min_income = min_income
        self._max_income = max_income
        self._rng = rng or random.Random()
        self._income_per_click = 0
        self.total_clicks = 0

    def click(self) -> None:
        """Клик: определяет случайный доход из диапазона"""
        self._income_per_click = self._rng.randint(
            self._min_income, self._max_income
        )
        self.total_clicks += 1

    @property
    def income_per_click(self) -> int:
        """
        Свойство для доступа к количеству монет за последний клик

        :return: количество монет (0, если кликов ещё не было)
        """
        return self._income_per_click
