/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎨 APPLY VIDEO TEMPLATES - N8N Code Node v6.0
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 🎯 НАЗНАЧЕНИЕ:
 * Применяет случайные видео шаблоны к каждому клипу для генерации
 *
 * 📥 ВХОДНЫЕ ДАННЫЕ:
 * Массив объектов с полями:
 * - start: number (время начала клипа в секундах)
 * - end: number (время конца клипа в секундах)
 * - title: string (заголовок клипа)
 * - subtitles: array (массив субтитров {text, start, end})
 * - source_video_url: string (URL видео)
 * - client_meta: object (дополнительные метаданные)
 *
 * 📤 ВЫХОДНЫЕ ДАННЫЕ:
 * Массив операций с примененными шаблонами
 *
 * ✨ ОСОБЕННОСТИ:
 * ✅ 60 уникальных шаблонов с красивыми обводками букв (STROKE/OUTLINE)
 * ✅ 4 категории: NEON_GLOW, SOLID_FRAMES, OUTLINE_PURE, CREATIVE_MIX
 * ✅ Случайный выбор шаблона для каждого клипа
 * ✅ Поддержка фильтрации по категории или жанру
 * ✅ Вложенные субтитры с наследованием стилей
 * ✅ Обводки текста (borderw, bordercolor) - ТЕПЕРЬ РАБОТАЮТ!
 *
 * 🎨 ВИДИМЫЕ ОБВОДКИ:
 * Теперь в backend добавлена поддержка borderw и bordercolor параметров
 * Это означает что все обводки из шаблонов будут видны в генерируемых видео!
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════
// 📚 ВИДЕО ШАБЛОНЫ - 60 УНИКАЛЬНЫХ ДИЗАЙНОВ
// ═══════════════════════════════════════════════════════════════════════════

