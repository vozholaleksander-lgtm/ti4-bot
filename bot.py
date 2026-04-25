import os
import logging
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# НАСТРОЙКИ
# =========================
# Никому не показывай токен. Лучше хранить его в переменной окружения BOT_TOKEN.
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# ТЕСТ
# =========================
# Теги:
# DIP      дипломатия, переговоры
# ECO      экономика, развитие
# WAR      агрессия, давление
# TRICK    интрига, скрытые ходы
# WEIRD    нестандарт, игра вне правил
# TECH     технологии, системность
# MOB      мобильность, обходные пути
# LAW      порядок, контроль, оборона
# PARASITE использование чужой силы/ресурсов
# FEAR     запугивание, демонстрация силы
# EXPLORE  исследование, любопытство
# BIO      рост, размножение, органичность
# MECATOL  стремление к центру/символической власти
# HUNGER   поглощение, захват, прожорливость
# INIT     инициатива, темп, ход первым

QUESTIONS = [
    {
        "text": "🌒 Ты входишь в старый трактир на границе королевств. В углу спорят вооружённые наёмники. Один из них задевает тебя плечом и смотрит вызывающе.\n\nЧто ты делаешь?",
        "answers": [
            ("Заговорю спокойно и попробую снять напряжение.", {"DIP": 2, "LAW": 1}),
            ("Отойду в сторону. Мне не нужна чужая драка.", {"ECO": 1, "LAW": 1, "MOB": 1}),
            ("Отвечу жёстко, чтобы сразу поняли границы.", {"WAR": 2, "FEAR": 1, "INIT": 1}),
            ("Подыграю им, будто мы одной крови.", {"TRICK": 2, "DIP": 1}),
            ("Проигнорирую. У меня есть дело важнее.", {"WEIRD": 2, "MOB": 1}),
        ],
    },
    {
        "text": "🧙 В подземелье ты находишь дверь с рунами. Маг говорит: за ней сокровище, но механизм может быть ловушкой.\n\nТвоё решение?",
        "answers": [
            ("Сначала изучу механизм и соберу максимум сведений.", {"TECH": 2, "EXPLORE": 1}),
            ("Позову остальных и предложу делить риск.", {"DIP": 2}),
            ("Открою. Кто боится — пусть стоит сзади.", {"WAR": 1, "INIT": 2}),
            ("Пусть кто-то другой откроет первым.", {"TRICK": 2, "PARASITE": 1}),
            ("Попробую найти проход, которого нет на карте.", {"WEIRD": 2, "MOB": 1}),
        ],
    },
    {
        "text": "🚀 На заброшенной орбитальной станции кислорода хватит не всем. До спасательного корабля — полчаса.\n\nЧто ты делаешь?",
        "answers": [
            ("Организую очередь и правила распределения.", {"LAW": 2, "DIP": 1}),
            ("Беру под контроль генератор и считаю ресурсы.", {"ECO": 2, "TECH": 1}),
            ("Забираю скафандр первым. Живой потом разберётся.", {"WAR": 2, "INIT": 1}),
            ("Убеждаю других, что знаю короткий путь.", {"TRICK": 2, "MOB": 1}),
            ("Ищу нестандартный способ выжить: шлюз, дроны, аварийный модуль.", {"WEIRD": 2, "EXPLORE": 1}),
        ],
    },
    {
        "text": "🏛️ В городе начинается выбор нового правителя. У тебя нет армии, но есть имя, связи и несколько долговых расписок.\n\nКак действуешь?",
        "answers": [
            ("Собираю коалицию из тех, кому выгоден порядок.", {"DIP": 2, "LAW": 1, "MECATOL": 1}),
            ("Покупаю поддержку через услуги и обмены.", {"DIP": 1, "ECO": 2}),
            ("Вывожу на улицы своих сторонников и давлю массой.", {"WAR": 1, "FEAR": 2, "MECATOL": 1}),
            ("Стравливаю кандидатов и становлюсь нужным посредником.", {"TRICK": 3}),
            ("Мне не нужен трон. Мне нужен тот, кто будет мне должен.", {"TRICK": 2, "PARASITE": 2}),
        ],
    },
    {
        "text": "🐉 Дракон спит на вершине башни. Внизу деревня просит защиты, но сокровище дракона может решить все твои проблемы.\n\nЧто выберешь?",
        "answers": [
            ("Договорюсь с драконом или деревней. Конфликт не всегда нужен.", {"DIP": 2, "LAW": 1}),
            ("Построю оборону и подготовлюсь к долгой игре.", {"LAW": 2, "ECO": 1}),
            ("Нападу первым, пока он спит.", {"WAR": 2, "INIT": 1}),
            ("Сделаю так, чтобы дракон и деревня ослабили друг друга.", {"TRICK": 2, "PARASITE": 1}),
            ("Попробую приручить или использовать саму природу дракона.", {"WEIRD": 1, "BIO": 2, "FEAR": 1}),
        ],
    },
    {
        "text": "🧬 В лаборатории будущего ты находишь организм, который растёт, копирует себя и приспосабливается к любой среде.\n\nТвоя первая мысль?",
        "answers": [
            ("Это надо изолировать и изучить.", {"TECH": 2, "LAW": 1}),
            ("Это можно вырастить во что-то полезное.", {"BIO": 3, "ECO": 1}),
            ("Это оружие.", {"WAR": 2, "BIO": 1}),
            ("Это можно продать тем, кто не понимает риска.", {"ECO": 1, "TRICK": 2}),
            ("Это не инструмент. Это новая форма власти.", {"WEIRD": 2, "BIO": 2}),
        ],
    },
    {
        "text": "🪐 Капитан предлагает короткий путь через нестабильную аномалию. Навигаторы против, но маршрут сэкономит недели.\n\nКак поступишь?",
        "answers": [
            ("Не рискую всем кораблём ради скорости.", {"LAW": 2, "ECO": 1}),
            ("Сначала отправлю зонд.", {"TECH": 2, "EXPLORE": 1}),
            ("Летим. Кто не рискует — не приходит первым.", {"MOB": 2, "INIT": 1, "WEIRD": 1}),
            ("Пущу слух, что другой корабль уже прошёл там.", {"TRICK": 2}),
            ("Именно такие пути и меняют карту мира.", {"WEIRD": 2, "MOB": 2}),
        ],
    },
    {
        "text": "⚔️ Твой союзник стал слишком сильным. Пока он улыбается, все уже понимают: скоро он станет проблемой.\n\nЧто ты делаешь?",
        "answers": [
            ("Открыто обсужу баланс сил.", {"DIP": 2, "LAW": 1}),
            ("Укреплюсь и буду ждать момента.", {"ECO": 1, "LAW": 2}),
            ("Ударю, пока поздно не стало.", {"WAR": 2, "INIT": 1}),
            ("Сделаю так, чтобы против него выступил кто-то другой.", {"TRICK": 3}),
            ("Изменю направление игры так, чтобы его сила стала бесполезной.", {"WEIRD": 2, "TECH": 1}),
        ],
    },
    {
        "text": "🕳️ В космосе обнаружена пустота, откуда возвращаются корабли без экипажа, но с полными трюмами.\n\nТвоя реакция?",
        "answers": [
            ("Закрыть район и предупредить всех.", {"LAW": 2, "DIP": 1}),
            ("Изучить феномен осторожно.", {"EXPLORE": 2, "TECH": 1}),
            ("Отправить туда заключённых или наёмников.", {"PARASITE": 2, "TRICK": 1}),
            ("Сделать из этого оружие страха.", {"FEAR": 2, "WAR": 1}),
            ("Если пустота даёт ресурсы — надо научиться её кормить.", {"HUNGER": 3, "WEIRD": 1}),
        ],
    },
    {
        "text": "📜 Ты нашёл древний закон, который никто давно не читал. Формально он всё ещё действует.\n\nЧто ты сделаешь?",
        "answers": [
            ("Использую его, чтобы восстановить порядок.", {"LAW": 3}),
            ("Продам знание тем, кому оно нужно.", {"ECO": 2, "DIP": 1}),
            ("Объявлю себя законным наследником права.", {"MECATOL": 2, "LAW": 1}),
            ("Подставлю противников под нарушение.", {"TRICK": 2, "LAW": 1}),
            ("Докажу, что правила можно переписать.", {"WEIRD": 2, "TRICK": 1}),
        ],
    },
    {
        "text": "🤖 Вражеский ИИ предлагает тебе доступ к своим данным. Он не врёт, но явно хочет использовать тебя.\n\nЧто ответишь?",
        "answers": [
            ("Соглашусь на ограниченный обмен.", {"DIP": 1, "TECH": 1, "LAW": 1}),
            ("Заберу данные и усилю свою систему.", {"TECH": 2, "ECO": 1}),
            ("Взломаю его ядро.", {"TECH": 2, "WAR": 1}),
            ("Позволю ему думать, что он использует меня.", {"TRICK": 2, "PARASITE": 1}),
            ("Я не буду с ним конкурировать. Я стану частью его логики.", {"WEIRD": 2, "PARASITE": 2}),
        ],
    },
    {
        "text": "🔥 В твоих руках оружие, одного вида которого достаточно, чтобы другие отступили.\n\nКак ты его используешь?",
        "answers": [
            ("Как сдерживание. Главное — чтобы его боялись, а не применяли.", {"FEAR": 2, "LAW": 1}),
            ("Как гарантию переговоров.", {"DIP": 1, "FEAR": 1}),
            ("Применю по важной цели.", {"WAR": 3}),
            ("Покажу всем, но ударю там, где не ждут.", {"TRICK": 1, "FEAR": 2}),
            ("Сделаю его центром всей стратегии.", {"FEAR": 2, "WEIRD": 1}),
        ],
    },
    {
        "text": "🧭 Перед тобой три дороги: безопасная, богатая и неизвестная.\n\nКуда пойдёшь?",
        "answers": [
            ("Безопасная дорога. Дойти важнее.", {"LAW": 2}),
            ("Богатая дорога. Ресурсы решают.", {"ECO": 3}),
            ("Туда, где можно встретить врага и забрать больше.", {"WAR": 2, "HUNGER": 1}),
            ("Неизвестная. Там меньше конкурентов.", {"EXPLORE": 2, "WEIRD": 1}),
            ("Пойду не дорогой, а через того, кто знает дороги.", {"TRICK": 1, "PARASITE": 2}),
        ],
    },
    {
        "text": "👑 В центре мира стоит пустой трон. Все говорят, что тот, кто сядет на него слишком рано, станет мишенью.\n\nЧто сделаешь?",
        "answers": [
            ("Подготовлю поддержку и займу его законно.", {"MECATOL": 2, "DIP": 1, "LAW": 1}),
            ("Подожду, пока другие устанут.", {"TRICK": 1, "ECO": 1, "LAW": 1}),
            ("Займу сейчас. Пусть попробуют выбить.", {"MECATOL": 2, "WAR": 2, "FEAR": 1}),
            ("Посажу туда другого — временно.", {"TRICK": 2, "PARASITE": 1}),
            ("Трон — приманка. Настоящая власть не там.", {"WEIRD": 2, "MOB": 1}),
        ],
    },
    {
        "text": "🌌 Финал близко. Все устали, союзы трещат, ресурсы на исходе. Тебе нужен последний шаг.\n\nКакой он?",
        "answers": [
            ("Собираю последнюю сделку и выигрываю через доверие.", {"DIP": 3}),
            ("Показываю, что моя система выдержала дольше всех.", {"ECO": 2, "LAW": 2}),
            ("Иду на решающий удар.", {"WAR": 3, "INIT": 1}),
            ("Поворачиваю чужие планы против них.", {"TRICK": 3}),
            ("Делаю ход, который никто не считал возможным.", {"WEIRD": 3, "MOB": 1}),
        ],
    },
]

