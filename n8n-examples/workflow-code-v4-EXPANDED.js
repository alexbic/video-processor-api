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

const GAMING_TEMPLATES = {
	// GAMING_CONTRAST (10) - Высококонтрастные цветовые схемы
	"cyber_neon": {
		name: "Cyber Neon",
		category: "GAMING_CONTRAST",
		best_for: ["cyberpunk", "tech", "sci-fi"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#00FFFF", // Яркий циан
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#000033@0.92", // Темно-синий фон
			boxborderw: 32
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#FF00FF", // Яркая фуксия
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"fire_ice": {
		name: "Fire & Ice",
		category: "GAMING_CONTRAST",
		best_for: ["action", "battle", "pvp"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 87,
			fontcolor: "#FF3300", // Огненно-красный
			x: "(w-text_w)/2",
			y: 195,
			box: 1,
			boxcolor: "#1a0000@0.94", // Почти черный с красным оттенком
			boxborderw: 34
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 77,
			fontcolor: "#00DDFF", // Ледяной циан
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"gold_purple": {
		name: "Gold & Purple",
		category: "GAMING_CONTRAST",
		best_for: ["rpg", "fantasy", "magic"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 83,
			fontcolor: "#FFD700", // Золотой
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#2d1b52@0.92", // Темно-фиолетовый
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#BB88FF", // Светло-фиолетовый
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"toxic_green": {
		name: "Toxic Green",
		category: "GAMING_CONTRAST",
		best_for: ["horror", "zombie", "survival"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#39FF14", // Неоново-зеленый
			x: "(w-text_w)/2",
			y: 198,
			box: 1,
			boxcolor: "#001100@0.95", // Темно-зеленый почти черный
			boxborderw: 33
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 76,
			fontcolor: "#FF0033", // Ярко-красный
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"electric_yellow": {
		name: "Electric Yellow",
		category: "GAMING_CONTRAST",
		best_for: ["racing", "speed", "energy"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#FFFF00", // Электрический желтый
			x: "(w-text_w)/2",
			y: 197,
			box: 1,
			boxcolor: "#000000@0.94", // Черный
			boxborderw: 32
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 76,
			fontcolor: "#0088FF", // Ярко-синий
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"blood_shadow": {
		name: "Blood Shadow",
		category: "GAMING_CONTRAST",
		best_for: ["dark", "vampire", "gothic"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 84,
			fontcolor: "#CC0000", // Кроваво-красный
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#0d0d0d@0.96", // Почти черный
			boxborderw: 31
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#DDDDDD", // Светло-серый
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"matrix_code": {
		name: "Matrix Code",
		category: "GAMING_CONTRAST",
		best_for: ["hacking", "cyber", "matrix"],
		title: {
			fontfile: "Monaco.ttf",
			fontsize: 85,
			fontcolor: "#00FF41", // Matrix зеленый
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#001a00@0.94", // Темно-зеленый
			boxborderw: 32
		},
		sub: {
			fontfile: "Menlo.ttc",
			fontsize: 75,
			fontcolor: "#00FFFF", // Циан
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"royal_blue": {
		name: "Royal Blue",
		category: "GAMING_CONTRAST",
		best_for: ["strategy", "empire", "rts"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 83,
			fontcolor: "#0055FF", // Королевский синий
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#00001a@0.93", // Темно-синий
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#FFD700", // Золотой
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"lava_glow": {
		name: "Lava Glow",
		category: "GAMING_CONTRAST",
		best_for: ["boss", "fire", "epic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#FF4400", // Лавовый оранжевый
			x: "(w-text_w)/2",
			y: 197,
			box: 1,
			boxcolor: "#1a0600@0.94", // Темно-красный почти черный
			boxborderw: 33
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 76,
			fontcolor: "#00FFFF", // Циан
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"cosmic_purple": {
		name: "Cosmic Purple",
		category: "GAMING_CONTRAST",
		best_for: ["space", "cosmic", "alien"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#AA55FF", // Космический фиолетовый
			x: "(w-text_w)/2",
			y: 203,
			box: 1,
			boxcolor: "#0d0d1a@0.93", // Темно-фиолетовый
			boxborderw: 31
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#00FF88", // Неоново-зеленый
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	// DOUBLE_BOX (10) - Оба текста с фоном
	"double_neon": {
		name: "Double Neon",
		category: "DOUBLE_BOX",
		best_for: ["important", "tutorial", "guide"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 82,
			fontcolor: "#00FFFF",
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#001a1a@0.93",
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#FFD700",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a00@0.91",
			boxborderw: 28
		}
	},

	"double_impact": {
		name: "Double Impact",
		category: "DOUBLE_BOX",
		best_for: ["alert", "breaking", "news"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "white",
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#CC0000@0.95",
			boxborderw: 32
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FFFF00",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#000000@0.93",
			boxborderw: 30
		}
	},

	"double_elegant": {
		name: "Double Elegant",
		category: "DOUBLE_BOX",
		best_for: ["education", "story", "lore"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 78,
			fontcolor: "#2C3E50",
			x: "(w-text_w)/2",
			y: 217,
			box: 1,
			boxcolor: "#ECF0F1@0.94",
			boxborderw: 30
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 70,
			fontcolor: "#5D6D7E",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "white@0.91",
			boxborderw: 28
		}
	},

	"double_toxic": {
		name: "Double Toxic",
		category: "DOUBLE_BOX",
		best_for: ["poison", "radioactive", "danger"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 83,
			fontcolor: "#39FF14",
			x: "(w-text_w)/2",
			y: 204,
			box: 1,
			boxcolor: "#001100@0.94",
			boxborderw: 31
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FF0033",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a0000@0.92",
			boxborderw: 29
		}
	},

	"double_gold": {
		name: "Double Gold",
		category: "DOUBLE_BOX",
		best_for: ["achievement", "victory", "epic"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#FFD700",
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a1a1a@0.93",
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 73,
			fontcolor: "#F4E5C2",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#2d2d2d@0.91",
			boxborderw: 28
		}
	},

	"double_cyber": {
		name: "Double Cyber",
		category: "DOUBLE_BOX",
		best_for: ["futuristic", "tech", "digital"],
		title: {
			fontfile: "Monaco.ttf",
			fontsize: 83,
			fontcolor: "#00FFFF",
			x: "(w-text_w)/2",
			y: 204,
			box: 1,
			boxcolor: "#001a1a@0.93",
			boxborderw: 31
		},
		sub: {
			fontfile: "Menlo.ttc",
			fontsize: 74,
			fontcolor: "#FF00FF",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a001a@0.92",
			boxborderw: 29
		}
	},

	"double_fire": {
		name: "Double Fire",
		category: "DOUBLE_BOX",
		best_for: ["battle", "war", "intense"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#FF4400",
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#8B0000@0.92",
			boxborderw: 32
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FFD700",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a1a@0.91",
			boxborderw: 30
		}
	},

	"double_ice": {
		name: "Double Ice",
		category: "DOUBLE_BOX",
		best_for: ["frost", "winter", "frozen"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 81,
			fontcolor: "#00DDFF",
			x: "(w-text_w)/2",
			y: 209,
			box: 1,
			boxcolor: "#00003a@0.92",
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#B0E0E6",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a2e@0.91",
			boxborderw: 28
		}
	},

	"double_purple": {
		name: "Double Purple",
		category: "DOUBLE_BOX",
		best_for: ["magic", "fantasy", "mystical"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#AA55FF",
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a0a1a@0.93",
			boxborderw: 30
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 73,
			fontcolor: "#DA70D6",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#2d1b52@0.91",
			boxborderw: 29
		}
	},

	"double_clean": {
		name: "Double Clean",
		category: "DOUBLE_BOX",
		best_for: ["tutorial", "howto", "guide"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 78,
			fontcolor: "#212121",
			x: "(w-text_w)/2",
			y: 214,
			box: 1,
			boxcolor: "white@0.94",
			boxborderw: 30
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 70,
			fontcolor: "#424242",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#F5F5F5@0.92",
			boxborderw: 28
		}
	},

	// NO_BOX (10) - Только обводка без фона
	"outline_neon": {
		name: "Outline Neon",
		category: "NO_BOX",
		best_for: ["clean", "minimal", "modern"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#00FFFF",
			x: "(w-text_w)/2",
			y: 188,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#FF00FF",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_fire": {
		name: "Outline Fire",
		category: "NO_BOX",
		best_for: ["action", "dynamic", "fast"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 89,
			fontcolor: "#FF4400",
			x: "(w-text_w)/2",
			y: 185,
			box: 0
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#FFD700",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_classic": {
		name: "Outline Classic",
		category: "NO_BOX",
		best_for: ["meme", "viral", "classic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 91,
			fontcolor: "white",
			x: "(w-text_w)/2",
			y: 180,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 81,
			fontcolor: "white",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_rainbow": {
		name: "Outline Rainbow",
		category: "NO_BOX",
		best_for: ["fun", "colorful", "happy"],
		title: {
			fontfile: "MarkerFelt.ttc",
			fontsize: 88,
			fontcolor: "#FF69B4",
			x: "(w-text_w)/2",
			y: 188,
			box: 0
		},
		sub: {
			fontfile: "MarkerFelt.ttc",
			fontsize: 78,
			fontcolor: "#00FF88",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_gold": {
		name: "Outline Gold",
		category: "NO_BOX",
		best_for: ["epic", "legendary", "rare"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 90,
			fontcolor: "#FFD700",
			x: "(w-text_w)/2",
			y: 183,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#FF8C00",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_toxic": {
		name: "Outline Toxic",
		category: "NO_BOX",
		best_for: ["poison", "acid", "bio"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 89,
			fontcolor: "#39FF14",
			x: "(w-text_w)/2",
			y: 186,
			box: 0
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#ADFF2F",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_blood": {
		name: "Outline Blood",
		category: "NO_BOX",
		best_for: ["horror", "dark", "brutal"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 90,
			fontcolor: "#DC143C",
			x: "(w-text_w)/2",
			y: 183,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#FF6347",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_ice": {
		name: "Outline Ice",
		category: "NO_BOX",
		best_for: ["frost", "cold", "frozen"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#00DDFF",
			x: "(w-text_w)/2",
			y: 188,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#87CEEB",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_purple": {
		name: "Outline Purple",
		category: "NO_BOX",
		best_for: ["magic", "arcane", "spell"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 89,
			fontcolor: "#AA55FF",
			x: "(w-text_w)/2",
			y: 186,
			box: 0
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 79,
			fontcolor: "#DA70D6",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	},

	"outline_contrast": {
		name: "Outline Contrast",
		category: "NO_BOX",
		best_for: ["universal", "readable", "safe"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 87,
			fontcolor: "white",
			x: "(w-text_w)/2",
			y: 190,
			box: 0
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 77,
			fontcolor: "#FFFF00",
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0
		}
	}
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
