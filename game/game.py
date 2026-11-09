"""Модуль с интерфейсом и реализацией класса игры"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any

from .clicker import AbstractClicker
from .exceptions import (
    ActionCancelled,
    EmptyBag,
    InvalidChoice,
    NotEnoughMoney,
    TamagochiIsGone,
)
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi

# Функция выбора: получает заголовок и список вариантов,
# возвращает индекс выбранного варианта
Chooser = Callable[[str, Sequence[str]], int]


def choose_in_console(title: str, options: Sequence[str]) -> int:
    """
    Спрашивает у игрока в консоли, какой вариант он выбирает

    :param title: заголовок меню
    :param options: варианты для выбора
    :return: индекс выбранного варианта (с нуля)
    :raises ActionCancelled: если игрок выбрал «0. Назад»
    :raises InvalidChoice: если введён несуществующий номер
    """
    print(title)
    for number, option in enumerate(options, start=1):
        print(f'{number}. {option}')
    print('0. Назад')
    answer = input('Ваш выбор: ').strip()
    if answer == '0':
        raise ActionCancelled('Действие отменено')
    if not answer.isdigit() or not 1 <= int(answer) <= len(options):
        raise InvalidChoice(f'Нет варианта «{answer}»')
    return int(answer) - 1


class AbstractGame(ABC):
    """Интерфейс для логики игры"""

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine]
    ):
        """
        Абстрактный метод инициализации класса игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды
        :param all_medicine: все доступные варианты лекарств
        """
        raise NotImplementedError

    @abstractmethod
    def work(self) -> int:
        """
        Абстрактный метод для логики действия "работа

        :return: количество заработанных монет
        """
        raise NotImplementedError

    @abstractmethod
    def buy_food(self) -> None:
        """Абстрактный метод для покупки еды"""
        raise NotImplementedError

    @abstractmethod
    def buy_medicine(self) -> None:
        """Абстрактный метод для покупки лекарства"""
        raise NotImplementedError

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Абстрактный метод для кормления тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Абстрактный метод для лечения тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest_tamagochi(self):
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def play_with_tamagochi(self):
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Абстрактный метод для получения статуса (всех характеристик) тамагочи

        :return: словарь со всеми характеристиками тамагочи
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """
        Абстрактное свойство для доступа к сумке с едой

        :return: список с имеющимися (купленными) объектами еды
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """
        Абстрактное свойство для доступа к сумке с лекарствами

        :return: список с имеющимися (купленными) объектами лекарств
        """
        raise NotImplementedError