FACTIONS = {
    "The Arborec": {
        "name_ru": "Арбореки",
        "desc": "Ты играешь через рост, закрепление и постепенное превращение карты в свою экосистему. Не самый быстрый стиль, зато очень атмосферный.",
        "tags": {"BIO": 5, "ECO": 2, "LAW": 1},
    },
    "The Barony of Letnev": {
        "name_ru": "Баронство Летнев",
        "desc": "Тебе подходят тяжёлая мощь, контроль ресурсов и уверенное давление без лишней суеты.",
        "tags": {"WAR": 3, "ECO": 3, "LAW": 2, "FEAR": 1},
    },
    "The Clan of Saar": {
        "name_ru": "Клан Саар",
        "desc": "Ты не любишь сидеть на месте. Твой стиль — движение, давление, гибкая экспансия и жизнь вне привычных рамок.",
        "tags": {"MOB": 5, "WAR": 3, "WEIRD": 1},
    },
    "The Embers of Muaat": {
        "name_ru": "Угли Муаата",
        "desc": "Ты любишь эффект присутствия: пусть все знают, что у тебя есть сила, с которой нельзя не считаться.",
        "tags": {"FEAR": 5, "WAR": 3, "TECH": 1},
    },
    "The Emirates of Hacan": {
        "name_ru": "Эмираты Хакана",
        "desc": "Ты видишь мир как сеть обменов. Деньги, сделки, услуги и связи — твоя настоящая армия.",
        "tags": {"DIP": 4, "ECO": 5, "TRICK": 1},
    },
    "The Federation of Sol": {
        "name_ru": "Федерация Сол",
        "desc": "Тебе подходит надёжная, понятная, сильная фракция. Ты выигрываешь через стабильность, темп и контроль важных точек.",
        "tags": {"ECO": 3, "LAW": 3, "WAR": 2},
    },
    "The Ghosts of Creuss": {
        "name_ru": "Призраки Креусса",
        "desc": "Ты выбираешь не лучшую дорогу, а дорогу, которой для других не существует.",
        "tags": {"WEIRD": 4, "MOB": 5, "EXPLORE": 2},
    },
    "The L1Z1X Mindnet": {
        "name_ru": "Сеть Разума L1Z1X",
        "desc": "Ты холодный захватчик: технология, сила, расчёт и точечное превращение чужого в своё.",
        "tags": {"TECH": 4, "WAR": 4, "PARASITE": 1},
    },
    "The Mentak Coalition": {
        "name_ru": "Коалиция Ментак",
        "desc": "Ты не всегда самый сильный, но умеешь быть неудобным. Чужая выгода редко проходит мимо тебя.",
        "tags": {"TRICK": 4, "DIP": 2, "PARASITE": 3},
    },
    "The Naalu Collective": {
        "name_ru": "Коллектив Наалу",
        "desc": "Ты ценишь темп, предвидение и контроль момента. Побеждать надо не громко, а вовремя.",
        "tags": {"TRICK": 3, "INIT": 4, "DIP": 1},
    },
    "The Nekro Virus": {
        "name_ru": "Вирус Некро",
        "desc": "Ты не развиваешься как все. Ты смотришь, что делают другие, и забираешь лучшее.",
        "tags": {"PARASITE": 5, "TECH": 4, "WEIRD": 3},
    },
    "Sardakk N'orr": {
        "name_ru": "Сардакк Н’орр",
        "desc": "Твой ответ на проблему — сила. Не дипломатия, не сложные схемы, а прямое давление.",
        "tags": {"WAR": 6, "FEAR": 2},
    },
    "The Universities of Jol-Nar": {
        "name_ru": "Университеты Джол-Нар",
        "desc": "Ты хочешь видеть игру глубже других: технологии, расчёт, долгий план и системное превосходство.",
        "tags": {"TECH": 6, "ECO": 2, "EXPLORE": 1},
    },
    "The Winnu": {
        "name_ru": "Винну",
        "desc": "Ты стремишься к символическому центру власти. Трон, столица, легитимность — это не декор, а стратегия.",
        "tags": {"MECATOL": 6, "LAW": 2, "DIP": 1},
    },
    "The Xxcha Kingdom": {
        "name_ru": "Королевство Ззча",
        "desc": "Ты играешь через терпение, защиту, закон и политическое влияние. Твой стиль — не шумный, но вязкий.",
        "tags": {"DIP": 3, "LAW": 5},
    },
    "The Yssaril Tribes": {
        "name_ru": "Племена Иссарил",
        "desc": "Ты любишь информацию, скрытые рычаги и момент, когда остальные понимают, что уже поздно.",
        "tags": {"TRICK": 6, "WEIRD": 1},
    },
    "The Argent Flight": {
        "name_ru": "Серебряная Стая",
        "desc": "Ты дисциплинированный хищник: порядок, скорость, точные удары и контроль неба.",
        "tags": {"LAW": 3, "WAR": 3, "MOB": 2, "INIT": 1},
    },
    "The Empyrean": {
        "name_ru": "Эмпиреи",
        "desc": "Ты хорошо чувствуешь границы, связи и пространство между игроками. Сила не всегда в ударе.",
        "tags": {"DIP": 3, "MOB": 2, "EXPLORE": 3, "WEIRD": 1},
    },
    "The Mahact Gene-Sorcerers": {
        "name_ru": "Генные Чародеи Махакт",
        "desc": "Ты не просто борешься за власть — ты хочешь подчинять чужую волю и превращать конфликт в ресурс.",
        "tags": {"TRICK": 3, "WAR": 2, "PARASITE": 3, "FEAR": 2},
    },
    "The Naaz-Rokha Alliance": {
        "name_ru": "Альянс Нааз-Рока",
        "desc": "Ты исследователь и охотник за возможностями. Твой стиль — находить ценность там, где другие видят случайность.",
        "tags": {"EXPLORE": 5, "ECO": 2, "TECH": 1},
    },
    "The Nomad": {
        "name_ru": "Номад",
        "desc": "Ты играешь не только текущей позицией, но и возможностью оказаться там, где тебя не ждали.",
        "tags": {"WEIRD": 3, "MOB": 3, "TRICK": 1, "ECO": 1},
    },
    "The Titans of Ul": {
        "name_ru": "Титаны Ула",
        "desc": "Ты любишь превращать пространство в крепость и силу. Стабильный рост, контроль и мощная основа.",
        "tags": {"LAW": 4, "ECO": 3, "TECH": 2},
    },
    "The Vuil'raith Cabal": {
        "name_ru": "Кабал Вуил’Рейт",
        "desc": "Ты не просто захватываешь — ты поглощаешь. Чужие ошибки становятся твоими ресурсами.",
        "tags": {"HUNGER": 5, "WAR": 3, "WEIRD": 2, "PARASITE": 2},
    },
    "The Council Keleres": {
        "name_ru": "Совет Келерес",
        "desc": "Ты играешь через баланс, порядок и умение быть полезным центром системы, пока остальные спорят.",
        "tags": {"DIP": 3, "LAW": 3, "MECATOL": 2},
    },
}

