// ═══════════════════════════════════════════════════════════════════════════
// 🔧 N8N CODE NODE: Deduplicate Shorts After Block Processing
// ═══════════════════════════════════════════════════════════════════════════
//
// НАЗНАЧЕНИЕ:
// Объединяет результаты обработки нескольких блоков и удаляет дубликаты
// СОБИРАЕТ видео обратно в ПРАВИЛЬНУЮ ПОСЛЕДОВАТЕЛЬНОСТЬ
//
// ПРОБЛЕМА:
// split-into-blocks разбивает видео на куски с overlap:
// - Block 1: 0-1890 (main_zone: 0-1800)
// - Block 2: 1710-3510 (main_zone: 1710-3420) 
// - Block 3: 3330-5130 (main_zone: 3330-5040)
// 
// Каждый блок AI обрабатывает, создаёт shorts. Но это куски одного видео!
// Нужно собрать их обратно, учитывая overlap-zones.
//
// ═══════════════════════════════════════════════════════════════════════════
// РЕШЕНИЕ (ЭТАП 1):
// Алгоритм сборки с правильными абсолютными координатами:
// 1. Группируем shorts по block_id
// 2. Для каждого short: пересчитываем на абсолютные координаты (block_start + relative)
// 3. Фильтруем по main_zone каждого блока (берём только shorts, начинающиеся в main_zone)
// 4. Сортируем блоки по block_id → собираем в правильном порядке
// 5. Сортируем all shorts по абсолютному start → хронологический порядок
// 6. Удаляем ТОЧНЫЕ дубликаты (одинаковый start+end)
// 
// РЕЗУЛЬТАТ: Shorts с правильными АБСОЛЮТНЫМИ временными метками!
//
// СЛЕДУЮЩИЙ ШАГ (потом): Анализ дубликатов по КОНТЕНТУ (текст, тема, overlap %)
// Когда у нас будут правильные временные метки, сможем найти shorts которые:
// - Сильно пересекаются (напр. 80%+ overlap)
// - Имеют похожий текст (близкие subtitles)
// - Ловят один и тот же момент (разные AI интерпретации)
//
// ═══════════════════════════════════════════════════════════════════════════
//
// ВХОД:
// Массив items от parse-ai-response (после Loop Over Items):
// [
//   {
//     json: {
//       source_video_url: "...",
//       shorts: [...],
//       block_metadata: {
//         block_start: 0,
//         block_end: 1890,
//         main_zone_start: 0,
//         main_zone_end: 1800,
//         block_id: 1,
//         total_blocks: 3
//       }
//     }
//   },
//   ...
// ]
//
// ВЫХОД:
// {
//   source_video_url: "...",
//   shorts: [...],  // собранные в правильном порядке, дубликаты в overlap удалены
//   stats: {
//     total_before: 20,
//     total_after: 5,
//     duplicates_removed: 15,
//     blocks_processed: 4
//   }
// }
//
// ═══════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 1: Собираем shorts по блокам и пересчитываем на абсолютные координаты
// ═══════════════════════════════════════════════════════════════════════════

const sourceVideoUrl = $json.source_video_url;
const blockMap = new Map(); // block_id → { metadata, shorts }

for (const item of $input.all()) {
	const blockMetadata = item.json.block_metadata || { block_id: 1 };
	const blockId = blockMetadata.block_id || 1;
	const shorts = item.json.shorts || [];
	const blockStart = blockMetadata.block_start || 0;
	const mainZoneStart = blockMetadata.main_zone_start || blockStart;
	const mainZoneEnd = blockMetadata.main_zone_end || blockMetadata.block_end;

	// Пересчитываем shorts на абсолютные координаты И фильтруем по main_zone
	const processedShorts = shorts
		.map(short => {
			const absoluteStart = blockStart + short.start;
			const absoluteEnd = blockStart + short.end;

			return {
				...short,
				// Сохраняем оригинальные (относительные) координаты
				original_start: short.start,
				original_end: short.end,
				// Устанавливаем абсолютные координаты
				start: absoluteStart,
				end: absoluteEnd
			};
		})
		// Фильтруем: берём shorts, которые НАЧИНАЮТСЯ в main_zone
		.filter(short => short.start >= mainZoneStart && short.start < mainZoneEnd);

	blockMap.set(blockId, {
		metadata: blockMetadata,
		shorts: processedShorts
	});
}

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 2: Сортируем блоки по block_id и собираем в правильном порядке
// ═══════════════════════════════════════════════════════════════════════════

const sortedBlockIds = Array.from(blockMap.keys()).sort((a, b) => a - b);
const allShorts = [];

for (const blockId of sortedBlockIds) {
	const { metadata, shorts } = blockMap.get(blockId);

	shorts.forEach(short => {
		// Добавляем метаданные
		const finalShort = {
			...short,
			block_id: blockId,
			source_video_url: sourceVideoUrl
		};

		allShorts.push(finalShort);
	});
}

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 3: Сортируем по абсолютному start (должны быть в хронологическом порядке)
// ═══════════════════════════════════════════════════════════════════════════

allShorts.sort((a, b) => a.start - b.start);

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 4: Дедупликация по ТОЧНОМУ совпадению координат (временное пересечение)
// ВНИМАНИЕ: Это ВРЕМЕННАЯ дедупликация!
// Полная дедупликация по контенту (текст, тема) будет позже.
// Здесь удаляем только АБСОЛЮТНО ИДЕНТИЧНЫЕ shorts (одинаковый start и end)
// ═══════════════════════════════════════════════════════════════════════════

const deduplicated = [];
const seen = new Set();

for (let i = 0; i < allShorts.length; i++) {
	const current = allShorts[i];
	
	// Уникальный ключ по абсолютным координатам
	const key = `${current.start.toFixed(2)}_${current.end.toFixed(2)}`;
	
	// Если уже встречали эти ТОЧНЫЕ координаты → полный дубликат, пропускаем
	if (seen.has(key)) {
		continue;
	}
	
	seen.add(key);
	deduplicated.push(current);
}

// ═══════════════════════════════════════════════════════════════════════════
// СТАТИСТИКА
// ═══════════════════════════════════════════════════════════════════════════

const stats = {
	total_before: allShorts.length,
	total_after: deduplicated.length,
	duplicates_removed: allShorts.length - deduplicated.length,
	blocks_processed: blockMap.size
};

// ═══════════════════════════════════════════════════════════════════════════
// ВОЗВРАТ РЕЗУЛЬТАТА (тот же формат, что от парсера + статистика)
// ═══════════════════════════════════════════════════════════════════════════

return [{
	json: {
		source_video_url: sourceVideoUrl,
		shorts: deduplicated,
		stats: stats
	}
}];
