# импортируем основные библиотеки
import config
import telebot
import pandas as pd
from tabulate import tabulate
import dbworker
from fuzzywuzzy import fuzz

# инициируем бота
bot = telebot.TeleBot(config.token)

# загружаем статистику
def upload_stats():

    df = pd.DataFrame()
    df = pd.read_csv('companies_new.csv', delimiter=';')

    return df


# обработчик команды start: запись информации о пользователе, перечисление списка основных команд
@bot.message_handler(commands=["start"])
def cmd_start(message):
    # Устанавливаем значение статуса в исходное положение для пользователя. Начало работы с чат-ботом.
    dbworker.set_state(message.chat.id, config.States.S_START.value)

    # перечисление списка основных команд
    bot.send_message(message.chat.id, "Привет! Я бот, который поможет тебе найти компанию на сайте habr.com\n"
                                      "Определись, пожалуйста, хочешь ли ты увидеть рейтинг или информацию\n"
                                      "о конкретной компании. Выбери /company или /rating\n"
                                      "\n"
                                      "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                      "Набери /commands, чтобы увидеть список доступных команд\n"
                                      "Набери /reset, чтобы сбросить выбранные параметры")

    # Ждем от пользователя выбор страны или рейтинга.
    dbworker.set_state(message.chat.id, config.States.S_RATING_OR_COMPANY.value)

# Обрабатываем выбор пользователя: /company или /rating
@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_RATING_OR_COMPANY.value
                     and message.text not in ('/reset', '/start', '/info', '/commands', '/listcities',
                                              '/listcountries', '/listhabs', '/listfields',
                                              '/topraiting', '/topposts', '/topsubscribers'
                                              )
                     )