SECRET_ENDINGS = [
    {
        "title": "👁 Скрытая концовка: «Ты не игрок, ты наблюдатель»",
        "condition": lambda s: s["WEIRD"] >= 9 and s["MOB"] >= 5,
        "factions": ["The Ghosts of Creuss", "The Nomad"],
        "text": "Ты не соревнуешься на обычной доске. Ты ищешь щели между правилами и появляешься там, где тебя не должно быть.",
    },
    {
        "title": "🧠 Скрытая концовка: «Угроза столу»",
        "condition": lambda s: s["WAR"] >= 7 and s["TRICK"] >= 6,
        "factions": ["The Mahact Gene-Sorcerers", "The L1Z1X Mindnet", "The Argent Flight"],
        "text": "Ты опасен не потому, что нападаешь. Ты опасен потому, что выбираешь правильный момент для давления.",
    },
    {
        "title": "🧬 Скрытая концовка: «Чужое станет твоим»",
        "condition": lambda s: s["PARASITE"] >= 6 and s["TECH"] >= 5,
        "factions": ["The Nekro Virus", "The L1Z1X Mindnet"],
        "text": "Ты не обязан быть источником силы. Достаточно понять, у кого она есть, и как её присвоить.",
    },
    {
        "title": "💰 Скрытая концовка: «Торговый хищник»",
        "condition": lambda s: s["DIP"] >= 6 and s["ECO"] >= 6 and s["TRICK"] >= 3,
        "factions": ["The Emirates of Hacan", "The Mentak Coalition"],
        "text": "Ты улыбаешься, договариваешься и считаешь выгоду быстрее остальных.",
    },
    {
        "title": "🔥 Скрытая концовка: «Звезда смерти в кармане»",
        "condition": lambda s: s["FEAR"] >= 7,
        "factions": ["The Embers of Muaat", "The Barony of Letnev"],
        "text": "Тебе нравится, когда угроза работает ещё до того, как ты сделал ход.",
    },
    {
        "title": "👑 Скрытая концовка: «Право на трон»",
        "condition": lambda s: s["MECATOL"] >= 5 and s["LAW"] >= 4,
        "factions": ["The Winnu", "The Council Keleres", "The Xxcha Kingdom"],
        "text": "Ты не просто хочешь победить. Ты хочешь, чтобы победа выглядела законной.",
    },
    {
        "title": "🕳 Скрытая концовка: «Голод из пустоты»",
        "condition": lambda s: s["HUNGER"] >= 4 and s["WEIRD"] >= 4,
        "factions": ["The Vuil'raith Cabal"],
        "text": "Для тебя карта — не территория. Это кормовая база.",
    },
    {
        "title": "🌿 Скрытая концовка: «Мир как сад»",
        "condition": lambda s: s["BIO"] >= 5 and s["ECO"] >= 3,
        "factions": ["The Arborec"],
        "text": "Ты не захватываешь мир мгновенно. Ты прорастаешь в него.",
    },
]

