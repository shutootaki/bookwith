// eslint.config.js
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import nextPlugin from '@next/eslint-plugin-next';
import importPlugin from 'eslint-plugin-import';
import prettierConfig from 'eslint-config-prettier';
import globals from 'globals';

// __dirname の代替
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default tseslint.config(
  // 0. グローバルな無視設定
  {
    ignores: [
      'node_modules/',
      '.next/',
      'dist/',
    ],
  },

  // 1. 基本設定: ESLint推奨 + TypeScript推奨 + Node/Browserグローバル + カスタムルール
  {
    files: ['**/*.ts', '**/*.tsx'],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      // ...tseslint.configs.recommendedTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        project: true,
        // tsconfigRootDir: __dirname,
      },
      globals: {
        ...globals.node,
        ...globals.browser,
      },
    },
    plugins: {
      import: importPlugin,
    },
    rules: {
      // --- TypeScript カスタムルール ---
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { ignoreRestSiblings: true, argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-var-requires': 'off',
      '@typescript-eslint/no-empty-interface': 'off',
      '@typescript-eslint/no-empty-function': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/ban-ts-comment': 'off',
      '@typescript-eslint/no-explicit-any': 'off',

      // --- import/order ルール (TSファイル内) ---
      'import/order': [
        'error', // Severity
        {       // Options
          alphabetize: { order: 'asc' },
          'newlines-between': 'always',
          groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
          pathGroups: [{ pattern: '@flow/**', group: 'internal' }],
          pathGroupsExcludedImportTypes: ['builtin'],
        },
      ],
      'import/no-anonymous-default-export': 'off',

      // --- その他のカスタムルール (TSファイル内) ---
      'no-empty': 'off',
    },
    settings: {
      // 'import/resolver': { typescript: {} },
    },
  },

  // 2. JavaScript ファイル用の基本設定
  {
    files: ['**/*.{js,mjs,cjs}'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
    plugins: {
      import: importPlugin,
    },
    rules: {
      // --- import/order ルール (JSファイル内) ---
      // ***** ここを修正しました *****
      'import/order': [
        'error', // Severity
        {       // Options (TSファイル用と同じ設定をコピー)
          alphabetize: { order: 'asc' },
          'newlines-between': 'always',
          groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
          pathGroups: [{ pattern: '@flow/**', group: 'internal' }],
          pathGroupsExcludedImportTypes: ['builtin'],
        },
      ],
      // ***** 修正ここまで *****
      'import/no-anonymous-default-export': 'off',
      'no-empty': 'off',
    },
    settings: {
      // 'import/resolver': { node: {} },
    },
  },

  // 3. Next.js 用の設定
  {
    files: ['apps/reader/**/*.{js,jsx,ts,tsx}'],
    plugins: {
      '@next/next': nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      // ...nextPlugin.configs['core-web-vitals'].rules,
    },
    settings: {
      next: {
        rootDir: path.join(__dirname, 'apps/reader'),
      },
    },
  },

  // 4. Prettier 連携 (必ず最後に記述)
  prettierConfig,
);
