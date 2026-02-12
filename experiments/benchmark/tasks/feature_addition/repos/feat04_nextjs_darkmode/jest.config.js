module.exports = {
  testEnvironment: "jsdom",
  moduleNameMapper: {
    "\\.(css|less|scss)$": "<rootDir>/tests/__mocks__/styleMock.js",
  },
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": ["babel-jest", { presets: ["next/babel"] }],
  },
};