def calculate_result(scores):
    # Сначала ищем секретную концовку
    for ending in SECRET_ENDINGS:
        if ending["condition"](scores):
            return {
                "secret": True,
                "title": ending["title"],
                "text": ending["text"],
                "factions": ending["factions"],
            }

    # Обычный скоринг: считаем близость игрока к профилю фракции
    faction_scores = []
    for faction, data in FACTIONS.items():
        total = 0
        for tag, weight in data["tags"].items():
            total += scores[tag] * weight
        faction_scores.append((total, faction))

    faction_scores.sort(reverse=True)
    top = [f for _, f in faction_scores[:3]]
    return {
        "secret": False,
        "title": "🏁 Твой результат",
        "text": "По ответам тебе ближе всего эти фракции:",
        "factions": top,
    }

def format_result(result, scores):
    style_map = {
        "DIP": "переговоры",
        "ECO": "развитие",
        "WAR": "давление",
        "TRICK": "интрига",
        "WEIRD": "нестандарт",
        "TECH": "технологии",
        "MOB": "мобильность",
        "LAW": "контроль",
        "PARASITE": "игра через других",
        "FEAR": "запугивание",
        "EXPLORE": "исследование",
        "BIO": "рост",
        "MECATOL": "власть",
        "HUNGER": "поглощение",
        "INIT": "инициатива",
    }

    top_traits = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    traits_text = ", ".join([style_map.get(k, k) for k, v in top_traits if v > 0])

    main = result["factions"][0]
    alt = result["factions"][1:3]

    text = f"🎯 ТВОЯ ФРАКЦИЯ:\n{main}\n\n"

    if alt:
        text += "⚡ Альтернативы:\n"
        for f in alt:
            text += f"- {f}\n"
        text += "\n"

    text += f"🧠 Твой стиль:\n{traits_text}\n\n"

    if scores["TRICK"] > 5:
        text += "😈 Ты играешь через хитрость. Люди редко понимают, когда ты уже выиграл.\n\n"
    elif scores["WAR"] > 5:
        text += "⚔️ Ты давишь. Если ты начал — кто-то уже проиграл.\n\n"
    elif scores["DIP"] > 5:
        text += "🤝 Ты управляешь людьми. Сделки — твоё оружие.\n\n"
    elif scores["WEIRD"] > 5:
        text += "🌀 Ты играешь вне правил. Ты не сильнее — ты просто в другой игре.\n\n"
    else:
        text += "🧱 Ты стабильный игрок. Ты не выигрываешь быстро — ты выигрываешь надёжно.\n\n"

    text += "⚠️ Твоя слабость:\n"
    if scores["WAR"] > scores["DIP"]:
        text += "Ты можешь начать слишком рано и стать целью.\n\n"
    else:
        text += "Ты можешь затянуть и дать другим вырваться вперёд.\n\n"

    text += "📲 Скинь тест другу:\nhttps://t.me/TwinImpFbot"

    return text
