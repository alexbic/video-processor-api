/**
 * Visual Templates Library for Shorts/TikTok/Reels
 *
 * Коллекция из 20 визуальных стилей оптимизированных для вирусности
 * на основе трендов 2025 года
 *
 * Категории:
 * - HIGH_CONTRAST: Максимальная читаемость, классические сочетания
 * - NEON_ENERGY: Яркие неоновые цвета, энергичные
 * - ELEGANT: Изящные, для образовательного контента
 * - MEME_STYLE: Impact font, мемы, вирусные форматы
 * - PLATFORM_SPECIFIC: Оптимизированные под конкретную платформу
 */

const VISUAL_TEMPLATES = {

  // ========================================
  // 🎯 HIGH CONTRAST (Максимальная читаемость)
  // ========================================

  "classic_white_bold": {
    name: "Classic White Bold",
    category: "HIGH_CONTRAST",
    best_for: ["educational", "tutorial", "universal"],
    title: {
      font: "Arial",
      fontsize: 76,
      fontcolor: "black",
      bordercolor: "white",
      borderw: 10,
      box: 1,
      boxcolor: "white@0.90",
      boxborderw: 25,
      shadowcolor: "black@0.3",
      shadowx: 3,
      shadowy: 3,
      y: 220
    },
    sub: {
      font: "Montserrat",
      fontsize: 68,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 8,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-340"
    }
  },

  "black_on_yellow": {
    name: "Black on Yellow",
    category: "HIGH_CONTRAST",
    best_for: ["attention", "important", "urgent"],
    title: {
      font: "Helvetica",
      fontsize: 80,
      fontcolor: "black",
      bordercolor: "#FFD700",
      borderw: 4,
      box: 1,
      boxcolor: "#FFEB3B@0.95",
      boxborderw: 30,
      shadowcolor: "black@0.4",
      shadowx: 4,
      shadowy: 4,
      y: 210
    },
    sub: {
      font: "Roboto",
      fontsize: 66,
      fontcolor: "#FFFF00",
      bordercolor: "#8B7500",
      borderw: 12,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-330"
    }
  },

  "white_on_black": {
    name: "White on Black",
    category: "HIGH_CONTRAST",
    best_for: ["dramatic", "serious", "cinema"],
    title: {
      font: "Bebas Neue",
      fontsize: 82,
      fontcolor: "white",
      bordercolor: "white",
      borderw: 0,
      box: 1,
      boxcolor: "black@0.85",
      boxborderw: 28,
      shadowcolor: "white@0.2",
      shadowx: 2,
      shadowy: 2,
      y: 200
    },
    sub: {
      font: "Arial",
      fontsize: 70,
      fontcolor: "white",
      bordercolor: "#666666",
      borderw: 10,
      shadowcolor: "black@0.7",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-320"
    }
  },

  "red_alert": {
    name: "Red Alert",
    category: "HIGH_CONTRAST",
    best_for: ["breaking", "alert", "important"],
    title: {
      font: "Impact",
      fontsize: 78,
      fontcolor: "white",
      bordercolor: "#FF0000",
      borderw: 6,
      box: 1,
      boxcolor: "#D32F2F@0.92",
      boxborderw: 26,
      shadowcolor: "black@0.5",
      shadowx: 4,
      shadowy: 4,
      y: 225
    },
    sub: {
      font: "Helvetica",
      fontsize: 68,
      fontcolor: "#FFCDD2",
      bordercolor: "#B71C1C",
      borderw: 11,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-335"
    }
  },

  "blue_professional": {
    name: "Blue Professional",
    category: "HIGH_CONTRAST",
    best_for: ["business", "professional", "tech"],
    title: {
      font: "Roboto",
      fontsize: 74,
      fontcolor: "white",
      bordercolor: "#2196F3",
      borderw: 5,
      box: 1,
      boxcolor: "#1976D2@0.88",
      boxborderw: 24,
      shadowcolor: "black@0.4",
      shadowx: 3,
      shadowy: 3,
      y: 230
    },
    sub: {
      font: "Montserrat",
      fontsize: 67,
      fontcolor: "#BBDEFB",
      bordercolor: "#0D47A1",
      borderw: 10,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-340"
    }
  },

  // ========================================
  // ⚡ NEON ENERGY (Яркие, энергичные)
  // ========================================

  "neon_green": {
    name: "Neon Green",
    category: "NEON_ENERGY",
    best_for: ["gaming", "tech", "youth"],
    title: {
      font: "Arial",
      fontsize: 78,
      fontcolor: "#00FF00",
      bordercolor: "#00FF00",
      borderw: 8,
      box: 1,
      boxcolor: "black@0.80",
      boxborderw: 25,
      shadowcolor: "#00FF00@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 235
    },
    sub: {
      font: "Roboto",
      fontsize: 66,
      fontcolor: "#00FF00",
      bordercolor: "#003300",
      borderw: 14,
      shadowcolor: "#00FF00@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-340"
    }
  },

  "neon_pink": {
    name: "Neon Pink",
    category: "NEON_ENERGY",
    best_for: ["beauty", "lifestyle", "viral"],
    title: {
      font: "Helvetica",
      fontsize: 76,
      fontcolor: "#FF00FF",
      bordercolor: "#FF1493",
      borderw: 7,
      box: 1,
      boxcolor: "black@0.82",
      boxborderw: 27,
      shadowcolor: "#FF00FF@0.5",
      shadowx: 0,
      shadowy: 0,
      y: 228
    },
    sub: {
      font: "Arial",
      fontsize: 68,
      fontcolor: "#FF69B4",
      bordercolor: "#8B008B",
      borderw: 12,
      shadowcolor: "#FF00FF@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-335"
    }
  },

  "cyber_blue": {
    name: "Cyber Blue",
    category: "NEON_ENERGY",
    best_for: ["tech", "gaming", "futuristic"],
    title: {
      font: "Bebas Neue",
      fontsize: 80,
      fontcolor: "#00FFFF",
      bordercolor: "#00CED1",
      borderw: 6,
      box: 1,
      boxcolor: "#001a1a@0.85",
      boxborderw: 28,
      shadowcolor: "#00FFFF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 215
    },
    sub: {
      font: "Montserrat",
      fontsize: 67,
      fontcolor: "#00FFFF",
      bordercolor: "#004d4d",
      borderw: 13,
      shadowcolor: "#00FFFF@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-330"
    }
  },

  "electric_orange": {
    name: "Electric Orange",
    category: "NEON_ENERGY",
    best_for: ["energy", "fitness", "motivation"],
    title: {
      font: "Impact",
      fontsize: 77,
      fontcolor: "#FF6600",
      bordercolor: "#FF8C00",
      borderw: 8,
      box: 1,
      boxcolor: "black@0.83",
      boxborderw: 26,
      shadowcolor: "#FF6600@0.5",
      shadowx: 0,
      shadowy: 0,
      y: 232
    },
    sub: {
      font: "Helvetica",
      fontsize: 69,
      fontcolor: "#FFA500",
      bordercolor: "#8B4500",
      borderw: 11,
      shadowcolor: "#FF6600@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-338"
    }
  },

  "neon_purple": {
    name: "Neon Purple",
    category: "NEON_ENERGY",
    best_for: ["creative", "art", "unique"],
    title: {
      font: "Arial",
      fontsize: 75,
      fontcolor: "#9C27B0",
      bordercolor: "#BA68C8",
      borderw: 7,
      box: 1,
      boxcolor: "black@0.81",
      boxborderw: 25,
      shadowcolor: "#9C27B0@0.5",
      shadowx: 0,
      shadowy: 0,
      y: 238
    },
    sub: {
      font: "Roboto",
      fontsize: 68,
      fontcolor: "#CE93D8",
      bordercolor: "#4A148C",
      borderw: 12,
      shadowcolor: "#9C27B0@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-342"
    }
  },

  // ========================================
  // 🎓 ELEGANT (Изящные, образовательные)
  // ========================================

  "serif_classic": {
    name: "Serif Classic",
    category: "ELEGANT",
    best_for: ["education", "literature", "classy"],
    title: {
      font: "Times New Roman",
      fontsize: 72,
      fontcolor: "#2C3E50",
      bordercolor: "#ECF0F1",
      borderw: 6,
      box: 1,
      boxcolor: "#ECF0F1@0.92",
      boxborderw: 28,
      shadowcolor: "black@0.2",
      shadowx: 2,
      shadowy: 2,
      y: 240
    },
    sub: {
      font: "Georgia",
      fontsize: 64,
      fontcolor: "#34495E",
      bordercolor: "#BDC3C7",
      borderw: 8,
      shadowcolor: "black@0.3",
      shadowx: 1,
      shadowy: 1,
      box: 0,
      y: "h-345"
    }
  },

  "minimal_modern": {
    name: "Minimal Modern",
    category: "ELEGANT",
    best_for: ["design", "minimal", "modern"],
    title: {
      font: "Helvetica Neue",
      fontsize: 70,
      fontcolor: "#212121",
      bordercolor: "white",
      borderw: 0,
      box: 1,
      boxcolor: "white@0.88",
      boxborderw: 30,
      shadowcolor: "black@0.15",
      shadowx: 1,
      shadowy: 1,
      y: 245
    },
    sub: {
      font: "Roboto",
      fontsize: 62,
      fontcolor: "#424242",
      bordercolor: "#EEEEEE",
      borderw: 6,
      shadowcolor: "black@0.2",
      shadowx: 1,
      shadowy: 1,
      box: 0,
      y: "h-350"
    }
  },

  "gold_premium": {
    name: "Gold Premium",
    category: "ELEGANT",
    best_for: ["luxury", "premium", "exclusive"],
    title: {
      font: "Georgia",
      fontsize: 73,
      fontcolor: "#FFD700",
      bordercolor: "#B8860B",
      borderw: 5,
      box: 1,
      boxcolor: "#1a1a1a@0.90",
      boxborderw: 27,
      shadowcolor: "#FFD700@0.3",
      shadowx: 2,
      shadowy: 2,
      y: 237
    },
    sub: {
      font: "Times New Roman",
      fontsize: 65,
      fontcolor: "#F4D03F",
      bordercolor: "#7D6608",
      borderw: 9,
      shadowcolor: "black@0.4",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-343"
    }
  },

  // ========================================
  // 😂 MEME STYLE (Вирусные, мемы)
  // ========================================

  "impact_meme": {
    name: "Impact Meme",
    category: "MEME_STYLE",
    best_for: ["memes", "viral", "funny"],
    title: {
      font: "Impact",
      fontsize: 84,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 12,
      box: 0,
      shadowcolor: "black@0.8",
      shadowx: 5,
      shadowy: 5,
      y: 180
    },
    sub: {
      font: "Impact",
      fontsize: 76,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 12,
      shadowcolor: "black@0.8",
      shadowx: 5,
      shadowy: 5,
      box: 0,
      y: "h-280"
    }
  },

  "comic_sans_chaos": {
    name: "Comic Sans Chaos",
    category: "MEME_STYLE",
    best_for: ["ironic", "casual", "fun"],
    title: {
      font: "Comic Sans MS",
      fontsize: 74,
      fontcolor: "#FF00FF",
      bordercolor: "#00FFFF",
      borderw: 8,
      box: 1,
      boxcolor: "black@0.75",
      boxborderw: 22,
      shadowcolor: "white@0.4",
      shadowx: 3,
      shadowy: 3,
      y: 242
    },
    sub: {
      font: "Comic Sans MS",
      fontsize: 66,
      fontcolor: "#00FF00",
      bordercolor: "#FF1493",
      borderw: 10,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-348"
    }
  },

  "all_caps_energy": {
    name: "ALL CAPS ENERGY",
    category: "MEME_STYLE",
    best_for: ["hype", "excited", "energy"],
    title: {
      font: "Arial Black",
      fontsize: 82,
      fontcolor: "yellow",
      bordercolor: "red",
      borderw: 10,
      box: 1,
      boxcolor: "black@0.80",
      boxborderw: 24,
      shadowcolor: "red@0.6",
      shadowx: 4,
      shadowy: 4,
      y: 205
    },
    sub: {
      font: "Arial Black",
      fontsize: 72,
      fontcolor: "white",
      bordercolor: "yellow",
      borderw: 14,
      shadowcolor: "black@0.7",
      shadowx: 4,
      shadowy: 4,
      box: 0,
      y: "h-315"
    }
  },

  // ========================================
  // 🎬 PLATFORM SPECIFIC
  // ========================================

  "youtube_optimal": {
    name: "YouTube Optimal",
    category: "PLATFORM_SPECIFIC",
    platform: "youtube",
    best_for: ["youtube_shorts"],
    title: {
      font: "Roboto",
      fontsize: 76,
      fontcolor: "white",
      bordercolor: "#FF0000",
      borderw: 6,
      box: 1,
      boxcolor: "#282828@0.88",
      boxborderw: 26,
      shadowcolor: "black@0.5",
      shadowx: 3,
      shadowy: 3,
      y: 220
    },
    sub: {
      font: "Roboto",
      fontsize: 68,
      fontcolor: "white",
      bordercolor: "#CC0000",
      borderw: 10,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-340"
    }
  },

  "tiktok_viral": {
    name: "TikTok Viral",
    category: "PLATFORM_SPECIFIC",
    platform: "tiktok",
    best_for: ["tiktok"],
    title: {
      font: "Montserrat",
      fontsize: 78,
      fontcolor: "#00F2EA",
      bordercolor: "#FE2C55",
      borderw: 7,
      box: 1,
      boxcolor: "black@0.82",
      boxborderw: 28,
      shadowcolor: "#00F2EA@0.5",
      shadowx: 0,
      shadowy: 0,
      y: 225
    },
    sub: {
      font: "Montserrat",
      fontsize: 70,
      fontcolor: "white",
      bordercolor: "#00F2EA",
      borderw: 12,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-335"
    }
  },

  "instagram_aesthetic": {
    name: "Instagram Aesthetic",
    category: "PLATFORM_SPECIFIC",
    platform: "instagram",
    best_for: ["instagram_reels"],
    title: {
      font: "Helvetica",
      fontsize: 74,
      fontcolor: "white",
      bordercolor: "#E1306C",
      borderw: 5,
      box: 1,
      boxcolor: "#833AB4@0.85",
      boxborderw: 25,
      shadowcolor: "black@0.4",
      shadowx: 2,
      shadowy: 2,
      y: 235
    },
    sub: {
      font: "Helvetica",
      fontsize: 66,
      fontcolor: "#FCAF45",
      bordercolor: "#C13584",
      borderw: 11,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-345"
    }
  }
};

/**
 * Получить случайный шаблон
 */
function getRandomTemplate() {
  const keys = Object.keys(VISUAL_TEMPLATES);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];
  return VISUAL_TEMPLATES[randomKey];
}

/**
 * Получить шаблон по категории
 */
function getTemplatesByCategory(category) {
  return Object.entries(VISUAL_TEMPLATES)
    .filter(([_, template]) => template.category === category)
    .map(([key, template]) => ({ key, ...template }));
}

/**
 * Получить шаблон для платформы
 */
function getTemplateForPlatform(platform) {
  const platformTemplates = Object.entries(VISUAL_TEMPLATES)
    .filter(([_, template]) => template.platform === platform);

  if (platformTemplates.length > 0) {
    const randomIdx = Math.floor(Math.random() * platformTemplates.length);
    return platformTemplates[randomIdx][1];
  }

  // Fallback to random template
  return getRandomTemplate();
}

// Export для использования в n8n
module.exports = {
  VISUAL_TEMPLATES,
  getRandomTemplate,
  getTemplatesByCategory,
  getTemplateForPlatform
};
