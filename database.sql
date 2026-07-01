-- ==========================================
-- 1. СБРОС СТАРЫХ ТАБЛИЦ (чтобы не было конфликтов при пересоздании)
-- ==========================================
DROP TABLE IF EXISTS training;
DROP TABLE IF EXISTS training_type;
DROP TABLE IF EXISTS membership;
DROP TABLE IF EXISTS [user];
DROP TABLE IF EXISTS role;

-- ==========================================
-- 2. СОЗДАНИЕ ТАБЛИЦ И СТРУКТУРЫ ДАННЫХ
-- ==========================================

-- Таблица ролей
CREATE TABLE role (
    role_type NVARCHAR(50) PRIMARY KEY
);

-- Таблица пользователей (Адаптирована под Telegram ID)
CREATE TABLE [user] (
    user_id BIGINT PRIMARY KEY,               -- BIGINT без IDENTITY, чтобы bot.py отправлял Telegram ID напрямую
    user_name NVARCHAR(100) NULL,             -- NULL, так как при /start мы знаем только юзернейм
    fio NVARCHAR(255) DEFAULT 'Заполняется',  -- Значение по умолчанию на время прохождения регистрации
    phone_number NVARCHAR(50) NULL,
    role_type NVARCHAR(50) DEFAULT 'user',
    FOREIGN KEY (role_type) REFERENCES role(role_type)
);

-- Таблица абонементов клиентов
CREATE TABLE membership (
    membership_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    type NVARCHAR(100),
    price DECIMAL(10, 2),
    validity_date DATE,
    FOREIGN KEY (user_id) REFERENCES [user](user_id) ON DELETE CASCADE
);

-- Таблица видов тренировок
CREATE TABLE training_type (
    tr_type_id INT IDENTITY(1,1) PRIMARY KEY,
    type NVARCHAR(100),
    time NVARCHAR(50) NOT NULL,
    num_of_places INT
);

-- Таблица расписания занятий
CREATE TABLE training (
    training_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id_coach BIGINT NOT NULL,            -- ID тренера из таблицы [user]
    membership_id_client INT NULL,            -- Ссылка на абонемент (если занятие персональное)
    tr_type_id INT NOT NULL,                  -- Ссылка на тип тренировки
    day_of_the_week INT NOT NULL,             -- День недели (1 - Понедельник, и т.д.)
    FOREIGN KEY (user_id_coach) REFERENCES [user](user_id),
    FOREIGN KEY (membership_id_client) REFERENCES membership(membership_id),
    FOREIGN KEY (tr_type_id) REFERENCES training_type(tr_type_id)
);

-- ==========================================
-- 3. НАПОЛНЕНИЕ НАЧАЛЬНЫМИ (ТЕСТОВЫМИ) ДАННЫМИ
-- ==========================================

-- Заполняем роли
INSERT INTO role (role_type) VALUES ('admin'), ('coach'), ('manager'), ('user');

-- Добавляем дефолтных тренеров (с фиксированными ID 1 и 2)
INSERT INTO [user] (user_id, fio, user_name, phone_number, role_type) VALUES
(1, N'Алексей Петров (Тренер)', 'alex_coach', '+375291112233', 'coach'),
(2, N'Мария Сидорова (Тренер)', 'maria_fit', '+375332223344', 'coach');

-- Заполняем типы тренировок
INSERT INTO training_type (type, time, num_of_places) VALUES
(N'Йога утром', '09:00:00', 15),
(N'Кроссфит вечер', '19:30:00', 10);

-- Создаем базовое расписание
INSERT INTO training (user_id_coach, tr_type_id, day_of_the_week) VALUES
(1, 2, 1), -- Алексей ведет Кроссфит в Понедельник
(2, 1, 3); -- Мария ведет Йогу в Среду