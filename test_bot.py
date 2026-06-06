# test_bot.py - Unit тесты для Telegram-бота погоды
# Запуск: python test_bot.py

import unittest
from datetime import datetime
import pytz
import sys
import os
from unittest.mock import patch
import datetime as dt

# Добавляем путь к основному файлу
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем функции для тестирования
from main import get_clothing_advice, get_digest_type, get_holiday_info
from database import Database


class TestClothingAdvice(unittest.TestCase):
    """Тесты функции рекомендаций по одежде"""
    
    def test_very_cold(self):
        """Температура ниже -10°C"""
        result = get_clothing_advice(-15)
        self.assertIn('шуба', result.lower())
        self.assertIn('пуховик', result.lower())
        print(f"✅ -15°C: {result}")
    
    def test_cold(self):
        """Температура от -10°C до 0°C"""
        result = get_clothing_advice(-5)
        self.assertIn('теплая куртка', result.lower())
        self.assertIn('шапка', result.lower())
        print(f"✅ -5°C: {result}")
    
    def test_cool(self):
        """Температура от 0°C до 10°C"""
        result = get_clothing_advice(5)
        self.assertIn('демисезонная куртка', result.lower())
        self.assertIn('водолазка', result.lower())
        print(f"✅ 5°C: {result}")
    
    def test_comfortable(self):
        """Температура от 10°C до 20°C"""
        result = get_clothing_advice(15)
        self.assertIn('свитер', result.lower())
        self.assertIn('толстовка', result.lower())
        print(f"✅ 15°C: {result}")
    
    def test_warm(self):
        """Температура от 20°C до 25°C"""
        result = get_clothing_advice(22)
        self.assertIn('футболка', result.lower())
        self.assertIn('шорты', result.lower())
        print(f"✅ 22°C: {result}")
    
    def test_very_warm(self):
        """Температура выше 25°C"""
        result = get_clothing_advice(30)
        self.assertIn('шорты', result.lower())
        self.assertIn('майка', result.lower())
        print(f"✅ 30°C: {result}")


class TestDigestType(unittest.TestCase):
    """Тесты определения типа дайджеста по времени суток"""
    
    def test_morning(self):
        """Утренний дайджест (5:00 - 12:00)"""
        time = datetime(2025, 1, 1, 8, 0)
        result = get_digest_type(time)
        self.assertEqual(result, "Утренний")
        print(f"✅ 08:00 → {result}")
    
    def test_noon(self):
        """Полдень (12:00)"""
        time = datetime(2025, 1, 1, 12, 0)
        result = get_digest_type(time)
        self.assertEqual(result, "Дневной")
        print(f"✅ 12:00 → {result}")
    
    def test_afternoon(self):
        """Дневной дайджест (12:00 - 17:00)"""
        time = datetime(2025, 1, 1, 14, 30)
        result = get_digest_type(time)
        self.assertEqual(result, "Дневной")
        print(f"✅ 14:30 → {result}")
    
    def test_evening(self):
        """Вечерний дайджест (17:00 - 22:00)"""
        time = datetime(2025, 1, 1, 19, 0)
        result = get_digest_type(time)
        self.assertEqual(result, "Вечерний")
        print(f"✅ 19:00 → {result}")
    
    def test_night(self):
        """Ночной дайджест (22:00 - 5:00)"""
        time = datetime(2025, 1, 1, 23, 0)
        result = get_digest_type(time)
        self.assertEqual(result, "Ночной")
        print(f"✅ 23:00 → {result}")
    
    def test_early_morning(self):
        """Раннее утро (2:00)"""
        time = datetime(2025, 1, 1, 2, 0)
        result = get_digest_type(time)
        self.assertEqual(result, "Ночной")
        print(f"✅ 02:00 → {result}")


