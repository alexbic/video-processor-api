/**
 * Visual Templates Library v3.0 - Gaming Edition
 *
 * 30 шаблонов специально для игрового контента
 *
 * Особенности:
 * - Только шрифты с поддержкой кириллицы
 * - Контрастные цветовые схемы (заголовок ≠ субтитры)
 * - Вариации стилей (box/no-box)
 * - Оптимизировано для gaming контента
 */

const GAMING_TEMPLATES = {

  // ========================================
  // 🎮 GAMING CONTRAST (10 шаблонов)
  // Заголовок на плашке, субтитры без плашки
  // ========================================

  "cyber_neon": {
    name: "Cyber Neon",
    category: "GAMING_CONTRAST",
    best_for: ["cyberpunk", "tech", "sci-fi"],
    title: {
      font: "Russo One",
      fontsize: 80,
      fontcolor: "#00FFFF",          // Cyan заголовок
      bordercolor: "#0080FF",
      borderw: 0,
      box: 1,
      boxcolor: "#0a0a0a@0.88",
      boxborderw: 28,
      shadowcolor: "#00FFFF@0.7",
      shadowx: 0,
      shadowy: 0,
      y: 210
    },
    sub: {
      font: "Montserrat",
      fontsize: 70,
      fontcolor: "#FF00FF",          // Magenta субтитры - контраст!
      bordercolor: "#800080",
      borderw: 12,
      shadowcolor: "#FF00FF@0.5",
      shadowx: 0,
      shadowy: 0,
      box: 0,                         // Субтитры БЕЗ плашки
      y: "h-330"
    }
  },

  "fire_ice": {
    name: "Fire & Ice",
    category: "GAMING_CONTRAST",
    best_for: ["action", "battle", "pvp"],
    title: {
      font: "Oswald",
      fontsize: 82,
      fontcolor: "#FF4500",          // Оранжевый "огонь"
      bordercolor: "#FF6347",
      borderw: 8,
      box: 1,
      boxcolor: "black@0.85",
      boxborderw: 26,
      shadowcolor: "#FF4500@0.6",
      shadowx: 2,
      shadowy: 2,
      y: 205
    },
    sub: {
      font: "PT Sans",
      fontsize: 68,
      fontcolor: "#00CED1",          // Голубой "лёд" - контраст!
      bordercolor: "#005F73",
      borderw: 14,
      shadowcolor: "#00CED1@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-335"
    }
  },

  "gold_purple": {
    name: "Gold & Purple",
    category: "GAMING_CONTRAST",
    best_for: ["rpg", "fantasy", "magic"],
    title: {
      font: "Fixel",
      fontsize: 76,
      fontcolor: "#FFD700",          // Золотой
      bordercolor: "#B8860B",
      borderw: 6,
      box: 1,
      boxcolor: "#1a0a2e@0.90",      // Тёмно-фиолетовый фон
      boxborderw: 30,
      shadowcolor: "#FFD700@0.4",
      shadowx: 3,
      shadowy: 3,
      y: 220
    },
    sub: {
      font: "Montserrat",
      fontsize: 67,
      fontcolor: "#9370DB",          // Фиолетовый субтитры
      bordercolor: "#4B0082",
      borderw: 11,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-340"
    }
  },

  "toxic_green": {
    name: "Toxic Green",
    category: "GAMING_CONTRAST",
    best_for: ["horror", "zombie", "survival"],
    title: {
      font: "Russo One",
      fontsize: 78,
      fontcolor: "#39FF14",          // Кислотно-зелёный
      bordercolor: "#00FF00",
      borderw: 7,
      box: 1,
      boxcolor: "#0d0d0d@0.87",
      boxborderw: 25,
      shadowcolor: "#39FF14@0.8",
      shadowx: 0,
      shadowy: 0,
      y: 215
    },
    sub: {
      font: "PT Sans",
      fontsize: 69,
      fontcolor: "#FF073A",          // Красный - кровь, контраст!
      bordercolor: "#8B0000",
      borderw: 13,
      shadowcolor: "black@0.7",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-328"
    }
  },

  "electric_yellow": {
    name: "Electric Yellow",
    category: "GAMING_CONTRAST",
    best_for: ["racing", "speed", "energy"],
    title: {
      font: "Oswald",
      fontsize: 81,
      fontcolor: "#FFFF00",          // Ярко-жёлтый
      bordercolor: "#FFD700",
      borderw: 5,
      box: 1,
      boxcolor: "black@0.83",
      boxborderw: 27,
      shadowcolor: "#FFFF00@0.5",
      shadowx: 2,
      shadowy: 2,
      y: 208
    },
    sub: {
      font: "Fixel",
      fontsize: 68,
      fontcolor: "#1E90FF",          // Синий - контраст!
      bordercolor: "#00008B",
      borderw: 12,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-332"
    }
  },

  "blood_shadow": {
    name: "Blood Shadow",
    category: "GAMING_CONTRAST",
    best_for: ["dark", "vampire", "gothic"],
    title: {
      font: "Russo One",
      fontsize: 77,
      fontcolor: "#8B0000",          // Тёмно-красный
      bordercolor: "#DC143C",
      borderw: 8,
      box: 1,
      boxcolor: "#1a0000@0.92",      // Почти чёрный с красным
      boxborderw: 29,
      shadowcolor: "#8B0000@0.6",
      shadowx: 4,
      shadowy: 4,
      y: 218
    },
    sub: {
      font: "Montserrat",
      fontsize: 66,
      fontcolor: "#C0C0C0",          // Серебристый - контраст!
      bordercolor: "#696969",
      borderw: 10,
      shadowcolor: "black@0.7",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-338"
    }
  },

  "matrix_code": {
    name: "Matrix Code",
    category: "GAMING_CONTRAST",
    best_for: ["hacking", "cyber", "matrix"],
    title: {
      font: "Fixel",
      fontsize: 79,
      fontcolor: "#00FF41",          // Matrix зелёный
      bordercolor: "#008F11",
      borderw: 6,
      box: 1,
      boxcolor: "black@0.89",
      boxborderw: 26,
      shadowcolor: "#00FF41@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 212
    },
    sub: {
      font: "PT Sans",
      fontsize: 69,
      fontcolor: "#00FFFF",          // Cyan - контраст!
      bordercolor: "#008B8B",
      borderw: 11,
      shadowcolor: "#00FFFF@0.4",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-334"
    }
  },

  "royal_blue": {
    name: "Royal Blue",
    category: "GAMING_CONTRAST",
    best_for: ["strategy", "empire", "rts"],
    title: {
      font: "Oswald",
      fontsize: 78,
      fontcolor: "#4169E1",          // Королевский синий
      bordercolor: "#1E90FF",
      borderw: 7,
      box: 1,
      boxcolor: "#0a0a2e@0.88",
      boxborderw: 28,
      shadowcolor: "black@0.5",
      shadowx: 3,
      shadowy: 3,
      y: 216
    },
    sub: {
      font: "Montserrat",
      fontsize: 68,
      fontcolor: "#FFD700",          // Золотой - контраст!
      bordercolor: "#B8860B",
      borderw: 12,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-336"
    }
  },

  "lava_glow": {
    name: "Lava Glow",
    category: "GAMING_CONTRAST",
    best_for: ["boss", "fire", "epic"],
    title: {
      font: "Russo One",
      fontsize: 80,
      fontcolor: "#FF4500",          // Оранжево-красный
      bordercolor: "#FF6347",
      borderw: 8,
      box: 1,
      boxcolor: "#2b0000@0.90",
      boxborderw: 27,
      shadowcolor: "#FF4500@0.7",
      shadowx: 0,
      shadowy: 0,
      y: 210
    },
    sub: {
      font: "Fixel",
      fontsize: 69,
      fontcolor: "#00FFFF",          // Cyan - максимальный контраст!
      bordercolor: "#008B8B",
      borderw: 13,
      shadowcolor: "#00FFFF@0.5",
      shadowx: 0,
      shadowy: 0,
      box: 0,
      y: "h-330"
    }
  },

  "cosmic_purple": {
    name: "Cosmic Purple",
    category: "GAMING_CONTRAST",
    best_for: ["space", "cosmic", "alien"],
    title: {
      font: "Fixel",
      fontsize: 77,
      fontcolor: "#9370DB",          // Фиолетовый
      bordercolor: "#8A2BE2",
      borderw: 6,
      box: 1,
      boxcolor: "#0a0015@0.88",
      boxborderw: 28,
      shadowcolor: "#9370DB@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 214
    },
    sub: {
      font: "PT Sans",
      fontsize: 68,
      fontcolor: "#00FF7F",          // Весенний зелёный - контраст!
      bordercolor: "#006400",
      borderw: 11,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-334"
    }
  },

  // ========================================
  // 💥 DOUBLE BOX (10 шаблонов)
  // Заголовок И субтитры на плашках
  // ========================================

  "double_neon": {
    name: "Double Neon",
    category: "DOUBLE_BOX",
    best_for: ["important", "tutorial", "guide"],
    title: {
      font: "Russo One",
      fontsize: 78,
      fontcolor: "#00FFFF",
      bordercolor: "#00CED1",
      borderw: 0,
      box: 1,
      boxcolor: "black@0.88",
      boxborderw: 26,
      shadowcolor: "#00FFFF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 215
    },
    sub: {
      font: "Montserrat",
      fontsize: 67,
      fontcolor: "#FFD700",          // Золотой
      bordercolor: "#FFA500",
      borderw: 0,
      shadowcolor: "black@0.4",
      shadowx: 2,
      shadowy: 2,
      box: 1,                         // Субтитры ТОЖЕ на плашке!
      boxcolor: "black@0.82",
      boxborderw: 20,
      y: "h-335"
    }
  },

  "double_impact": {
    name: "Double Impact",
    category: "DOUBLE_BOX",
    best_for: ["alert", "breaking", "news"],
    title: {
      font: "Oswald",
      fontsize: 80,
      fontcolor: "white",
      bordercolor: "#FF0000",
      borderw: 6,
      box: 1,
      boxcolor: "#8B0000@0.92",      // Тёмно-красный
      boxborderw: 28,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      y: 208
    },
    sub: {
      font: "PT Sans",
      fontsize: 68,
      fontcolor: "#FFFF00",          // Жёлтый
      bordercolor: "#FFD700",
      borderw: 0,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 1,
      boxcolor: "black@0.85",
      boxborderw: 22,
      y: "h-332"
    }
  },

  "double_elegant": {
    name: "Double Elegant",
    category: "DOUBLE_BOX",
    best_for: ["education", "story", "lore"],
    title: {
      font: "Fixel",
      fontsize: 74,
      fontcolor: "#2C3E50",
      bordercolor: "#34495E",
      borderw: 0,
      box: 1,
      boxcolor: "#ECF0F1@0.92",      // Светлый
      boxborderw: 30,
      shadowcolor: "black@0.2",
      shadowx: 2,
      shadowy: 2,
      y: 222
    },
    sub: {
      font: "Montserrat",
      fontsize: 64,
      fontcolor: "#34495E",
      bordercolor: "#2C3E50",
      borderw: 0,
      shadowcolor: "black@0.15",
      shadowx: 1,
      shadowy: 1,
      box: 1,
      boxcolor: "white@0.88",
      boxborderw: 24,
      y: "h-342"
    }
  },

  "double_toxic": {
    name: "Double Toxic",
    category: "DOUBLE_BOX",
    best_for: ["poison", "radioactive", "danger"],
    title: {
      font: "Russo One",
      fontsize: 79,
      fontcolor: "#39FF14",          // Кислотно-зелёный
      bordercolor: "#00FF00",
      borderw: 0,
      box: 1,
      boxcolor: "#0d0d0d@0.90",
      boxborderw: 27,
      shadowcolor: "#39FF14@0.7",
      shadowx: 0,
      shadowy: 0,
      y: 212
    },
    sub: {
      font: "Oswald",
      fontsize: 68,
      fontcolor: "#FF073A",          // Красный
      bordercolor: "#DC143C",
      borderw: 0,
      shadowcolor: "black@0.6",
      shadowx: 2,
      shadowy: 2,
      box: 1,
      boxcolor: "#1a0000@0.88",
      boxborderw: 23,
      y: "h-334"
    }
  },

  "double_gold": {
    name: "Double Gold",
    category: "DOUBLE_BOX",
    best_for: ["achievement", "victory", "epic"],
    title: {
      font: "Fixel",
      fontsize: 76,
      fontcolor: "#FFD700",
      bordercolor: "#FFA500",
      borderw: 0,
      box: 1,
      boxcolor: "#1a1a0a@0.90",
      boxborderw: 28,
      shadowcolor: "#FFD700@0.4",
      shadowx: 3,
      shadowy: 3,
      y: 218
    },
    sub: {
      font: "Montserrat",
      fontsize: 66,
      fontcolor: "#F0E68C",          // Светло-золотой
      bordercolor: "#DAA520",
      borderw: 0,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 1,
      boxcolor: "#2b2b15@0.87",
      boxborderw: 24,
      y: "h-338"
    }
  },

  "double_cyber": {
    name: "Double Cyber",
    category: "DOUBLE_BOX",
    best_for: ["futuristic", "tech", "digital"],
    title: {
      font: "Russo One",
      fontsize: 78,
      fontcolor: "#00FFFF",
      bordercolor: "#00CED1",
      borderw: 0,
      box: 1,
      boxcolor: "#001a1a@0.89",
      boxborderw: 26,
      shadowcolor: "#00FFFF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 214
    },
    sub: {
      font: "PT Sans",
      fontsize: 67,
      fontcolor: "#FF00FF",          // Magenta
      bordercolor: "#C71585",
      borderw: 0,
      shadowcolor: "#FF00FF@0.5",
      shadowx: 0,
      shadowy: 0,
      box: 1,
      boxcolor: "#1a001a@0.86",
      boxborderw: 21,
      y: "h-336"
    }
  },

  "double_fire": {
    name: "Double Fire",
    category: "DOUBLE_BOX",
    best_for: ["battle", "war", "intense"],
    title: {
      font: "Oswald",
      fontsize: 80,
      fontcolor: "#FF4500",
      bordercolor: "#FF6347",
      borderw: 0,
      box: 1,
      boxcolor: "#2b0000@0.91",
      boxborderw: 27,
      shadowcolor: "#FF4500@0.6",
      shadowx: 2,
      shadowy: 2,
      y: 210
    },
    sub: {
      font: "Fixel",
      fontsize: 68,
      fontcolor: "#FFD700",          // Золотой
      bordercolor: "#FFA500",
      borderw: 0,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 1,
      boxcolor: "#1a1a00@0.88",
      boxborderw: 22,
      y: "h-332"
    }
  },

  "double_ice": {
    name: "Double Ice",
    category: "DOUBLE_BOX",
    best_for: ["frost", "winter", "frozen"],
    title: {
      font: "Fixel",
      fontsize: 77,
      fontcolor: "#00CED1",          // Бирюзовый
      bordercolor: "#5F9EA0",
      borderw: 0,
      box: 1,
      boxcolor: "#001a2b@0.89",
      boxborderw: 28,
      shadowcolor: "#00CED1@0.5",
      shadowx: 0,
      shadowy: 0,
      y: 216
    },
    sub: {
      font: "Montserrat",
      fontsize: 67,
      fontcolor: "#B0E0E6",          // Светло-голубой
      bordercolor: "#4682B4",
      borderw: 0,
      shadowcolor: "black@0.4",
      shadowx: 1,
      shadowy: 1,
      box: 1,
      boxcolor: "#00151f@0.85",
      boxborderw: 23,
      y: "h-337"
    }
  },

  "double_purple": {
    name: "Double Purple",
    category: "DOUBLE_BOX",
    best_for: ["magic", "fantasy", "mystical"],
    title: {
      font: "Russo One",
      fontsize: 78,
      fontcolor: "#9370DB",
      bordercolor: "#8A2BE2",
      borderw: 0,
      box: 1,
      boxcolor: "#1a0a2e@0.90",
      boxborderw: 27,
      shadowcolor: "#9370DB@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 213
    },
    sub: {
      font: "PT Sans",
      fontsize: 68,
      fontcolor: "#DA70D6",          // Орхидея
      bordercolor: "#BA55D3",
      borderw: 0,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 1,
      boxcolor: "#2b0a3d@0.87",
      boxborderw: 22,
      y: "h-334"
    }
  },

  "double_clean": {
    name: "Double Clean",
    category: "DOUBLE_BOX",
    best_for: ["tutorial", "how-to", "guide"],
    title: {
      font: "Montserrat",
      fontsize: 75,
      fontcolor: "#212121",
      bordercolor: "#424242",
      borderw: 0,
      box: 1,
      boxcolor: "white@0.92",
      boxborderw: 30,
      shadowcolor: "black@0.15",
      shadowx: 1,
      shadowy: 1,
      y: 220
    },
    sub: {
      font: "PT Sans",
      fontsize: 65,
      fontcolor: "#424242",
      bordercolor: "#616161",
      borderw: 0,
      shadowcolor: "black@0.12",
      shadowx: 1,
      shadowy: 1,
      box: 1,
      boxcolor: "#F5F5F5@0.90",
      boxborderw: 25,
      y: "h-343"
    }
  },

  // ========================================
  // ⚡ NO BOX (10 шаблонов)
  // Заголовок И субтитры БЕЗ плашек - только обводка
  // ========================================

  "outline_neon": {
    name: "Outline Neon",
    category: "NO_BOX",
    best_for: ["clean", "minimal", "modern"],
    title: {
      font: "Russo One",
      fontsize: 82,
      fontcolor: "#00FFFF",
      bordercolor: "#008B8B",
      borderw: 12,
      box: 0,                         // БЕЗ плашки!
      shadowcolor: "#00FFFF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 200
    },
    sub: {
      font: "Montserrat",
      fontsize: 72,
      fontcolor: "#FF00FF",
      bordercolor: "#8B008B",
      borderw: 14,
      shadowcolor: "#FF00FF@0.5",
      shadowx: 0,
      shadowy: 0,
      box: 0,                         // БЕЗ плашки!
      y: "h-310"
    }
  },

  "outline_fire": {
    name: "Outline Fire",
    category: "NO_BOX",
    best_for: ["action", "dynamic", "fast"],
    title: {
      font: "Oswald",
      fontsize: 84,
      fontcolor: "#FF4500",
      bordercolor: "#8B0000",
      borderw: 14,
      box: 0,
      shadowcolor: "black@0.8",
      shadowx: 4,
      shadowy: 4,
      y: 195
    },
    sub: {
      font: "Fixel",
      fontsize: 74,
      fontcolor: "#FFD700",
      bordercolor: "#B8860B",
      borderw: 16,
      shadowcolor: "black@0.7",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-305"
    }
  },

  "outline_classic": {
    name: "Outline Classic",
    category: "NO_BOX",
    best_for: ["meme", "viral", "classic"],
    title: {
      font: "Russo One",
      fontsize: 86,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 15,
      box: 0,
      shadowcolor: "black@0.9",
      shadowx: 5,
      shadowy: 5,
      y: 190
    },
    sub: {
      font: "PT Sans",
      fontsize: 76,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 14,
      shadowcolor: "black@0.8",
      shadowx: 4,
      shadowy: 4,
      box: 0,
      y: "h-300"
    }
  },

  "outline_rainbow": {
    name: "Outline Rainbow",
    category: "NO_BOX",
    best_for: ["fun", "colorful", "happy"],
    title: {
      font: "Fixel",
      fontsize: 83,
      fontcolor: "#FF69B4",          // Розовый
      bordercolor: "#FF1493",
      borderw: 13,
      box: 0,
      shadowcolor: "#FF00FF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 198
    },
    sub: {
      font: "Montserrat",
      fontsize: 73,
      fontcolor: "#00FF7F",          // Весенний зелёный
      bordercolor: "#008B45",
      borderw: 15,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-308"
    }
  },

  "outline_gold": {
    name: "Outline Gold",
    category: "NO_BOX",
    best_for: ["epic", "legendary", "rare"],
    title: {
      font: "Oswald",
      fontsize: 85,
      fontcolor: "#FFD700",
      bordercolor: "#B8860B",
      borderw: 14,
      box: 0,
      shadowcolor: "black@0.7",
      shadowx: 4,
      shadowy: 4,
      y: 193
    },
    sub: {
      font: "Russo One",
      fontsize: 75,
      fontcolor: "#FFA500",          // Оранжевый
      bordercolor: "#FF8C00",
      borderw: 16,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-303"
    }
  },

  "outline_toxic": {
    name: "Outline Toxic",
    category: "NO_BOX",
    best_for: ["poison", "acid", "bio"],
    title: {
      font: "Russo One",
      fontsize: 84,
      fontcolor: "#39FF14",
      bordercolor: "#00FF00",
      borderw: 15,
      box: 0,
      shadowcolor: "#39FF14@0.8",
      shadowx: 0,
      shadowy: 0,
      y: 196
    },
    sub: {
      font: "Fixel",
      fontsize: 74,
      fontcolor: "#ADFF2F",          // Жёлто-зелёный
      bordercolor: "#7FFF00",
      borderw: 14,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-306"
    }
  },

  "outline_blood": {
    name: "Outline Blood",
    category: "NO_BOX",
    best_for: ["horror", "dark", "brutal"],
    title: {
      font: "Oswald",
      fontsize: 85,
      fontcolor: "#DC143C",          // Малиновый
      bordercolor: "#8B0000",
      borderw: 16,
      box: 0,
      shadowcolor: "black@0.8",
      shadowx: 5,
      shadowy: 5,
      y: 194
    },
    sub: {
      font: "PT Sans",
      fontsize: 75,
      fontcolor: "#FF6347",          // Томатный
      bordercolor: "#B22222",
      borderw: 14,
      shadowcolor: "black@0.7",
      shadowx: 4,
      shadowy: 4,
      box: 0,
      y: "h-304"
    }
  },

  "outline_ice": {
    name: "Outline Ice",
    category: "NO_BOX",
    best_for: ["frost", "cold", "frozen"],
    title: {
      font: "Fixel",
      fontsize: 83,
      fontcolor: "#00CED1",
      bordercolor: "#008B8B",
      borderw: 13,
      box: 0,
      shadowcolor: "#00FFFF@0.6",
      shadowx: 0,
      shadowy: 0,
      y: 197
    },
    sub: {
      font: "Montserrat",
      fontsize: 73,
      fontcolor: "#87CEEB",          // Небесно-голубой
      bordercolor: "#4682B4",
      borderw: 15,
      shadowcolor: "black@0.5",
      shadowx: 2,
      shadowy: 2,
      box: 0,
      y: "h-307"
    }
  },

  "outline_purple": {
    name: "Outline Purple",
    category: "NO_BOX",
    best_for: ["magic", "arcane", "spell"],
    title: {
      font: "Russo One",
      fontsize: 84,
      fontcolor: "#9370DB",
      bordercolor: "#4B0082",
      borderw: 14,
      box: 0,
      shadowcolor: "#9370DB@0.7",
      shadowx: 0,
      shadowy: 0,
      y: 195
    },
    sub: {
      font: "Oswald",
      fontsize: 74,
      fontcolor: "#DA70D6",
      bordercolor: "#8B008B",
      borderw: 16,
      shadowcolor: "black@0.6",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-305"
    }
  },

  "outline_contrast": {
    name: "Outline Contrast",
    category: "NO_BOX",
    best_for: ["universal", "readable", "safe"],
    title: {
      font: "Montserrat",
      fontsize: 82,
      fontcolor: "white",
      bordercolor: "black",
      borderw: 13,
      box: 0,
      shadowcolor: "black@0.8",
      shadowx: 4,
      shadowy: 4,
      y: 198
    },
    sub: {
      font: "PT Sans",
      fontsize: 72,
      fontcolor: "#FFFF00",          // Жёлтый
      bordercolor: "black",
      borderw: 15,
      shadowcolor: "black@0.7",
      shadowx: 3,
      shadowy: 3,
      box: 0,
      y: "h-308"
    }
  }
};

/**
 * Получить случайный шаблон
 */
function getRandomTemplate() {
  const keys = Object.keys(GAMING_TEMPLATES);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];
  return GAMING_TEMPLATES[randomKey];
}

/**
 * Получить шаблон по категории
 */
function getTemplatesByCategory(category) {
  return Object.entries(GAMING_TEMPLATES)
    .filter(([_, template]) => template.category === category)
    .map(([key, template]) => ({ key, ...template }));
}

// Export
module.exports = {
  GAMING_TEMPLATES,
  getRandomTemplate,
  getTemplatesByCategory
};
