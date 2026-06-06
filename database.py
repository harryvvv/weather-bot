# Database v1.2 - 2025-12-07
# Полные исправления для совместимости с Python 3.12
# Добавлено: улучшенная обработка UTF-8, исправление проблем с Windows

import sqlite3
import logging
import sys
import os
from config import Config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с SQLite базой данных (совместимый с Python 3.12)"""
    
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            # Создаем директорию для БД, если её нет
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            
            # Явно указываем кодировку UTF-8 и другие параметры
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Устанавливаем кодировку для соединения
            conn.execute('PRAGMA encoding = "UTF-8"')
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('PRAGMA busy_timeout = 30000')  # 30 секунд ожидания
            
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    city TEXT DEFAULT 'Москва',
                    notification_times TEXT DEFAULT '08:00,18:00',
                    timezone TEXT DEFAULT 'Europe/Moscow',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица для праздников (кэширование)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holidays (
                    date TEXT PRIMARY KEY,
                    holiday_name TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info(f"✅ База данных инициализирована: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}", exc_info=True)
            raise
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def get_user(self, user_id):
        """Получить пользователя из базы"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'city': row[4],
                    'notification_times': row[5].split(',') if row[5] else Config.DEFAULT_NOTIFICATION_TIMES,
                    'timezone': row[6]
                }
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}", exc_info=True)
            return None
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def create_or_update_user(self, user_id, username=None, first_name=None, last_name=None, city=None):
        """Создать или обновить пользователя"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Обновляем существующего пользователя
                update_fields = []
                update_values = []
                
                if username is not None:
                    update_fields.append("username = ?")
                    update_values.append(username)
                
                if first_name is not None:
                    update_fields.append("first_name = ?")
                    update_values.append(first_name)
                
                if last_name is not None:
                    update_fields.append("last_name = ?")
                    update_values.append(last_name)
                
                if city is not None:
                    update_fields.append("city = ?")
                    update_values.append(city)
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                if update_fields:
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
                    update_values.append(user_id)
                    cursor.execute(query, update_values)
                    logger.info(f"🔄 Обновлен пользователь {user_id}")
            else:
                # Создаем нового пользователя
                default_city = city or 'Москва'
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, city)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, default_city))
                logger.info(f"🆕 Создан новый пользователь {user_id}")
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания/обновления пользователя {user_id}: {e}", exc_info=True)
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def update_user_city(self, user_id, city):
        """Обновить город пользователя"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET city = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", 
                          (city, user_id))
            conn.commit()
            logger.info(f"🏙 Обновлен город для пользователя {user_id}: {city}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления города для {user_id}: {e}", exc_info=True)
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def update_notification_times(self, user_id, times):
        """Обновить время уведомлений"""
        try:
            # Проверяем формат времени
            valid_times = []
            for time_str in times:
                time_str = time_str.strip()
                if ':' in time_str:
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            valid_times.append(f"{hour:02d}:{minute:02d}")
                    except ValueError:
                        continue
            
            if not valid_times:
                valid_times = Config.DEFAULT_NOTIFICATION_TIMES
            
            # Ограничиваем количество уведомлений
            valid_times = valid_times[:Config.MAX_NOTIFICATION_TIMES]
            
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET notification_times = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", 
                          (','.join(valid_times), user_id))
            conn.commit()
            logger.info(f"⏰ Обновлены уведомления для {user_id}: {valid_times} (МСК)")
            return valid_times
        except Exception as e:
            logger.error(f"❌ Ошибка обновления уведомлений для {user_id}: {e}", exc_info=True)
            return Config.DEFAULT_NOTIFICATION_TIMES
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def reset_user_settings(self, user_id):
        """Сбросить настройки пользователя до базовых"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET 
                    city = 'Москва',
                    notification_times = '08:00,18:00',
                    timezone = 'Europe/Moscow',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            logger.info(f"🔄 Сброшены настройки пользователя {user_id} (время по МСК)")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сброса настроек для {user_id}: {e}", exc_info=True)
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
    def get_all_users_with_notifications(self):
        """Получить всех пользователей с настройками уведомлений (время по Московскому)"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            conn.execute('PRAGMA encoding = "UTF-8"')
            
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, notification_times FROM users")
            users = cursor.fetchall()
            
            result = []
            for user_id, notification_times_str in users:
                times = notification_times_str.split(',') if notification_times_str else Config.DEFAULT_NOTIFICATION_TIMES
                result.append({
                    'user_id': user_id,
                    'notification_times': times,
                    'timezone': 'Europe/Moscow'  # ВСЕГДА Московское время
                })
            
            logger.info(f"👥 Найдено пользователей с уведомлениями: {len(result)} (время по МСК)")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователей с уведомлениями: {e}", exc_info=True)
            return []
        finally:
            if 'conn' in locals() and conn:
                conn.close()