class SimpleGame(AbstractGame):
    """
    Игра «Тамагочи-кликер».

    Игрок зарабатывает монеты на работе, покупает еду и лекарства
    в сумку и ухаживает за тамагочи. Каждое действие с тамагочи — это ход:
    после него тамагочи проживает ещё один тик (update).
    Игра заканчивается, когда тамагочи погибает
    """

    DEFAULT_START_COINS = 50

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
        start_coins: int = DEFAULT_START_COINS,
        chooser: Chooser = choose_in_console,
    ) -> None:
        """
        Инициализация игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды (магазин)
        :param all_medicine: все доступные варианты лекарств (аптека)
        :param start_coins: стартовое количество монет
        :param chooser: функция выбора варианта из списка
            (по умолчанию — ввод из консоли)
        """
        self.tamagochi = tamagochi
        self._clicker = clicker
        self._shop_food = list(all_food)
        self._shop_medicine = list(all_medicine)
        self._coins = start_coins
        self._choose = chooser
        self._food_bag: list[Food] = []
        self._medicine_bag: list[Medicine] = []

    @property
    def coins(self) -> int:
        """
        Свойство для доступа к количеству монет игрока

        :return: количество монет
        """
        return self._coins

    @property
    def is_over(self) -> bool:
        """
        Проверяет, закончена ли игра

        :return: True если тамагочи погиб, иначе False
        """
        return not self.tamagochi.is_alive()

    @property
    def food(self) -> list[Food]:
        """
        Свойство для доступа к сумке с едой

        :return: копия списка купленной еды (изменения не затронут сумку)
        """
        return list(self._food_bag)

    @property
    def medicine(self) -> list[Medicine]:
        """
        Свойство для доступа к сумке с лекарствами

        :return: копия списка купленных лекарств
        """
        return list(self._medicine_bag)

    def work(self) -> int:
        """
        Работа: кликер приносит монеты

        :return: количество заработанных монет
        :raises TamagochiIsGone: если игра уже закончена
        """
        self._ensure_not_over()
        self._clicker.click()
        income = self._clicker.income_per_click
        self._coins += income
        return income

    def buy_food(self) -> None:
        """
        Выбор еды в магазине и покупка её в сумку

        :raises TamagochiIsGone: если игра уже закончена
        :raises NotEnoughMoney: если не хватает монет
        :raises ActionCancelled: если игрок отменил покупку
        :raises InvalidChoice: если выбран несуществующий товар
        """
        self._ensure_not_over()
        index = self._choose('Магазин еды:', self._labels(self._shop_food))
        product = self._shop_food[index]
        self._pay(product.price)
        self._food_bag.append(replace(product))

    def buy_medicine(self) -> None:
        """
        Выбор лекарства в аптеке и покупка его в сумку.
        Покупается новая упаковка — со всеми использованиями

        :raises TamagochiIsGone: если игра уже закончена
        :raises NotEnoughMoney: если не хватает монет
        :raises ActionCancelled: если игрок отменил покупку
        :raises InvalidChoice: если выбран несуществующий товар
        """
        self._ensure_not_over()
        index = self._choose('Аптека:', self._labels(self._shop_medicine))
        product = self._shop_medicine[index]
        self._pay(product.price)
        self._medicine_bag.append(replace(product, uses=0))

    def feed_tamagochi(self) -> None:
        """
        Кормление тамагочи едой из сумки. Это ход

        :raises TamagochiIsGone: если игра уже закончена
        :raises EmptyBag: если в сумке нет еды
        :raises ActionCancelled: если игрок отменил действие
        :raises InvalidChoice: если выбрана несуществующая еда
        """
        self._ensure_not_over()
        if not self._food_bag:
            raise EmptyBag('В сумке нет еды. Сначала купите её')
        index = self._choose('Чем покормить?', self._labels(self._food_bag))
        self.tamagochi.feed(self._food_bag[index])
        self._food_bag.pop(index)
        self._next_turn()

    def heal_tamagochi(self) -> None:
        """
        Лечение тамагочи лекарством из сумки. Это ход.
        Закончившееся лекарство убирается из сумки

        :raises TamagochiIsGone: если игра уже закончена
        :raises EmptyBag: если в сумке нет лекарств
        :raises ActionCancelled: если игрок отменил действие
        :raises InvalidChoice: если выбрано несуществующее лекарство
        """
        self._ensure_not_over()
        if not self._medicine_bag:
            raise EmptyBag('В сумке нет лекарств. Сначала купите их')
        index = self._choose(
            'Чем лечить?', self._labels(self._medicine_bag)
        )
        medicine = self._medicine_bag[index]
        self.tamagochi.heal(medicine)
        if medicine.is_empty():
            self._medicine_bag.pop(index)
        self._next_turn()

    def rest_tamagochi(self) -> None:
        """
        Отдых тамагочи. Это ход

        :raises TamagochiIsGone: если игра уже закончена
        """
        self._ensure_not_over()
        self.tamagochi.rest()
        self._next_turn()

    def play_with_tamagochi(self) -> None:
        """
        Игра с тамагочи. Это ход

        :raises TamagochiIsGone: если игра уже закончена
        :raises TamagochiIsTired: если у тамагочи не хватает энергии
        """
        self._ensure_not_over()
        self.tamagochi.play()
        self._next_turn()

    def get_status(self) -> dict[str, Any]:
        """
        Получение статуса игры

        :return: словарь со всеми характеристиками тамагочи
            и количеством монет (ключ coins)
        """
        return {**self.tamagochi.status, 'coins': self._coins}

    def _pay(self, price: int) -> None:
        """
        Списывает монеты за покупку

        :param price: стоимость покупки
        :raises NotEnoughMoney: если монет не хватает
        """
        if price > self._coins:
            raise NotEnoughMoney(
                f'Недостаточно монет: нужно {price}, а у вас {self._coins}'
            )
        self._coins -= price

    def _next_turn(self) -> None:
        """Завершает ход: тамагочи проживает ещё один тик"""
        self.tamagochi.update()

    def _ensure_not_over(self) -> None:
        """
        Проверяет, что игра продолжается

        :raises TamagochiIsGone: если тамагочи погиб и игра окончена
        """
        if self.is_over:
            raise TamagochiIsGone('Игра окончена: тамагочи погиб')

    @staticmethod
    def _labels(items: Sequence[Food | Medicine]) -> list[str]:
        """
        Готовит подписи товаров для меню выбора

        :param items: еда или лекарства
        :return: список строковых описаний
        """
        return [repr(item) for item in items]
