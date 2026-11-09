"""Модуль с интерфейсом и реализациями класса тамагочи"""

import random
from abc import ABC, abstractmethod

from .exceptions import MedicineIsEmpty, TamagochiIsGone, TamagochiIsTired
from .models import Food, Medicine

MIN_STAT = 0
MAX_STAT = 100


def clamp(value: int, low: int = MIN_STAT, high: int = MAX_STAT) -> int:
    """
    Ограничивает значение показателя диапазоном

    :param value: исходное значение
    :param low: нижняя граница
    :param high: верхняя граница
    :return: значение, приведённое к отрезку [low, high]
    """
    return max(low, min(high, value))


class AbstractTamagochi(ABC):
    """Интерфейс логики тамагочи"""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """
        Абстрактный метод для кормления тамагочи

        :param food: объект еды для кормления
        """
        raise NotImplementedError

    @abstractmethod
    def play(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """
        Абстрактный метод для лечения тамагочи

        :param medicine: лекарство для лечения
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """
        Абстрактное свойство для доступа ко всем состояниям тамагочи

        :return: словарь со всеми состояниями тамагочи
        """
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Абстрактный метод для проверки жив ли тамагочи

        :return: True если жив, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def is_sick(self) -> bool:
        """
        Абстрактный метод для проверки, не заболел ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """
        Абстрактный метод для обновления состояний тамагочи.
        Должен использоваться после каждого взаимодействия с тамагочи
        """
        raise NotImplementedError


class SimpleTamagochi(AbstractTamagochi):
    """
    Тамагочи с показателями голода, усталости, энергии и здоровья.

    Все показатели лежат в диапазоне от 0 до 100:
    голод и усталость — чем больше, тем хуже;
    здоровье и энергия — чем больше, тем лучше.
    Когда здоровье опускается до нуля, тамагочи погибает.
    """

    # Изменения за один ход (update)
    HUNGER_PER_TICK = 5
    ENERGY_PER_TICK = 3
    FATIGUE_PER_TICK = 3

    # Пороги, после которых тамагочи теряет здоровье
    CRITICAL_HUNGER = 80
    CRITICAL_FATIGUE = 80
    STARVATION_DAMAGE = 10
    EXHAUSTION_DAMAGE = 5
    NO_ENERGY_DAMAGE = 5

    # Болезнь
    BASE_SICK_CHANCE = 0.05
    RISKY_SICK_CHANCE = 0.25
    RISKY_HUNGER = 60
    RISKY_FATIGUE = 60
    SICKNESS_DAMAGE = 7
    SICKNESS_FATIGUE = 5

    # Действия
    FEED_ENERGY_COST = 2
    OVEREAT_DAMAGE = 5
    PLAY_ENERGY_COST = 15
    PLAY_FATIGUE = 10
    PLAY_HUNGER = 10
    PLAY_HP_BONUS = 3
    REST_ENERGY = 30
    REST_FATIGUE = 30
    REST_HUNGER = 5
    SICK_REST_FACTOR = 2  # во столько раз хуже отдых во время болезни

    def __init__(
        self,
        name: str = 'Тамагочи',
        rng: random.Random | None = None,
    ) -> None:
        """
        Инициализация тамагочи

        :param name: имя питомца
        :param rng: генератор случайных чисел (удобно подменять в тестах)
        """
        self.name = name
        self._rng = rng or random.Random()
        self._hunger = 30
        self._fatigue = 0
        self._energy = 80
        self._hp = MAX_STAT
        self._sick = False

    def feed(self, food: Food) -> None:
        """
        Кормит тамагочи: голод падает, энергия немного тратится.
        Если тамагочи уже сыт, переедание отнимает здоровье

        :param food: объект еды для кормления
        :raises TamagochiIsGone: если тамагочи погиб
        """
        self._ensure_alive()
        if self._hunger == MIN_STAT:
            self._hp = clamp(self._hp - self.OVEREAT_DAMAGE)
        self._hunger = clamp(self._hunger - food.satiety)
        self._energy = clamp(self._energy - self.FEED_ENERGY_COST)

    def play(self) -> None:
        """
        Игра с тамагочи: тратит энергию, повышает голод и усталость,
        но здоровому тамагочи немного прибавляет здоровья

        :raises TamagochiIsGone: если тамагочи погиб
        :raises TamagochiIsTired: если энергии не хватает на игру
        """
        self._ensure_alive()
        if self._energy < self.PLAY_ENERGY_COST:
            raise TamagochiIsTired(
                f'{self.name} слишком устал, чтобы играть. Дайте ему отдохнуть'
            )
        self._energy = clamp(self._energy - self.PLAY_ENERGY_COST)
        self._fatigue = clamp(self._fatigue + self.PLAY_FATIGUE)
        self._hunger = clamp(self._hunger + self.PLAY_HUNGER)
        if not self._sick:
            self._hp = clamp(self._hp + self.PLAY_HP_BONUS)

    def rest(self) -> None:
        """
        Отдых: энергия растёт, усталость падает.
        Во время болезни отдых действует вдвое слабее

        :raises TamagochiIsGone: если тамагочи погиб
        """
        self._ensure_alive()
        factor = self.SICK_REST_FACTOR if self._sick else 1
        self._energy = clamp(self._energy + self.REST_ENERGY // factor)
        self._fatigue = clamp(self._fatigue - self.REST_FATIGUE // factor)
        self._hunger = clamp(self._hunger + self.REST_HUNGER)

    def heal(self, medicine: Medicine) -> None:
        """
        Лечит тамагочи: тратит одно использование лекарства,
        восстанавливает здоровье и снимает болезнь

        :param medicine: лекарство для лечения
        :raises TamagochiIsGone: если тамагочи погиб
        :raises MedicineIsEmpty: если у лекарства не осталось использований
        """
        self._ensure_alive()
        if medicine.is_empty():
            raise MedicineIsEmpty(f'Лекарство «{medicine.name}» закончилось')
        medicine.uses += 1
        self._hp = clamp(self._hp + medicine.heal_hp)
        self._sick = False

    @property
    def status(self) -> dict[str, int]:
        """
        Свойство для доступа ко всем состояниям тамагочи

        :return: словарь с ключами hunger, fatigue, energy, hp
        """
        return {
            'hunger': self._hunger,
            'fatigue': self._fatigue,
            'energy': self._energy,
            'hp': self._hp,
        }

    def is_alive(self) -> bool:
        """
        Проверяет, жив ли тамагочи

        :return: True если здоровье больше нуля, иначе False
        """
        return self._hp > MIN_STAT

    def is_sick(self) -> bool:
        """
        Проверяет, болеет ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        return self._sick

    def update(self) -> None:
        """
        Проживает один ход: растут голод и усталость, тратится энергия.
        При сильном голоде, усталости, нулевой энергии и болезни тамагочи
        теряет здоровье. Голодный или уставший тамагочи заболевает чаще.
        Для погибшего тамагочи ничего не происходит
        """
        if not self.is_alive():
            return

        self._hunger = clamp(self._hunger + self.HUNGER_PER_TICK)
        self._energy = clamp(self._energy - self.ENERGY_PER_TICK)
        self._fatigue = clamp(self._fatigue + self.FATIGUE_PER_TICK)

        if not self._sick and self._rng.random() < self._sick_chance():
            self._sick = True

        damage = 0
        if self._hunger >= self.CRITICAL_HUNGER:
            damage += self.STARVATION_DAMAGE
        if self._fatigue >= self.CRITICAL_FATIGUE:
            damage += self.EXHAUSTION_DAMAGE
        if self._energy == MIN_STAT:
            damage += self.NO_ENERGY_DAMAGE
        if self._sick:
            damage += self.SICKNESS_DAMAGE
            self._fatigue = clamp(self._fatigue + self.SICKNESS_FATIGUE)
        self._hp = clamp(self._hp - damage)

    def _sick_chance(self) -> float:
        """
        Рассчитывает вероятность заболеть на этом ходу

        :return: вероятность от 0 до 1
        """
        if (
            self._hunger >= self.RISKY_HUNGER
            or self._fatigue >= self.RISKY_FATIGUE
        ):
            return self.RISKY_SICK_CHANCE
        return self.BASE_SICK_CHANCE

    def _ensure_alive(self) -> None:
        """
        Проверяет, что тамагочи жив

        :raises TamagochiIsGone: если тамагочи погиб
        """
        if not self.is_alive():
            raise TamagochiIsGone(f'{self.name} погиб')