def company_or_rating(message):
    # на всякий случай, очищаем выбор пользователя в базе
    dbworker.del_state(str(message.chat.id) + '_rating_or_company')

    # обрабатываем ввод пользователя
    if message.text.lower().strip() == '/company':
        bot.send_message(message.chat.id, "Отлично! Тебе нужна информация о компании.\n"
                                          "Пожалуйста, введи название компании.\n"
                                          "\n"
                                          "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                          "Набери /reset, чтобы сбросить выбранные параметры")

        # запишем выбор пользователя
        dbworker.set_state(str(message.chat.id) + '_rating_or_company', 'company')
        # Ждем от пользователя ввода названия компании или поля для формирования рейтинга
        dbworker.set_state(message.chat.id, config.States.S_ENTER_RATING_OR_COMPANY.value)

    elif message.text.lower().strip() == '/rating':
        bot.send_message(message.chat.id, "Отлично! Тебе нужен общий рейтинг компаний\n"
                                          "Пожалуйста, введи поле для формирования рейтинга.\n"
                                          "\n"
                                          "Набери /listfields, чтобы узнать список полей\n"
                                          "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                          "Набери /reset, чтобы сбросить выбранные параметры")

        # запишем выбор пользователя
        dbworker.set_state(str(message.chat.id) + '_rating_or_company', 'rating')
        # Ждем от пользователя ввода названия компании или поля для формирования рейтинга
        dbworker.set_state(message.chat.id, config.States.S_ENTER_RATING_OR_COMPANY.value)

    else:
        bot.send_message(message.chat.id, "Я так не играю. \"Не понимаю я по вашему.\"\n"
                                          "\n"
                                          "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                          "Набери /reset, чтобы сбросить выбранные параметры")

# Обрабатываем ввод пользователя: название компани или поле для формирования рейтинга
@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_RATING_OR_COMPANY    .value
                     and message.text not in ('/reset', '/start', '/info', '/commands', '/listcities',
                                              '/listcountries', '/listhabs', '/listfields',
                                              '/topraiting', '/topposts', '/topsubscribers'
                                              )
                     )
def enter_company_or_rating(message):

    # выгружаем выбор пользователя с прошлого шага
    company_or_rating = dbworker.get_current_state(str(message.chat.id)+'_rating_or_company')

    df = upload_stats()

    if company_or_rating == 'company':

        # добавляем нечеткую логику
        fuzzy_matches = {}
        company_names = df['company_name']

        # перебираем все названия, составляем парты индекс / вероятность
        for i in range(len(company_names)):
            partial_ratio = fuzz.ratio(company_names.iloc[i], message.text.strip())
            fuzzy_matches[i] = (partial_ratio, i)

        # выбираем наилучшее совпадение
        x = sorted(fuzzy_matches, key=lambda k: fuzzy_matches[k][0], reverse=True)
        confidence, selection = fuzzy_matches[x[0]][0], x[0]

        # если вероятнсть > 50%, то выводим информацию о компании
        if confidence >= 50:
            str_message = ''
            for_sending = df[df['company_name'] == company_names[selection]]
            header_names = for_sending.columns

            for i in range(len(header_names)):
                str_message += header_names[i] + ' - ' + str(for_sending.iloc[0, i]) + '\n'

            bot.send_message(message.chat.id, 'Вероятноть больше {} процентов'.format(confidence))
            bot.send_message(message.chat.id, str_message)

        else:
            bot.send_message(message.chat.id, "Не могу найти компанию с таким названием.\n"
                                              "Попробуй ввести еще раз.\n"
                                              "\n"
                                              "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                              "Набери /reset, чтобы сбросить выбранные параметры")
    elif company_or_rating == 'rating':
        listfields = ['company_raiting', 'company_blog_posts', 'company_news', 'company_vacancies',
                      'company_subscribers', 'company_employees']

        if message.text.strip() not in listfields:
            bot.send_message(message.chat.id, "Не могу найти такое поле в таблице.\n"
                                              "Попробуй ввести еще раз.\n"
                                              "\n"
                                              "Набери /listfields, чтобы увидеть список полей\n"
                                              "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                              "Набери /reset, чтобы сбросить выбранные параметры")
        else:
            fields_list = ['company_name']
            sort_by = []
            str_message = ''

            fields_list.append(message.text.strip())
            sort_by.append(message.text.strip())

            for_sending = df[fields_list].sort_values(by=sort_by, ascending=False).head(20)

            for i in range(len(for_sending)):
                str_message += str((i + 1)) + '. ' + for_sending.iloc[i, 0] + ' - ' + str(for_sending.iloc[i, 1]) + '\n'

            bot.send_message(message.chat.id, str_message)

# бработчик команды commands: перечисление списка доступных команд
@bot.message_handler(commands=["commands"])
def cmd_commands(message):
    bot.send_message(message.chat.id, "/reset - сброс текущего выбора параметров\n"
                                      "/start - начинаем работу заново\n"
                                      "/info - подробная информация о моих возможностях\n"
                                      "/commands - перечисление полного списка команд\n"
                                      "/listcities - перечисление списка ТОП-20 городов\n"
                                      "/listcountries - перечисление списка ТОП-20 стран\n"
                                      "/listhabs - перечисление списка ТОП-20 хабов\n"
                                      "/listfields - перечисление списка полей\n"
                                      "/topraiting - список ТОП-20 компаний по рейтингу\n"
                                      "/topposts - список ТОП-20 компаний по количеству публикаций\n"
                                      "/topsubscribers - список ТОП-20 компаний по количеству подписчиков\n"
                     )

# обработчик команды info: описание возможностей бота
@bot.message_handler(commands=["info"])
def cmd_info(message):
    bot.send_message(message.chat.id, "Я могу предоставить информацию по компаниям, зарегистрированным на habr.com\n"
                                      "Для начала посмотри общую статистику по странам, городам, хабам\n"
                                      "Выбери одну из команд /listcities, /listcountries или /listhabs\n"
                                      "Я покажу сводную информацию"
                     )
    bot.send_message(message.chat.id, "Далее можно посмотреть ТОП-20 компаний по рейтингу, количеству публикаций или подписчиков\n"
                                      "Выбери одну из команд /topraiting, /topposts или /topsubscribers\n"
                                      "Я покажу рейтинги"
                     )
    bot.send_message(message.chat.id, "Это далеко не все мои возможности\n"
                                      "Набери /commands, чтобы увидеть список доступных команд\n"
                                      "Набери /reset, чтобы сбросить выбранные параметры"
                     )


# обработчик команды listcities: вывод списка ТОП-20 городов
@bot.message_handler(commands=["listcities"])
def cmd_listcities(message):

    df = upload_stats()

    for_sending = df['company_city'].value_counts().head(20)
    keys = for_sending.keys().to_list()
    values = for_sending.to_list()
    str_message = ''

    for i in range(len(for_sending)):
        str_message += str(i + 1) + '. ' + keys[i] + ' - ' + str(values[i]) + '\n'

    bot.send_message(message.chat.id, str_message)


# обработчик команды listcountries: вывод списка ТОП-20 стран
@bot.message_handler(commands=["listcountries"])
def cmd_listcountries(message):

    df = upload_stats()

    for_sending = df['company_country'].value_counts().head(20)
    keys = for_sending.keys().to_list()
    values = for_sending.to_list()
    str_message = ''

    for i in range(len(for_sending)):
        str_message += str(i + 1) + '. ' + keys[i] + ' - ' + str(values[i]) + '\n'

    bot.send_message(message.chat.id, str_message)

# обработчик команды listhabs: вывод списка ТОП-20 хабов
@bot.message_handler(commands=["listhabs"])
def cmd_listhabs(message):

    df = upload_stats()
    habs_dict = {}
    habs_info = []
    str_message = ''

    for company_hab in df['company_habs_name']:
        if isinstance(company_hab, str):
            habs = map(str.strip, company_hab.split(','))
            for hab in habs:
                if habs_dict.get(hab) != None:
                    habs_dict[hab] += 1
                else:
                    habs_dict[hab] = 1

    for key, value in habs_dict.items():
        habs_info.append({'hab_name': key, 'counter': value})

    for_sending = pd.DataFrame(habs_info)
    for_sending = for_sending.sort_values(by='counter', ascending=False).head(20)

    for i in range(len(for_sending)):
        str_message += str((i + 1)) + '. ' + for_sending.iloc[i, 0] + ' - ' + str(for_sending.iloc[i, 1]) + '\n'

    bot.send_message(message.chat.id, str_message)

# обработчик команды listfields: вывод списка полей для формирования рейтинга
@bot.message_handler(commands=["listfields"])
def cmd_listfields(message):

    listfields = ['company_raiting', 'company_blog_posts', 'company_news', 'company_vacancies',
                  'company_subscribers', 'company_employees']
    bot.send_message(message.chat.id, "\n".join(listfields))

# обработчик команды topraiting: вывод списка ТОП-20 компаний по рейтингу
@bot.message_handler(commands=["topraiting"])
def cmd_topraiting(message):

    df = upload_stats()
    fields_list = ['company_name', 'company_raiting']
    sort_by = ['company_raiting']
    str_message = ''

    for_sending = df[fields_list].sort_values(by=sort_by, ascending=False).head(20)
    for i in range(len(for_sending)):
        str_message += str((i + 1)) + '. ' + for_sending.iloc[i, 0] + ' - ' + str(for_sending.iloc[i, 1]) + '\n'

    bot.send_message(message.chat.id, str_message)


# обработчик команды topposts: вывод списка ТОП-20 компаний по количеству публикаций
@bot.message_handler(commands=["topposts"])
def cmd_topposts(message):

    df = upload_stats()
    fields_list = ['company_name', 'company_blog_posts']
    sort_by = ['company_blog_posts']
    str_message = ''

    for_sending = df[fields_list].sort_values(by=sort_by, ascending=False).head(20)

    for i in range(len(for_sending)):
        str_message += str((i + 1)) + '. ' + for_sending.iloc[i, 0] + ' - ' + str(for_sending.iloc[i, 1]) + '\n'

    bot.send_message(message.chat.id, str_message)

# обработчик команды topsubscribers: вывод списка ТОП-20 омпаний по количеству подписчико
@bot.message_handler(commands=["topsubscribers"])
def cmd_topsubscribers(message):

    df = upload_stats()
    fields_list = ['company_name', 'company_subscribers']
    sort_by = ['company_subscribers']
    str_message = ''

    for_sending = df[fields_list].sort_values(by=sort_by, ascending=False).head(20)

    for i in range(len(for_sending)):
        str_message += str((i + 1)) + '. ' + for_sending.iloc[i, 0] + ' - ' + str(for_sending.iloc[i, 1]) + '\n'

    bot.send_message(message.chat.id, str_message)

# обработчик команды reset: сброс состояния, начало работы
@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    bot.send_message(message.chat.id, "Ок, давай начнем заново.\n"
                                      "Определись, пожалуйста, хочешь ли ты увидеть рейтинг или информацию\n"
                                      "о конкретной компании. Выбери /company или /rating\n"
                                      "\n"
                                      "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                      "Набери /commands, чтобы увидеть список доступных команд\n"                                      
                                      "Набери /reset, чтобы сбросить выбранные параметры"
                     )

    # Ждем от пользователя выбор страны или рейтинга.
    dbworker.set_state(message.chat.id, config.States.S_RATING_OR_COMPANY.value)

# Обрабатываем ввод прочих сообщений пользователя
@bot.message_handler(func = lambda message: message.text not in ('/reset', '/start', '/info', '/commands', '/listcities',
                                                              '/listcountries', '/listhabs', '/listfields',
                                                              '/topraiting', '/topposts', '/topsubscribers'
                                                              )
                     )
def cmd_misc(message):
    bot.send_message(message.chat.id, "Я так не играю. \"Не понимаю я по вашему.\"\n"
                                      "\n"
                                      "Набери /info, чтобы узнать чем я могу тебе помочь\n"
                                      "Набери /reset, чтобы сбросить выбранные параметры")

# запускаем бота
if __name__ == '__main__':
    bot.infinity_polling()