#!/usr/bin/python3.5

import requests
import time
import datetime
import telebot
from telebot import types
from dbhelper import DBHelper, ChatSearch, Item
from re import sub
from decimal import Decimal
import logging
from logging.handlers import RotatingFileHandler
import sys
import threading
import os
import locale
from fake_useragent import UserAgent

TOKEN = os.getenv("BOT_TOKEN", "Bot Token does not exist")
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
URL_ITEMS = "https://api.wallapop.com/api/v3/search?source=search_box"
PROFILE = os.getenv("PROFILE")

# Configurar base de datos según el entorno
if PROFILE is None:
    db = DBHelper()
else:
    # En Docker o entornos controlados, usar directorio específico para persistencia
    db_dir = os.getenv('DB_DIR', '/app/data')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'db.sqlite')
    db = DBHelper(db_path)


ICON_VIDEO_GAMES = u'\U0001F3AE'  # 🎮
ICON_WARNING____ = u'\U000026A0'  # ⚠️
ICON_HIGH_VOLTAG = u'\U000026A1'  # ⚡️
ICON_COLLISION__ = u'\U0001F4A5'  # 💥
ICON_EXCLAMATION = u'\U00002757'  # ❗
ICON_DIRECT_HIT_ = u'\U0001F3AF'  # 🎯

# Estado de usuarios para formularios paso a paso
user_states = {}

def create_main_menu():
    """Crear menú principal con botones inline"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_add = types.InlineKeyboardButton("➕ Añadir búsqueda", callback_data="add_search")
    btn_list = types.InlineKeyboardButton("📋 Mis búsquedas", callback_data="list_searches")
    btn_categories = types.InlineKeyboardButton("📂 Categorías", callback_data="show_categories")
    btn_help = types.InlineKeyboardButton("❓ Ayuda", callback_data="show_help")
    
    markup.add(btn_add, btn_list)
    markup.add(btn_categories, btn_help)
    
    return markup

def create_categories_menu():
    """Crear menú de categorías populares"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    categories = [
        ("📱 Móviles", "24103"),
        ("💻 Informática", "12800"),
        ("🚗 Motor", "100"),
        ("🏠 Hogar", "12467"),
        ("👔 Moda", "12465"),
        ("🎮 Consolas", "12543"),
        ("📚 Libros", "12463"),
        ("⚽ Deporte", "12579")
    ]
    
    for name, cat_id in categories:
        btn = types.InlineKeyboardButton(name, callback_data=f"cat_{cat_id}")
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("🔙 Volver", callback_data="main_menu")
    markup.add(btn_back)
    
    return markup

