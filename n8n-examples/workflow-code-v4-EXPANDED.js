// 🎮 Gaming Templates v4.0 - НОВАЯ версия с разбором Title
// ПРАВИЛЬНЫЙ ФОРМАТ: каждый субтитр = отдельный text_item
// (НЕ вложенный subtitles.items, а развёрнутый массив)
// 
// РАЗНИЦА ОТ LEGACY:
// - Title разбивается на отдельные атомы (если содержит несколько строк)
// - Каждый atom становится отдельным text_item
// - Идеально для создания многоуровневых заголовков
//
// Для старого поведения (Title как есть) используйте: workflow-code-v4-LEGACY.js

// ✅ ДОСТУПНЫЕ ШРИФТЫ В ПУБЛИЧНОЙ ВЕРСИИ (10 штук):
// 1. Charter.ttc - Modern Serif
// 2. Copperplate.ttc - Декоративный стиль
// 3. HelveticaNeue.ttc - Premium Sans-Serif
// 4. LucidaGrande.ttc - Элегантный Sans-Serif
// 5. MarkerFelt.ttc - Креативный стиль
// 6. Menlo.ttc - Monospace
// 7. Monaco.ttf - Monospace
// 8. PTSans.ttc - Русский шрифт
// 9. Palatino.ttc - Классический Serif
// 10. STIXTwoText-Italic.ttf - Научный (Math)

// ═══════════════════════════════════════════════════════════════════════════
// 📋 ИНСТРУКЦИЯ: ВСТАВКА ШАБЛОНОВ В N8N
// ═══════════════════════════════════════════════════════════════════════════
//
// ⚠️ ВАЖНО: Шаблоны хранятся в отдельном файле templates-definitions.js
//
// 📁 Файл с шаблонами: n8n-examples/templates-definitions.js
//    Содержит 60 универсальных шаблонов в 4 категориях
//
// 🔧 ИНСТРУКЦИЯ ПО ВСТАВКЕ:
// 1. Откройте файл templates-definitions.js
// 2. Скопируйте весь объект VIDEO_TEMPLATES (строки 39-1865)
// 3. Вставьте его содержимое ВМЕСТО пустого объекта ниже
//
// 📝 Результат должен выглядеть так:
//    const VIDEO_TEMPLATES = {
//       "cyber_neon": { name: "Cyber Neon", ... },
//       "fire_ice": { name: "Fire & Ice", ... },
//       ... (всего 60 шаблонов)
//    };
//
// ═══════════════════════════════════════════════════════════════════════════

// 👇 ВСТАВЬТЕ СЮДА СОДЕРЖИМОЕ VIDEO_TEMPLATES ИЗ templates-definitions.js
const VIDEO_TEMPLATES = {
	// ЗДЕСЬ БУДУТ ВАШИ 60 ШАБЛОНОВ
	// Скопируйте содержимое объекта VIDEO_TEMPLATES из templates-definitions.js (строки 39-1865)
};

// =====================================================
// ФУНКЦИЯ ВЫБОРА ШАБЛОНА
// =====================================================
function selectTemplate(clientMeta) {
	let filteredTemplates = Object.entries(GAMING_TEMPLATES);

	// Фильтр по точному имени шаблона
	if (clientMeta.template_name && GAMING_TEMPLATES[clientMeta.template_name]) {
		filteredTemplates = [[clientMeta.template_name, GAMING_TEMPLATES[clientMeta.template_name]]];
	}
	// Фильтр по категории
	else if (clientMeta.template_category) {
		filteredTemplates = filteredTemplates.filter(([key, tpl]) =>
			tpl.category === clientMeta.template_category
		);
	}

	// Фильтр по жанру (если есть)
	if (clientMeta.template_genre && filteredTemplates.length > 1) {
		const genreFiltered = filteredTemplates.filter(([key, tpl]) =>
			tpl.best_for.includes(clientMeta.template_genre)
		);
		if (genreFiltered.length > 0) {
			filteredTemplates = genreFiltered;
		}
	}

	// Случайный выбор из отфильтрованных
	const [templateKey, tpl] = filteredTemplates[Math.floor(Math.random() * filteredTemplates.length)];
	return { templateKey, tpl, totalFiltered: filteredTemplates.length };
}

// =====================================================
// ПРАВИЛЬНАЯ ФУНКЦИЯ: раскрывает каждый субтитр в text_item
// =====================================================
function createOperation(item, templateKey, tpl) {
	const data = item.json;
	const shorts = data.shorts || data;
	const clientMeta = shorts.client_meta || data.client_meta || {};
	const sourceUrl = data.source_video_url || shorts.source_video_url;

	// Создаем массив text_items
	const textItems = [];

	// Item 1: Title (заголовок всегда)
	textItems.push({
		text: shorts.title,
		fontfile: tpl.title.fontfile,
		fontsize: tpl.title.fontsize,
		fontcolor: tpl.title.fontcolor,
		x: tpl.title.x,
		y: tpl.title.y,
		start: 0.0,
		end: 999,  // До конца видео
		box: tpl.title.box,
		boxcolor: tpl.title.boxcolor || undefined,
		boxborderw: tpl.title.boxborderw || undefined
	});

	// Items 2+: КАЖДЫЙ СУБТИТР - отдельный text_item с одинаковыми параметрами
	// но разными текстом и временем
	if (shorts.subtitles && shorts.subtitles.length > 0) {
		shorts.subtitles.forEach((subtitleObj) => {
			// Поддерживаем оба формата: простой текст или объект с timing
			const subtitleText = subtitleObj.text || subtitleObj;
			const startTime = subtitleObj.start !== undefined ? subtitleObj.start : 0;
			const endTime = subtitleObj.end !== undefined ? subtitleObj.end : (startTime + 5);

			textItems.push({
				text: subtitleText,
				fontfile: tpl.sub.fontfile,
				fontsize: tpl.sub.fontsize,
				fontcolor: tpl.sub.fontcolor,
				x: tpl.sub.x,
				y: tpl.sub.y,
				start: startTime,
				end: endTime,
				box: tpl.sub.box,
				boxcolor: tpl.sub.boxcolor || undefined,
				boxborderw: tpl.sub.boxborderw || undefined
			});
		});
	}

	return {
		json: {
			video_url: sourceUrl,
			execution: "async",
			operations: [{
				type: "make_short",
				start_time: shorts.start,
				end_time: shorts.end,
				crop_mode: "letterbox",
				letterbox_config: {
					blur_radius: 20
				},
				text_items: textItems,  // ✅ Плоский массив, каждый субтитр = отдельный item
				generate_thumbnail: true,
				thumbnail_timestamp: 0.5
			}],
			client_meta: {
				...clientMeta,
				_template_key: templateKey,
				_template_name: tpl.name,
				_template_category: tpl.category,
				_template_genres: tpl.best_for,
				_templates_available: 0,
				_input_item_index: item.index
			}
		}
	};
}

// =====================================================
// ГЛАВНАЯ ЛОГИКА
// =====================================================
const items = $input.all();
const results = items.map((item) => {
	const clientMeta = (item.json.shorts || item.json).client_meta || item.json.client_meta || {};
	const { templateKey, tpl, totalFiltered } = selectTemplate(clientMeta);
	const operation = createOperation(item, templateKey, tpl);

	operation.json.client_meta._templates_available = totalFiltered;

	return operation;
});

return results;
