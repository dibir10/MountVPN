from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.context import FSMContext


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    choose_tariff = State()        # Состояние ожидания выбора тарифа
    upload_photo = State()     # Состояние ожидания загрузки фото чека