USE ProjectDB; -- подставьте вашу базу
GO

-- Очищаем старые таблицы, если они были (в обратном порядке из-за связей)

DROP TABLE IF EXISTS training;

DROP TABLE IF EXISTS training_type;

DROP TABLE IF EXISTS membership;

DROP TABLE IF EXISTS [user];

DROP TABLE IF EXISTS role;

GO



-- 1. Справочник ролей

CREATE TABLE role (

    role_type NVARCHAR(50) PRIMARY KEY

);



-- Наполнение ролей

INSERT INTO role (role_type) VALUES ('admin'), ('coach'), ('manager'), ('user');

GO



-- 2. Таблица пользователей

CREATE TABLE [user] (

    user_id INT IDENTITY(1,1) PRIMARY KEY, 

    fio NVARCHAR(255) NOT NULL,            

    user_name NVARCHAR(100) UNIQUE NOT NULL,

    phone_number NVARCHAR(20),

    user_data NVARCHAR(MAX),               

    role_type NVARCHAR(50),

    FOREIGN KEY (role_type) REFERENCES role(role_type)

);



-- Заполняем пользователей

INSERT INTO [user] (fio, user_name, phone_number, role_type) VALUES

(N'Анфиса Синковец (Тренер)', 'anfisa_boss', '+375293555177', 'coach'),

(N'Полина Шинкоренко (Тренер)', 'polina_nagibator', '+375445117899', 'coach'),

(N'Иван Иванов (Клиент)', 'vanya_client', '+375445556677', 'user'),

(N'Елена Смирнова (Клиент)', 'elena_smart', '+375258889900', 'user');

GO



-- 3. Таблица абонементов

CREATE TABLE membership (

    membership_id INT IDENTITY(1,1) PRIMARY KEY,

    user_id INT NOT NULL,

    type NVARCHAR(100),

    price DECIMAL(10, 2), 

    validity_date DATE,

    FOREIGN KEY (user_id) REFERENCES [user](user_id) ON DELETE CASCADE

);



-- Заполняем абонементы. Т.к. база создается с нуля, у Ивана будет user_id = 3, у Елены = 4

INSERT INTO membership (user_id, type, price, validity_date) VALUES

(3, N'Безлимит 1 месяц', 150.00, '2026-07-30'), 

(4, N'8 занятий', 95.50, '2026-08-15');        

GO



-- 4. Таблица типов тренировок

CREATE TABLE training_type (

    tr_type_id INT IDENTITY(1,1) PRIMARY KEY,

    type NVARCHAR(100),

    time TIME,

    num_of_places INT

);



-- Заполняем типы тренировок

INSERT INTO training_type (type, time, num_of_places) VALUES

(N'Йога утром', '09:00:00', 15),

(N'Кроссфит вечер', '19:30:00', 10);

GO



-- 5. Таблица тренировок

CREATE TABLE training (

    training_id INT IDENTITY(1,1) PRIMARY KEY,

    user_id_coach INT NOT NULL,      

    membership_id_client INT,        

    tr_type_id INT NOT NULL,         

    day_of_the_week INT NOT NULL,    

    

    FOREIGN KEY (user_id_coach) REFERENCES [user](user_id),

    FOREIGN KEY (membership_id_client) REFERENCES membership(membership_id),

    FOREIGN KEY (tr_type_id) REFERENCES training_type(tr_type_id)

);



-- Назначаем тренировки (теперь id абонементов 1 и 2 гарантированно сядут на свои места)

INSERT INTO training (user_id_coach, membership_id_client, tr_type_id, day_of_the_week) VALUES

(2, 1, 2, 1),

(1, 2, 1, 3);

GO



-- ВЫВОД РЕЗУЛЬТАТА

SELECT 

    t.training_id AS [ID Занятия],

    u_coach.fio AS [ФИО Тренера],

    u_coach.phone_number AS [Телефон тренера],

    tt.type AS [Тип тренировки],

    tt.time AS [Время начала],

    t.day_of_the_week AS [День недели (1-Пн, 3-Ср)],

    u_client.fio AS [ФИО Клиента],

    m.type AS [Тип абонемента],

    m.price AS [Цена абонемента (BYN)]

FROM training t

JOIN [user] u_coach ON t.user_id_coach = u_coach.user_id

JOIN training_type tt ON t.tr_type_id = tt.tr_type_id

LEFT JOIN membership m ON t.membership_id_client = m.membership_id

LEFT JOIN [user] u_client ON m.user_id = u_client.user_id;

