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
// Алгоритм сборки с дедупликацией по OVERLAP:
// 1. Собираем все shorts из всех блоков
// 2. Shorts уже имеют АБСОЛЮТНЫЕ координаты (от AI агента)
// 3. Сортируем по абсолютному start
// 4. ДЕДУПЛИКАЦИЯ: Находим shorts с 80%+ overlap
//    - Если overlap > 80% → это дубликаты одного момента
//    - Из группы выбираем SHORT с МАКСИМАЛЬНОЙ virality_score
//    - Остальные удаляем
//
// РЕЗУЛЬТАТ: Shorts с правильными абсолютными координатами + лучшие по вирусности!
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
//   shorts: [...],  // дубликаты (80%+ overlap) удалены, останы лучшие по virality_score
//   stats: {
//     total_before: 20,
//     total_after: 8,
//     duplicates_removed: 12,
//     blocks_processed: 4,
//     overlap_threshold: 80
//   }
// }
//
// ═══════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 1: Собираем все shorts из всех блоков (уже с абсолютными координатами)
// ═══════════════════════════════════════════════════════════════════════════

const sourceVideoUrl = $json.source_video_url;
const allShorts = [];

// DEBUG: Логируем количество входных items
const inputItems = $input.all();
const debugInfo = {
	input_items_count: inputItems.length,
	blocks_details: []
};

for (const item of inputItems) {
	const blockMetadata = item.json.block_metadata || {};
	const blockId = blockMetadata.block_id || 1;
	const blockStart = blockMetadata.block_start;
	const mainZoneStart = blockMetadata.main_zone_start;
	const mainZoneEnd = blockMetadata.main_zone_end;

	// DEBUG: Показываем ВСЕ ключи в JSON
	const allKeys = Object.keys(item.json);
	const shorts = item.json.shorts || [];

	// DEBUG: Логируем детали блока с РЕАЛЬНЫМИ значениями
	debugInfo.blocks_details.push({
		block_id: blockId,
		block_start: blockStart,
		main_zone_start: mainZoneStart,
		main_zone_end: mainZoneEnd,
		all_json_keys: allKeys,  // ВСЕ ключи в JSON
		block_metadata_received: blockMetadata,  // Весь block_metadata для отладки
		shorts_received: shorts.length,
		shorts_before_filter: shorts.map(s => ({ start: s.start, end: s.end })),
		shorts_after_filter: shorts.length,
		virality_scores: shorts.map(s => s.client_meta?.virality_score || 0)
	});

	// Собираем все shorts (они уже с абсолютными координатами!)
	shorts.forEach(short => {
		const finalShort = {
			...short,
			block_id: blockId,
			source_video_url: sourceVideoUrl
		};
		allShorts.push(finalShort);
	});
}

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 2: Сортируем по абсолютному start
// ═══════════════════════════════════════════════════════════════════════════

allShorts.sort((a, b) => a.start - b.start);

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 3: Расчёт процента overlap между двумя временными интервалами
// ═══════════════════════════════════════════════════════════════════════════

function calculateOverlapPercent(short1, short2) {
	const start1 = short1.start;
	const end1 = short1.end;
	const start2 = short2.start;
	const end2 = short2.end;

	// Находим границы пересечения
	const overlapStart = Math.max(start1, start2);
	const overlapEnd = Math.min(end1, end2);

	// Если нет пересечения
	if (overlapStart >= overlapEnd) {
		return 0;
	}

	// Длительность пересечения
	const overlapDuration = overlapEnd - overlapStart;

	// Длительности shorts
	const duration1 = end1 - start1;
	const duration2 = end2 - start2;

	// Процент overlap относительно МЕНЬШЕГО shorts
	// Если 80% меньшего совпадает с большим → дубликат
	const minDuration = Math.min(duration1, duration2);
	const overlapPercent = (overlapDuration / minDuration) * 100;

	return overlapPercent;
}

// ═══════════════════════════════════════════════════════════════════════════
// ШАГ 4: Дедупликация по OVERLAP (80%+ = дубликат)

const OVERLAP_THRESHOLD = 80; // 80% overlap = дубликат
const deduplicated = [];
const processed = new Set(); // Индексы уже обработанных shorts

for (let i = 0; i < allShorts.length; i++) {
	// Пропускаем если уже обработан
	if (processed.has(i)) {
		continue;
	}

	const current = allShorts[i];
	let bestShort = current;
	let bestScore = current.client_meta?.virality_score || 0;
	const duplicateGroup = [i]; // Индексы shorts в этой группе дубликатов

	// Ищем все shorts с 80%+ overlap с текущим
	for (let j = i + 1; j < allShorts.length; j++) {
		if (processed.has(j)) {
			continue;
		}

		const candidate = allShorts[j];
		const overlap = calculateOverlapPercent(current, candidate);

		// Если overlap > 80% → это дубликат
		if (overlap > OVERLAP_THRESHOLD) {
			duplicateGroup.push(j);

			// Проверяем virality_score
			const candidateScore = candidate.client_meta?.virality_score || 0;
			if (candidateScore > bestScore) {
				bestScore = candidateScore;
				bestShort = candidate;
			}
		}
	}

	// Добавляем лучший short из группы
	deduplicated.push(bestShort);

	// Отмечаем всю группу как обработанную
	duplicateGroup.forEach(idx => processed.add(idx));
}

// ═══════════════════════════════════════════════════════════════════════════
// СТАТИСТИКА
// ═══════════════════════════════════════════════════════════════════════════

const stats = {
	total_before: allShorts.length,
	total_after: deduplicated.length,
	duplicates_removed: allShorts.length - deduplicated.length,
	blocks_processed: inputItems.length,
	overlap_threshold: OVERLAP_THRESHOLD
};

// ═══════════════════════════════════════════════════════════════════════════
// ВОЗВРАТ РЕЗУЛЬТАТА (тот же формат, что от парсера + статистика)
// ═══════════════════════════════════════════════════════════════════════════

return [{
	json: {
		source_video_url: sourceVideoUrl,
		shorts: deduplicated,
		stats: stats,
		debug: debugInfo  // Добавляем debug информацию для диагностики
	}
}];
