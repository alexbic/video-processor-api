// ═══════════════════════════════════════════════════════════════════════════
// 🔧 N8N CODE NODE: Parse AI Agent Response (Clean JSON or Markdown)
// ═══════════════════════════════════════════════════════════════════════════
//
// НАЗНАЧЕНИЕ:
// Извлекает чистый JSON из ответа AI агента (Claude, OpenAI, etc.)
//
// ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:
// 1. ✅ Чистый JSON (приоритет) - парсится напрямую
// 2. ✅ Markdown блок ```json...``` - для обратной совместимости
//
// ИСПОЛЬЗОВАНИЕ В N8N:
// 1. Вход: $input.item.json.output содержит ответ AI агента
// 2. Выход: массив с одним элементом [{json: parsedObject}]
//
// ═══════════════════════════════════════════════════════════════════════════

const item = $input.item;
const rawOutput = item.json.output;
let cleanJson = null;

// ══════════════════════════════════════════════════════════════════════════
// СТРАТЕГИЯ 1: Попытка парсинга чистого JSON (новый формат, приоритет)
// ══════════════════════════════════════════════════════════════════════════
try {
    cleanJson = JSON.parse(rawOutput);
    console.log("✅ Успешно распарсен чистый JSON (без markdown)");
} catch (directParseError) {
    console.log("⚠️ Чистый JSON не распарсился, пробуем markdown формат...");

    // ══════════════════════════════════════════════════════════════════════
    // СТРАТЕГИЯ 2: Извлечение из markdown блока ```json...```
    // (для обратной совместимости со старыми промтами)
    // ══════════════════════════════════════════════════════════════════════
    const markdownMatch = rawOutput.match(/```json\s*([\s\S]*?)\s*```/);

    if (markdownMatch && markdownMatch[1]) {
        try {
            cleanJson = JSON.parse(markdownMatch[1]);
            console.log("✅ Успешно извлечен JSON из markdown блока");
        } catch (markdownParseError) {
            console.error("❌ Ошибка парсинга JSON из markdown:", markdownParseError);
            cleanJson = {
                error: 'Failed to parse JSON content from markdown block',
                raw_output: rawOutput,
                parse_error: markdownParseError.message
            };
        }
    } else {
        // ══════════════════════════════════════════════════════════════════
        // СТРАТЕГИЯ 3: Если ни один формат не подошёл - возвращаем ошибку
        // ══════════════════════════════════════════════════════════════════
        console.error("❌ Не найден ни чистый JSON, ни markdown блок");
        console.error("Первые 200 символов ответа:", rawOutput.substring(0, 200));

        cleanJson = {
            error: 'Invalid AI response format',
            details: 'Response is neither valid JSON nor markdown JSON block',
            raw_output: rawOutput,
            direct_parse_error: directParseError.message
        };
    }
}

// ══════════════════════════════════════════════════════════════════════════
// ВАЛИДАЦИЯ РЕЗУЛЬТАТА
// ══════════════════════════════════════════════════════════════════════════
if (cleanJson && !cleanJson.error) {
    // Проверяем базовую структуру ответа
    if (Array.isArray(cleanJson)) {
        console.log(`✅ Распарсен массив с ${cleanJson.length} элементами`);
    } else if (cleanJson.shorts && Array.isArray(cleanJson.shorts)) {
        console.log(`✅ Распарсен объект с ${cleanJson.shorts.length} shorts`);
    } else {
        console.warn("⚠️ Нестандартная структура JSON (нет массива shorts)");
    }
}

// ══════════════════════════════════════════════════════════════════════════
// ВОЗВРАТ РЕЗУЛЬТАТА
// ══════════════════════════════════════════════════════════════════════════
// Возвращаем массив с ОДНИМ элементом для n8n
return [{ json: cleanJson }];
