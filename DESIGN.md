# Design System — ООО «ПрофЭксперт» (Izometry Architectural B2B)

> Category: Enterprise B2B / Industrial Compliance / Architectural Minimalist
> Style Family: Izometry Grid System, High-contrast Monochrome, Crisp Technical Typography

---

## 1. Visual Theme & Atmosphere

- **Core Character:** Строгий, инженерный, авторитетный B2B-стиль без «мусорных» градиентов и дешевых украшений (Anti-AI-Slop).
- **Inspiration:** Архитектурная сетка, строгие линии, прямоугольные блоки с тонкими контурами (1px solid #d8d8d8), контраст глубокого черного (#020203) и чистого белого (#ffffff).
- **Emotional Stance:** Экспертность, надежность, защита от проверок ГИТ и штрафов.

---

## 2. Color Tokens (CSS Variables)

- --color-primary: #020203 (Основные заголовки, активные кнопки, сильные акценты)
- --color-secondary: #676767 (Второстепенный текст, описания)
- --color-muted: #888888 (Подписи, даты, плейсхолдеры, технические метки)
- --color-bg-main: #fbfbfb (Основной фон страницы)
- --color-bg-surface: #ffffff (Карточки, модальные окна, таблицы, инпуты)
- --color-bg-alt: #efefef (Бейджи, подложки тегов, вторичные плашки)
- --color-border: #d8d8d8 (Разделители, контуры карточек строго 1px)
- --color-hover: #7f7f7f (Состояния наведения ссылок и кнопок)
- --color-danger: #dc2626 (Ошибки валидации, удаление)
- --color-success: #16a34a (Успешные статусы, бейджи)

---

## 3. Typography & Hierarchy

- **Font Family:** 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **H1 (Hero):** clamp(1.6rem, 3.2vw, 2.5rem) — font-weight: 700; line-height: 1.15; letter-spacing: -0.02em
- **H2 (Section Titles):** clamp(1.6rem, 3.2vw, 2.5rem) — font-weight: 700; line-height: 1.2
- **H3 (Card Titles):** clamp(1.2rem, 2vw, 1.5rem) — font-weight: 600; line-height: 1.3
- **Body text:** 0.9375rem (15px) — line-height: 1.6; color: var(--color-secondary)
- **Small / Meta:** 0.75rem (12px) — font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em
- **Tiny:** 0.6875rem (11px) — метки, бейджи

---

## 4. Spacing & Grid System

- **Container Max Width:** 1200px (padding: 0 24px / 0 16px на мобильных)
- **Header Height:** 96px (десктоп) / 72px (мобильный)
- **Section Spacing:** 80px–120px между смысловыми блоками
- **Card Padding:** 32px–40px (десктоп) / 20px–24px (мобильный)
- **Border Radius:** 0px (строгая прямоугольная архитектурная геометрия)

---

## 5. Anti-AI-Slop & Quality Discipline

- Запрещено: Размытые фиолетово-синие градиенты, гигантские скругления, летающие шары, пустые шаблонные карточки.
- Обязательно: Четкая верстка по сетке, реальный инженерный контент, высокая контрастность, идеальный мобильный респонсив.
