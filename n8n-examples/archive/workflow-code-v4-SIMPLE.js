// 🎮 Gaming Templates v4.0 - SIMPLE VERSION (Вложенные subtitles)
// ИСПОЛЬЗОВАНИЕ:
// На вход: массив объектов, каждый содержит shorts (или fields) с video_url, title, start, end, subtitles
// На выход: массив операций, по одному на каждый входной элемент
//
// ОСОБЕННОСТЬ: Subtitles передаются как вложенный объект в один text_item
// Каждый элемент из массива subtitles становится отдельным drawtext фильтром
// но с наследованием параметров стиля от родительского item'а

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

// Функция перемешивания массива (Fisher-Yates shuffle)
function shuffleArray(array) {
	const shuffled = [...array];
	for (let i = shuffled.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
	}
	return shuffled;
}

// Функция выбора темплейта по фильтрам
function selectTemplate(clientMeta) {
	let filteredTemplates = Object.entries(VIDEO_TEMPLATES);

	// Фильтр по точному имени темплейта
	if (clientMeta.template_name && VIDEO_TEMPLATES[clientMeta.template_name]) {
		filteredTemplates = [[clientMeta.template_name, VIDEO_TEMPLATES[clientMeta.template_name]]];
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

	// ✅ ПОЛНОСТЬЮ СЛУЧАЙНЫЙ ВЫБОР: перемешиваем массив перед выбором
	filteredTemplates = shuffleArray(filteredTemplates);

	// Берём первый элемент из перемешанного массива
	const [templateKey, tpl] = filteredTemplates[0];
	return { templateKey, tpl, totalFiltered: filteredTemplates.length };
}

// Функция создания операции для одного входного элемента (ВЛОЖЕННЫЙ ФОРМАТ subtitles)
function createOperation(item, templateKey, tpl) {
	const data = item.json;
	const shorts = data.shorts || data;
	const clientMeta = shorts.client_meta || data.client_meta || {};
	const sourceUrl = data.source_video_url || shorts.source_video_url;

	// Создаем text_items массив (максимум 2 элемента для публичной версии)
	const textItems = [];

	// Item 1: Title (start=0, увеличенная продолжительность)
	textItems.push({
		text: shorts.title,
		fontfile: tpl.title.fontfile,
		fontsize: tpl.title.fontsize,
		fontcolor: tpl.title.fontcolor,
		x: tpl.title.x,
		y: tpl.title.y,
		start: 0.0,
		end: 7.0, // ✅ Увеличено с 5 до 7 секунд
		box: tpl.title.box,
		boxcolor: tpl.title.boxcolor || undefined,
		boxborderw: tpl.title.boxborderw || undefined,
		max_lines: tpl.title.max_lines || 3
	});

	// Item 2: Subtitles (если есть) - ВЛОЖЕННЫЙ ФОРМАТ с коррекцией timing
	if (shorts.subtitles && shorts.subtitles.length > 0) {
		// ✅ Корректируем первый субтитр: start=0, end оставляем как есть
		const correctedSubtitles = shorts.subtitles.map((sub, index) => {
			if (index === 0) {
				// Первый субтитр: start=0, end не меняем
				return {
					...sub,
					start: 0.0
				};
			}
			// Остальные субтитры без изменений
			return sub;
		});

		// Используем динамические субтитры как вложенный объект
		textItems.push({
			text: "", // Пустой текст, так как используются динамические subtitles
			fontfile: tpl.sub.fontfile,
			fontsize: tpl.sub.fontsize,
			fontcolor: tpl.sub.fontcolor,
			x: tpl.sub.x,
			y: tpl.sub.y,
			box: tpl.sub.box,
			boxcolor: tpl.sub.boxcolor || undefined,
			boxborderw: tpl.sub.boxborderw || undefined,
			max_lines: tpl.sub.max_lines || 3,
			// ✅ Вложенные субтитры с скорректированным timing
			subtitles: {
				items: correctedSubtitles
			}
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
				text_items: textItems,
				generate_thumbnail: true,
				thumbnail_timestamp: 0.5
			}],
			client_meta: {
				...clientMeta,
				_template_key: templateKey,
				_template_name: tpl.name,
				_template_category: tpl.category,
				_template_genres: tpl.best_for,
				_templates_available: 0, // Будет заполнено ниже
				_input_item_index: item.index
			}
		}
	};
}

// ОСНОВНАЯ ЛОГИКА: обработка каждого входного элемента
const items = $input.all();
const results = items.map((item) => {
	const clientMeta = (item.json.shorts || item.json).client_meta || item.json.client_meta || {};
	const { templateKey, tpl, totalFiltered } = selectTemplate(clientMeta);
	const operation = createOperation(item, templateKey, tpl);

	// Добавляем счётчик доступных шаблонов
	operation.json.client_meta._templates_available = totalFiltered;

	return operation;
});

return results;
