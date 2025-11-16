// ===================================================================
// n8n Code Node: УПРОЩЁННАЯ ВЕРСИЯ
// Скопируйте этот код в Code Node в n8n
// ===================================================================

// 5 готовых шаблонов
const templates = [
  // 1. Классический белый
  {
    name: "Classic White",
    title: { fontsize: 72, fontcolor: "black", bordercolor: "white", borderw: 8,
             box: 1, boxcolor: "white@0.85", boxborderw: 20, y: 250 },
    subtitles: { fontsize: 68, fontcolor: "black", bordercolor: "white",
                borderw: 10, box: 0, y: "h-350" }
  },
  // 2. Жёлтая энергия
  {
    name: "Yellow Energy",
    title: { fontsize: 80, fontcolor: "black", bordercolor: "yellow", borderw: 4,
             box: 1, boxcolor: "yellow@0.95", boxborderw: 30, y: 220 },
    subtitles: { fontsize: 64, fontcolor: "#FFFF00", bordercolor: "#FFD700",
                borderw: 12, box: 0, y: "h-320" }
  },
  // 3. Неоновый зелёный
  {
    name: "Neon Green",
    title: { fontsize: 76, fontcolor: "white", bordercolor: "#00FF00", borderw: 6,
             box: 1, boxcolor: "black@0.80", boxborderw: 25, y: 240 },
    subtitles: { fontsize: 66, fontcolor: "#00FF00", bordercolor: "#006400",
                borderw: 14, box: 0, y: "h-340" }
  },
  // 4. Красная тревога
  {
    name: "Red Alert",
    title: { fontsize: 78, fontcolor: "white", bordercolor: "red", borderw: 5,
             box: 1, boxcolor: "red@0.90", boxborderw: 28, y: 230 },
    subtitles: { fontsize: 70, fontcolor: "#FF6B6B", bordercolor: "#8B0000",
                borderw: 10, box: 0, y: "h-330" }
  },
  // 5. Синий премиум
  {
    name: "Blue Premium",
    title: { fontsize: 74, fontcolor: "white", bordercolor: "#00BFFF", borderw: 6,
             box: 1, boxcolor: "#0066CC@0.88", boxborderw: 26, y: 235 },
    subtitles: { fontsize: 67, fontcolor: "#87CEEB", bordercolor: "#00008B",
                borderw: 11, box: 0, y: "h-345" }
  }
];

// Случайный выбор
const tpl = templates[Math.floor(Math.random() * templates.length)];

// Входящие данные
const data = $input.first().json;

// Формируем запрос
return {
  json: {
    video_url: data.source_video_url,
    execution: "async",
    operations: [{
      type: "make_short",
      start_time: data.start,
      end_time: data.end,
      crop_mode: "letterbox",
      letterbox_config: { blur_radius: 20 },
      title: {
        text: data.title,
        font: "DejaVu Sans Bold",
        ...tpl.title,
        x: "center",
        start_time: 0.0,
        duration: 5,
        fade_in: 0.3,
        fade_out: 0.5
      },
      subtitles: {
        items: data.subtitles,
        font: "Roboto",
        ...tpl.subtitles
      },
      generate_thumbnail: true,
      thumbnail_timestamp: 0.5
    }],
    client_meta: data.client_meta || {},

    // Для логов
    _template: tpl.name
  }
};
