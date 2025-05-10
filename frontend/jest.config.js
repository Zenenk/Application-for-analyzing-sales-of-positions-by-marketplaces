module.exports = {
    // Используем jsdom для эмуляции DOM в тестах React
    testEnvironment: "jsdom",
    // Используем babel-jest для трансформации JS/JSX (ES6+)
    transform: {
      "^.+\\.[jt]sx?$": "babel-jest"
    },
    // Добавляем исключение для модулей с ES6-импортами (например, axios) для трансформации
    transformIgnorePatterns: [
      "/node_modules/(?!axios)"  // трансформировать axios, игнорируя остальные
    ],
    // При необходимости можно добавить моки или мапперы модулей
    // moduleNameMapper: { "^axios$": "axios/dist/browser/axios.cjs" } // пример, не обязателен при наличии transformIgnorePatterns
  };
  