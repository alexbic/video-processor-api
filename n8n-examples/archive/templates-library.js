/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 📚 TEMPLATES LIBRARY v5.0 - Template Import & Conversion Utility
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 🎯 НАЗНАЧЕНИЕ:
 * Этот файл НЕ используется напрямую в n8n workflows.
 * Он служит как утилита для импорта и конвертации шаблонов из templates-definitions.js
 * в формат, совместимый с legacy API или другими системами.
 *
 * 📁 ИСТОЧНИК ДАННЫХ:
 * Импортирует шаблоны из templates-definitions.js (60 универсальных шаблонов)
 *
 * 🔧 ФУНКЦИОНАЛЬНОСТЬ:
 * 1. Импорт VIDEO_TEMPLATES из templates-definitions.js
 * 2. Конвертация формата шаблонов (если требуется)
 * 3. Экспорт в нужном формате для внешних систем
 *
 * ⚠️ ВАЖНО:
 * - Для n8n workflows используйте templates-definitions.js напрямую
 * - Этот файл нужен только для интеграции с другими системами
 * - Содержит утилиты для работы с шаблонами (фильтрация, поиск, конвертация)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

// Импорт шаблонов из templates-definitions.js
const { VIDEO_TEMPLATES } = require('./templates-definitions.js');

/**
 * Конвертирует формат шаблонов из templates-definitions.js в legacy формат
 * (если требуется для совместимости с legacy API)
 *
 * @param {Object} templates - Объект VIDEO_TEMPLATES
 * @returns {Object} Конвертированные шаблоны
 */
function convertToLegacyFormat(templates) {
	const converted = {};

	for (const [key, template] of Object.entries(templates)) {
		converted[key] = {
			name: template.name,
			category: template.category,
			best_for: template.best_for,
			title: {
				// Переименовываем fontfile -> font если нужно
				font: template.title.fontfile,
				fontsize: template.title.fontsize,
				fontcolor: template.title.fontcolor,
				bordercolor: template.title.bordercolor,
				borderw: template.title.borderw,
				x: template.title.x,
				y: template.title.y,
				box: template.title.box,
				boxcolor: template.title.boxcolor,
				boxborderw: template.title.boxborderw,
				max_lines: template.title.max_lines
			},
			sub: {
				font: template.sub.fontfile,
				fontsize: template.sub.fontsize,
				fontcolor: template.sub.fontcolor,
				bordercolor: template.sub.bordercolor,
				borderw: template.sub.borderw,
				x: template.sub.x,
				y: template.sub.y,
				box: template.sub.box,
				boxcolor: template.sub.boxcolor,
				boxborderw: template.sub.boxborderw,
				max_lines: template.sub.max_lines
			}
		};
	}

	return converted;
}

/**
 * Фильтрует шаблоны по категории
 *
 * @param {string} category - Название категории (NEON_GLOW, SOLID_FRAMES, etc.)
 * @returns {Object} Отфильтрованные шаблоны
 */
function filterByCategory(category) {
	const filtered = {};
	for (const [key, template] of Object.entries(VIDEO_TEMPLATES)) {
		if (template.category === category) {
			filtered[key] = template;
		}
	}
	return filtered;
}

/**
 * Фильтрует шаблоны по тегу best_for
 *
 * @param {string} tag - Тег (например, "Minecraft", "horror", "fps")
 * @returns {Object} Отфильтрованные шаблоны
 */
function filterByTag(tag) {
	const filtered = {};
	for (const [key, template] of Object.entries(VIDEO_TEMPLATES)) {
		if (template.best_for.includes(tag)) {
			filtered[key] = template;
		}
	}
	return filtered;
}

/**
 * Возвращает статистику по шаблонам
 *
 * @returns {Object} Статистика
 */
function getTemplateStats() {
	const stats = {
		total: Object.keys(VIDEO_TEMPLATES).length,
		categories: {},
		tags: new Set()
	};

	for (const template of Object.values(VIDEO_TEMPLATES)) {
		// Подсчёт по категориям
		if (!stats.categories[template.category]) {
			stats.categories[template.category] = 0;
		}
		stats.categories[template.category]++;

		// Сбор всех тегов
		for (const tag of template.best_for) {
			stats.tags.add(tag);
		}
	}

	stats.tags = Array.from(stats.tags).sort();

	return stats;
}

// ═══════════════════════════════════════════════════════════════════════════
// ЭКСПОРТ
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
	// Оригинальные шаблоны из templates-definitions.js
	VIDEO_TEMPLATES,

	// Legacy формат (для совместимости со старыми API)
	GAMING_TEMPLATES: VIDEO_TEMPLATES, // Alias для обратной совместимости

	// Утилиты
	convertToLegacyFormat,
	filterByCategory,
	filterByTag,
	getTemplateStats
};

// ═══════════════════════════════════════════════════════════════════════════
// ПРИМЕР ИСПОЛЬЗОВАНИЯ
// ═══════════════════════════════════════════════════════════════════════════

/*
// Импорт всех шаблонов
const { VIDEO_TEMPLATES } = require('./templates-library.js');

// Фильтрация по категории
const { filterByCategory } = require('./templates-library.js');
const neonTemplates = filterByCategory('NEON_GLOW');

// Фильтрация по тегу
const { filterByTag } = require('./templates-library.js');
const minecraftTemplates = filterByTag('Minecraft');

// Статистика
const { getTemplateStats } = require('./templates-library.js');
const stats = getTemplateStats();
console.log(`Total templates: ${stats.total}`);
console.log(`Categories: ${Object.keys(stats.categories).join(', ')}`);
console.log(`Total tags: ${stats.tags.length}`);
*/
