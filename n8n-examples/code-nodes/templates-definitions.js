/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 📚 VIDEO TEMPLATES LIBRARY v6.0 - Universal Template Definitions
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 60 UNIQUE TEMPLATES for video content (gaming, tutorials, reviews, etc.)
 *
 * 🎨 DESIGN PRINCIPLES:
 * ✅ High contrast colors: fontcolor ≠ bordercolor (maximum readability!)
 * ✅ Variety: boxes/outlines/borders in different combinations
 * ✅ 10 public fonts (system fonts, Cyrillic support)
 * ✅ Optimized for small screens (mobile-friendly)
 *
 * 📱 FONTS:
 * 1. Charter.ttc - Modern Serif
 * 2. Copperplate.ttc - Decorative
 * 3. HelveticaNeue.ttc - Premium Sans-Serif
 * 4. LucidaGrande.ttc - Elegant Sans-Serif
 * 5. MarkerFelt.ttc - Creative
 * 6. Menlo.ttc - Monospace
 * 7. Monaco.ttf - Monospace
 * 8. PTSans.ttc - Russian font
 * 9. Palatino.ttc - Classic Serif
 * 10. STIXTwoText-Italic.ttf - Scientific
 *
 * 🎯 CATEGORIES (60 templates):
 * - NEON_GLOW (15) - Title on box, Sub with outline
 * - SOLID_FRAMES (15) - Both on boxes
 * - OUTLINE_PURE (15) - Both with outlines (critical contrast!)
 * - CREATIVE_MIX (15) - Mixed variations
 *
 * ⚠️ IMPORTANT: fontcolor and bordercolor must be HIGHLY CONTRASTED!
 * Examples of contrast pairs:
 * - Light text (#FFFFFF) + Dark border (#000000)
 * - Bright color (#00FFFF) + Dark outline (#004D4D)
 * - Dark text (#1A1A1A) + Light border (#FFFFFF)
 */

const VIDEO_TEMPLATES = {

	// ═══════════════════════════════════════════════════════════════════════
	// ✨ NEON_GLOW (15 templates)
	// Title on box WITHOUT outline, Sub WITHOUT box WITH contrasting outline
	// ═══════════════════════════════════════════════════════════════════════

	"cyber_neon": {
		name: "Cyber Neon",
		category: "NEON_GLOW",
		best_for: ["Valorant", "CSGO", "cyberpunk", "fps"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#00FFFF",          // Bright cyan
			bordercolor: "#004D4D",        // Dark cyan (contrast!)
			borderw: 0,                     // On box - no border needed
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
			fontcolor: "#FF00FF",          // Bright fuchsia
			bordercolor: "#000000",        // Black outline (CONTRAST!)
			borderw: 14,                    // Thick outline for readability
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
			fontcolor: "#FF4400",          // Fire orange
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
			fontcolor: "#00DDFF",          // Ice cyan
			bordercolor: "#000000",        // Black outline (CONTRAST!)
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
			fontcolor: "#FFD700",          // Gold
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
			fontcolor: "#BB88FF",          // Light purple
			bordercolor: "#1A0033",        // Dark purple (CONTRAST!)
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
			fontcolor: "#39FF14",          // Neon green
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
			fontcolor: "#FF0033",          // Bright red
			bordercolor: "#FFFFFF",        // White outline (MAXIMUM CONTRAST!)
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
			fontcolor: "#FFFF00",          // Electric yellow
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000000",        // Black outline (classic!)
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
			fontcolor: "#DDDDDD",          // Light gray
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#00FF41",          // Matrix green
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
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#000000",        // Black outline (contrast with gold!)
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
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#00FF88",          // Neon green
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FF10F0",          // Neon pink
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
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FF8C00",          // Dark orange
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#00BFFF",          // Deep sky blue
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#00334D",        // Dark blue outline
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
			fontcolor: "#DC143C",          // Crimson
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
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#50C878",          // Emerald
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#003D1F",        // Dark green outline
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	// ═══════════════════════════════════════════════════════════════════════
	// 📦 SOLID_FRAMES (15 templates)
	// Both texts on boxes - outline minimal or absent
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
			borderw: 0,                     // On box - no outline
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
			borderw: 0,                     // On box - no outline
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
			fontcolor: "#FF6347",          // Tomato
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
			fontcolor: "#FFD700",          // Gold
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
			fontcolor: "#1E90FF",          // Dodger Blue
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
			fontcolor: "#87CEEB",          // Sky Blue
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
			fontcolor: "#228B22",          // Forest Green
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
			fontcolor: "#90EE90",          // Light Green
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
			fontcolor: "#FF4500",          // Orange Red
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
			fontcolor: "#FFFF00",          // Yellow
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
			fontcolor: "#B0C4DE",          // Light Steel Blue
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
			fontcolor: "#FFD700",          // Gold
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
	// ⚡ OUTLINE_PURE (15 templates)
	// WITHOUT boxes - CRITICAL: thick contrasting outlines!
	// fontcolor and bordercolor MUST be contrasted!
	// ═══════════════════════════════════════════════════════════════════════

	"outline_neon": {
		name: "Outline Neon",
		category: "OUTLINE_PURE",
		best_for: ["Beat Saber", "Geometry Dash", "clean", "minimal"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 88,
			fontcolor: "#FFFFFF",          // White text
			bordercolor: "#000000",        // Black outline (MAXIMUM CONTRAST!)
			borderw: 15,                    // Thick outline!
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#00FFFF",          // Cyan text
			bordercolor: "#000000",        // Black outline (contrast!)
			borderw: 16,                    // Even thicker for subtitles
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
			fontcolor: "#FFFF00",          // Yellow text
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: 185,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#FF4400",          // Orange text
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000000",        // Black (meme classic!)
			borderw: 16,                    // Very thick
			x: "(w-text_w)/2",
			y: 180,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 81,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000000",        // Black
			borderw: 17,                    // Maximum thick!
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
			fontcolor: "#FF1493",          // Deep Pink
			bordercolor: "#FFFFFF",        // White outline (contrast!)
			borderw: 14,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "MarkerFelt.ttc",
			fontsize: 78,
			fontcolor: "#00FF00",          // Lime
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#000000",        // Black outline (contrast with gold!)
			borderw: 15,
			x: "(w-text_w)/2",
			y: 183,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#4D3900",        // Dark gold outline
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
			fontcolor: "#39FF14",          // Neon Green
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#ADFF2F",          // Green Yellow
			bordercolor: "#003D00",        // Dark green outline
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
			fontcolor: "#FF0000",          // Red
			bordercolor: "#FFFFFF",        // White outline (STRONG CONTRAST!)
			borderw: 15,
			x: "(w-text_w)/2",
			y: 183,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 80,
			fontcolor: "#DC143C",          // Crimson
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#E0FFFF",          // Light Cyan
			bordercolor: "#00334D",        // Dark blue outline (contrast!)
			borderw: 15,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#004D66",        // Blue outline
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
			fontcolor: "#DA70D6",          // Orchid
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 79,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#2A1533",        // Dark purple outline
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
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000000",        // Black
			borderw: 16,                    // Maximum readability!
			x: "(w-text_w)/2",
			y: 190,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 77,
			fontcolor: "#FFFF00",          // Yellow
			bordercolor: "#000000",        // Black
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
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#000066",        // Dark blue outline (contrast!)
			borderw: 15,
			x: "(w-text_w)/2",
			y: 185,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 79,
			fontcolor: "#FFFF00",          // Yellow
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#4D0000",        // Dark red outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 78,
			fontcolor: "#FF6347",          // Tomato
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#50C878",          // Emerald
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: 190,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 77,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#154724",        // Dark green outline
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
			fontcolor: "#E0115F",          // Ruby
			bordercolor: "#FFFFFF",        // White outline (contrast!)
			borderw: 14,
			x: "(w-text_w)/2",
			y: 186,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 79,
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#000000",        // Black outline
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
			fontcolor: "#0F52BA",          // Sapphire
			bordercolor: "#FFFFFF",        // White outline (contrast!)
			borderw: 15,
			x: "(w-text_w)/2",
			y: 188,
			box: 0,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 78,
			fontcolor: "#87CEEB",          // Sky Blue
			bordercolor: "#000033",        // Dark blue outline
			borderw: 16,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	// ═══════════════════════════════════════════════════════════════════════
	// 🔀 CREATIVE_MIX (15 templates)
	// Mixed variations: different combinations of boxes and outlines
	// ═══════════════════════════════════════════════════════════════════════

	"hybrid_neon_mix": {
		name: "Hybrid Neon Mix",
		category: "CREATIVE_MIX",
		best_for: ["GTA V", "Saints Row", "mixed", "versatile"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#FFFFFF",        // White outline
			borderw: 8,                     // Medium outline ON box
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#000033@0.85",      // Semi-transparent box
			boxborderw: 28,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#FF1493",          // Deep Pink
			bordercolor: "#000000",        // Black outline
			borderw: 14,                    // Thick without box
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_fire_outline": {
		name: "Hybrid Fire Outline",
		category: "CREATIVE_MIX",
		best_for: ["Apex Legends", "Titanfall", "dynamic", "energetic"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 83,
			fontcolor: "#FF4500",          // Orange Red
			bordercolor: "#FFFF00",        // Yellow outline (fire!)
			borderw: 10,                    // On box with outline
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#1a0000@0.88",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 73,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#FF4500",        // Orange outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_gold_shadow": {
		name: "Hybrid Gold Shadow",
		category: "CREATIVE_MIX",
		best_for: ["World of Warcraft", "Lost Ark", "premium", "vip"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#FFFFFF",        // White outline on box
			borderw: 6,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a1a00@0.90",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 72,
			fontcolor: "#F4E5C2",          // Cream
			bordercolor: "#4D3900",        // Dark gold outline
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_ice_fire": {
		name: "Hybrid Ice Fire",
		category: "CREATIVE_MIX",
		best_for: ["Street Fighter", "Tekken", "contrast", "fighting"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#00DDFF",          // Ice Blue
			bordercolor: "#FFFFFF",        // White outline
			borderw: 7,
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#000033@0.87",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#FF4400",          // Orange
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_purple_glow": {
		name: "Hybrid Purple Glow",
		category: "CREATIVE_MIX",
		best_for: ["Control", "Psychonauts", "mystic", "magical"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 81,
			fontcolor: "#AA55FF",          // Purple
			bordercolor: "#FFFFFF",        // White outline
			borderw: 8,
			x: "(w-text_w)/2",
			y: 209,
			box: 1,
			boxcolor: "#1a0033@0.89",
			boxborderw: 28,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 71,
			fontcolor: "#00FF88",          // Green Cyan
			bordercolor: "#003D1F",        // Dark green outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_toxic_warning": {
		name: "Hybrid Toxic Warning",
		category: "CREATIVE_MIX",
		best_for: ["Fallout", "Stalker", "danger", "radioactive"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 83,
			fontcolor: "#39FF14",          // Neon Green
			bordercolor: "#000000",        // Black outline on box
			borderw: 9,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#001a00@0.91",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 73,
			fontcolor: "#FFFF00",          // Yellow
			bordercolor: "#330000",        // Dark red outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_ocean_wave": {
		name: "Hybrid Ocean Wave",
		category: "CREATIVE_MIX",
		best_for: ["Subnautica", "Sea of Thieves", "water", "marine"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 84,
			fontcolor: "#1E90FF",          // Dodger Blue
			bordercolor: "#FFFFFF",        // White outline
			borderw: 7,
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#00001a@0.88",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 74,
			fontcolor: "#87CEEB",          // Sky Blue
			bordercolor: "#00334D",        // Dark blue outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_sunset_dream": {
		name: "Hybrid Sunset Dream",
		category: "CREATIVE_MIX",
		best_for: ["Firewatch", "What Remains", "calm", "peaceful"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#FF6347",          // Tomato
			bordercolor: "#FFFF00",        // Yellow outline
			borderw: 6,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#1a0a00@0.90",
			boxborderw: 28,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 72,
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#4D0000",        // Dark red outline
			borderw: 13,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_forest_light": {
		name: "Hybrid Forest Light",
		category: "CREATIVE_MIX",
		best_for: ["Valheim", "Green Hell", "nature", "survival"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 81,
			fontcolor: "#228B22",          // Forest Green
			bordercolor: "#FFFFFF",        // White outline
			borderw: 8,
			x: "(w-text_w)/2",
			y: 209,
			box: 1,
			boxcolor: "#001a00@0.89",
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 71,
			fontcolor: "#90EE90",          // Light Green
			bordercolor: "#003D00",        // Dark green outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_blood_moon": {
		name: "Hybrid Blood Moon",
		category: "CREATIVE_MIX",
		best_for: ["Bloodborne", "Castlevania", "horror", "halloween"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 83,
			fontcolor: "#DC143C",          // Crimson
			bordercolor: "#FFFF00",        // Yellow outline (moon!)
			borderw: 7,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#0d0000@0.92",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 73,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#330000",        // Dark red outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_crystal_clear": {
		name: "Hybrid Crystal Clear",
		category: "CREATIVE_MIX",
		best_for: ["Journey", "Abzu", "pure", "clean"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 82,
			fontcolor: "#E0FFFF",          // Light Cyan
			bordercolor: "#00334D",        // Dark blue outline
			borderw: 8,
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#000033@0.85",      // Semi-transparent
			boxborderw: 28,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 72,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#004D66",        // Blue outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_lava_stone": {
		name: "Hybrid Lava Stone",
		category: "CREATIVE_MIX",
		best_for: ["Monster Hunter", "Dragon's Dogma", "volcano", "hot"],
		title: {
			fontfile: "Copperplate.ttc",
			fontsize: 84,
			fontcolor: "#FF4500",          // Orange Red
			bordercolor: "#000000",        // Black outline
			borderw: 9,
			x: "(w-text_w)/2",
			y: 202,
			box: 1,
			boxcolor: "#1a0600@0.91",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "LucidaGrande.ttc",
			fontsize: 74,
			fontcolor: "#FFD700",          // Gold
			bordercolor: "#4D1100",        // Dark orange outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_electric_storm": {
		name: "Hybrid Electric Storm",
		category: "CREATIVE_MIX",
		best_for: ["Infamous", "Prototype", "thunder", "lightning"],
		title: {
			fontfile: "Monaco.ttf",
			fontsize: 83,
			fontcolor: "#00FFFF",          // Cyan
			bordercolor: "#FFFF00",        // Yellow outline (lightning!)
			borderw: 8,
			x: "(w-text_w)/2",
			y: 205,
			box: 1,
			boxcolor: "#00001a@0.90",
			boxborderw: 30,
			max_lines: 3
		},
		sub: {
			fontfile: "Menlo.ttc",
			fontsize: 73,
			fontcolor: "#FFFFFF",          // White
			bordercolor: "#000066",        // Dark blue outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_shadow_light": {
		name: "Hybrid Shadow Light",
		category: "CREATIVE_MIX",
		best_for: ["Persona", "SMT", "balance", "duality"],
		title: {
			fontfile: "Palatino.ttc",
			fontsize: 82,
			fontcolor: "#2C3E50",          // Dark Slate
			bordercolor: "#FFFFFF",        // White outline (contrast!)
			borderw: 10,                    // Thick on dark text
			x: "(w-text_w)/2",
			y: 207,
			box: 1,
			boxcolor: "#ECF0F1@0.92",      // Light box
			boxborderw: 29,
			max_lines: 3
		},
		sub: {
			fontfile: "Charter.ttc",
			fontsize: 72,
			fontcolor: "#ECF0F1",          // Light Gray
			bordercolor: "#000000",        // Black outline
			borderw: 14,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	},

	"hybrid_neon_city": {
		name: "Hybrid Neon City",
		category: "CREATIVE_MIX",
		best_for: ["GTA V", "Cyberpunk", "urban", "city"],
		title: {
			fontfile: "HelveticaNeue.ttc",
			fontsize: 85,
			fontcolor: "#FF1493",          // Deep Pink
			bordercolor: "#00FFFF",        // Cyan outline (neon!)
			borderw: 7,
			x: "(w-text_w)/2",
			y: 200,
			box: 1,
			boxcolor: "#1a001a@0.88",
			boxborderw: 31,
			max_lines: 3
		},
		sub: {
			fontfile: "PTSans.ttc",
			fontsize: 75,
			fontcolor: "#00FF00",          // Lime
			bordercolor: "#000000",        // Black outline
			borderw: 15,
			x: "(w-text_w)/2",
			y: "h-330",
			box: 0,
			max_lines: 3
		}
	}
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
	module.exports = { VIDEO_TEMPLATES };
}
