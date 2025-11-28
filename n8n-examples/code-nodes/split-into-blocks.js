// ═══════════════════════════════════════════════════════════════════════════
// 🔧 N8N CODE NODE: Split Video Into Blocks (Intelligent & Configurable)
// ═══════════════════════════════════════════════════════════════════════════
//
// НАЗНАЧЕНИЕ:
// Разбивает длинное видео (транскрипцию + word-level timestamps) на БЛОКИ
// с перекрытиями для последовательной обработки AI агентом
//
// ОСОБЕННОСТИ:
// ✅ Настраиваемое количество блоков (max_blocks)
// ✅ Автоматический расчет оптимального количества блоков
// ✅ Интеллектуальная логика разбивки
// ✅ Перекрытия для сохранения контекста
// ✅ Правильная схема: первый блок с 0, последний без overlap после
//
// ВХОД:
// $input.item.json содержит:
// - text_llm: полная транскрипция видео
// - words_llm: массив {w, s, e} с абсолютными таймкодами
// - video_duration: длительность в секундах
// - duration: ISO8601 формат (PT1H30M0S)
// - duration_ms: миллисекунды
// - language: язык
// - client_meta: метаданные клиента
//
// ВЫХОД:
// Массив блоков для Loop Over Items:
// [
//   {
//     block_id: 1,
//     total_blocks: 3,
//     block_start: 0,
//     block_end: 1890,
//     main_zone_start: 0,
//     main_zone_end: 1800,
//     text_llm: "транскрипция для этого блока...",
//     words_llm: [{w, s, e}, ...],
//     video_duration: 5400,
//     duration: "PT1H30M0S",
//     duration_ms: 5400000,
//     language: "ru",
//     client_meta: {...}
//   },
//   ...
// ]
//
// ═══════════════════════════════════════════════════════════════════════════

const item = $input.item.json;

// ═══════════════════════════════════════════════════════════════════════════
// КОНФИГУРАЦИЯ (настраивается!)
// ═══════════════════════════════════════════════════════════════════════════

const BLOCK_CONFIG = {
	// Максимальное количество блоков (можно настроить!)
	max_blocks: item.client_meta?.max_blocks || 3,

	// Минимальная длительность одного блока в секундах (20 минут)
	min_block_duration: 1200,

	// Перекрытие в секундах (90 сек = 1.5 минуты)
	overlap_seconds: item.client_meta?.overlap_seconds || 90,

	// Минимальная длительность видео для разбивки (30 минут)
	min_video_for_split: 1800
};

// ═══════════════════════════════════════════════════════════════════════════
// ФУНКЦИЯ: Определение стратегии разбивки
// ═══════════════════════════════════════════════════════════════════════════

function determineBlockStrategy(videoDuration, config) {
	// Если видео короче порога - не разбиваем
	if (videoDuration < config.min_video_for_split) {
		return {
			numBlocks: 1,
			overlap: 0,
			blockSize: videoDuration,
			reason: `Видео ${Math.round(videoDuration/60)} мин - обработка целиком (короче ${Math.round(config.min_video_for_split/60)} мин)`
		};
	}

	// Вычисляем оптимальное количество блоков
	// Формула: ceil(duration / (min_block_duration + overlap))
	let numBlocks = Math.ceil(videoDuration / (config.min_block_duration + config.overlap_seconds));

	// Ограничиваем максимумом
	numBlocks = Math.min(numBlocks, config.max_blocks);

	// Если получился 1 блок - убираем overlap
	if (numBlocks === 1) {
		return {
			numBlocks: 1,
			overlap: 0,
			blockSize: videoDuration,
			reason: `Видео ${Math.round(videoDuration/60)} мин - умещается в 1 блок`
		};
	}

	const blockSize = videoDuration / numBlocks;

	return {
		numBlocks: numBlocks,
		overlap: config.overlap_seconds,
		blockSize: blockSize,
		reason: `Видео ${Math.round(videoDuration/60)} мин → ${numBlocks} блоков по ~${Math.round(blockSize/60)} мин`
	};
}

// ═══════════════════════════════════════════════════════════════════════════
// ФУНКЦИЯ: Извлечение текста из диапазона времени
// ═══════════════════════════════════════════════════════════════════════════