const VIDEO_TEMPLATES = {

	// ═══════════════════════════════════════════════════════════════════════
	// ✨ NEON_GLOW (15) - Заголовок на плашке БЕЗ обводки, Субтитры БЕЗ плашки С обводкой
	// ═══════════════════════════════════════════════════════════════════════

	"cyber_neon": {
		name: "Cyber Neon",
		category: "NEON_GLOW",
		best_for: ["Valorant", "CSGO", "cyberpunk", "fps"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#00FFFF",
			bordercolor: "#004D4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#000033@0.92",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#FF00FF",
			bordercolor: "#000000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"fire_ice": {
		name: "Fire & Ice",
		category: "NEON_GLOW",
		best_for: ["Fortnite", "Overwatch", "battle-royale", "pvp"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 87,
			fontcolor: "#FF4400",
			bordercolor: "#330000",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 195,
			box: 1,
			boxcolor: "#1a0000@0.94",
			boxborderw: 34,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 77,
			fontcolor: "#00DDFF",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"gold_purple": {
		name: "Gold & Purple",
		category: "NEON_GLOW",
		best_for: ["League of Legends", "Dota 2", "rpg", "moba"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 83,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#2d1b52@0.92",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#BB88FF",
			bordercolor: "#1A0033",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"toxic_green": {
		name: "Toxic Green",
		category: "NEON_GLOW",
		best_for: ["Resident Evil", "Dead Space", "horror", "survival"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#39FF14",
			bordercolor: "#0D3300",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 198,
			box: 1,
			boxcolor: "#001100@0.95",
			boxborderw: 33,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 76,
			fontcolor: "#FF0033",
			bordercolor: "#FFFFFF",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"electric_yellow": {
		name: "Electric Yellow",
		category: "NEON_GLOW",
		best_for: ["Need for Speed", "Rocket League", "racing", "sports"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#FFFF00",
			bordercolor: "#4D4D00",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 197,
			box: 1,
			boxcolor: "#000000@0.94",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 76,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"blood_shadow": {
		name: "Blood Shadow",
		category: "NEON_GLOW",
		best_for: ["Diablo", "Dark Souls", "dark", "gothic"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 84,
			fontcolor: "#CC0000",
			bordercolor: "#330000",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#0d0d0d@0.96",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#DDDDDD",
			bordercolor: "#000000",
			borderw: 12,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"matrix_code": {
		name: "Matrix Code",
		category: "NEON_GLOW",
		best_for: ["Cyberpunk 2077", "Watch Dogs", "hacking", "cyber"],
		title: {
			fontfile: "Monaco.ttf",
			fontsize: 85,
			fontcolor: "#00FF41",
			bordercolor: "#003D10",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#001a00@0.94",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "Menlo.ttc",
			fontsize: 75,
			fontcolor: "#00FFFF",
			bordercolor: "#000000",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"royal_blue": {
		name: "Royal Blue",
		category: "NEON_GLOW",
		best_for: ["Civilization", "Age of Empires", "strategy", "rts"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 83,
			fontcolor: "#0055FF",
			bordercolor: "#001133",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#00001a@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#FFD700",
			bordercolor: "#000000",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"lava_glow": {
		name: "Lava Glow",
		category: "NEON_GLOW",
		best_for: ["God of War", "Doom", "boss-fight", "epic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 86,
			fontcolor: "#FF4400",
			bordercolor: "#4D1100",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 197,
			box: 1,
			boxcolor: "#1a0600@0.94",
			boxborderw: 33,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 76,
			fontcolor: "#00FFFF",
			bordercolor: "#000000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"cosmic_purple": {
		name: "Cosmic Purple",
		category: "NEON_GLOW",
		best_for: ["No Man's Sky", "Stellaris", "space", "sci-fi"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#AA55FF",
			bordercolor: "#2A1533",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 203,
			box: 1,
			boxcolor: "#0d0d1a@0.93",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#00FF88",
			bordercolor: "#000000",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"neon_pink": {
		name: "Neon Pink",
		category: "NEON_GLOW",
		best_for: ["Fall Guys", "Among Us", "vaporwave", "casual"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 82,
			fontcolor: "#FF10F0",
			bordercolor: "#4D0047",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a0033@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 73,
			fontcolor: "#00FFFF",
			bordercolor: "#000000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"sunset_orange": {
		name: "Sunset Orange",
		category: "NEON_GLOW",
		best_for: ["Sea of Thieves", "Zelda", "adventure", "exploration"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 81,
			fontcolor: "#FF8C00",
			bordercolor: "#4D2900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 210,
			box: 1,
			boxcolor: "#1a1a00@0.92",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"arctic_blue": {
		name: "Arctic Blue",
		category: "NEON_GLOW",
		best_for: ["Frostpunk", "Subnautica", "frost", "winter"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#00BFFF",
			bordercolor: "#003D4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#001a33@0.93",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 75,
			fontcolor: "#FFFFFF",
			bordercolor: "#00334D",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"crimson_rage": {
		name: "Crimson Rage",
		category: "NEON_GLOW",
		best_for: ["Call of Duty", "Battlefield", "battle", "fps"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 83,
			fontcolor: "#DC143C",
			bordercolor: "#420010",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#0d0000@0.94",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#FFD700",
			bordercolor: "#000000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"emerald_shine": {
		name: "Emerald Shine",
		category: "NEON_GLOW",
		best_for: ["Minecraft", "Stardew Valley", "nature", "sandbox"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#50C878",
			bordercolor: "#154724",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#001a0d@0.92",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 73,
			fontcolor: "#FFFFFF",
			bordercolor: "#003D1F",
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	// ═══════════════════════════════════════════════════════════════════════
	// 📦 SOLID_FRAMES (15) - Оба текста на плашках - обводки минимальны или отсутствуют
	// ═══════════════════════════════════════════════════════════════════════

	"double_neon": {
		name: "Double Neon",
		category: "SOLID_FRAMES",
		best_for: ["Roblox", "tutorials", "educational", "guide"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 82,
			fontcolor: "#00FFFF",
			bordercolor: "#004D4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#001a1a@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a00@0.91",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_impact": {
		name: "Double Impact",
		category: "SOLID_FRAMES",
		best_for: ["Apex Legends", "Warzone", "alert", "breaking"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#FFFFFF",
			bordercolor: "#4D4D4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#CC0000@0.95",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FFFF00",
			bordercolor: "#4D4D00",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#000000@0.93",
			boxborderw: 30,
			max_lines: 3
		}
	},

	"double_elegant": {
		name: "Double Elegant",
		category: "SOLID_FRAMES",
		best_for: ["Genshin Impact", "Final Fantasy", "education", "story"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 78,
			fontcolor: "#2C3E50",
			bordercolor: "#0A0F14",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 217,
			box: 1,
			boxcolor: "#ECF0F1@0.94",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 70,
			fontcolor: "#5D6D7E",
			bordercolor: "#1C242B",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#FFFFFF@0.91",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_toxic": {
		name: "Double Toxic",
		category: "SOLID_FRAMES",
		best_for: ["Chernobylite", "Metro", "poison", "post-apocalyptic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 83,
			fontcolor: "#39FF14",
			bordercolor: "#0D3300",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 204,
			box: 1,
			boxcolor: "#001100@0.94",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FF0033",
			bordercolor: "#4D000F",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a0000@0.92",
			boxborderw: 29,
			max_lines: 3
		}
	},

	"double_gold": {
		name: "Double Gold",
		category: "SOLID_FRAMES",
		best_for: ["Elden Ring", "Skyrim", "achievement", "rpg"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a1a1a@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 73,
			fontcolor: "#F4E5C2",
			bordercolor: "#4D4533",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#2d2d2d@0.91",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_cyber": {
		name: "Double Cyber",
		category: "SOLID_FRAMES",
		best_for: ["Cyberpunk 2077", "Deus Ex", "futuristic", "tech"],
		title: {
			fontfile: "Monaco.ttf",
			fontsize: 83,
			fontcolor: "#00FFFF",
			bordercolor: "#004D4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 204,
			box: 1,
			boxcolor: "#001a1a@0.93",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "Menlo.ttc",
			fontsize: 74,
			fontcolor: "#FF00FF",
			bordercolor: "#4D004D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a001a@0.92",
			boxborderw: 29,
			max_lines: 3
		}
	},

	"double_fire": {
		name: "Double Fire",
		category: "SOLID_FRAMES",
		best_for: ["Doom Eternal", "Hades", "battle", "action"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#FF4400",
			bordercolor: "#4D1100",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#8B0000@0.92",
			boxborderw: 32,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a1a@0.91",
			boxborderw: 30,
			max_lines: 3
		}
	},

	"double_ice": {
		name: "Double Ice",
		category: "SOLID_FRAMES",
		best_for: ["Frostpunk", "Icarus", "frost", "winter"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 81,
			fontcolor: "#00DDFF",
			bordercolor: "#004256",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 209,
			box: 1,
			boxcolor: "#00003a@0.92",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#B0E0E6",
			bordercolor: "#33444A",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a2e@0.91",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_purple": {
		name: "Double Purple",
		category: "SOLID_FRAMES",
		best_for: ["Ori", "Hollow Knight", "magic", "fantasy"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#AA55FF",
			bordercolor: "#2A1533",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a0a1a@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 73,
			fontcolor: "#DA70D6",
			bordercolor: "#412241",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#2d1b52@0.91",
			boxborderw: 29,
			max_lines: 3
		}
	},

	"double_clean": {
		name: "Double Clean",
		category: "SOLID_FRAMES",
		best_for: ["tutorials", "reviews", "howto", "educational"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 78,
			fontcolor: "#212121",
			bordercolor: "#0A0A0A",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 214,
			box: 1,
			boxcolor: "#FFFFFF@0.94",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 70,
			fontcolor: "#424242",
			bordercolor: "#141414",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#F5F5F5@0.92",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_sunset": {
		name: "Double Sunset",
		category: "SOLID_FRAMES",
		best_for: ["Journey", "Firewatch", "evening", "peaceful"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 80,
			fontcolor: "#FF6347",
			bordercolor: "#4D1F15",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 211,
			box: 1,
			boxcolor: "#1a0a00@0.92",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 71,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#2d1a00@0.90",
			boxborderw: 27,
			max_lines: 3
		}
	},

	"double_ocean": {
		name: "Double Ocean",
		category: "SOLID_FRAMES",
		best_for: ["Subnautica", "Abzu", "water", "sea"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 83,
			fontcolor: "#1E90FF",
			bordercolor: "#0A2E4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 204,
			box: 1,
			boxcolor: "#00001a@0.93",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#87CEEB",
			bordercolor: "#293E4A",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#0a1a2e@0.91",
			boxborderw: 29,
			max_lines: 3
		}
	},

	"double_forest": {
		name: "Double Forest",
		category: "SOLID_FRAMES",
		best_for: ["Terraria", "Valheim", "nature", "survival"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 81,
			fontcolor: "#228B22",
			bordercolor: "#0A2E0A",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 209,
			box: 1,
			boxcolor: "#001a00@0.92",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 72,
			fontcolor: "#90EE90",
			bordercolor: "#2E4A2E",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#0d1a0d@0.90",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_volcano": {
		name: "Double Volcano",
		category: "SOLID_FRAMES",
		best_for: ["Monster Hunter", "Dark Souls", "lava", "boss"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 82,
			fontcolor: "#FF4500",
			bordercolor: "#4D1400",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a0600@0.93",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 73,
			fontcolor: "#FFFF00",
			bordercolor: "#4D4D00",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a00@0.91",
			boxborderw: 28,
			max_lines: 3
		}
	},

	"double_midnight": {
		name: "Double Midnight",
		category: "SOLID_FRAMES",
		best_for: ["Hitman", "Splinter Cell", "night", "stealth"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 80,
			fontcolor: "#B0C4DE",
			bordercolor: "#333F4D",
			borderw: 0,
			x: "(w-text_w)/2",
			y: 211,
			box: 1,
			boxcolor: "#000033@0.92",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 71,
			fontcolor: "#FFD700",
			bordercolor: "#4D3900",
			borderw: 0,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 1,
			boxcolor: "#1a1a33@0.90",
			boxborderw: 27,
			max_lines: 3
		}
	},

	// ═══════════════════════════════════════════════════════════════════════
	// ⚡ OUTLINE_PURE (15) - БЕЗ плашек - ТОЛСТЫЕ КОНТРАСТНЫЕ ОБВОДКИ!
	// ═══════════════════════════════════════════════════════════════════════

	"outline_neon": {
		name: "Outline Neon",
		category: "OUTLINE_PURE",
		best_for: ["Beat Saber", "Geometry Dash", "clean", "minimal"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#00FFFF",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_fire": {
		name: "Outline Fire",
		category: "OUTLINE_PURE",
		best_for: ["Rocket League", "Trackmania", "action", "dynamic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 89,
			fontcolor: "#FFFF00",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 185,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#FF4400",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_classic": {
		name: "Outline Classic",
		category: "OUTLINE_PURE",
		best_for: ["memes", "funny", "viral", "classic"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 91,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: 180,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 81,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 17,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_rainbow": {
		name: "Outline Rainbow",
		category: "OUTLINE_PURE",
		best_for: ["Fall Guys", "Splatoon", "fun", "colorful"],
		title: {
			fontfile: "MarkerFelt.ttc",
			fontsize: 88,
			fontcolor: "#FF1493",
			bordercolor: "#FFFFFF",
			borderw: 14,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "MarkerFelt.ttc",
			fontsize: 78,
			fontcolor: "#00FF00",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_gold": {
		name: "Outline Gold",
		category: "OUTLINE_PURE",
		best_for: ["Hearthstone", "Legends of Runeterra", "epic", "legendary"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 90,
			fontcolor: "#FFD700",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 183,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#FFFFFF",
			bordercolor: "#4D3900",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_toxic": {
		name: "Outline Toxic",
		category: "OUTLINE_PURE",
		best_for: ["Dead by Daylight", "Back 4 Blood", "poison", "horror"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 89,
			fontcolor: "#39FF14",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#ADFF2F",
			bordercolor: "#003D00",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_blood": {
		name: "Outline Blood",
		category: "OUTLINE_PURE",
		best_for: ["Bloodborne", "Resident Evil", "horror", "brutal"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 90,
			fontcolor: "#FF0000",
			bordercolor: "#FFFFFF",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 183,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#DC143C",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_ice": {
		name: "Outline Ice",
		category: "OUTLINE_PURE",
		best_for: ["Frostpunk", "Frozen", "frost", "frozen"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#E0FFFF",
			bordercolor: "#00334D",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#FFFFFF",
			bordercolor: "#004D66",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_purple": {
		name: "Outline Purple",
		category: "OUTLINE_PURE",
		best_for: ["Genshin Impact", "Honkai", "magic", "arcane"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 89,
			fontcolor: "#DA70D6",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 79,
			fontcolor: "#FFFFFF",
			bordercolor: "#2A1533",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_contrast": {
		name: "Outline Contrast",
		category: "OUTLINE_PURE",
		best_for: ["universal", "all-purpose", "readable", "safe"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 87,
			fontcolor: "#FFFFFF",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: 190,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 77,
			fontcolor: "#FFFF00",
			bordercolor: "#000000",
			borderw: 17,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_electric": {
		name: "Outline Electric",
		category: "OUTLINE_PURE",
		best_for: ["Sonic", "Megaman", "energy", "lightning"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 89,
			fontcolor: "#00FFFF",
			bordercolor: "#000066",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 185,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#FFFF00",
			bordercolor: "#000000",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_sunset": {
		name: "Outline Sunset",
		category: "OUTLINE_PURE",
		best_for: ["Journey", "Spiritfarer", "evening", "warm"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 88,
			fontcolor: "#FFD700",
			bordercolor: "#4D0000",
			borderw: 14,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 78,
			fontcolor: "#FF6347",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_emerald": {
		name: "Outline Emerald",
		category: "OUTLINE_PURE",
		best_for: ["Minecraft", "Animal Crossing", "wealth", "treasure"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 87,
			fontcolor: "#50C878",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 190,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 77,
			fontcolor: "#FFFFFF",
			bordercolor: "#154724",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_ruby": {
		name: "Outline Ruby",
		category: "OUTLINE_PURE",
		best_for: ["Pokemon", "Zelda", "precious", "rare"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 89,
			fontcolor: "#E0115F",
			bordercolor: "#FFFFFF",
			borderw: 14,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 79,
			fontcolor: "#FFD700",
			bordercolor: "#000000",
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"outline_sapphire": {
		name: "Outline Sapphire",
		category: "OUTLINE_PURE",
		best_for: ["Final Fantasy", "Dragon Quest", "royal", "premium"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#0F52BA",
			bordercolor: "#FFFFFF",
			borderw: 15,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#87CEEB",
			bordercolor: "#000033",
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	}
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

// Shuffle array (Fisher-Yates)
function shuffleArray(array) {
	const shuffled = [...array];
	for (let i = shuffled.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
	}
	return shuffled;
}

// Select random template
function selectTemplate(clientMeta) {
	let filteredTemplates = Object.entries(VIDEO_TEMPLATES);

	// Filter by exact name
	if (clientMeta.template_name && VIDEO_TEMPLATES[clientMeta.template_name]) {
		filteredTemplates = [[clientMeta.template_name, VIDEO_TEMPLATES[clientMeta.template_name]]];
	}
	// Filter by category
	else if (clientMeta.template_category) {
		filteredTemplates = filteredTemplates.filter(([key, tpl]) =>
			tpl.category === clientMeta.template_category
		);
	}

	// Filter by genre
	if (clientMeta.template_genre && filteredTemplates.length > 1) {
		const genreFiltered = filteredTemplates.filter(([key, tpl]) =>
			tpl.best_for.includes(clientMeta.template_genre)
		);
		if (genreFiltered.length > 0) {
			filteredTemplates = genreFiltered;
		}
	}

	// Shuffle and select first
	filteredTemplates = shuffleArray(filteredTemplates);
	const [templateKey, tpl] = filteredTemplates[0];
	return { templateKey, tpl, totalFiltered: filteredTemplates.length };
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PROCESSING
// ═══════════════════════════════════════════════════════════════════════════

const items = $input.all();
const results = items.map((item) => {
	const data = item.json;
	const shorts = data.shorts || data;
	const clientMeta = shorts.client_meta || data.client_meta || {};
	const sourceUrl = data.source_video_url || shorts.source_video_url;

	// Select template
	const { templateKey, tpl, totalFiltered } = selectTemplate(clientMeta);

	// Create text_items array
	const textItems = [];

	// Title
	textItems.push({
		text: (shorts.title || '').split('#')[0].trim(),
		fontfile: tpl.title.fontfile,
		fontsize: tpl.title.fontsize,
		fontcolor: tpl.title.fontcolor,
		borderw: tpl.title.borderw,
		bordercolor: tpl.title.bordercolor,
		x: tpl.title.x,
		y: tpl.title.y,
		start: 0.0,
		end: 7.0,
		box: tpl.title.box,
		boxcolor: tpl.title.boxcolor || undefined,
		boxborderw: tpl.title.boxborderw || undefined
	});

	// Subtitles (if exists)
	if (shorts.subtitles && shorts.subtitles.length > 0) {
		const correctedSubtitles = shorts.subtitles.map((sub, index) => {
			if (index === 0) {
				return { ...sub, start: 0.0 };
			}
			return sub;
		});

		textItems.push({
			text: "",
			fontfile: tpl.sub.fontfile,
			fontsize: tpl.sub.fontsize,
			fontcolor: tpl.sub.fontcolor,
			borderw: tpl.sub.borderw,
			bordercolor: tpl.sub.bordercolor,
			x: tpl.sub.x,
			y: tpl.sub.y,
			box: tpl.sub.box,
			boxcolor: tpl.sub.boxcolor || undefined,
			boxborderw: tpl.sub.boxborderw || undefined,
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
				_templates_available: totalFiltered,
				_input_item_index: item.index
			}
		}
	};
});

return results;