class TestHolidayInfo(unittest.TestCase):
    """Тесты функции получения информации о праздниках"""
    
    @patch('main.datetime')
    def test_new_year(self, mock_datetime):
        """Новый год (01.01)"""
        mock_datetime.now.return_value = dt.datetime(2025, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: dt.datetime(*args, **kwargs)
        
        result = get_holiday_info()
        self.assertIsNotNone(result)
        self.assertIn('Новый год', result)
        print(f"✅ 01.01: {result}")
    
    @patch('main.datetime')
    def test_victory_day(self, mock_datetime):
        """День Победы (09.05)"""
        mock_datetime.now.return_value = dt.datetime(2025, 5, 9)
        mock_datetime.side_effect = lambda *args, **kwargs: dt.datetime(*args, **kwargs)
        
        result = get_holiday_info()
        self.assertIsNotNone(result)
        self.assertIn('День Победы', result)
        print(f"✅ 09.05: {result}")
    
    @patch('main.datetime')
    def test_no_holiday(self, mock_datetime):
        """Обычный день (без праздников)"""
        mock_datetime.now.return_value = dt.datetime(2025, 3, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: dt.datetime(*args, **kwargs)
        
        result = get_holiday_info()
        self.assertIsNone(result)
        print(f"✅ 15.03: {result} (нет праздника)")


class TestDatabase(unittest.TestCase):
    """Тесты работы с базой данных"""
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.db = Database()
        self.test_user_id = 999999999  # Тестовый ID
    
    def test_create_user(self):
        """Создание нового пользователя"""
        result = self.db.create_or_update_user(
            user_id=self.test_user_id,
            username='test_user',
            first_name='Тест',
            last_name='Тестов'
        )
        self.assertTrue(result)
        print(f"✅ Пользователь {self.test_user_id} создан")
    
    def test_get_user(self):
        """Получение пользователя"""
        self.db.create_or_update_user(
            user_id=self.test_user_id,
            username='test_user',
            first_name='Тест'
        )
        
        user = self.db.get_user(self.test_user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'test_user')
        self.assertEqual(user['city'], 'Москва')
        print(f"✅ Пользователь получен: {user}")
    
    def test_update_city(self):
        """Обновление города"""
        self.db.create_or_update_user(
            user_id=self.test_user_id,
            username='test_user',
            first_name='Тест'
        )
        
        result = self.db.update_user_city(self.test_user_id, 'Санкт-Петербург')
        self.assertTrue(result)
        
        user = self.db.get_user(self.test_user_id)
        self.assertEqual(user['city'], 'Санкт-Петербург')
        print(f"✅ Город обновлен: {user['city']}")
    
    def test_update_notifications(self):
        """Обновление времени уведомлений"""
        self.db.create_or_update_user(
            user_id=self.test_user_id,
            username='test_user',
            first_name='Тест'
        )
        
        new_times = ['08:00', '13:00', '20:00']
        result = self.db.update_notification_times(self.test_user_id, new_times)
        self.assertEqual(result, new_times)
        
        user = self.db.get_user(self.test_user_id)
        self.assertEqual(user['notification_times'], new_times)
        print(f"✅ Уведомления обновлены: {user['notification_times']}")
    
    def test_reset_settings(self):
        """Сброс настроек"""
        self.db.create_or_update_user(
            user_id=self.test_user_id,
            username='test_user',
            first_name='Тест',
            city='Казань'
        )
        self.db.update_notification_times(self.test_user_id, ['10:00', '22:00'])
        
        result = self.db.reset_user_settings(self.test_user_id)
        self.assertTrue(result)
        
        user = self.db.get_user(self.test_user_id)
        self.assertEqual(user['city'], 'Москва')
        self.assertEqual(user['notification_times'], ['08:00', '18:00'])
        print(f"✅ Настройки сброшены: город={user['city']}, время={user['notification_times']}")
    
    def tearDown(self):
        """Очистка после каждого теста"""
        try:
            import sqlite3
            conn = sqlite3.connect('users.db')
            conn.execute('DELETE FROM users WHERE user_id = ?', (self.test_user_id,))
            conn.commit()
            conn.close()
            print(f"🗑️ Тестовый пользователь {self.test_user_id} удален")
        except:
            pass


def run_tests():
    """Запуск всех тестов с красивым выводом"""
    print("=" * 70)
    print("🧪 ЗАПУСК UNIT ТЕСТОВ TELEGRAM-БОТА ПОГОДЫ")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestClothingAdvice))
    suite.addTests(loader.loadTestsFromTestCase(TestDigestType))
    suite.addTests(loader.loadTestsFromTestCase(TestHolidayInfo))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"✅ Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Ошибки: {len(result.errors)}")
    print(f"⚠️  Провалы: {len(result.failures)}")
    print(f"📝 Всего тестов: {result.testsRun}")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_tests()