def create_price_range_menu():
    """Crear menú de rangos de precio"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    ranges = [
        ("💰 Hasta 50€", "0-50"),
        ("💵 50€ - 100€", "50-100"),
        ("💴 100€ - 200€", "100-200"),
        ("💶 200€ - 500€", "200-500"),
        ("💷 500€ - 1000€", "500-1000"),
        ("💸 Más de 1000€", "1000-")
    ]
    
    for name, price_range in ranges:
        btn = types.InlineKeyboardButton(name, callback_data=f"price_{price_range}")
        markup.add(btn)
    
    btn_custom = types.InlineKeyboardButton("✍️ Personalizar", callback_data="price_custom")
    btn_skip = types.InlineKeyboardButton("⏭️ Sin límite", callback_data="price_skip")
    btn_back = types.InlineKeyboardButton("🔙 Volver", callback_data="add_search")
    
    markup.add(btn_custom)
    markup.add(btn_skip, btn_back)
    
    return markup


def notel(chat_id, price, title, url_item, obs=None, seller_info=None):
    # https://apps.timwhitlock.info/emoji/tables/unicode
    if obs is not None:
        text = ICON_EXCLAMATION
    else:
        text = ICON_DIRECT_HIT_
    text += ' *' + title + '*'
    text += '\n'
    if obs is not None:
        text += ICON_COLLISION__ + ' '
    text += locale.currency(price, grouping=True)
    if obs is not None:
        text += obs
        text += ' ' + ICON_COLLISION__
    text += '\n'
    
    # Agregar información del vendedor si está disponible
    if seller_info:
        text += '\n' + u'\U0001F464' + ' *Vendedor:*'  # 👤
        if seller_info.get('reviews_count', 0) > 0:
            avg_rating = seller_info.get('average_rating', 0)
            reviews_count = seller_info.get('reviews_count', 0)
            text += f" {avg_rating:.0f}% ({reviews_count} valoraciones)"
            if avg_rating >= 90:
                text += ' ' + u'\U00002B50'  # ⭐
            elif avg_rating >= 80:
                text += ' ' + u'\U0001F44D'  # 👍
        else:
            text += " Sin valoraciones"
        
        if seller_info.get('is_top_profile', False):
            text += ' ' + u'\U0001F31F'  # 🌟 (Perfil destacado)
        text += '\n'
    
    text += 'https://es.wallapop.com/item/'
    text += url_item
    urlz0rb0t = URL + "sendMessage?chat_id=%s&parse_mode=markdown&text=%s" % (chat_id, text)
    requests.get(url=urlz0rb0t)


def get_url_list(search):
    url = URL_ITEMS
    url += '&keywords='
    url += "+".join(search.kws.split(" "))
    url += '&time_filter=today'
    if search.cat_ids is not None:
        url += '&category_ids='
        url += search.cat_ids
    if search.min_price is not None:
        url += '&min_sale_price='
        url += search.min_price
    if search.max_price is not None:
        url += '&max_sale_price='
        url += search.max_price
    if search.dist is not None:
        url += '&dist='
        url += search.dist
    if search.orde is not None:
        url += '&order_by='
        url += search.orde
    return url


def get_user_reviews(user_id, headers):
    """Obtener las valoraciones de un usuario"""
    try:
        reviews_url = f"https://api.wallapop.com/api/v3/users/{user_id}/reviews"
        reviews_response = requests.get(url=reviews_url, headers=headers)
        
        if reviews_response.status_code == 200:
            reviews = reviews_response.json()
            return reviews
        else:
            return []
    except:
        return []

def calculate_average_rating(reviews):
    """Calcular la puntuación media de las valoraciones"""
    if not reviews:
        return None
    
    total_score = sum(review.get('review', {}).get('scoring', 0) for review in reviews)
    return total_score / len(reviews)

def get_items(url, chat_id, search_keywords):
    try:
   
        ua = UserAgent()

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es,ru;q=0.9,en;q=0.8,de;q=0.7,pt;q=0.6',
            'Connection': 'keep-alive',
            'DeviceOS': '0',
            'Origin': 'https://es.wallapop.com',
            'Referer': 'https://es.wallapop.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': f'{ua.random}',
            'X-AppVersion': '75491',
            'X-DeviceOS': '0',
            'sec-ch-ua-mobile': '?0',
        }

        response = requests.get(url=url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()

            items = data.get('data', {}).get('section', {}).get('payload', {}).get('items', [])

            for x in items:
                # Filtrar solo los elementos que contengan las palabras clave en el título
                title_lower = x['title'].lower()
                keywords_lower = [kw.strip().lower() for kw in search_keywords.split()]
                
                # Verificar que todas las palabras clave estén en el título
                if not all(keyword in title_lower for keyword in keywords_lower):
                    continue
                logging.info('Encontrado: id=%s, price=%s, title=%s, user=%s',
                             str(x['id']),
                             locale.currency(x['price']['amount'], grouping=True),
                             x['title'],
                             x['user_id'])

                # Obtener información del vendedor
                seller_info = None
                try:
                    user_reviews = get_user_reviews(x['user_id'], headers)
                    is_top_profile = x.get('is_top_profile', {}).get('flag', False)
                    
                    seller_info = {
                        'reviews_count': len(user_reviews),
                        'is_top_profile': is_top_profile
                    }
                    
                    if user_reviews:
                        avg_rating = calculate_average_rating(user_reviews)
                        seller_info['average_rating'] = avg_rating
                except Exception as e:
                    logging.warning(f"Error obteniendo info del vendedor {x['user_id']}: {e}")

                i = db.search_item(x['id'], chat_id)
                
                if i is None:
                    db.add_item(x['id'], chat_id, x['title'], x['price']['amount'], x['web_slug'], x['user_id'])
                    notel(chat_id, x['price']['amount'], x['title'], x['web_slug'], seller_info=seller_info)
                    logging.info('New: id=%s, price=%s, title=%s', str(x['id']), locale.currency(x['price']['amount'], grouping=True), x['title'])
                else:
                    money = str(x['price']['amount'])
                    value_json = Decimal(sub(r'[^\d.]', '', money))
                    value_db = Decimal(sub(r'[^\d.]', '', i.price))
                    
                    if value_json < value_db:
                        new_obs = locale.currency(i.price, grouping=True)
                        if i.observaciones is not None:
                            new_obs += ' < ' + i.observaciones
                        db.update_item(x['id'], money, new_obs)
                        obs = ' < ' + new_obs
                        notel(chat_id, x['price']['amount'], x['title'], x['web_slug'], obs, seller_info=seller_info)
                        logging.info('Baja: id=%s, price=%s, title=%s', str(x['id']), locale.currency(x['price']['amount'], grouping=True), x['title'])
        else:
            logging.error(f"Failed to fetch data: {response.status_code}")

    except Exception as e:
        logging.error(e)


def handle_exception(self, exception):
    logging.exception(exception)
    logging.error("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
    print("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
    bot.polling(none_stop=True, timeout=3000)


# INI Actualización de db a partir de la librería de Telegram
# bot = telebot.TeleBot(TOKEN, exception_handler=handle_exception)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help', 's', 'h'])
def send_welcome(message):
    text = '🤖 ¡Hola! Soy **WallBot**\n\n'
    text += '🔍 Tu asistente para búsquedas en Wallapop\n\n'
    text += '✨ **Características:**\n'
    text += '• 🎯 Búsqueda inteligente solo en títulos\n'
    text += '• ⭐ Información de valoraciones del vendedor\n'
    text += '• 💰 Alertas de bajadas de precio\n'
    text += '• 📱 Interfaz visual fácil de usar\n\n'
    text += '👇 **Usa los botones para empezar:**'
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu())


# Manejadores de callbacks para botones inline
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        
        if call.data == "main_menu":
            show_main_menu(call.message)
        
        elif call.data == "add_search":
            start_add_search_wizard(call.message)
        
        elif call.data == "list_searches":
            show_searches_list(call.message)
        
        elif call.data == "show_categories":
            show_categories_menu(call.message)
        
        elif call.data == "show_help":
            show_help(call.message)
        
        elif call.data.startswith("cat_"):
            category_id = call.data[4:]
            if user_id in user_states:
                user_states[user_id]['category'] = category_id
            select_price_range(call.message, category_id)
        
        elif call.data.startswith("price_"):
            handle_price_selection(call.message, call.data, user_id)
        
        elif call.data.startswith("del_"):
            encoded_kws = call.data[4:]
            handle_delete_search(call.message, encoded_kws)
        
        elif call.data.startswith("wizprice_"):
            handle_wizard_price_selection(call.message, call.data, user_id)
        
        # Responder al callback para quitar el loading
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logging.error(f"Error en callback: {e}")
        bot.answer_callback_query(call.id, "❌ Error procesando la solicitud")

def show_main_menu(message):
    text = '🏠 **Menú Principal**\n\n'
    text += 'Selecciona una opción:'
    
    bot.edit_message_text(text, message.chat.id, message.message_id, 
                         parse_mode="Markdown", reply_markup=create_main_menu())

def start_add_search_wizard(message):
    text = '➕ **Añadir nueva búsqueda - Paso 1/2**\n\n'
    text += '🔍 **¿Qué quieres buscar?**\n'
    text += 'Escribe las palabras clave del producto:\n\n'
    text += '📝 _Ejemplo: iPhone 15 Pro Max_\n\n'
    text += '💡 **Tip:** Sé específico para mejores resultados'
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 Volver al menú", callback_data="main_menu")
    markup.add(btn_back)
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=markup)
    
    # Establecer estado del usuario
    user_states[message.chat.id] = {'step': 'waiting_keywords'}

def show_categories_menu(message):
    text = '📂 **Categorías Populares**\n\n'
    text += 'Selecciona una categoría para búsquedas rápidas:'
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=create_categories_menu())

def select_price_range(message, category_id):
    text = '💰 **Selecciona rango de precio**\n\n'
    text += f'📂 Categoría: {category_id}\n'
    text += 'Elige el rango de precio que te interesa:'
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=create_price_range_menu())

def handle_price_selection(message, price_data, user_id):
    # Procesar selección de precio y finalizar búsqueda
    price_range = price_data[6:]  # Quitar "price_"
    
    if price_range == "skip":
        price_range = None
    elif price_range == "custom":
        # Solicitar precio personalizado
        ask_custom_price(message)
        return
    
    # Finalizar creación de búsqueda con categoría y precio
    finalize_category_search(message, user_id, price_range)

def ask_custom_price(message):
    text = '✍️ **Precio personalizado**\n\n'
    text += '💰 Escribe el rango de precio:\n'
    text += '📝 _Formato: min-max_\n'
    text += '🔢 _Ejemplo: 100-500_\n\n'
    text += '💡 Deja vacío min o max si no quieres límite'
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("🔙 Volver", callback_data="show_categories")
    markup.add(btn_back)
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

def finalize_category_search(message, user_id, price_range):
    if user_id not in user_states:
        return
    
    category_id = user_states[user_id].get('category')
    
    # Crear búsqueda automática basada en categoría
    category_names = {
        "24103": "móviles",
        "12800": "informática", 
        "100": "motor",
        "12467": "hogar",
    }
    
    search_term = category_names.get(category_id, f"categoría_{category_id}")
    
    # Crear y guardar búsqueda
    cs = ChatSearch()
    cs.chat_id = message.chat.id
    cs.kws = search_term
    cs.cat_ids = category_id
    
    if price_range and price_range != "skip":
        if '-' in price_range:
            min_price, max_price = price_range.split('-', 1)
            cs.min_price = min_price if min_price else None
            cs.max_price = max_price if max_price else None
    
    cs.username = message.chat.username
    cs.active = 1
    
    db.add_search(cs)
    
    # Mensaje de confirmación
    text = '✅ **Búsqueda añadida correctamente**\n\n'
    text += f'🔍 Categoría: {search_term}\n'
    if price_range:
        text += f'💰 Precio: {price_range}€\n'
    text += '\n🔔 Recibirás notificaciones cuando encuentre resultados'
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=create_main_menu())
    
    # Limpiar estado
    if user_id in user_states:
        del user_states[user_id]

def show_searches_list(message):
    searches = db.get_chat_searchs(message.chat.id)
    
    if not searches:
        text = '📋 **Mis búsquedas**\n\n'
        text += '❌ No tienes búsquedas activas\n\n'
        text += '💡 Usa "➕ Añadir búsqueda" para crear una'
        markup = create_main_menu()
    else:
        text = '📋 **Mis búsquedas activas**\n\n'
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for i, search in enumerate(searches, 1):
            # Crear descripción de la búsqueda
            desc = f'{search.kws}'
            if search.min_price or search.max_price:
                desc += f' ({search.min_price or "0"}€-{search.max_price or "∞"}€)'
            
            text += f'🔍 **{i}.** {desc}\n'
            
            # Botón para borrar esta búsqueda
            btn_delete = types.InlineKeyboardButton(
                f"�️ Borrar: {search.kws[:20]}...", 
                callback_data=f"del_{search.kws.replace(' ', '_')}"
            )
            markup.add(btn_delete)
        
        btn_back = types.InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")
        markup.add(btn_back)
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

def handle_delete_search(message, encoded_kws):
    try:
        # Decodificar las palabras clave
        kws = encoded_kws.replace('_', ' ')
        
        # Borrar la búsqueda usando el método existente
        db.del_chat_search(message.chat.id, kws)
        
        # Mostrar confirmación y lista actualizada
        text = '✅ **Búsqueda eliminada correctamente**\n\n'
        text += f'�️ Eliminada: "{kws}"\n\n'
        text += '📋 Lista actualizada:'
        
        bot.edit_message_text(text, message.chat.id, message.message_id, parse_mode="Markdown")
        time.sleep(1)  # Pausa breve para mostrar confirmación
        show_searches_list(message)
        
    except Exception as e:
        logging.error(f"Error eliminando búsqueda: {e}")
        bot.edit_message_text('❌ Error al eliminar la búsqueda', 
                            message.chat.id, message.message_id)

def show_help(message):
    text = '❓ **Ayuda - WallBot**\n\n'
    text += '🤖 **¿Qué hace este bot?**\n'
    text += 'Busca productos en Wallapop y te notifica cuando encuentra resultados o bajadas de precio.\n\n'
    text += '✨ **Características:**\n'
    text += '• 🎯 Búsqueda inteligente solo en títulos\n'
    text += '• ⭐ Muestra valoraciones del vendedor\n'
    text += '• 💰 Alertas de bajadas de precio\n'
    text += '• 📱 Interfaz visual fácil\n\n'
    text += '📝 **Comandos tradicionales:**\n'
    text += '• `/add producto,min-max,categoría`\n'
    text += '• `/list` - Ver búsquedas\n'
    text += '• `/del producto` - Borrar búsqueda\n\n'
    text += '💡 **Tip:** Usa palabras específicas para mejores resultados'
    
    bot.edit_message_text(text, message.chat.id, message.message_id,
                         parse_mode="Markdown", reply_markup=create_main_menu())


@bot.message_handler(commands=['del', 'borrar', 'd'])
def delete_search(message):
    parametros = str(message.text).split(' ', 1)
    if len(parametros) < 2:
        # Solo puso el comando
        return
    db.del_chat_search(message.chat.id, ' '.join(parametros[1:]))


@bot.message_handler(commands=['lis', 'listar', 'l'])
def get_searchs(message):
    text = ''
    for chat_search in db.get_chat_searchs(message.chat.id):
        if len(text) > 0:
            text += '\n'
        text += chat_search.kws
        text += '|'
        if chat_search.min_price is not None:
            text += chat_search.min_price
        text += '-'
        if chat_search.max_price is not None:
            text += chat_search.max_price
        if chat_search.cat_ids is not None:
            text += '|'
            text += chat_search.cat_ids
    if len(text) > 0:
        bot.send_message(message.chat.id, (text,))


# /add búsqueda,min-max,categorías separadas por comas
@bot.message_handler(commands=['add', 'añadir', 'append', 'a'])
def add_search(message):
    cs = ChatSearch()
    cs.chat_id = message.chat.id
    parametros = str(message.text).split(' ', 1)
    if len(parametros) < 2:
        # Solo puso el comando
        return
    token = ' '.join(parametros[1:]).split(',')
    if len(token) < 1:
        # Puso un espacio después del comando, nada más
        return
    cs.kws = token[0].strip()
    if len(token) > 1:
        rango = token[1].split('-')
        cs.min_price = rango[0].strip()
        if len(rango) > 1:
            cs.max_price = rango[1].strip()
    if len(token) > 2:
        cs.cat_ids = sub('[\s+]', '', ','.join(token[2:]))
        if len(cs.cat_ids) == 0:
            cs.cat_ids = None
    cs.username = message.from_user.username
    cs.name = message.from_user.first_name
    cs.active = 1
    logging.info('%s', cs)
    db.add_search(cs)
    
    # Enviar mensaje de confirmación
    confirmation_text = f"✅ *Búsqueda añadida correctamente*\n\n"
    confirmation_text += f"🔍 Búsqueda: `{cs.kws}`\n"
    if cs.min_price is not None or cs.max_price is not None:
        confirmation_text += f"💰 Rango de precio: "
        if cs.min_price is not None:
            confirmation_text += f"{cs.min_price}€"
        confirmation_text += " - "
        if cs.max_price is not None:
            confirmation_text += f"{cs.max_price}€"
        confirmation_text += "\n"
    if cs.cat_ids is not None:
        confirmation_text += f"📂 Categorías: `{cs.cat_ids}`\n"
    
    bot.send_message(message.chat.id, confirmation_text, parse_mode='Markdown')


# Manejador para texto cuando el usuario está en un wizard
@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_wizard_text(message):
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    
    if state.get('step') == 'waiting_keywords':
        # Usuario escribió las palabras clave para búsqueda
        keywords = message.text.strip()
        
        if not keywords:
            bot.send_message(user_id, "❌ Por favor, escribe algo para buscar")
            return
        
        # Guardar keywords y mostrar opciones de precio
        user_states[user_id]['keywords'] = keywords
        user_states[user_id]['step'] = 'select_price'
        
        show_price_selection_step(message, keywords)
    
    elif state.get('step') == 'waiting_custom_price':
        # Usuario escribió precio personalizado
        handle_custom_price_input(message)

def show_price_selection_step(message, keywords):
    text = f'➕ **Añadir nueva búsqueda - Paso 2/2**\n\n'
    text += f'🔍 Producto: `{keywords}`\n\n'
    text += '� **¿Qué rango de precio te interesa?**\n'
    text += 'Selecciona una opción:'
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Rangos predefinidos
    ranges = [
        ("💸 Hasta 50€", "0-50"),
        ("💵 50€ - 100€", "50-100"),
        ("💴 100€ - 200€", "100-200"),
        ("💶 200€ - 500€", "200-500"),
        ("💷 500€+", "500-")
    ]
    
    for name, price_range in ranges:
        btn = types.InlineKeyboardButton(name, callback_data=f"wizprice_{price_range}")
        markup.add(btn)
    
    # Opciones adicionales
    btn_custom = types.InlineKeyboardButton("✍️ Personalizar", callback_data="wizprice_custom")
    btn_no_limit = types.InlineKeyboardButton("🔄 Sin límite", callback_data="wizprice_none")
    markup.add(btn_custom, btn_no_limit)
    
    btn_back = types.InlineKeyboardButton("🔙 Cambiar búsqueda", callback_data="add_search")
    markup.add(btn_back)
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


def handle_wizard_price_selection(message, callback_data, user_id):
    price_selection = callback_data[9:]  # Quitar "wizprice_"
    state = user_states.get(user_id, {})
    keywords = state.get('keywords', '')
    
    if price_selection == "custom":
        # Solicitar precio personalizado
        text = '✍️ **Precio personalizado**\n\n'
        text += f'🔍 Producto: `{keywords}`\n\n'
        text += '💰 **Escribe el rango de precio en el siguiente mensaje:**\n\n'
        text += '📝 **Formato:** `min-max`\n\n'
        text += '🔢 **Ejemplos válidos:**\n'
        text += '• `100-500` → entre 100€ y 500€\n'
        text += '• `200-` → desde 200€ (sin límite superior)\n'
        text += '• `-300` → hasta 300€ (sin límite inferior)\n'
        text += '• `150` → precio máximo 150€\n\n'
        text += '⚠️ **Importante:** Escribe el precio en tu próximo mensaje'
        
        markup = types.InlineKeyboardMarkup()
        btn_cancel = types.InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")
        markup.add(btn_cancel)
        
        # Enviar un mensaje nuevo en lugar de editar
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
        
        user_states[user_id]['step'] = 'waiting_custom_price'
        return
    
    # Procesar selección de precio y crear búsqueda
    min_price = None
    max_price = None
    
    if price_selection != "none":
        if '-' in price_selection:
            parts = price_selection.split('-')
            min_price = parts[0] if parts[0] else None
            max_price = parts[1] if len(parts) > 1 and parts[1] else None
    
    # Crear la búsqueda
    create_final_search(message, user_id, keywords, min_price, max_price)

def create_final_search(message, user_id, keywords, min_price, max_price):
    try:
        # Crear búsqueda
        cs = ChatSearch()
        cs.chat_id = user_id
        cs.kws = keywords
        cs.min_price = min_price
        cs.max_price = max_price
        cs.username = message.from_user.username if hasattr(message, 'from_user') else None
        cs.name = message.from_user.first_name if hasattr(message, 'from_user') else None
        cs.active = 1
        
        logging.info('Creando búsqueda: %s', cs)
        db.add_search(cs)
        
        # Mensaje de confirmación final
        text = '✅ **¡Búsqueda creada exitosamente!**\n\n'
        text += f'🔍 **Producto:** `{keywords}`\n'
        
        if min_price or max_price:
            text += f'💰 **Rango de precio:** {min_price or "0"}€ - {max_price or "∞"}€\n'
        else:
            text += f'� **Precio:** Sin límite\n'
            
        text += '\n🔔 **Te notificaré cuando encuentre:**\n'
        text += '• Nuevos productos que coincidan\n'
        text += '• Bajadas de precio\n'
        text += '• Información del vendedor\n\n'
        text += '⏱️ Revisión cada 5 minutos'
        
        markup = create_main_menu()
        
        # Usar send_message en lugar de edit_message_text para evitar problemas
        bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=markup)
        
        # Limpiar estado
        if user_id in user_states:
            del user_states[user_id]
            
    except Exception as e:
        logging.error(f"Error creando búsqueda final: {e}")
        error_text = "❌ **Error al crear la búsqueda**\n\n"
        error_text += "Inténtalo de nuevo con /start"
        
        bot.send_message(user_id, error_text, parse_mode='Markdown')
        
        # Limpiar estado incluso si hay error
        if user_id in user_states:
            del user_states[user_id]


def handle_custom_price_input(message):
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    keywords = state.get('keywords', '')
    price_text = message.text.strip()
    
    try:
        # Limpiar texto de entrada (quitar símbolos € si los hay)
        price_text = price_text.replace('€', '').replace(',', '.')
        
        min_price = None
        max_price = None
        
        if '-' in price_text:
            # Formato: min-max, -max, o min-
            parts = price_text.split('-', 1)
            min_part = parts[0].strip()
            max_part = parts[1].strip() if len(parts) > 1 else ""
            
            # Validar precio mínimo
            if min_part:
                if not is_valid_price(min_part):
                    raise ValueError(f"Precio mínimo '{min_part}' no es válido")
                min_price = min_part
                
            # Validar precio máximo  
            if max_part:
                if not is_valid_price(max_part):
                    raise ValueError(f"Precio máximo '{max_part}' no es válido")
                max_price = max_part
                
        else:
            # Solo un número: asumir que es precio máximo
            if price_text:
                if not is_valid_price(price_text):
                    raise ValueError(f"Precio '{price_text}' no es válido")
                max_price = price_text
        
        # Verificar que al menos uno de los precios esté definido
        if not min_price and not max_price:
            raise ValueError("Debes especificar al menos un precio (mínimo o máximo)")
        
        # Verificar lógica de precios (min < max)
        if min_price and max_price:
            if float(min_price) >= float(max_price):
                raise ValueError("El precio mínimo debe ser menor que el máximo")
        
        # Crear la búsqueda final
        success_text = f"✅ **Precio configurado correctamente**\n\n"
        success_text += f"🔍 Producto: `{keywords}`\n"
        success_text += f"💰 Precio: {min_price or '0'}€ - {max_price or '∞'}€\n\n"
        success_text += "⏳ Creando búsqueda..."
        
        bot.send_message(user_id, success_text, parse_mode='Markdown')
        create_final_search(message, user_id, keywords, min_price, max_price)
        
    except ValueError as e:
        error_text = f"❌ **Error en el formato**\n\n"
        error_text += f"**Problema:** {str(e)}\n\n"
        error_text += f"📝 **Formatos válidos:**\n"
        error_text += f"• `100-500` → entre 100€ y 500€\n"
        error_text += f"• `200-` → desde 200€\n"
        error_text += f"• `-300` → hasta 300€\n"
        error_text += f"• `150` → máximo 150€\n\n"
        error_text += f"💡 Vuelve a escribir el precio:"
        
        bot.send_message(user_id, error_text, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Error procesando precio personalizado: {e}")
        error_text = f"❌ **Error inesperado**\n\n"
        error_text += f"Inténtalo de nuevo o cancela con /start"
        
        bot.send_message(user_id, error_text, parse_mode='Markdown')

def is_valid_price(price_str):
    """Validar que una cadena sea un precio válido (número positivo)"""
    try:
        price = float(price_str)
        return price >= 0
    except (ValueError, TypeError):
        return False


# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     print('echo: "' + message.text + '"')
#     bot.reply_to(message, message.text)

# Configurar ruta de logs según el entorno
pathlog = 'wallbot.log'
if PROFILE is None:
    pathlog = '/logs/' + pathlog
else:
    # En Docker o entornos controlados, usar directorio específico
    log_dir = os.getenv('LOG_DIR', '/app/logs')
    os.makedirs(log_dir, exist_ok=True)
    pathlog = os.path.join(log_dir, 'wallbot.log')

logging.basicConfig(
    handlers=[RotatingFileHandler(pathlog, maxBytes=1000000, backupCount=10)],
#    filename='wallbot.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

#logger = telebot.logger
#formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
#                              '%m-%d %H:%M:%S')
#ch = logging.StreamHandler(sys.stdout)
#logger.addHandler(ch)
#logger.setLevel(logging.INFO)  # or use logging.INFO
#ch.setFormatter(formatter)


# FIN

def wallapop():
    while True:
        # Recupera de db las búsquedas que hay que hacer en wallapop con sus respectivos chats_id
        for search in db.get_chats_searchs():
            u = get_url_list(search)

            # Lanza las búsquedas y notificaciones ...
            get_items(u, search.chat_id, search.kws)

        # Borrar items antiguos (> 24hrs?)
        # No parece buena idea. Vuelven a entrar cada 5min algunos
        # db.deleteItems(24)

        time.sleep(300)
        continue


def recovery(times):
    try:
        time.sleep(times)
        logging.info("Conexión a Telegram.")
        print("Conexión a Telegram")
        bot.polling(none_stop=True, timeout=3000)
    except Exception as e:
        logging.error("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión", e)
        print("Ha ocurrido un error con la llamada a Telegram. Se reintenta la conexión")
        if times > 16:
            times = 16
        recovery(times*2)


def main():
    print("JanJanJan starting...")
    logging.info("JanJanJan starting...")
    db.setup(readVersion())
    threading.Thread(target=wallapop).start()
    recovery(1)


def readVersion():
    file = open("VERSION", "r")
    version = file.readline()
    logging.info("Version %s", version)
    return version


if __name__ == '__main__':
    main()
