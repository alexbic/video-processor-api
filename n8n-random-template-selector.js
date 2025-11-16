// ===================================================================
// n8n Code Node: Random Template Selector
// ===================================================================
// Этот код выбирает случайный шаблон из 5 визуальных стилей
// и подставляет данные из входящего JSON
// ===================================================================

// Шаблоны визуальных стилей
const templates = [
  {
    name: "Classic White",
    description: "Классический стиль: чёрный текст на белом фоне",
    title: {
      font: "DejaVu Sans Bold",
      fontsize: 72,
      fontcolor: "black",
      bordercolor: "white",
      borderw: 8,
      box: 1,
      boxcolor: "white@0.85",
      boxborderw: 20,
      y: 250
    },
    subtitles: {
      font: "Roboto",
      fontsize: 68,
      fontcolor: "black",
      bordercolor: "white",
      borderw: 10,
      box: 0,
      y: "h-350"
    }
  },
  {
    name: "Bright Yellow Energy",
    description: "Яркая энергичная плашка: чёрный текст на жёлтом фоне",
    title: {
      font: "DejaVu Sans Bold",
      fontsize: 80,
      fontcolor: "black",
      bordercolor: "yellow",
      borderw: 4,
      box: 1,
      boxcolor: "yellow@0.95",
      boxborderw: 30,
      y: 220
    },
    subtitles: {
      font: "Roboto",
      fontsize: 64,
      fontcolor: "#FFFF00",
      bordercolor: "#FFD700",
      borderw: 12,
      box: 0,
      y: "h-320"
    }
  },
  {
    name: "Neon Green Cyber",
    description: "Киберпанк стиль: неоновый зелёный с размытием",
    title: {
      font: "DejaVu Sans Bold",
      fontsize: 76,
      fontcolor: "white",
      bordercolor: "#00FF00",
      borderw: 6,
      box: 1,
      boxcolor: "black@0.80",
      boxborderw: 25,
      y: 240
    },
    subtitles: {
      font: "Roboto",
      fontsize: 66,
      fontcolor: "#00FF00",
      bordercolor: "#006400",
      borderw: 14,
      box: 0,
      y: "h-340"
    }
  },
  {
    name: "Red Alert Bold",
    description: "Привлекающий внимание: белый текст на красном фоне",
    title: {
      font: "DejaVu Sans Bold",
      fontsize: 78,
      fontcolor: "white",
      bordercolor: "red",
      borderw: 5,
      box: 1,
      boxcolor: "red@0.90",
      boxborderw: 28,
      y: 230
    },
    subtitles: {
      font: "Roboto",
      fontsize: 70,
      fontcolor: "#FF6B6B",
      bordercolor: "#8B0000",
      borderw: 10,
      box: 0,
      y: "h-330"
    }
  },
  {
    name: "Cool Blue Premium",
    description: "Премиальный стиль: белый текст на синем градиенте",
    title: {
      font: "DejaVu Sans Bold",
      fontsize: 74,
      fontcolor: "white",
      bordercolor: "#00BFFF",
      borderw: 6,
      box: 1,
      boxcolor: "#0066CC@0.88",
      boxborderw: 26,
      y: 235
    },
    subtitles: {
      font: "Roboto",
      fontsize: 67,
      fontcolor: "#87CEEB",
      bordercolor: "#00008B",
      borderw: 11,
      box: 0,
      y: "h-345"
    }
  }
];

// Получаем входящие данные
const inputData = $input.first().json;

// Случайно выбираем шаблон
const randomTemplate = templates[Math.floor(Math.random() * templates.length)];

// Формируем финальный запрос с выбранным шаблоном
const requestBody = {
  video_url: inputData.source_video_url,
  execution: "async",
  operations: [
    {
      type: "make_short",
      start_time: inputData.start,
      end_time: inputData.end,
      crop_mode: "letterbox",
      letterbox_config: {
        blur_radius: 20
      },
      title: {
        text: inputData.title,
        font: randomTemplate.title.font,
        fontsize: randomTemplate.title.fontsize,
        fontcolor: randomTemplate.title.fontcolor,
        bordercolor: randomTemplate.title.bordercolor,
        borderw: randomTemplate.title.borderw,
        box: randomTemplate.title.box,
        boxcolor: randomTemplate.title.boxcolor,
        boxborderw: randomTemplate.title.boxborderw,
        x: "center",
        y: randomTemplate.title.y,
        start_time: 0.0,
        duration: 5,
        fade_in: 0.3,
        fade_out: 0.5
      },
      subtitles: {
        items: inputData.subtitles,
        font: randomTemplate.subtitles.font,
        fontsize: randomTemplate.subtitles.fontsize,
        fontcolor: randomTemplate.subtitles.fontcolor,
        bordercolor: randomTemplate.subtitles.bordercolor,
        borderw: randomTemplate.subtitles.borderw,
        box: randomTemplate.subtitles.box,
        y: randomTemplate.subtitles.y
      },
      generate_thumbnail: true,
      thumbnail_timestamp: 0.5
    }
  ],
  client_meta: inputData.client_meta || {}
};

// Возвращаем результат
return {
  json: {
    // Запрос для video-processor-api
    request_body: requestBody,

    // Метаданные о выбранном шаблоне (для логирования)
    template_used: randomTemplate.name,
    template_description: randomTemplate.description,

    // Оригинальные данные (на случай если понадобятся)
    original_data: inputData
  }
};