function extractTextForRange(words, startTime, endTime) {
	return words
		.filter(w => w.s >= startTime && w.s < endTime)
		.map(w => w.w)
		.join(' ');
}

// ═══════════════════════════════════════════════════════════════════════════
// ФУНКЦИЯ: Извлечение слов из диапазона времени
// ═══════════════════════════════════════════════════════════════════════════

function extractWordsForRange(words, startTime, endTime) {
	return words.filter(w => w.s >= startTime && w.s < endTime);
}

// ═══════════════════════════════════════════════════════════════════════════
// ОСНОВНАЯ ЛОГИКА
// ═══════════════════════════════════════════════════════════════════════════

const videoDuration = item.video_duration || 0;
const words = item.words_llm || [];
const fullText = item.text_llm || '';

// Определяем стратегию
const strategy = determineBlockStrategy(videoDuration, BLOCK_CONFIG);

console.log(`📊 Стратегия разбивки: ${strategy.reason}`);
console.log(`   - Количество блоков: ${strategy.numBlocks}`);
console.log(`   - Перекрытие: ${strategy.overlap} сек`);
console.log(`   - Размер блока: ~${Math.round(strategy.blockSize/60)} мин`);

// ⚠️ ВАЖНО: Если только 1 блок - возвращаем ОРИГИНАЛЬНЫЙ ITEM БЕЗ block_id
// Это позволит AI агенту понять, что видео обрабатывается целиком, а не по блокам
if (strategy.numBlocks === 1) {
	console.log(`✅ Видео обрабатывается целиком (БЕЗ блочной структуры)`);

	// Возвращаем оригинальный item без полей блоков
	return [item];
}

// ═══════════════════════════════════════════════════════════════════════════
// РАЗБИВКА НА БЛОКИ
// ═══════════════════════════════════════════════════════════════════════════

const blocks = [];
const blockSize = strategy.blockSize;
const overlap = strategy.overlap;

for (let i = 0; i < strategy.numBlocks; i++) {
	const isFirst = (i === 0);
	const isLast = (i === strategy.numBlocks - 1);

	// Начало главной зоны (без overlap для первого блока)
	const mainZoneStart = Math.round(i * blockSize);

	// Конец главной зоны
	const mainZoneEnd = Math.round(isLast ? videoDuration : (i + 1) * blockSize);

	// Начало блока (с overlap ДО для всех кроме первого)
	const blockStart = Math.round(isFirst ? 0 : Math.max(0, mainZoneStart - overlap));

	// Конец блока (с overlap ПОСЛЕ для всех кроме последнего)
	const blockEnd = Math.round(isLast ? videoDuration : Math.min(videoDuration, mainZoneEnd + overlap));

	// Извлекаем текст и слова для этого блока
	const blockText = extractTextForRange(words, blockStart, blockEnd);
	const blockWords = extractWordsForRange(words, blockStart, blockEnd);

	blocks.push({
		block_id: i + 1,
		total_blocks: strategy.numBlocks,
		block_start: blockStart,
		block_end: blockEnd,
		main_zone_start: mainZoneStart,
		main_zone_end: mainZoneEnd,
		text_llm: blockText,
		words_llm: blockWords,
		video_duration: videoDuration,
		duration: item.duration,
		duration_ms: item.duration_ms,
		language: item.language,
		client_meta: item.client_meta || {}
	});

	console.log(`   Block ${i+1}/${strategy.numBlocks}:`);
	console.log(`     - Block range: ${Math.round(blockStart/60)}m → ${Math.round(blockEnd/60)}m`);
	console.log(`     - Main zone: ${Math.round(mainZoneStart/60)}m → ${Math.round(mainZoneEnd/60)}m`);
	console.log(`     - Words count: ${blockWords.length}`);
	console.log(`     - Text length: ${blockText.length} chars`);
}

// ═══════════════════════════════════════════════════════════════════════════
// ВОЗВРАТ РЕЗУЛЬТАТА
// ═══════════════════════════════════════════════════════════════════════════

console.log(`✅ Создано ${blocks.length} блоков для последовательной обработки`);

return blocks;
