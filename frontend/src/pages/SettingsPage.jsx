// frontend/src/pages/SettingsPage.jsx
import { useState } from "react";
import { API } from "../services/api";

const SettingsPage = () => {
  const [csvFile, setCsvFile] = useState(null);
  const [message, setMessage] = useState(null);
  const [importing, setImporting] = useState(false);

  const [marketplace, setMarketplace] = useState("Ozon");
  const [parseType, setParseType] = useState("category");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [startMessage, setStartMessage] = useState(null);
  const [startError, setStartError] = useState(null);
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [screenshotMarketplace, setScreenshotMarketplace] = useState("Ozon");
  const [screenshotMessage, setScreenshotMessage] = useState(null);
  const [screenshotError, setScreenshotError] = useState(null);
  const [screenshotUploading, setScreenshotUploading] = useState(false);

  const handleCsvImport = async () => {
    if (!csvFile) {
      setMessage({ type: "error", text: "Выберите CSV-файл." });
      return;
    }

    setImporting(true);
    try {
      const result = await API.importCsv(csvFile);
      setMessage({
        type: "success",
        text: `Импортировано: ${result.inserted}. Ошибок: ${result.errors.length}`,
      });
    } catch (err) {
      setMessage({
        type: "error",
        text: `Ошибка при импорте: ${err.response?.data?.error || err.message}`,
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="p-4 space-y-8">
      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Настройки парсинга</h2>
        <div>
          <label className="block">Маркетплейс</label>
          <select
            value={marketplace}
            onChange={(e) => setMarketplace(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="Ozon">Ozon</option>
            <option value="Wildberries">Wildberries</option>
          </select>
        </div>

        <div>
          <label className="block">Тип запроса</label>
          <select
            value={parseType}
            onChange={(e) => setParseType(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="category">Категория</option>
            <option value="product">Товар</option>
          </select>
        </div>

        <div>
          <label className="block">
            {parseType === "category" ? "Название категории" : "Артикул товара"}
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="border rounded px-2 py-1 w-full"
            placeholder="Например: хлебцы или 1234567"
          />
        </div>

        {parseType === "category" && (
          <div>
            <label className="block">Кол-во товаров (до 50)</label>
            <input
              type="number"
              min="1"
              max="50"
              value={limit}
              onChange={(e) => setLimit(Math.min(50, Math.max(1, parseInt(e.target.value))))}
              className="border rounded px-2 py-1 w-full"
            />
          </div>
        )}

        <button
          onClick={async () => {
            setStartMessage(null);
            setStartError(null);
            try {
              const settings = {
                marketplace,
                type: parseType,
                query,
                limit: parseType === "category" ? limit : 1,
              };
              const result = await API.startProcess(settings);
              setStartMessage(`Успешно: получено ${result.products?.length ?? 0} товаров.`);
            } catch (err) {
              setStartError("Ошибка при запуске процесса: " + (err.response?.data?.error || err.message));
            }
          }}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Запустить анализ
        </button>
        {startMessage && <div className="text-green-600">{startMessage}</div>}
        {startError && <div className="text-red-600">{startError}</div>}
      </div>

      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Импорт CSV</h2>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setCsvFile(e.target.files[0])}
          className="border px-2 py-1 rounded w-full"
        />
        <button
          onClick={handleCsvImport}
          disabled={importing}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          {importing ? "Импортируем..." : "Загрузить CSV"}
        </button>
        {message && (
          <div className={message.type === "error" ? "text-red-600" : "text-green-600"}>{message.text}</div>
        )}
      </div>



      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Импорт из скриншота</h2>

        <div>
          <label className="block">Маркетплейс скриншота</label>
          <select
            value={screenshotMarketplace}
            onChange={e => setScreenshotMarketplace(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="Ozon">Ozon</option>
            <option value="Wildberries">Wildberries</option>
          </select>
        </div>

        <div>
          <label className="block">Скриншот (PNG/JPG)</label>
          <input
            type="file"
            accept="image/png, image/jpeg"
            onChange={e => setScreenshotFile(e.target.files[0])}
            className="border rounded px-2 py-1 w-full"
          />
        </div>

        <button
          onClick={async () => {
            if (!screenshotFile) {
              setScreenshotError("Выберите файл-скриншот.");
              return;
            }
            setScreenshotError(null);
            setScreenshotMessage(null);
            setScreenshotUploading(true);
            try {
              const result = await API.importScreenshot(
                screenshotFile,
                screenshotMarketplace
              );
              setScreenshotMessage("Импортировано: " + JSON.stringify(result));
            } catch (err) {
              setScreenshotError(
                "Ошибка импорта скриншота: " +
                  (err.response?.data?.error || err.message)
              );
            } finally {
              setScreenshotUploading(false);
            }
          }}
          disabled={screenshotUploading}
          className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
        >
          {screenshotUploading ? "Импортируем..." : "Загрузить скриншот"}
        </button>

        {screenshotMessage && (
          <div className="text-green-600">{screenshotMessage}</div>
        )}
        {screenshotError && (
          <div className="text-red-600">{screenshotError}</div>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