def get_question_keyboard(q_index):
    question = QUESTIONS[q_index]
    keyboard = []
    for i, (answer_text, _) in enumerate(question["answers"]):
        keyboard.append([InlineKeyboardButton(answer_text, callback_data=f"answer:{q_index}:{i}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["q_index"] = 0
    context.user_data["scores"] = defaultdict(int)

    intro = (
        "🌌 Тест-приключение: какая фракция Twilight Imperium тебе подходит?\n\n"
        "Это не прямой тест про игру. Отвечай на жизненные, RPG и sci-fi ситуации.\n"
        "Выбирай быстро: первый импульс честнее.\n\n"
        "Начинаем."
    )
    await update.message.reply_text(intro)
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data.get("q_index", 0)

    if q_index >= len(QUESTIONS):
        scores = context.user_data.get("scores", defaultdict(int))
        result = calculate_result(scores)
        await update.effective_chat.send_message(format_result(result, scores))
        return

    question = QUESTIONS[q_index]
    await update.effective_chat.send_message(
        f"Вопрос {q_index + 1}/{len(QUESTIONS)}\n\n{question['text']}",
        reply_markup=get_question_keyboard(q_index),
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, q_index_str, answer_index_str = query.data.split(":")
    q_index = int(q_index_str)
    answer_index = int(answer_index_str)

    current_q = context.user_data.get("q_index", 0)
    if q_index != current_q:
        await query.edit_message_text("Этот вопрос уже неактуален. Нажми /start, если хочешь начать заново.")
        return

    answer_text, tags = QUESTIONS[q_index]["answers"][answer_index]

    scores = context.user_data.get("scores")
    if scores is None:
        scores = defaultdict(int)
        context.user_data["scores"] = scores

    for tag, value in tags.items():
        scores[tag] += value

    await query.edit_message_text(
        f"Вопрос {q_index + 1}/{len(QUESTIONS)}\n\n"
        f"Твой выбор:\n{answer_text}"
    )

    context.user_data["q_index"] = q_index + 1
    await ask_question(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start — начать тест заново\n"
        "/help — помощь\n\n"
        "Бот задаёт ситуации и в конце подбирает фракцию из TI4 + Prophecy of Kings."
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Укажи токен в переменной окружения BOT_TOKEN."
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^answer:"))

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()